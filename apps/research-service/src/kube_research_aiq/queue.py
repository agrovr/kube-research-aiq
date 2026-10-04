"""A reliable Redis queue.

Workers take jobs with BLMOVE, which moves the job id from the queue into a processing list in
one step. The id leaves the processing list only after the job is saved as finished. If a worker
dies mid-run the id stays behind, and ``reap`` returns it to the queue once the job's heartbeat
(its ``updated_at``) is older than ``stale_after_seconds``.
"""

from __future__ import annotations

from datetime import timedelta

from redis import Redis
from redis.exceptions import RedisError

from kube_research_aiq.models import JobStatus, now
from kube_research_aiq.settings import Settings
from kube_research_aiq.store import JobStore


class ResearchQueue:
    def __init__(self, settings: Settings, client: Redis | None = None):
        self.settings = settings
        self._redis: Redis | None = client
        self._redis_error: str | None = None
        if client is None and settings.redis_url:
            try:
                self.ensure_redis()
            except RedisError as exc:
                self._redis = None
                self._redis_error = str(exc)

    @property
    def processing_name(self) -> str:
        return f"{self.settings.queue_name}:processing"

    @property
    def available(self) -> bool:
        if self.settings.redis_url and not self._redis:
            try:
                self.ensure_redis()
            except RedisError:
                return False
        return self._redis is not None

    @property
    def configured(self) -> bool:
        return self.settings.redis_url is not None or self._redis is not None

    @property
    def error(self) -> str | None:
        return self._redis_error

    def depth(self) -> tuple[int, int]:
        """(waiting, in progress)"""
        if not self.available or not self._redis:
            return 0, 0
        try:
            return (int(self._redis.llen(self.settings.queue_name)),
                    int(self._redis.llen(self.processing_name)))
        except RedisError:
            return 0, 0

    def enqueue(self, job_id: str) -> bool:
        if not self.available or not self._redis:
            return False
        self._redis.lpush(self.settings.queue_name, job_id)
        return True

    def dequeue(self, timeout: int = 5) -> str | None:
        if not self.available or not self._redis:
            return None
        return self._redis.blmove(
            self.settings.queue_name, self.processing_name, timeout, "RIGHT", "LEFT"
        )

    def ack(self, job_id: str) -> None:
        if self._redis:
            self._redis.lrem(self.processing_name, 0, job_id)

    def reap(self, store: JobStore) -> list[str]:
        """Requeue or fail jobs whose worker has gone quiet. Returns the ids it acted on."""
        if not self.available or not self._redis:
            return []
        acted: list[str] = []
        deadline = now() - timedelta(seconds=self.settings.stale_after_seconds)
        for job_id in self._redis.lrange(self.processing_name, 0, -1):
            job = store.get(job_id)
            if job is None or job.status.finished:
                self.ack(job_id)  # finished but never acknowledged, or deleted
                continue
            if job.updated_at > deadline:
                continue  # still alive
            # One reaper per job, even with many workers running this loop.
            if not self._redis.set(f"{self.settings.queue_name}:reap:{job_id}", "1", nx=True,
                                   ex=self.settings.stale_after_seconds):
                continue
            if job.attempts >= self.settings.max_attempts:
                job.status = JobStatus.failed
                job.error = f"The worker stopped responding on {job.attempts} attempts."
                job.finished_at = now()
                job.log(job.error, level="error")
                store.save(job)
                self.ack(job_id)
            else:
                job.status = JobStatus.queued
                job.log("Worker went quiet; returned to the queue.", level="warn")
                store.save(job)
                pipe = self._redis.pipeline()
                pipe.lrem(self.processing_name, 0, job_id)
                pipe.rpush(self.settings.queue_name, job_id)  # front of the line
                pipe.execute()
            acted.append(job_id)
        return acted

    def ensure_redis(self) -> None:
        if not self.settings.redis_url:
            return
        self._redis = Redis.from_url(self.settings.redis_url, decode_responses=True)
        self._redis.ping()
        self._redis_error = None
