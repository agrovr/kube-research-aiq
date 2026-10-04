import asyncio
import json

import httpx
import pytest

from kube_research_aiq.llm import LlmClient
from kube_research_aiq.models import (
    JobStatus,
    ResearchDepth,
    ResearchJob,
    ResearchRequest,
    Stage,
)
from kube_research_aiq.researcher import ResearchRunner, choose_depth
from kube_research_aiq.writer import ModelWriter

DEEP_QUERY = "Compare Kubernetes deployment strategies for AI research agents."


def new_job(store, query=DEEP_QUERY, depth=ResearchDepth.auto):
    return store.create(ResearchJob(request=ResearchRequest(query=query, depth=depth)))


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        (DEEP_QUERY, ResearchDepth.deep),
        ("What is a StatefulSet?", ResearchDepth.shallow),
        ("How do probes work", ResearchDepth.shallow),
        ("Should we self-host models? What about GPUs? And cost?", ResearchDepth.deep),
    ],
)
def test_auto_routing(query, expected):
    assert choose_depth(query, ResearchDepth.auto)[0] == expected


def test_requested_depth_wins():
    assert choose_depth(DEEP_QUERY, ResearchDepth.shallow)[0] == ResearchDepth.shallow


def test_deep_dive_produces_a_cited_report(store, runner):
    job = asyncio.run(runner.run(new_job(store).id))
    assert job.status == JobStatus.succeeded
    assert job.selected_depth == ResearchDepth.deep
    assert job.progress == 1.0 and job.stage == Stage.surface
    assert len(job.sections) == 5 and job.summary
    ids = [s.id for s in job.sources]
    assert ids == list(range(1, len(ids) + 1))  # numbered 1..n without gaps
    assert len({s.title for s in job.sources}) == len(ids)  # one number per document
    for section in job.sections:
        assert section.body and set(section.source_ids) <= set(ids)
    assert job.metadata["citation_coverage"] == 1.0
    assert job.report.startswith("# Kubernetes deployment strategies for AI research agents")
    assert "## Sources" in job.report and "Written offline" in job.report
    stages = [e.stage for e in job.events if e.message.endswith("…")]
    assert stages == list(Stage)
    assert set(job.metadata["stage_seconds"]) == {s.value for s in Stage}


def test_shallow_dive_has_one_answer(store, runner):
    job = asyncio.run(runner.run(new_job(store, "What is KEDA?").id))
    assert job.selected_depth == ResearchDepth.shallow
    assert [s.title for s in job.sections] == ["Answer"]
    assert "KEDA" in job.sections[0].body


def test_progress_is_saved_as_the_dive_advances(store, settings):
    seen = []

    def observe(stage, seconds):
        seen.append((stage, store.get(job_id).progress))

    job_id = new_job(store).id
    asyncio.run(ResearchRunner(settings, store, on_stage=observe).run(job_id))
    assert [stage for stage, _ in seen] == list(Stage)
    progress = [p for _, p in seen]
    assert progress == sorted(progress) and progress[-1] == 1.0


def test_cancellation_stops_at_the_next_checkpoint(store, settings):
    job_id = new_job(store).id

    def cancel_after_plan(stage, seconds):
        if stage == Stage.plan:
            stored = store.get(job_id)
            stored.status = JobStatus.cancelled
            store.save(stored)

    job = asyncio.run(ResearchRunner(settings, store, on_stage=cancel_after_plan).run(job_id))
    assert job.status == JobStatus.cancelled
    assert job.report is None
    assert store.get(job_id).status == JobStatus.cancelled


def test_a_cancelled_job_is_not_run(store, runner):
    job = new_job(store)
    job.status = JobStatus.cancelled
    store.save(job)
    assert asyncio.run(runner.run(job.id)).attempts == 0


def test_retries_start_clean(store, runner):
    job_id = new_job(store).id
    first = asyncio.run(runner.run(job_id))
    second = asyncio.run(runner.run(job_id))
    assert second.attempts == 2
    assert [s.id for s in second.sources] == [s.id for s in first.sources]


def test_model_failures_mark_the_job_failed(store, settings):
    def broken(request):
        return httpx.Response(503)

    keyed = settings.model_copy(update={"provider": "nvidia", "nvidia_api_key": "test"})
    writer = ModelWriter(keyed, LlmClient(keyed, transport=httpx.MockTransport(broken)))
    job = asyncio.run(ResearchRunner(keyed, store, writer=writer).run(new_job(store).id))
    assert job.status == JobStatus.failed
    assert "HTTP 503" in job.error
    assert job.events[-1].level == "error"


def test_model_writer_end_to_end(store, settings):
    def reply(request):
        body = json.loads(request.content)
        system = body["messages"][0]["content"]
        if "plan research reports" in system:
            content = json.dumps({"sections": [
                {"title": "Scaling", "question": "How should workers scale?"},
                {"title": "Recommendation", "question": "What first?"}]})
        elif "findings" in system:
            content = "- Scale on queue depth [1].\n- Start small [2]."
        else:
            content = "Workers should scale on queue depth [1] and start small [2]."
        return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})

    keyed = settings.model_copy(update={"provider": "nvidia", "nvidia_api_key": "test"})
    llm = LlmClient(keyed, transport=httpx.MockTransport(reply))
    runner = ResearchRunner(keyed, store, writer=ModelWriter(keyed, llm))
    job = asyncio.run(runner.run(new_job(store).id))
    assert job.status == JobStatus.succeeded, job.error
    assert [s.title for s in job.sections] == ["Scaling", "Recommendation"]
    assert job.summary == ["Scale on queue depth [1].", "Start small [2]."]
    assert job.sections[0].source_ids == [1, 2]
    assert job.metadata["writer"] == "model"
    assert "Written offline" not in job.report
