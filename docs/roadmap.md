# Roadmap

## Done

- API and worker on Kubernetes, Redis queue, PostgreSQL store, Helm chart, Argo CD, CI
- A five-stage research pipeline with depth routing, recorded per job
- Retrieval from a bundled library (BM25) with optional Tavily web search, and source ranking that
  favours fresh documents per section
- Numbered citations that always point at a real source; an offline writer that never invents text
- Model writing through any OpenAI-compatible endpoint, with a fallback plan
- Live progress over server-sent events, cancel and retry
- Reliable queue (`BLMOVE` with a processing list), heartbeats, a stalled-job reaper and attempt limits
- Worker metrics for dive and stage durations, a Grafana dashboard and KEDA queue-length scaling
- Markdown report export, a citation-coverage quality signal and a scheduled benchmark dive
- The dive console: a live sounding line, a report reader with citation chips, and a timeline

## Next

- Hybrid retrieval: embeddings alongside BM25, and private document upload per tenant
- Concurrent researchers within a deep dive, bounded per job
- OpenTelemetry traces from the API through the queue to each model and search call
- Per-tenant quotas and fair scheduling on the shared queue
- Report feedback captured in the console, feeding an evaluation set
- PDF export
- External Secrets Operator and cert-manager examples for the production profile
