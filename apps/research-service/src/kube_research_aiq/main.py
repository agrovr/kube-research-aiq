from fastapi import BackgroundTasks, FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, generate_latest

from kube_research_aiq.models import EnqueueResponse, JobList, ResearchJob, ResearchRequest
from kube_research_aiq.queue import ResearchQueue
from kube_research_aiq.researcher import ResearchRunner
from kube_research_aiq.settings import get_settings
from kube_research_aiq.store import JobStore

settings = get_settings()
store = JobStore(settings)
queue = ResearchQueue(settings)
runner = ResearchRunner(settings, store)

app = FastAPI(title=settings.app_name, version="0.1.0")
cors_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

jobs_created = Counter("krai_jobs_created_total", "Research jobs created")
jobs_completed = Counter("krai_jobs_completed_total", "Research jobs completed through API")
queue_available = Gauge("krai_queue_available", "Whether Redis-backed queue is available")
jobs_by_status = Gauge("krai_jobs_by_status", "Research jobs by status", ["status"])
jobs_by_depth = Gauge("krai_jobs_by_depth", "Research jobs by selected or requested depth", ["depth"])


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
def readyz(response: Response) -> dict[str, object]:
    if store.wants_postgres and not store.using_postgres:
        try:
            store.ensure_postgres()
        except RuntimeError:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            return {
                "status": "not_ready",
                "queue": queue.available,
                "store": "postgres",
                "error": "PostgreSQL is configured but unavailable.",
            }

    store_backend = "postgres" if store.using_postgres else "redis" if store.using_redis else "file"
    return {
        "status": "ready",
        "queue": queue.available,
        "store": store_backend,
        "provider": settings.provider,
    }


@app.get("/metrics")
def metrics() -> Response:
    queue_available.set(1 if queue.available else 0)
    jobs = store.list()
    for status_value in ["queued", "running", "succeeded", "failed"]:
        jobs_by_status.labels(status=status_value).set(
            sum(1 for job in jobs if job.status.value == status_value)
        )
    for depth_value in ["auto", "shallow", "deep"]:
        jobs_by_depth.labels(depth=depth_value).set(
            sum(1 for job in jobs if (job.selected_depth or job.request.depth).value == depth_value)
        )
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/v1/research", response_model=EnqueueResponse, status_code=202)
async def create_research_job(
    request: ResearchRequest,
    background_tasks: BackgroundTasks,
) -> EnqueueResponse:
    job = ResearchJob(request=request)
    store.create(job)
    jobs_created.inc()

    if queue.available:
        queue.enqueue(job.id)
        message = "Job queued for worker execution."
    elif settings.enable_background_local_runs:
        background_tasks.add_task(runner.run, job.id)
        message = "Redis is unavailable; job scheduled on local API background task."
    else:
        message = "Job created. Queue unavailable; run it manually with POST /v1/research/{id}/run."

    return EnqueueResponse(job_id=job.id, status=job.status, message=message)


@app.get("/v1/research", response_model=JobList)
def list_research_jobs() -> JobList:
    return JobList(jobs=store.list())


@app.get("/v1/research/{job_id}", response_model=ResearchJob)
def get_research_job(job_id: str) -> ResearchJob:
    job = store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return job


@app.get("/v1/research/{job_id}/report.md")
def download_markdown_report(job_id: str) -> Response:
    job = store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    if not job.report:
        raise HTTPException(status_code=409, detail="report is not ready")

    tags = ", ".join(job.request.tags) if job.request.tags else "none"
    citations = "\n".join(f"- {citation}" for citation in job.citations) or "- none"
    content = (
        f"# KubeResearch AIQ Report\n\n"
        f"**Job ID:** `{job.id}`\n\n"
        f"**Tenant:** `{job.request.tenant}`\n\n"
        f"**Status:** `{job.status}`\n\n"
        f"**Requested depth:** `{job.request.depth}`\n\n"
        f"**Selected depth:** `{job.selected_depth or 'pending'}`\n\n"
        f"**Tags:** {tags}\n\n"
        f"## Query\n\n{job.request.query}\n\n"
        f"## Report\n\n{job.report}\n\n"
        f"## Citations\n\n{citations}\n"
    )
    filename = f"kube-research-aiq-{job.id}.md"
    return Response(
        content,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/v1/research/{job_id}/run", response_model=ResearchJob)
async def run_research_job(job_id: str) -> ResearchJob:
    if not store.get(job_id):
        raise HTTPException(status_code=404, detail="job not found")
    job = await runner.run(job_id)
    jobs_completed.inc()
    return job
