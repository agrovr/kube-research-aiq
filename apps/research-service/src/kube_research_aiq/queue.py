from redis import Redis
from redis.exceptions import RedisError

from kube_research_aiq.settings import Settings


class ResearchQueue:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._redis: Redis | None = None
        self._redis_error: str | None = None
        if settings.redis_url:
            try:
                self.ensure_redis()
            except RedisError as exc:
                self._redis = None
                self._redis_error = str(exc)

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
        return self.settings.redis_url is not None

    @property
    def error(self) -> str | None:
        return self._redis_error

    def enqueue(self, job_id: str) -> None:
        if not self.available:
            return
        if not self._redis:
            return
        self._redis.lpush(self.settings.queue_name, job_id)

    def dequeue(self, timeout: int = 5) -> str | None:
        if not self.available:
            return None
        if not self._redis:
            return None
        item = self._redis.brpop(self.settings.queue_name, timeout=timeout)
        if not item:
            return None
        _, job_id = item
        return job_id

    def ensure_redis(self) -> None:
        if not self.settings.redis_url:
            return
        self._redis = Redis.from_url(self.settings.redis_url, decode_responses=True)
        self._redis.ping()
        self._redis_error = None
