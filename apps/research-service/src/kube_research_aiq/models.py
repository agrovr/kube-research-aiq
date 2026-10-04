from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class ResearchDepth(StrEnum):
    auto = "auto"
    shallow = "shallow"
    deep = "deep"


class JobStatus(StrEnum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"

    @property
    def finished(self) -> bool:
        return self in (JobStatus.succeeded, JobStatus.failed, JobStatus.cancelled)


class Stage(StrEnum):
    """The five legs of a research dive."""

    survey = "survey"  # read the question and choose a depth
    plan = "plan"  # break it into sub-questions
    descend = "descend"  # gather sources for every sub-question
    draft = "draft"  # write each section with citations
    surface = "surface"  # summarise and assemble the report


STAGE_ORDER: tuple[Stage, ...] = tuple(Stage)


def now() -> datetime:
    return datetime.now(UTC)


class ResearchRequest(BaseModel):
    query: str = Field(min_length=4, max_length=4000)
    depth: ResearchDepth = ResearchDepth.auto
    tenant: str = Field(default="demo", min_length=1, max_length=80)
    tags: list[str] = Field(default_factory=list, max_length=20)


class Source(BaseModel):
    id: int = Field(description="Citation number used in the report, starting at 1.")
    title: str
    url: str | None = None
    snippet: str
    origin: str = Field(description="knowledge for the bundled library, web for live search")
    score: float = 0.0


class Section(BaseModel):
    title: str
    question: str
    body: str = ""
    source_ids: list[int] = Field(default_factory=list)


class JobEvent(BaseModel):
    at: datetime = Field(default_factory=now)
    stage: Stage | None = None
    message: str
    level: str = "info"


class ResearchJob(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    request: ResearchRequest
    title: str = ""
    status: JobStatus = JobStatus.queued
    created_at: datetime = Field(default_factory=now)
    updated_at: datetime = Field(default_factory=now)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    attempts: int = 0
    selected_depth: ResearchDepth | None = None
    stage: Stage | None = None
    progress: float = 0.0
    plan: list[str] = Field(default_factory=list)
    sections: list[Section] = Field(default_factory=list)
    summary: list[str] = Field(default_factory=list)
    sources: list[Source] = Field(default_factory=list)
    report: str | None = None
    error: str | None = None
    events: list[JobEvent] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def touch(self) -> None:
        self.updated_at = now()

    def log(self, message: str, *, stage: Stage | None = None, level: str = "info") -> None:
        self.events.append(JobEvent(stage=stage or self.stage, message=message, level=level))
        # Keep the timeline bounded; the first event (creation) is always kept.
        if len(self.events) > 200:
            self.events = self.events[:1] + self.events[-199:]

    @property
    def duration_seconds(self) -> float | None:
        if not self.started_at:
            return None
        end = self.finished_at or now()
        return (end - self.started_at).total_seconds()


class JobList(BaseModel):
    jobs: list[ResearchJob]


class EnqueueResponse(BaseModel):
    job_id: str
    status: JobStatus
    message: str


class LibraryDocument(BaseModel):
    slug: str
    title: str
    url: str | None
    topics: list[str]
    passages: int
