---
title: Metrics and observability for asynchronous jobs
url: https://prometheus.io/docs/practices/instrumentation/
topics: observability, prometheus, metrics, grafana, monitoring, histogram, alerts, queue, latency
---
Prometheus guidance for offline processing systems is to track items coming in, items in progress, the last time something was processed and items sent out. Each major stage of a pipeline deserves its own duration measurement so that slow stages can be found quickly.

Histograms record distributions such as job duration and stage latency and support percentile queries like the 95th percentile of deep research runs. Label cardinality must stay small: labels such as status, depth and stage are safe, while labels such as job ID or tenant name can explode the number of time series.

A ServiceMonitor from the Prometheus Operator tells Prometheus which Services to scrape, and a Grafana dashboard can be shipped as a labelled ConfigMap that a sidecar loads automatically. Useful alerts for research platforms include a growing queue with no completions, a rising failure ratio and stale running jobs.
