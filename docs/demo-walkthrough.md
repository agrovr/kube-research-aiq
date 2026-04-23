# Demo Walkthrough

Use this guide for repository walkthroughs, interview demos, and short technical
presentations of KubeResearch AIQ.

## 90-second pitch

KubeResearch AIQ is a Kubernetes-native AI research agent platform inspired by
NVIDIA AI-Q. It takes a user research request, routes it through shallow or deep
research workflows, runs the work asynchronously through API and worker
Deployments, stores durable reports, and exposes the whole system through Helm,
GitOps, metrics, autoscaling, NetworkPolicy, and a React operator dashboard.

Resume-ready line:

> Built KubeResearch AIQ, a Kubernetes-native AI research agent platform with
> async API/worker orchestration, NVIDIA-hosted model integration, Helm
> packaging, GitOps deployment, persistent state, observability, and production
> overlays.

## Repository tour

Start with the repository overview:

- CI badge is green
- Dashboard screenshot shows the operator workflow
- `apps/research-service` contains the FastAPI API and worker logic
- `apps/dashboard` contains the React dashboard
- `charts/kube-research-aiq` contains the Kubernetes-native deployment
- `deploy/argocd` shows the GitOps path
- `docs/deployment-options.md` compares local and public deployment tracks

## Local demo path

Use mock mode for a fast demo without external services:

```powershell
cd apps/research-service
python -m pip install -e ".[dev]"
$env:KRAI_PROVIDER = "mock"
$env:KRAI_REDIS_URL = ""
$env:KRAI_DATABASE_URL = ""
python -m uvicorn kube_research_aiq.main:app --reload
```

In a second terminal:

```powershell
cd apps/dashboard
npm install
$env:VITE_API_BASE_URL = "http://127.0.0.1:8000"
npm run dev -- --host 127.0.0.1 --port 5173
```

Open `http://127.0.0.1:5173`, create a deep research request, and show:

- Runtime readiness strip
- Job queue
- Selected report inspector
- Markdown report download

## Kubernetes demo path

Use kind to demonstrate the Kubernetes deployment locally:

```powershell
.\scripts\local-demo.ps1
```

For a manual deployment:

```powershell
.\scripts\create-kind-cluster.ps1
.\scripts\deploy-kind.ps1
kubectl -n aiq-system get pods
kubectl -n aiq-system port-forward svc/kuberesearch-kube-research-aiq-dashboard 5173:80
```

For real NVIDIA calls in kind:

```powershell
$env:KRAI_NVIDIA_API_KEY = "paste-key-here"
.\scripts\deploy-kind-nvidia.ps1
.\scripts\smoke-kind-nvidia.ps1
```

Call out that kind port-forwards are local-only. A public URL requires a
reachable Kubernetes cluster and Ingress, as described in
`docs/deployment-options.md`.

## Public deployment path

For a no-cost public Kubernetes demo, use the Oracle Always Free plus k3s track:

```powershell
.\scripts\deploy-free-k3s.ps1 `
  -HostName "203.0.113.10.sslip.io" `
  -LetsEncryptEmail "admin@example.com"
```

This keeps the public deployment Kubernetes-native without requiring a paid
managed Kubernetes control plane or managed load balancer. The DigitalOcean
guide documents a managed-cluster option for environments where a paid platform
is acceptable.

If Oracle Always Free Ampere capacity is unavailable, use the smaller Google
Cloud `e2-micro` k3s profile:

```bash
./scripts/deploy-gce-free-k3s.sh "203.0.113.10.sslip.io"
```

This is a constrained public demo profile. The full Kubernetes architecture is
still demonstrated locally with kind.

For the paid managed-cluster alternative, use:

```powershell
.\scripts\deploy-doks.ps1 `
  -ClusterName "kube-research-aiq" `
  -HostName "research.example.com" `
  -LetsEncryptEmail "admin@example.com"
```

Show these Kubernetes objects:

```powershell
kubectl -n aiq-system get deploy,statefulset,svc,ingress,hpa
kubectl -n aiq-system get configmap,secret,networkpolicy
kubectl -n aiq-system get pods -o wide
```

## Architecture talking points

- The API and worker are separate Deployments so request handling and research
  execution scale independently.
- Redis backs asynchronous queueing; PostgreSQL stores durable job/report state.
- The dashboard is a static React app served by nginx and proxied to the API in
  Kubernetes.
- Helm packages the app with production-like objects: Deployments, StatefulSets,
  ConfigMaps, Secrets, HPA, NetworkPolicy, Ingress, ServiceMonitor, and CronJob.
- ArgoCD manifests show how the same chart can be promoted with GitOps.
- Mock provider mode keeps CI deterministic; NVIDIA mode validates real hosted
  chat completions through a Kubernetes Secret.

## Questions to be ready for

Why Kubernetes?

> The project is about orchestrating AI agent workloads. Kubernetes gives the
> system repeatable deployment, horizontal scaling, rollout control, secret
> management, service discovery, and operational hooks like metrics and health
> checks.

Why API plus worker?

> Research jobs can run longer than an HTTP request. Splitting the API and worker
> lets the API stay responsive while workers scale based on queue pressure.

Why mock mode?

> CI and local demos should be reliable without paid external model calls. The
> same workflow switches to NVIDIA mode through environment configuration and
> Kubernetes Secrets.

What would be improved next?

> Add managed Redis/PostgreSQL for the public cluster, SLO dashboards,
> structured evaluation datasets, and ArgoCD image automation for SHA-pinned
> releases.
