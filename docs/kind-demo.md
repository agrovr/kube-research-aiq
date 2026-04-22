# kind Demo

This project targets `kind` for the local Kubernetes demo path. `kind` is a good
portfolio target because it lets reviewers run the platform on a laptop without
cloud credentials.

## Prerequisites

- Docker Desktop running with the Linux engine enabled
- `kubectl`
- `helm`
- `kind`

## Create the cluster

```powershell
.\scripts\create-kind-cluster.ps1
```

## Deploy the platform

```powershell
.\scripts\deploy-kind.ps1
```

The kind values file deploys Redis for queueing and PostgreSQL for durable job
metadata. Both run as single-replica StatefulSets for local demo simplicity.

The chart also renders a Grafana dashboard ConfigMap. In a cluster with the
Grafana sidecar enabled, it can be discovered by the `grafana_dashboard=1` label.

## Open the dashboard

```powershell
kubectl -n aiq-system port-forward svc/kuberesearch-kube-research-aiq-dashboard 5173:80
```

Open `http://localhost:5173`.

This URL is only reachable from your laptop while the port-forward process is
running. It is perfect for a local demo, but it is not a public deployment. Use
[deployment options](deployment-options.md) when you want a live URL that other
people can open.

The Helm chart mounts an nginx config into the dashboard pod so `/v1`,
`/readyz`, `/healthz`, and `/metrics` are proxied to the API service. That means
the dashboard works through a single port-forward.

## Open the API

```powershell
kubectl -n aiq-system port-forward svc/kuberesearch-kube-research-aiq-api 8000:80
```

Check readiness:

```powershell
Invoke-RestMethod http://localhost:8000/readyz
```

## Use NVIDIA-hosted endpoints

Do not commit API keys into Helm values. Put the key in your shell and create a
Kubernetes Secret:

```powershell
$env:KRAI_NVIDIA_API_KEY = "paste-key-here"
.\scripts\set-nvidia-secret.ps1
```

Deploy kind with NVIDIA provider mode:

```powershell
.\scripts\deploy-kind-nvidia.ps1
```

Use a specific model returned by the NVIDIA models endpoint:

```powershell
.\scripts\deploy-kind-nvidia.ps1 -Model "ai21labs/jamba-1.5-large-instruct"
```

Run an end-to-end smoke test through Kubernetes:

```powershell
.\scripts\smoke-kind-nvidia.ps1
```

The smoke test creates a shallow research job and fails if the result still came
from the mock provider.

## Validate chat completions locally

The basic key validator checks `/models`. To also verify chat completions:

```powershell
.\scripts\validate-nvidia-key.ps1 -Chat -ChatModel "01-ai/yi-large"
```

If a model appears in `/models` but fails with `404` on `/chat/completions`, use
another chat-capable model. The default kind NVIDIA model is currently
`mistralai/mixtral-8x7b-instruct-v0.1` because it validates against the hosted
chat completions endpoint.
