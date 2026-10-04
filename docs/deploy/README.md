# Deployment options

KubeResearch AIQ supports two deployment modes: a local Kubernetes environment
for reproducible demos and a public Kubernetes environment for external access.

## Choosing a guide

| Guide | Where it runs | Cost | What it shows |
| :-- | :-- | :-- | :-- |
| [kind](kind.md) | Your machine | Free | The full chart: Redis, PostgreSQL, workers, Grafana dashboard, benchmark CronJob |
| [Oracle Always Free + k3s](oracle-k3s.md) | A public VM | Free within limits | The full platform behind Traefik and Let's Encrypt |
| [Google Cloud e2-micro + k3s](gce-e2-micro.md) | A public VM | Free within limits | A trimmed profile: API and dashboard only, dives run in the API |
| [DigitalOcean Kubernetes](digitalocean.md) | Managed cluster | Paid | Managed control plane, load balancer and TLS |

## Local demo with kind

The kind workflow runs the full platform on a local development device. It is
ideal for screenshots, interviews, and repository reviewers who want to verify
the Kubernetes manifests without cloud spend.

Port-forwarding creates a local tunnel into the kind cluster. For example,
`http://127.0.0.1:5173` is reachable only on the local device while the
port-forward process is running. It is not a public URL.

Use this mode to demonstrate:

- Helm installation
- Deployments, StatefulSets, ConfigMaps, Secrets, HPA, and NetworkPolicies
- NVIDIA-backed smoke tests with a local runtime key
- Dashboard screenshots and API examples

## Public Kubernetes deployment

Use a reachable Kubernetes cluster when external reviewers need to access the
dashboard or API without running the project themselves.

The recommended free public track is:

- Oracle Cloud Always Free Ampere A1 VM
- k3s as the Kubernetes distribution
- Traefik and ServiceLB from k3s for ingress
- `sslip.io` or an owned domain for DNS

See [Oracle Always Free with k3s](oracle-k3s.md). This path is designed to avoid paid
managed Kubernetes clusters and paid cloud load balancers, as long as you stay
inside the cloud provider's Always Free limits.

If Oracle Ampere capacity is unavailable, use the smaller Google Cloud
`e2-micro` plus k3s track in [Google Cloud e2-micro with k3s](gce-e2-micro.md).
That profile disables Redis, PostgreSQL, autoscaling, and worker replicas so it
can fit on a free-tier VM. It is a constrained public demo profile rather than
the full production architecture.

Paid managed-cluster alternatives are:

- DigitalOcean Kubernetes
- GKE Autopilot
- Azure AKS
- Amazon EKS
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

Add `KRAI_TAVILY_API_KEY` to the same Secret and set `secrets.tavilyExistingSecretName` to
enable live web search next to the bundled library.

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

Before applying it to a target cluster, update:

- `spec.source.repoURL`
- `ingress.host`
- `config.corsOrigins`
- TLS issuer annotation if your cluster uses a different cert-manager issuer
