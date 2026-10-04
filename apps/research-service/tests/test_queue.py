import asyncio
from datetime import timedelta

from kube_research_aiq.models import JobStatus, ResearchJob, ResearchRequest, now
from kube_research_aiq.worker import Worker


def queued_job(store, queue):
    job = store.create(ResearchJob(request=ResearchRequest(query="What is KEDA?")))
    queue.enqueue(job.id)
    return job


def test_taking_a_job_parks_it_in_processing(store, queue):
    job = queued_job(store, queue)
    assert queue.dequeue(timeout=1) == job.id
    assert queue.depth() == (0, 1)
    queue.ack(job.id)
    assert queue.depth() == (0, 0)


def test_worker_runs_and_acknowledges(settings, store, queue):
    job = queued_job(store, queue)
    worker = Worker(settings, store, queue)
    assert asyncio.run(worker.step(timeout=1))
    assert store.get(job.id).status == JobStatus.succeeded
    assert queue.depth() == (0, 0)
    assert not asyncio.run(worker.step(timeout=1))


def stall(store, queue, attempts=1):
    """Simulate a worker that took a job and died."""
    job = queued_job(store, queue)
    queue.dequeue(timeout=1)
    job = store.get(job.id)
    job.status, job.attempts = JobStatus.running, attempts
    store.save(job)
    # Age the heartbeat past the deadline without going through save(), which refreshes it.
    raw = store._file_jobs()
    raw[job.id].updated_at = now() - timedelta(seconds=queue.settings.stale_after_seconds + 5)
    store._write_file_jobs(raw)
    return job


def test_reaper_requeues_stalled_jobs(store, queue):
    job = stall(store, queue)
    assert queue.reap(store) == [job.id]
    assert queue.depth() == (1, 0)
    assert store.get(job.id).status == JobStatus.queued
    assert queue.reap(store) == []  # nothing left in processing


def test_reaper_fails_jobs_that_keep_stalling(store, queue):
    job = stall(store, queue, attempts=queue.settings.max_attempts)
    queue.reap(store)
    stored = store.get(job.id)
    assert stored.status == JobStatus.failed and "stopped responding" in stored.error
    assert queue.depth() == (0, 0)


def test_reaper_leaves_live_jobs_alone(store, queue):
    job = queued_job(store, queue)
    queue.dequeue(timeout=1)
    running = store.get(job.id)
    running.status = JobStatus.running
    store.save(running)  # fresh heartbeat
    assert queue.reap(store) == []
    assert queue.depth() == (0, 1)


def test_reaper_clears_finished_but_unacknowledged_jobs(store, queue):
    job = queued_job(store, queue)
    queue.dequeue(timeout=1)
    done = store.get(job.id)
    done.status = JobStatus.succeeded
    store.save(done)
    queue.reap(store)
    assert queue.depth() == (0, 0)
