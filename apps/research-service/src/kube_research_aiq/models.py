from datetime import datetime, timezone
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


class ResearchRequest(BaseModel):
    query: str = Field(min_length=4, max_length=4000)
    depth: ResearchDepth = ResearchDepth.auto
    tenant: str = Field(default="demo", min_length=1, max_length=80)
    tags: list[str] = Field(default_factory=list, max_length=20)


class ResearchJob(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    request: ResearchRequest
    status: JobStatus = JobStatus.queued
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    selected_depth: ResearchDepth | None = None
    plan: list[str] = Field(default_factory=list)
    report: str | None = None
    citations: list[str] = Field(default_factory=list)
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)


class JobList(BaseModel):
    jobs: list[ResearchJob]


class EnqueueResponse(BaseModel):
    job_id: str
    status: JobStatus
    message: str
