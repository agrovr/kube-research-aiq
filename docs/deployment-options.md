# Deployment Options

KubeResearch AIQ has two different access stories: a local portfolio demo and a
public Kubernetes deployment.

## Local demo with kind

The kind workflow runs the full platform on your laptop. It is ideal for
screenshots, interviews, and reviewers who want to clone the repo and verify the
Kubernetes manifests without cloud spend.

Port-forwarding is only a local tunnel from your machine into the kind cluster.
For example, `http://127.0.0.1:15173` works only on your laptop while the
port-forward process is running. It is not a public URL.

Use this mode when you want to demonstrate:

- Helm installation
- Deployments, StatefulSets, ConfigMaps, Secrets, HPA, and NetworkPolicies
- NVIDIA-backed smoke tests with your own key
- Dashboard screenshots and API examples

## Public Kubernetes deployment

Use a reachable Kubernetes cluster when other people need to open the dashboard
or API without running the project themselves. Good targets are:

- GKE Autopilot
- Amazon EKS
- Azure AKS
- DigitalOcean Kubernetes
- A homelab cluster with a public ingress controller

The production values file assumes:

- Images are published to GitHub Container Registry.
- `nginx-ingress` or another Ingress controller is installed.
- `cert-manager` issues TLS certificates.
- PostgreSQL and Redis are managed services or separately installed operators.
- Runtime secrets are stored in a Kubernetes Secret named `krai-runtime-secrets`.

Create the runtime secret in the target namespace:

```bash
kubectl create namespace aiq-system
kubectl -n aiq-system create secret generic krai-runtime-secrets \
  --from-literal=KRAI_NVIDIA_API_KEY="$KRAI_NVIDIA_API_KEY" \
  --from-literal=KRAI_DATABASE_URL="$KRAI_DATABASE_URL" \
  --from-literal=KRAI_REDIS_URL="$KRAI_REDIS_URL"
```

Install with Helm:

```bash
helm upgrade --install kuberesearch charts/kube-research-aiq \
  --namespace aiq-system \
  --create-namespace \
  --values charts/kube-research-aiq/values.yaml \
  --values charts/kube-research-aiq/values-production.yaml \
  --set ingress.host=your-domain.example.com \
  --set config.corsOrigins=https://your-domain.example.com
```

## GitOps deployment with ArgoCD

After the repository is pushed to GitHub, apply the ArgoCD application:

```bash
kubectl apply -f deploy/argocd/application-production.yaml
```

Before using it in a real cluster, update:

- `spec.source.repoURL`
- `ingress.host`
- `config.corsOrigins`
- TLS issuer annotation if your cluster uses a different cert-manager issuer

## Recommended portfolio narrative

For GitHub and interviews, present this project as:

> A Kubernetes-native AI research agent platform with async API/worker
> orchestration, NVIDIA-hosted model integration, Helm packaging, GitOps
> deployment, persistent state, observability, and production overlays.
