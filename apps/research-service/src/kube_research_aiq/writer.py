"""Planning and writing for research reports.

Two writers share one interface:

* ``OfflineWriter`` needs no model. It plans from templates and writes by selecting the
  sentences from retrieved sources that best answer each question, citing every one. CI, demos and
  clusters without credentials get real, traceable reports this way.
* ``ModelWriter`` sends the same plan, sources and questions to an OpenAI-compatible model and
  asks for prose that cites the numbered sources. It falls back to the offline plan if the model's
  plan can't be parsed.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from kube_research_aiq.llm import LlmClient
from kube_research_aiq.models import ResearchDepth, Section
from kube_research_aiq.retrieval import Hit, tokenize
from kube_research_aiq.settings import Settings

LEADING_PHRASES = re.compile(
    r"^(please\s+)?(can you\s+|could you\s+)?(help me\s+)?"
    r"(compare|evaluate|explain|describe|outline|investigate|research|analy[sz]e|assess|review|"
    r"summari[sz]e|recommend|design|propose|tell me about|what is|what are|what's|"
    r"why do|why does|why is|why are)\s+",
    re.IGNORECASE,
)
SENTENCE = re.compile(r"(?<=[.!?])\s+(?=[A-Za-z0-9])")
CITED_SENTENCE = re.compile(r"(?<=\])\s+(?=[A-Z0-9])")
TRAILING_ASKS = re.compile(
    r",?\s+(and|then)\s+(recommend|suggest|propose|choose|pick|explain|outline|describe|"
    r"summari[sz]e|design|list)\b.*$",
    re.IGNORECASE,
)
CITATION = re.compile(r"\[(\d{1,2})\]")


HOW_TO = re.compile(
    r"^(how to|how do i|how do we|how should i|how should we|how can i|how can we)\s+",
    re.IGNORECASE,
)
VOWELS = set("aeiou")


def gerund(verb: str) -> str:
    """secure → securing, run → running, deploy → deploying."""
    word = verb.lower()
    if word.endswith("ie"):
        return word[:-2] + "ying"
    if word.endswith("e") and not word.endswith(("ee", "ye", "oe")):
        return word[:-1] + "ing"
    if (len(word) <= 4 and len(word) >= 3 and word[-1] not in VOWELS | set("wxy")
            and word[-2] in VOWELS and word[-3] not in VOWELS):
        return word + word[-1] + "ing"
    return word + "ing"


def subject_of(query: str) -> str:
    """The topic of a question as a noun phrase, with the instruction words removed."""
    text = " ".join(query.strip().split())
    previous = None
    while text != previous:  # "Evaluate how to …" needs two passes
        previous = text
        how_to = HOW_TO.match(text)
        if how_to:
            # "how to secure and observe X" → "securing and observing X"
            words = text[how_to.end():].split()
            if words:
                words[0] = gerund(words[0])
                if len(words) > 2 and words[1].lower() in ("and", "or"):
                    words[2] = gerund(words[2])
            text = " ".join(words)
            break
        text = LEADING_PHRASES.sub("", text, count=1).strip()
    text = TRAILING_ASKS.sub("", text).rstrip(" ?.!,")
    return text or query.strip()


def title_of(query: str) -> str:
    subject = subject_of(query)
    first = re.split(r"(?<=[a-z])\.\s|;\s|\?\s", subject)[0]
    first = first[:1].upper() + first[1:]
    return first if len(first) <= 90 else first[:87].rsplit(" ", 1)[0] + "…"


@dataclass(frozen=True)
class Facet:
    title: str
    question: str  # shown to people; {subject} is filled in
    terms: str  # extra retrieval terms that steer each section toward its angle


DEEP_FACETS = (
    Facet("Context", "Which goals and constraints shape {subject}?",
          "requirements constraints asynchronous workload"),
    Facet("Approaches", "Which approaches and building blocks are available for {subject}?",
          "options approaches deployment architecture components"),
    Facet("Trade-offs", "What are the trade-offs, risks and costs of those approaches?",
          "tradeoffs risks cost reliability failure"),
    Facet("Operating it", "How is it scaled, secured and observed in production?",
          "autoscaling security observability metrics operations"),
    Facet("Recommendation", "What should a team adopt first, and what can wait?",
          "production start first recommend default"),
)

DEFINITION = re.compile(r"^\S+(\s+\S+)?\s+(is|are)\s+(a|an|the)\b", re.IGNORECASE)
ADVICE = re.compile(r"\b(should|keep|use|avoid|prefer|start|make|lets|let|cap|limit|need)\b", re.I)


class OfflineWriter:
    name = "offline"

    def __init__(self, settings: Settings):
        self.settings = settings

    async def plan(self, query: str, depth: ResearchDepth) -> list[Section]:
        subject = subject_of(query)
        if depth == ResearchDepth.shallow:
            return [Section(title="Answer", question=query.strip())]
        facets = DEEP_FACETS[: self.settings.max_report_sections]
        phrase = subject
        return [Section(title=f.title, question=f.question.format(subject=phrase)) for f in facets]

    def search_query(self, query: str, section: Section, depth: ResearchDepth) -> str:
        if depth == ResearchDepth.shallow:
            return query
        facet = next((f for f in DEEP_FACETS if f.title == section.title), None)
        subject = subject_of(query)
        # The subject is repeated so it outweighs the facet's steering terms.
        return f"{subject} {subject} {facet.terms if facet else section.question}"

    async def draft(self, query: str, section: Section, sources: list[tuple[int, Hit]],
                    used: set[str]) -> str:
        """Pick the sentences that best match the question and cite each one."""
        focus = set(tokenize(f"{query} {section.question}"))
        lead = tokenize(subject_of(query))[:1]
        candidates: list[tuple[float, int, int, str]] = []
        for rank, (number, hit) in enumerate(sources):
            for position, sentence in enumerate(SENTENCE.split(hit.text)):
                sentence = sentence.strip()
                if len(sentence) < 40 or sentence in used:
                    continue
                overlap = len(focus & set(tokenize(sentence)))
                score = overlap + 0.6 / (rank + 1) + (0.3 if position == 0 else 0.0)
                if section.title == "Recommendation" and ADVICE.search(sentence):
                    score += 1.5
                if lead and tokenize(sentence)[:1] == lead:
                    score += 0.8  # a sentence about the subject itself
                    if DEFINITION.match(sentence):
                        score += 0.7  # "KEDA is a …" answers "What is KEDA?"
                candidates.append((score, rank, position, sentence + f" [{number}]"))
        if not candidates:
            return "The sources gathered for this question did not cover it directly."
        limit = {"Answer": 5, "Recommendation": 4}.get(section.title, 3)
        chosen = sorted(candidates, key=lambda c: (-c[0], c[1], c[2]))[:limit]
        for item in chosen:
            used.add(item[3].rsplit(" [", 1)[0])
        if section.title == "Recommendation":
            return "\n".join(f"- {c[3]}" for c in chosen)
        if section.title != "Answer":
            # Present the chosen sentences in source order so the paragraph reads naturally.
            chosen.sort(key=lambda c: (c[1], c[2]))
        return " ".join(c[3] for c in chosen)

    async def summarize(self, query: str, sections: list[Section]) -> list[str]:
        if len(sections) < 2:
            return []  # a single answer is its own summary
        findings = []
        for section in sections:
            first_line = section.body.strip().splitlines()[0].lstrip("- ").strip()
            first = CITED_SENTENCE.split(first_line)[0].strip()
            if first and "did not cover" not in first:
                findings.append(first)
        return findings[:5]


class ModelWriter:
    name = "model"

    def __init__(self, settings: Settings, llm: LlmClient | None = None):
        self.settings = settings
        self.llm = llm or LlmClient(settings)
        self.fallback = OfflineWriter(settings)

    def _model(self, depth: ResearchDepth) -> str:
        deep = depth == ResearchDepth.deep
        return self.settings.deep_model if deep else self.settings.shallow_model

    async def plan(self, query: str, depth: ResearchDepth) -> list[Section]:
        if depth == ResearchDepth.shallow:
            return await self.fallback.plan(query, depth)
        count = self.settings.max_report_sections
        reply = await self.llm.complete(
            model=self.settings.classifier_model,
            system=(
                "You plan research reports. Reply with JSON only: "
                '{"sections": [{"title": "...", "question": "..."}]}. '
                f"Use 3 to {count} sections. Titles are two or three words. Each question is one "
                "specific sentence a researcher could search for. End with a recommendation."
            ),
            user=query,
            max_tokens=500,
        )
        try:
            match = re.search(r"\{.*\}", reply, re.DOTALL)
            data = json.loads(match.group(0) if match else reply)
            sections = [
                Section(title=str(s["title"])[:60], question=str(s["question"])[:300])
                for s in data["sections"]
                if s.get("title") and s.get("question")
            ][:count]
        except (ValueError, KeyError, TypeError, AttributeError):
            sections = []
        return sections if len(sections) >= 2 else await self.fallback.plan(query, depth)

    def search_query(self, query: str, section: Section, depth: ResearchDepth) -> str:
        if depth == ResearchDepth.shallow:
            return query
        return f"{section.question} {subject_of(query)}"[:400]

    async def draft(self, query: str, section: Section, sources: list[tuple[int, Hit]],
                    used: set[str]) -> str:
        listing = "\n\n".join(f"[{n}] {hit.title}\n{hit.text}" for n, hit in sources)
        length = "three short paragraphs" if section.title == "Answer" else "one or two paragraphs"
        return await self.llm.complete(
            model=self._model(ResearchDepth.deep if section.title != "Answer" else
                              ResearchDepth.shallow),
            system=(
                "You write one section of a research report. Use only the numbered sources. "
                "Cite every factual sentence with its source number in square brackets, like [2]. "
                f"Write {length} of plain prose without a heading. If the sources do not answer "
                "the question, say so."
            ),
            user=f"Report topic: {query}\n\nSection: {section.title}\nQuestion: {section.question}"
                 f"\n\nSources:\n{listing}",
        )

    async def summarize(self, query: str, sections: list[Section]) -> list[str]:
        body = "\n\n".join(f"## {s.title}\n{s.body}" for s in sections)
        reply = await self.llm.complete(
            model=self.settings.shallow_model,
            system=(
                "List the three to five most important findings of this report as bullet points "
                "starting with '- '. Keep each under 30 words and keep the [n] citations."
            ),
            user=f"Topic: {query}\n\n{body}",
            max_tokens=400,
        )
        findings = [line.lstrip("-•* ").strip() for line in reply.splitlines()
                    if line.strip().startswith(("-", "•", "*"))]
        return findings[:5] or await self.fallback.summarize(query, sections)


def cited_numbers(text: str, valid: set[int]) -> list[int]:
    seen: list[int] = []
    for match in CITATION.finditer(text):
        number = int(match.group(1))
        if number in valid and number not in seen:
            seen.append(number)
    return seen


def make_writer(settings: Settings) -> OfflineWriter | ModelWriter:
    return ModelWriter(settings) if settings.uses_model else OfflineWriter(settings)
