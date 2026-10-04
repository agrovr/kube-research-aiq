# Demo walkthrough

A five-minute tour for code reviews, interviews and short talks.

## The pitch

KubeResearch AIQ runs research agents on Kubernetes. Ask a question and it decides how deep to
go: a shallow dive returns one cited answer, a deep dive plans the question, gathers sources for
each part and writes a full report where every claim cites its source. The API, workers, queue and
store are separate workloads that scale and recover on their own, packaged with Helm and delivered
with Argo CD.

## 1. Start it

```bash
make install dashboard-install
make run-api        # terminal 1: offline API with paced dives on :8000
make dashboard-dev  # terminal 2: the console on :5173
```

Or the whole platform with Redis, PostgreSQL and a separate worker: `docker compose up --build`.

## 2. Run a deep dive

Pick the first example question and press **Dive**. Point out:

- The **sounding line** descending through survey, plan, descend, draft and surface, with each
  stage's time. A deep dive bottoms out at 4,000 m; try "What is KEDA?" to see a 200 m shallow one.
- The **routing reason** under the gauge: why it chose deep.
- Sections filling in as they are drafted, each with its question.
- **Citation chips**: click one to jump to the source, with its link and the passage used.
- **Cancel dive** while it runs, then **Dive again**.
- **Download Markdown** when it surfaces.

## 3. Show the platform

```bash
./scripts/local-demo.ps1        # Windows: kind cluster, chart, port-forwards, smoke test
kubectl -n aiq-system get deploy,statefulset,svc,hpa,networkpolicy,cronjob
curl -s localhost:8000/v1/meta | jq
```

Talking points:

- API and workers are separate Deployments, so request handling and research scale apart.
- Workers take jobs with `BLMOVE`; a crashed worker's job is requeued by heartbeat, never lost.
- Rollouts are graceful: a worker finishes its dive after SIGTERM.
- Workers can scale on queue length with KEDA instead of CPU.
- Offline mode keeps CI deterministic and still produces real, cited reports; the same chart
  switches to NVIDIA-hosted or self-hosted models with one value and a Secret.

## Questions to be ready for

**Why Kubernetes?** The project is about orchestrating long-running agent work: independent
scaling, rollouts, health checks, secrets, network isolation and metrics come with the platform.

**Why not just call a model?** A single call can't show its sources. The pipeline retrieves first
and writes from numbered sources, so every claim is traceable and coverage is measurable.

**What happens if a worker dies mid-dive?** The job id stays in the processing list. Once its
heartbeat is older than five minutes, another worker returns it to the front of the queue. After
three attempts it is failed with the reason.

**What would you build next?** See the [roadmap](roadmap.md): hybrid retrieval, concurrent
researchers, tracing and per-tenant fairness.
