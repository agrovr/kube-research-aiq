import json
import threading
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from redis import Redis
from redis.exceptions import RedisError

from kube_research_aiq.models import ResearchJob
from kube_research_aiq.settings import Settings


class JobStore:
    """Small storage facade.

    Redis is used in Kubernetes. A JSON file fallback keeps local demos and tests simple.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self._lock = threading.Lock()
        self._redis: Redis | None = None
        self._postgres_ready = False
        self._postgres_error: str | None = None
        if settings.database_url:
            try:
                self._init_postgres()
                self._postgres_ready = True
                self._postgres_error = None
            except psycopg.Error as exc:
                self._postgres_ready = False
                self._postgres_error = str(exc)
        if settings.redis_url:
            try:
                self._redis = Redis.from_url(settings.redis_url, decode_responses=True)
                self._redis.ping()
            except RedisError:
                self._redis = None

    @property
    def using_redis(self) -> bool:
        return self._redis is not None

    @property
    def using_postgres(self) -> bool:
        return self._postgres_ready

    @property
    def wants_postgres(self) -> bool:
        return self.settings.database_url is not None

    @property
    def postgres_error(self) -> str | None:
        return self._postgres_error

    def create(self, job: ResearchJob) -> ResearchJob:
        self.save(job)
        if self._redis:
            self._redis.rpush("krai:jobs:index", job.id)
        return job

    def get(self, job_id: str) -> ResearchJob | None:
        if self.settings.database_url:
            self.ensure_postgres()
            with self._connect() as conn:
                row = conn.execute(
                    "select payload from research_jobs where id = %s",
                    (job_id,),
                ).fetchone()
                return ResearchJob.model_validate(row["payload"]) if row else None
        if self._redis:
            raw = self._redis.get(self._key(job_id))
            return ResearchJob.model_validate_json(raw) if raw else None
        return self._file_jobs().get(job_id)

    def list(self) -> list[ResearchJob]:
        if self.settings.database_url:
            self.ensure_postgres()
            with self._connect() as conn:
                rows = conn.execute(
                    """
                    select payload
                    from research_jobs
                    order by updated_at desc
                    limit 200
                    """
                ).fetchall()
                return [ResearchJob.model_validate(row["payload"]) for row in rows]
        if self._redis:
            ids = self._redis.lrange("krai:jobs:index", 0, -1)
            jobs = [self.get(job_id) for job_id in ids]
            return [job for job in jobs if job is not None]
        return list(self._file_jobs().values())

    def save(self, job: ResearchJob) -> None:
        job.touch()
        if self.settings.database_url:
            self.ensure_postgres()
            payload = job.model_dump(mode="json")
            with self._connect() as conn:
                conn.execute(
                    """
                    insert into research_jobs (
                        id, tenant, status, requested_depth, selected_depth,
                        created_at, updated_at, payload
                    )
                    values (%s, %s, %s, %s, %s, %s, %s, %s)
                    on conflict (id) do update set
                        tenant = excluded.tenant,
                        status = excluded.status,
                        requested_depth = excluded.requested_depth,
                        selected_depth = excluded.selected_depth,
                        updated_at = excluded.updated_at,
                        payload = excluded.payload
                    """,
                    (
                        job.id,
                        job.request.tenant,
                        job.status.value,
                        job.request.depth.value,
                        job.selected_depth.value if job.selected_depth else None,
                        job.created_at,
                        job.updated_at,
                        Jsonb(payload),
                    ),
                )
            return
        if self._redis:
            self._redis.set(self._key(job.id), job.model_dump_json())
            return

        with self._lock:
            jobs = self._file_jobs()
            jobs[job.id] = job
            self._write_file_jobs(jobs)

    def _file_jobs(self) -> dict[str, ResearchJob]:
        path = self.settings.storage_path
        if not path.exists():
            return {}
        raw = json.loads(path.read_text(encoding="utf-8"))
        return {job_id: ResearchJob.model_validate(value) for job_id, value in raw.items()}

    def _write_file_jobs(self, jobs: dict[str, ResearchJob]) -> None:
        path = self.settings.storage_path
        Path(path.parent).mkdir(parents=True, exist_ok=True)
        payload = {job_id: job.model_dump(mode="json") for job_id, job in jobs.items()}
        temp_path = path.with_suffix(".tmp")
        temp_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        temp_path.replace(path)

    @staticmethod
    def _key(job_id: str) -> str:
        return f"krai:jobs:{job_id}"

    def _connect(self) -> psycopg.Connection:
        if not self.settings.database_url:
            raise RuntimeError("database_url is not configured")
        return psycopg.connect(self.settings.database_url, row_factory=dict_row)

    def _init_postgres(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                create table if not exists research_jobs (
                    id text primary key,
                    tenant text not null,
                    status text not null,
                    requested_depth text not null,
                    selected_depth text,
                    created_at timestamptz not null,
                    updated_at timestamptz not null,
                    payload jsonb not null
                )
                """
            )
            conn.execute(
                """
                create index if not exists research_jobs_tenant_updated_idx
                on research_jobs (tenant, updated_at desc)
                """
            )
            conn.execute(
                """
                create index if not exists research_jobs_status_updated_idx
                on research_jobs (status, updated_at desc)
                """
            )

    def ensure_postgres(self) -> None:
        if self._postgres_ready:
            return
        try:
            self._init_postgres()
            self._postgres_ready = True
            self._postgres_error = None
        except psycopg.Error as exc:
            self._postgres_error = str(exc)
            raise RuntimeError(f"PostgreSQL is configured but unavailable: {exc}") from exc
