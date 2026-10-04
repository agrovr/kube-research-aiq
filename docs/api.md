# API

Interactive docs are served at `/docs` by the running API. Every response is JSON unless noted.

| Method and path | Purpose |
| :-- | :-- |
| `POST /v1/research` | Start a dive. Returns `202` with the job id |
| `GET /v1/research?status=&limit=` | Dives, newest first |
| `GET /v1/research/{id}` | One dive: plan, sections, sources, timeline, report |
| `GET /v1/research/{id}/events` | Server-sent events: the job whenever it changes, then `done` |
| `GET /v1/research/{id}/report.md` | The report as a Markdown download (`409` until it is ready) |
| `POST /v1/research/{id}/cancel` | Stop a waiting or running dive |
| `POST /v1/research/{id}/retry` | Send a failed or cancelled dive down again |
| `POST /v1/research/{id}/run` | Run a waiting dive in the API process (useful without Redis) |
| `GET /v1/meta` | Version, writer, sources, models, queue depth and store |
| `GET /v1/library` | The bundled reference library |
| `GET /healthz`, `/readyz`, `/metrics` | Liveness, readiness (checks PostgreSQL) and Prometheus metrics |

## Start a dive

```bash
curl -X POST localhost:8000/v1/research -H 'Content-Type: application/json' \
  -d '{"query": "How should research workers autoscale on a Redis queue?", "depth": "auto",
       "tenant": "docs", "tags": ["autoscaling"]}'
```

```json
{"job_id": "6f1c…", "status": "queued", "message": "Queued for a worker."}
```

`depth` is `auto`, `shallow` or `deep`. `query` is 4 to 4,000 characters.

## Follow it

```bash
curl -N localhost:8000/v1/research/6f1c…/events
```

```text
event: job
data: {"id": "6f1c…", "status": "running", "stage": "descend", "progress": 0.37, …}

event: job
data: {"id": "6f1c…", "status": "succeeded", "stage": "surface", "progress": 1.0, …}

event: done
data: {"status": "succeeded"}
```

A comment line keeps idle connections open every 15 seconds. Behind a proxy, turn buffering off
for `/v1` (the chart's nginx and ingress settings already do).

## A finished job

```json
{
  "id": "6f1c…",
  "title": "Research workers autoscale on a Redis queue",
  "status": "succeeded",
  "selected_depth": "shallow",
  "stage": "surface",
  "progress": 1.0,
  "sections": [{"title": "Answer", "question": "…", "body": "… [1] … [2]", "source_ids": [1, 2]}],
  "summary": [],
  "sources": [{"id": 1, "title": "Event-driven autoscaling with KEDA", "url": "https://keda.sh/…",
               "snippet": "…", "origin": "knowledge", "score": 7.91}],
  "events": [{"at": "…", "stage": "survey", "message": "Auto-routed shallow: a focused question.",
              "level": "info"}],
  "metadata": {"writer": "offline", "citation_coverage": 1.0, "sources_cited": 3,
               "stage_seconds": {"survey": 0.0, "plan": 0.0, "descend": 0.01, "draft": 0.02,
                                 "surface": 0.0}},
  "report": "# Research workers autoscale on a Redis queue\n…"
}
```
