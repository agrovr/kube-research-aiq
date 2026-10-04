import asyncio
import json

import pytest

from kube_research_aiq.models import ResearchDepth, Section
from kube_research_aiq.retrieval import Hit
from kube_research_aiq.writer import (
    ModelWriter,
    OfflineWriter,
    cited_numbers,
    gerund,
    subject_of,
    title_of,
)


@pytest.mark.parametrize(
    ("query", "title"),
    [
        ("Compare Kubernetes deployment strategies for AI agents and recommend an architecture.",
         "Kubernetes deployment strategies for AI agents"),
        ("Evaluate how to secure and observe an LLM platform",
         "Securing and observing an LLM platform"),
        ("What is KEDA?", "KEDA"),
        ("how should we run Postgres?", "Running Postgres"),
        ("GPU scheduling trade-offs", "GPU scheduling trade-offs"),
    ],
)
def test_titles_drop_the_instruction(query, title):
    assert title_of(query) == title


def test_gerunds():
    assert [gerund(w) for w in ["secure", "run", "deploy", "tie", "see"]] == [
        "securing", "running", "deploying", "tying", "seeing"]


def test_subject_never_empty():
    assert subject_of("Explain") == "Explain"


def test_offline_plans(settings):
    writer = OfflineWriter(settings)
    deep = asyncio.run(writer.plan("Compare queue options for agents", ResearchDepth.deep))
    assert [s.title for s in deep] == ["Context", "Approaches", "Trade-offs", "Operating it",
                                       "Recommendation"]
    assert "queue options for agents" in deep[0].question
    shallow = asyncio.run(writer.plan("What is KEDA?", ResearchDepth.shallow))
    assert [s.title for s in shallow] == ["Answer"]


def test_offline_plan_respects_section_limit(settings):
    writer = OfflineWriter(settings.model_copy(update={"max_report_sections": 3}))
    assert len(asyncio.run(writer.plan("Compare things", ResearchDepth.deep))) == 3


def test_offline_draft_cites_every_sentence_and_avoids_repeats(settings):
    writer = OfflineWriter(settings)
    hits = [(1, Hit("A", None, "Queues hold work for workers. Workers scale on queue depth.",
                    "knowledge", 2.0, "a")),
            (2, Hit("B", None, "Redis lists make simple queues for background workers.",
                    "knowledge", 1.0, "b"))]
    section = Section(title="Answer", question="How do queues and workers fit together?")
    used: set[str] = set()
    body = asyncio.run(writer.draft("queues and workers", section, hits, used))
    sentences = [s for s in body.split("] ") if s]
    assert all("[" in s or s.endswith("]") for s in sentences)
    assert cited_numbers(body, {1, 2}) and used
    again = asyncio.run(writer.draft("queues and workers", section, hits, used))
    assert "did not cover" in again or not (set(again.split(" [")) & set(body.split(" [")))


def test_cited_numbers_ignores_unknown_sources():
    assert cited_numbers("A [2]. B [9]. C [2] and [1].", {1, 2}) == [2, 1]


class FakeLlm:
    def __init__(self, replies):
        self.replies = list(replies)
        self.prompts = []

    async def complete(self, *, model, system, user, max_tokens=900):
        self.prompts.append((model, system, user))
        return self.replies.pop(0)


def test_model_writer_parses_a_json_plan(settings):
    plan = {"sections": [{"title": "Background", "question": "Why queues?"},
                         {"title": "Choice", "question": "Which queue?"}]}
    llm = FakeLlm(["Here you go:\n" + json.dumps(plan)])
    sections = asyncio.run(ModelWriter(settings, llm).plan("Compare queues", ResearchDepth.deep))
    assert [s.title for s in sections] == ["Background", "Choice"]


def test_model_writer_falls_back_when_the_plan_is_unusable(settings):
    llm = FakeLlm(["I would rather not"])
    sections = asyncio.run(ModelWriter(settings, llm).plan("Compare queues", ResearchDepth.deep))
    assert sections[0].title == "Context"


def test_model_writer_sends_numbered_sources(settings):
    llm = FakeLlm(["Queues decouple work [3]."])
    hit = Hit("Redis queues", None, "LMOVE moves items.", "knowledge", 1.0, "r")
    body = asyncio.run(ModelWriter(settings, llm).draft(
        "queues", Section(title="Answer", question="?"), [(3, hit)], set()))
    assert body == "Queues decouple work [3]."
    assert "[3] Redis queues\nLMOVE moves items." in llm.prompts[0][2]
