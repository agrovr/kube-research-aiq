import asyncio
import logging
import signal

from kube_research_aiq.queue import ResearchQueue
from kube_research_aiq.researcher import ResearchRunner
from kube_research_aiq.settings import get_settings
from kube_research_aiq.store import JobStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("kube-research-aiq-worker")


async def main() -> None:
    settings = get_settings()
    store = JobStore(settings)
    queue = ResearchQueue(settings)
    runner = ResearchRunner(settings, store)
    stopping = False

    def stop(*_: object) -> None:
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    if not queue.available:
        logger.warning("Redis queue is unavailable. Worker is idle.")

    while not stopping:
        job_id = queue.dequeue(timeout=5)
        if not job_id:
            await asyncio.sleep(0.2)
            continue
        logger.info("processing job %s", job_id)
        job = await runner.run(job_id)
        logger.info("finished job %s with status %s", job.id, job.status)

    logger.info("worker stopped")


if __name__ == "__main__":
    asyncio.run(main())
