"""The research pipeline: survey → plan → descend → draft → surface.

Every stage records a timeline event and a progress value on the job and saves it, so the API,
the dashboard stream and the worker heartbeat all see the run advance. Between steps the runner
re-reads the job, so a cancellation from the API stops the dive at the next checkpoint.
"""

from __future__ import annotations

import asyncio
import re
import time
from collections.abc import Callable

from kube_research_aiq.llm import LlmError
from kube_research_aiq.models import (
    JobStatus,
    ResearchDepth,
    ResearchJob,
    Source,
    Stage,
    now,
)
from kube_research_aiq.retrieval import Hit, Retriever
from kube_research_aiq.settings import Settings
from kube_research_aiq.store import JobStore
from kube_research_aiq.writer import (
    ModelWriter,
    OfflineWriter,
    cited_numbers,
    make_writer,
    title_of,
)

DEEP_SIGNALS = re.compile(
    r"\b(compare|comparison|versus|vs\.?|evaluate|trade-?offs?|architecture|strategy|strategies|"
    r"design|recommend|pros and cons|options|alternatives|in depth|deep dive|plan for|roadmap)\b",
    re.IGNORECASE,
)
SHALLOW_SIGNALS = re.compile(
    r"^\s*(what is|what are|what's|define|who|when|which)\b", re.IGNORECASE
)

# Progress at the end of each stage. Descend and draft fill their share step by step.
STAGE_END = {
    Stage.survey: 0.08,
    Stage.plan: 0.18,
    Stage.descend: 0.5,
    Stage.draft: 0.9,
    Stage.surface: 1.0,
}


class Cancelled(Exception):
    pass


StageObserver = Callable[[Stage, float], None]


def choose_depth(query: str, requested: ResearchDepth) -> tuple[ResearchDepth, str]:
    if requested != ResearchDepth.auto:
        return requested, f"{requested.value.capitalize()} dive requested."
    words = len(query.split())
    signal = DEEP_SIGNALS.search(query)
    if signal:
        return ResearchDepth.deep, f'Auto-routed deep: the question asks to "{signal.group(0)}".'
    if words > 28 or query.count("?") > 1:
        return ResearchDepth.deep, "Auto-routed deep: the question has several parts."
    if SHALLOW_SIGNALS.search(query):
        return ResearchDepth.shallow, "Auto-routed shallow: a direct, factual question."
    return ResearchDepth.shallow, "Auto-routed shallow: a focused question."


