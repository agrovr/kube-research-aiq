---
title: Distributed tracing with OpenTelemetry
url: https://opentelemetry.io/docs/concepts/signals/traces/
topics: tracing, opentelemetry, spans, observability, latency, debugging, agents
---
A trace records the path of a request through a system as a tree of spans, each with a start time, duration and attributes. For agent platforms, a trace per research job can show the time spent in planning, each search call and each model completion.

OpenTelemetry provides vendor-neutral SDKs and a Collector that receives, processes and exports telemetry to back ends such as Jaeger, Tempo or commercial services. Context propagation carries the trace identifier from the API that accepts a job to the worker that runs it, even across a queue.

Recording model name, token counts and retrieval counts as span attributes turns traces into a practical tool for tuning cost and latency.
