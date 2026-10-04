# Operating it

## Configuration

Every setting is an environment variable with the `KRAI_` prefix; the chart sets them from
`values.yaml`.

| Variable | Default | Effect |
| :-- | :-- | :-- |
| `KRAI_PROVIDER` | `mock` | `mock` writes offline from sources; `nvidia` uses an OpenAI-compatible model |
| `KRAI_LLM_BASE_URL` | NVIDIA hosted | Any OpenAI-compatible base URL (NIM, vLLM) |
| `KRAI_NVIDIA_API_KEY` | | Model API key |
| `KRAI_SHALLOW_MODEL`, `KRAI_DEEP_MODEL`, `KRAI_CLASSIFIER_MODEL` | | Models for findings, sections and planning |
| `KRAI_TAVILY_API_KEY` | | Adds live web search |
| `KRAI_SOURCES_PER_QUESTION` | `4` | Sources gathered per section (shallow dives get two more) |
| `KRAI_MAX_REPORT_SECTIONS` | `5` | Sections in a deep report |
| `KRAI_REDIS_URL`, `KRAI_DATABASE_URL` | | Queue and durable store; without them, a JSON file and in-API runs |
| `KRAI_STALE_AFTER_SECONDS` | `300` | Heartbeat age after which a running dive is requeued |
| `KRAI_MAX_ATTEMPTS` | `3` | Attempts before a repeatedly stalled dive is marked failed |
| `KRAI_WORKER_METRICS_PORT` | `0` | Worker `/metrics` port (the chart uses `9100`) |
| `KRAI_MOCK_LATENCY_SECONDS` | `0` | Offline only: pause between stages for demos |

## Metrics

| Metric | Type | Labels | From |
| :-- | :-- | :-- | :-- |
| `krai_jobs_created_total` | counter | `depth` | API |
| `krai_queue_waiting`, `krai_queue_in_progress` | gauge | | API |
| `krai_queue_available` | gauge | | API |
| `krai_jobs_by_status` | gauge | `status` | API |
| `krai_jobs_finished_total` | counter | `status`, `depth` | worker |
| `krai_job_duration_seconds` | histogram | `depth` | worker |
| `krai_stage_duration_seconds` | histogram | `stage` | worker |
| `krai_sources_retrieved_total` | counter | `origin` | worker |
| `krai_jobs_reaped_total` | counter | | worker |

Labels stay low-cardinality on purpose: no job ids or tenants. With `grafanaDashboard.enabled`, the
chart ships a dashboard showing queue depth, failure ratio, requeued dives, p50 and p95 dive time
by depth, p95 time per stage, finishes by status and cited sources by origin.

Useful alerts:

```promql
# Work is piling up and nothing is finishing
max(krai_queue_waiting) > 10 and sum(rate(krai_jobs_finished_total[10m])) == 0

# More than a quarter of dives failing
sum(rate(krai_jobs_finished_total{status="failed"}[30m]))
  / sum(rate(krai_jobs_finished_total[30m])) > 0.25

# Workers keep dying mid-dive
increase(krai_jobs_reaped_total[1h]) > 3
```

## Scaling workers on queue length

Research workers spend most of their time waiting on models and search, so CPU understates
demand. With [KEDA](https://keda.sh) installed:

```bash
helm upgrade --install kuberesearch charts/kube-research-aiq -n aiq-system \
  --set keda.enabled=true --set keda.jobsPerWorker=2 --set keda.maxReplicas=8
```

The chart then renders a `ScaledObject` on the Redis queue, drops the worker HPA, and lets
workers scale to zero when nothing is waiting.