class ResearchRunner:
    def __init__(
        self,
        settings: Settings,
        store: JobStore,
        retriever: Retriever | None = None,
        writer: OfflineWriter | ModelWriter | None = None,
        on_stage: StageObserver | None = None,
    ):
        self.settings = settings
        self.store = store
        self.retriever = retriever or Retriever(settings)
        self.writer = writer or make_writer(settings)
        self.on_stage = on_stage

    async def run(self, job_id: str) -> ResearchJob:
        job = self.store.get(job_id)
        if not job:
            raise ValueError(f"job {job_id} does not exist")
        if job.status == JobStatus.cancelled:
            return job

        job.status = JobStatus.running
        job.attempts += 1
        job.error = None
        job.started_at = now()
        job.finished_at = None
        job.progress = 0.0
        job.stage = None
        job.plan, job.sections, job.summary, job.sources, job.report = [], [], [], [], None
        job.metadata.pop("stage_seconds", None)
        job.title = job.title or title_of(job.request.query)
        job.metadata.update(writer=self.writer.name, retrieval=self.retriever.origins)
        if job.attempts > 1:
            job.log(f"Attempt {job.attempts} of {self.settings.max_attempts}.", stage=None)
        self.store.save(job)

        try:
            await self._dive(job)
        except Cancelled:
            job.status = JobStatus.cancelled
            job.log("Dive cancelled.", level="warn")
        except (LlmError, ValueError, RuntimeError) as exc:
            job.status = JobStatus.failed
            job.error = str(exc)
            job.log(f"Dive failed: {exc}", level="error")
        else:
            job.status = JobStatus.succeeded
            job.progress = 1.0
            count = len(job.sources)
            job.log(f"Surfaced with {count} source{'s' if count != 1 else ''} "
                    f"in {job.duration_seconds:.1f}s.")
        job.finished_at = now()
        self.store.save(job)
        return job

    # -- stages -------------------------------------------------------------------------------

    async def _dive(self, job: ResearchJob) -> None:
        query = job.request.query

        stamp = self._enter(job, Stage.survey)
        depth, reason = choose_depth(query, job.request.depth)
        job.selected_depth = depth
        job.metadata["route_reason"] = reason
        job.log(reason)
        await self._pace()
        self._leave(job, Stage.survey, stamp)

        stamp = self._enter(job, Stage.plan)
        sections = await self.writer.plan(query, depth)
        job.sections = sections
        job.plan = [s.question for s in sections]
        job.log(f"Planned {len(sections)} question{'s' if len(sections) != 1 else ''}.")
        await self._pace()
        self._leave(job, Stage.plan, stamp)

        stamp = self._enter(job, Stage.descend)
        gathered: dict[int, list[tuple[int, Hit]]] = {}
        registry: dict[str, Source] = {}
        for index, section in enumerate(sections):
            self._checkpoint(job)
            search = self.writer.search_query(query, section, depth)
            extra = 2 if depth == ResearchDepth.shallow else 0
            limit = self.settings.sources_per_question + extra
            hits, warning = await self.retriever.search(search, limit * 3)
            if warning:
                job.log(warning, level="warn")
            # Prefer documents no earlier question has drawn on, so each section adds evidence.
            fresh_hits = [h for h in hits if h.key not in registry]
            hits = (fresh_hits + [h for h in hits if h.key in registry])[:limit]
            numbered: list[tuple[int, Hit]] = []
            for hit in hits:
                source = registry.get(hit.key)
                if source is None:
                    source = Source(id=len(registry) + 1, title=hit.title, url=hit.url,
                                    snippet=hit.text, origin=hit.origin, score=hit.score)
                    registry[hit.key] = source
                    job.sources.append(source)
                numbered.append((source.id, hit))
            gathered[index] = numbered
            fresh = len({n for n, _ in numbered})
            job.log(f"{section.title}: {fresh} source{'s' if fresh != 1 else ''} found.")
            job.progress = self._between(Stage.descend, (index + 1) / len(sections))
            self._save(job)
            await self._pace(0.6)
        if not job.sources:
            job.log("No sources matched; the report will say so.", level="warn")
        self._leave(job, Stage.descend, stamp)

        stamp = self._enter(job, Stage.draft)
        used: set[str] = set()
        valid = {s.id for s in job.sources}
        if depth == ResearchDepth.deep and len(sections) > 2:
            # The closing section weighs everything gathered, not only its own search.
            last = len(sections) - 1
            seen = {hit.text for _, hit in gathered[last]}
            for index in range(last):
                for number, hit in gathered[index]:
                    if hit.text not in seen:
                        seen.add(hit.text)
                        gathered[last].append((number, hit))
        for index, section in enumerate(sections):
            self._checkpoint(job)
            section.body = (await self.writer.draft(query, section, gathered[index], used)).strip()
            section.source_ids = cited_numbers(section.body, valid)
            job.log(f"Drafted {section.title} citing {len(section.source_ids)} source"
                    f"{'s' if len(section.source_ids) != 1 else ''}.")
            job.progress = self._between(Stage.draft, (index + 1) / len(sections))
            self._save(job)
            await self._pace(0.6)
        self._leave(job, Stage.draft, stamp)

        stamp = self._enter(job, Stage.surface)
        job.summary = await self.writer.summarize(query, sections)
        cited = {n for s in sections for n in s.source_ids}
        job.metadata["citation_coverage"] = round(
            sum(1 for s in sections if s.source_ids) / max(len(sections), 1), 2)
        job.metadata["sources_cited"] = len(cited)
        job.report = render_report(job)
        await self._pace()
        self._leave(job, Stage.surface, stamp)

    # -- helpers ------------------------------------------------------------------------------

    def _enter(self, job: ResearchJob, stage: Stage) -> float:
        job.stage = stage
        job.log(f"{stage.value.capitalize()}…", stage=stage)
        self._save(job)
        return time.perf_counter()

    def _leave(self, job: ResearchJob, stage: Stage, started: float) -> None:
        elapsed = time.perf_counter() - started
        job.progress = STAGE_END[stage]
        timings = job.metadata.setdefault("stage_seconds", {})
        timings[stage.value] = round(elapsed, 3)
        self._save(job)
        if self.on_stage:
            self.on_stage(stage, elapsed)

    @staticmethod
    def _between(stage: Stage, fraction: float) -> float:
        order = list(STAGE_END)
        start = STAGE_END[order[order.index(stage) - 1]] if order.index(stage) else 0.0
        return round(start + (STAGE_END[stage] - start) * fraction, 3)

    def _save(self, job: ResearchJob) -> None:
        """Save progress, unless the job was cancelled meanwhile (which would be overwritten)."""
        self._checkpoint(job)
        self.store.save(job)

    def _checkpoint(self, job: ResearchJob) -> None:
        stored = self.store.get(job.id)
        if stored and stored.status == JobStatus.cancelled:
            raise Cancelled

    async def _pace(self, factor: float = 1.0) -> None:
        if self.settings.mock_latency_seconds and not self.settings.uses_model:
            await asyncio.sleep(self.settings.mock_latency_seconds * factor)


def render_report(job: ResearchJob) -> str:
    title = job.title or title_of(job.request.query)
    lines = [f"# {title}", "", f"> {job.request.query.strip()}", ""]
    if job.summary:
        lines += ["## Key findings", ""] + [f"- {item}" for item in job.summary] + [""]
    for section in job.sections:
        lines += [f"## {section.title}", "", f"*{section.question}*", "", section.body, ""]
    if job.sources:
        lines += ["## Sources", ""]
        for source in job.sources:
            link = f" — <{source.url}>" if source.url else ""
            origin = "library" if source.origin == "knowledge" else "web"
            lines.append(f"{source.id}. {source.title} ({origin}){link}")
        lines.append("")
    if job.metadata.get("writer") == "offline":
        lines += ["---", "",
                  "_Written offline: every sentence above is taken from the cited source. "
                  "Set a model provider to have the report written by a model._", ""]
    return "\n".join(lines)
