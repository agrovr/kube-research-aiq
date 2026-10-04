"""The research API: accepts dives, reports on them, and streams their progress."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from kube_research_aiq import __version__, telemetry
from kube_research_aiq.models import (
    EnqueueResponse,
    JobList,
    JobStatus,
    LibraryDocument,
    ResearchJob,
    ResearchRequest,
)
from kube_research_aiq.queue import ResearchQueue
from kube_research_aiq.researcher import ResearchRunner
from kube_research_aiq.settings import Settings, get_settings
from kube_research_aiq.store import JobStore
from kube_research_aiq.writer import title_of


def create_app(
    settings: Settings | None = None,
    store: JobStore | None = None,
    queue: ResearchQueue | None = None,
    runner: ResearchRunner | None = None,
    stream_interval: float = 0.5,
) -> FastAPI:
    settings = settings or get_settings()
    store = store or JobStore(settings)
    queue = queue or ResearchQueue(settings)
    runner = runner or ResearchRunner(settings, store, on_stage=telemetry.record_stage)

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description="Research agents that dive as deep as the question.",
    )
    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.settings, app.state.store, app.state.queue, app.state.runner = (
        settings, store, queue, runner)

    def load(job_id: str) -> ResearchJob:
        job = store.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="job not found")
        return job

    async def execute(job_id: str) -> ResearchJob:
        job = await runner.run(job_id)
        telemetry.record_finished(job)
        return job

    def dispatch(job: ResearchJob, background: BackgroundTasks) -> str:
        if queue.available and queue.enqueue(job.id):
            return "Queued for a worker."
        if settings.enable_background_local_runs:
            background.add_task(execute, job.id)
            return "No queue available; running on the API's background task."
        return "Created. No queue is available; start it with POST /v1/research/{id}/run."

    # -- operations ---------------------------------------------------------------------------

    @app.get("/healthz", tags=["operations"])
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/readyz", tags=["operations"])
    def readyz(response: Response) -> dict[str, object]:
        if store.wants_postgres and not store.using_postgres:
            try:
                store.ensure_postgres()
            except RuntimeError:
                response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
                return {"status": "not_ready", "queue": queue.available, "store": "postgres",
                        "error": "PostgreSQL is configured but unavailable."}
        return {"status": "ready", "queue": queue.available, "store": store.backend,
                "provider": settings.provider}

    @app.get("/metrics", tags=["operations"])
    def metrics() -> Response:
        telemetry.QUEUE_AVAILABLE.set(1 if queue.available else 0)
        waiting, in_progress = queue.depth()
        telemetry.QUEUE_WAITING.set(waiting)
        telemetry.QUEUE_IN_PROGRESS.set(in_progress)
        jobs = store.list()
        for value in JobStatus:
            telemetry.JOBS_BY_STATUS.labels(status=value.value).set(
                sum(1 for job in jobs if job.status == value))
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.get("/v1/meta", tags=["platform"])
    def meta() -> dict[str, object]:
        """What this installation is running: version, writer, sources, models and backends."""
        waiting, in_progress = queue.depth()
        return {
            "name": settings.app_name,
            "version": __version__,
            "environment": settings.environment,
            "provider": settings.provider,
            "writer": runner.writer.name,
            "retrieval": runner.retriever.origins,
            "models": {"shallow": settings.shallow_model, "deep": settings.deep_model,
                       "planner": settings.classifier_model} if settings.uses_model else None,
            "queue": {"available": queue.available, "waiting": waiting,
                      "in_progress": in_progress},
            "store": store.backend,
            "library_documents": len(runner.retriever.library.documents),
        }

    @app.get("/v1/library", response_model=list[LibraryDocument], tags=["platform"])
    def library() -> list[LibraryDocument]:
        """The bundled reference library that every dive can cite."""
        return [
            LibraryDocument(slug=d.slug, title=d.title, url=d.url, topics=list(d.topics),
                            passages=len(d.passages))
            for d in runner.retriever.library.documents
        ]

    # -- research -----------------------------------------------------------------------------

    @app.post("/v1/research", response_model=EnqueueResponse, status_code=202, tags=["research"])
    async def create_research_job(request: ResearchRequest,
                                  background: BackgroundTasks) -> EnqueueResponse:
        job = ResearchJob(request=request, title=title_of(request.query))
        job.log("Dive requested.", stage=None)
        store.create(job)
        telemetry.JOBS_CREATED.labels(depth=request.depth.value).inc()
        message = dispatch(job, background)
        return EnqueueResponse(job_id=job.id, status=job.status, message=message)

    @app.get("/v1/research", response_model=JobList, tags=["research"])
    def list_research_jobs(
        status_filter: JobStatus | None = Query(default=None, alias="status"),
        limit: int = Query(default=100, ge=1, le=200),
    ) -> JobList:
        jobs = store.list()
        if status_filter:
            jobs = [job for job in jobs if job.status == status_filter]
        return JobList(jobs=jobs[:limit])

    @app.get("/v1/research/{job_id}", response_model=ResearchJob, tags=["research"])
    def get_research_job(job_id: str) -> ResearchJob:
        return load(job_id)

    @app.get("/v1/research/{job_id}/events", tags=["research"])
    async def stream_research_job(job_id: str, request: Request) -> StreamingResponse:
        """Server-sent events: the job as JSON whenever it changes, until it finishes."""
        load(job_id)

        async def events() -> AsyncIterator[str]:
            last = None
            idle = 0.0
            while True:
                if await request.is_disconnected():
                    break
                job = await asyncio.to_thread(store.get, job_id)
                if job is None:
                    yield "event: gone\ndata: {}\n\n"
                    break
                if job.updated_at != last:
                    last, idle = job.updated_at, 0.0
                    yield f"event: job\ndata: {job.model_dump_json()}\n\n"
                    if job.status.finished:
                        yield f"event: done\ndata: {json.dumps({'status': job.status.value})}\n\n"
                        break
                elif idle >= 15:
                    idle = 0.0
                    yield ": keep-alive\n\n"
                await asyncio.sleep(stream_interval)
                idle += stream_interval

        return StreamingResponse(
            events(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @app.get("/v1/research/{job_id}/report.md", tags=["research"])
    def download_markdown_report(job_id: str) -> Response:
        job = load(job_id)
        if not job.report:
            raise HTTPException(status_code=409, detail="report is not ready")
        depth = (job.selected_depth or job.request.depth).value
        tags = ", ".join(job.request.tags) or "none"
        header = (
            f"<!-- KubeResearch AIQ · job {job.id} · {depth} dive · tenant {job.request.tenant}"
            f" · tags {tags} · {job.updated_at:%Y-%m-%d %H:%M} UTC -->\n\n"
        )
        return Response(
            header + job.report,
            media_type="text/markdown",
            headers={"Content-Disposition":
                     f'attachment; filename="kube-research-aiq-{job.id[:8]}.md"'},
        )

    @app.post("/v1/research/{job_id}/run", response_model=ResearchJob, tags=["research"])
    async def run_research_job(job_id: str) -> ResearchJob:
        """Run a job in the API process. Useful without Redis."""
        job = load(job_id)
        if job.status == JobStatus.running:
            raise HTTPException(status_code=409, detail="job is already running")
        return await execute(job_id)

    @app.post("/v1/research/{job_id}/cancel", response_model=ResearchJob, tags=["research"])
    def cancel_research_job(job_id: str) -> ResearchJob:
        """Stop a queued or running dive. A running dive stops at its next checkpoint."""
        job = load(job_id)
        if job.status.finished:
            raise HTTPException(status_code=409, detail=f"job already {job.status.value}")
        was_running = job.status == JobStatus.running
        job.status = JobStatus.cancelled
        if not was_running:
            job.log("Cancelled before it started.", level="warn")
        else:
            job.log("Cancellation requested.", level="warn")
        store.save(job)
        return job

    @app.post("/v1/research/{job_id}/retry", response_model=EnqueueResponse, tags=["research"])
    def retry_research_job(job_id: str, background: BackgroundTasks) -> EnqueueResponse:
        """Send a failed or cancelled dive back down."""
        job = load(job_id)
        if job.status not in (JobStatus.failed, JobStatus.cancelled):
            raise HTTPException(status_code=409, detail="only failed or cancelled jobs can retry")
        job.status = JobStatus.queued
        job.error = None
        job.attempts = 0
        job.log("Retry requested.", stage=None)
        store.save(job)
        return EnqueueResponse(job_id=job.id, status=job.status,
                               message=dispatch(job, background))

    return app


app = create_app()
