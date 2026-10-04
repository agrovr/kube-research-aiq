"""Prometheus metrics. Labels stay low-cardinality: status, depth, stage, origin."""

from prometheus_client import Counter, Gauge, Histogram

JOBS_CREATED = Counter("krai_jobs_created_total", "Research jobs accepted by the API", ["depth"])
JOBS_FINISHED = Counter("krai_jobs_finished_total", "Research jobs finished", ["status", "depth"])
JOB_DURATION = Histogram(
    "krai_job_duration_seconds",
    "Wall-clock time of a research dive",
    ["depth"],
    buckets=(1, 2.5, 5, 10, 20, 30, 60, 120, 300, 600),
)
STAGE_DURATION = Histogram(
    "krai_stage_duration_seconds",
    "Time spent in each stage of a dive",
    ["stage"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30, 60, 120),
)
SOURCES_RETRIEVED = Counter("krai_sources_retrieved_total", "Sources cited in reports", ["origin"])
JOBS_REAPED = Counter("krai_jobs_reaped_total", "Stalled jobs requeued or failed by the reaper")
QUEUE_AVAILABLE = Gauge("krai_queue_available", "Whether the Redis queue is reachable")
QUEUE_WAITING = Gauge("krai_queue_waiting", "Job ids waiting in the queue")
QUEUE_IN_PROGRESS = Gauge("krai_queue_in_progress", "Job ids taken by a worker and not yet done")
JOBS_BY_STATUS = Gauge("krai_jobs_by_status", "Stored research jobs by status", ["status"])


def record_finished(job) -> None:  # noqa: ANN001 - avoids an import cycle with models
    depth = (job.selected_depth or job.request.depth).value
    JOBS_FINISHED.labels(status=job.status.value, depth=depth).inc()
    if job.duration_seconds is not None:
        JOB_DURATION.labels(depth=depth).observe(job.duration_seconds)
    for source in job.sources:
        if source.id in {n for s in job.sections for n in s.source_ids}:
            SOURCES_RETRIEVED.labels(origin=source.origin).inc()


def record_stage(stage, seconds: float) -> None:  # noqa: ANN001
    STAGE_DURATION.labels(stage=stage.value).observe(seconds)
