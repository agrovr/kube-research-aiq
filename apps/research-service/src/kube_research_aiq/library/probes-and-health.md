---
title: Liveness, readiness and startup probes
url: https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/
topics: probes, readiness, liveness, health, startup, availability, operations
---
Kubernetes uses three kinds of probes. A liveness probe restarts a container that has stopped making progress, a readiness probe removes a Pod from Service endpoints while it cannot serve traffic, and a startup probe protects slow-starting containers from premature liveness failures.

A readiness endpoint should check the dependencies a request actually needs, such as the database, and report not ready when they are unavailable. A liveness endpoint should stay cheap and avoid checking downstream systems, otherwise an outage in a database can trigger a cascade of pointless restarts.

For a research API, a typical split is a /healthz liveness check that only proves the process is alive and a /readyz check that verifies the job store. Workers without an HTTP server can expose a small metrics or health port, or rely on process exit to signal failure.
