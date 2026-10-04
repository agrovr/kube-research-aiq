# The research engine

A dive has five stages. Each one writes a timeline event, a progress value and its duration to the
job, so the dashboard, the API stream and the worker heartbeat all see it advance.

| Stage | What happens | Progress at the end |
| :-- | :-- | :-- |
| **Survey** | Read the question and choose a depth, recording why | 8% |
| **Plan** | Break the question into sections, each with one question | 18% |
| **Descend** | Search for sources for every question; number each new document | 50% |
| **Draft** | Write each section from its sources, citing them as [n] | 90% |
| **Surface** | Write the key findings and assemble the Markdown report | 100% |

The dashboard draws these as a sounding line: a shallow dive bottoms out at 200 m, a deep one at
4,000 m.

## Choosing a depth

`auto` routes deep when the question asks to compare, evaluate, design, recommend or weigh
trade-offs, or when it has several parts; direct questions ("What is KEDA?") go shallow. A
shallow dive is one section with more sources. A deep dive plans up to `maxReportSections`
sections (five by default): context, approaches, trade-offs, operations and a recommendation.
The recommendation also sees every source gathered for the earlier sections.

## Sources

**The bundled library** is 25 short briefs on running AI agents on Kubernetes: workloads and
rollouts, autoscaling and KEDA, reliable queues, storage, probes, GPUs, inference serving, the
AI-Q blueprint, retrieval, network policy, secrets, observability, tracing, GitOps, Helm, ingress,
pod security, multi-tenancy, batch jobs, disruptions, evaluation and cost. Each brief links to the
official documentation it summarises. They live in
[`apps/research-service/src/kube_research_aiq/library`](../apps/research-service/src/kube_research_aiq/library),
one Markdown file each:

```markdown
---
title: Horizontal Pod Autoscaling
url: https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/
topics: autoscaling, hpa, cpu, scaling
---
First paragraph. Each paragraph is a passage that can be retrieved and cited.

Second paragraph.
```

Passages are ranked with BM25 (title and topics are folded into every passage, and a small
stemmer matches forms like secure and security). No embeddings, GPU or network are needed, and
results are deterministic. To extend the library, add a file; it is picked up on the next start.

**Web search** joins in when `KRAI_TAVILY_API_KEY` is set. Web and library results are
interleaved so both are represented. If the search fails, the dive continues on the library and
the timeline records a warning.

Each section prefers documents that no earlier section has used, so every section adds evidence.
A document keeps the same number everywhere it is cited.

## Writers

**Offline** (the default, `KRAI_PROVIDER=mock`) needs no model. It writes each section by picking
the sentences from that section's sources that best match its question, and cites every one.
Nothing is invented, and the report says so in a footer. CI, demos and clusters without keys get
real, traceable reports this way.

**Model** (`KRAI_PROVIDER=nvidia` with `KRAI_NVIDIA_API_KEY`) calls any OpenAI-compatible
endpoint: NVIDIA's hosted NIM by default, or a vLLM or NIM server via `KRAI_LLM_BASE_URL`.

- The planner model returns the sections as JSON. Anything unparseable falls back to the offline
  plan.
- The deep model writes each section from the numbered sources and must cite them.
- The shallow model writes the key findings.

Citations that point at a source the section wasn't given are ignored.

## Quality signals

Every finished job records `citation_coverage` (the share of sections that cite at least one
source), `sources_cited` and per-stage timings in its metadata. The worker exports dive and stage
durations and cited sources by origin to Prometheus.
