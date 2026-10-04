---
title: Reliable queues with Redis lists
url: https://redis.io/docs/latest/commands/lmove/
topics: redis, queue, reliability, at least once, worker, crash, lmove, retry, idempotency
---
A basic Redis queue built on LPUSH and BRPOP loses a job if the worker crashes after popping it but before finishing, because the item no longer exists anywhere. The reliable queue pattern avoids this by atomically moving each item into a processing list with LMOVE or its blocking form BLMOVE.

The worker removes the item from the processing list with LREM only after the job is complete. If the worker dies, the item stays in the processing list, and a monitor can return items that have been there too long to the main queue.

This gives at-least-once delivery, so job handlers must be idempotent: running the same research job twice should overwrite the same record rather than create duplicates. Tracking an attempt counter on each job lets the platform stop retrying a job that keeps failing.

Heartbeats are a practical way to detect stalled work: a running job updates a timestamp as it progresses, and anything silent for longer than a deadline is treated as abandoned and requeued.
