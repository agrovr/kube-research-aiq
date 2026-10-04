---
title: PostgreSQL as a durable job store
url: https://www.postgresql.org/docs/current/datatype-json.html
topics: postgres, postgresql, jsonb, database, persistence, index, reports, storage
---
PostgreSQL's jsonb type stores structured documents in a binary form that can be indexed and queried, which suits research jobs whose reports, sources and timelines change shape over time. A hybrid table keeps frequently filtered fields such as status, tenant and timestamps in ordinary columns and the full job document in a jsonb payload.

Composite indexes on tenant and updated time, or on status and updated time, keep dashboard queries fast as the number of jobs grows. An upsert with INSERT ... ON CONFLICT DO UPDATE makes saves idempotent, which matters when a queue delivers a job more than once.

Keeping PostgreSQL as the durable store and Redis as the queue separates two concerns: losing Redis loses only pending queue entries, which can be rebuilt from jobs still marked queued. Connection strings belong in Kubernetes Secrets, never in ConfigMaps or images.
