"""The research worker: takes jobs from the queue, runs the dive, and acknowledges them.

On SIGTERM it finishes the job in hand and exits, which suits Kubernetes rollouts. Every
``reap_interval`` seconds it also returns stalled jobs (from workers that died) to the queue.
"""

from __future__ import annotations

import asyncio
import logging
import signal
import time

from prometheus_client import start_http_server

from kube_research_aiq import telemetry
from kube_research_aiq.queue import ResearchQueue
from kube_research_aiq.researcher import ResearchRunner
from kube_research_aiq.settings import Settings, get_settings
from kube_research_aiq.store import JobStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("kube-research-aiq-worker")


class Worker:
    def __init__(self, settings: Settings, store: JobStore, queue: ResearchQueue,
                 runner: ResearchRunner | None = None, reap_interval: float = 30.0):
        self.settings = settings
        self.store = store
        self.queue = queue
        self.runner = runner or ResearchRunner(settings, store, on_stage=telemetry.record_stage)
        self.reap_interval = reap_interval
        self.stopping = False
        self._last_reap = 0.0

    def stop(self, *_: object) -> None:
        if not self.stopping:
            logger.info("stopping after the current job")
        self.stopping = True

    def reap(self) -> None:
        self._last_reap = time.monotonic()
        for job_id in self.queue.reap(self.store):
            telemetry.JOBS_REAPED.inc()
            logger.warning("reaped stalled job %s", job_id)

    async def step(self, timeout: int = 5) -> bool:
        """Process at most one job. Returns True if one was processed."""
        if time.monotonic() - self._last_reap >= self.reap_interval:
            self.reap()
        job_id = await asyncio.to_thread(self.queue.dequeue, timeout)
        if not job_id:
            return False
        logger.info("diving %s", job_id)
        try:
            job = await self.runner.run(job_id)
        except ValueError:
            logger.warning("job %s no longer exists", job_id)
        else:
            telemetry.record_finished(job)
            logger.info("surfaced %s: %s", job.id, job.status.value)
        self.queue.ack(job_id)
        return True

    async def run(self) -> None:
        if not self.queue.available:
            logger.warning("Redis queue is unavailable; waiting for it.")
        while not self.stopping:
            if not self.queue.available:
                await asyncio.sleep(2)
                continue
            if not await self.step():
                await asyncio.sleep(0.1)
        logger.info("worker stopped")


async def main() -> None:
    settings = get_settings()
    if settings.worker_metrics_port:
        start_http_server(settings.worker_metrics_port)
        logger.info("metrics on :%s/metrics", settings.worker_metrics_port)
    store = JobStore(settings)
    worker = Worker(settings, store, ResearchQueue(settings))
    signal.signal(signal.SIGTERM, worker.stop)
    signal.signal(signal.SIGINT, worker.stop)
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
