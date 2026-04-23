# Deploy to DigitalOcean Kubernetes

This guide documents a managed Kubernetes deployment for KubeResearch AIQ on
DigitalOcean Kubernetes, or DOKS. It keeps the deployment architecture focused on
standard Kubernetes objects while offloading control-plane management to
DigitalOcean. This is not the no-cost deployment path.

For a no-cost public deployment, use [deploy-free-k3s.md](deploy-free-k3s.md).

The guide uses a pragmatic live-demo profile:

- DOKS for the public Kubernetes cluster
- GitHub Container Registry images from this repository
- ingress-nginx for public HTTP/HTTPS routing
- cert-manager and Let's Encrypt for TLS
- In-cluster Redis and PostgreSQL StatefulSets for a simple portfolio deployment
- NVIDIA-hosted chat completions through a Kubernetes Secret

For a stricter production profile, keep the same chart but move Redis and
PostgreSQL to managed services and use `values-production.yaml`.

## Prerequisites

- A DigitalOcean account and a DOKS cluster
- `doctl`, authenticated with DigitalOcean
- `kubectl`
- `helm`
- A DNS name for the deployment, for example `research.example.com`
- An NVIDIA API key exported in the active shell as `KRAI_NVIDIA_API_KEY`

DigitalOcean documents DOKS as a managed Kubernetes service that works with
standard Kubernetes tools and DigitalOcean load balancers. The connection guide
uses `doctl kubernetes cluster kubeconfig save <cluster-name>` to merge DOKS
credentials into a local kubeconfig.

## Create or select a DOKS cluster

Create the cluster in the DigitalOcean UI, or use `doctl` from a terminal. For a
demonstration environment, a small multi-node cluster makes Deployments,
StatefulSets, HPAs, and rollouts meaningful.

Connect `kubectl`:

```powershell
doctl kubernetes cluster kubeconfig save kube-research-aiq
kubectl get nodes
```

## Deploy with the helper script

Set the NVIDIA key only in the active shell:

```powershell
$env:KRAI_NVIDIA_API_KEY = "paste-key-here"
```

Run:

```powershell
.\scripts\deploy-doks.ps1 `
  -ClusterName "kube-research-aiq" `
  -HostName "research.example.com" `
  -LetsEncryptEmail "admin@example.com"
```

The script:

- Connects `kubectl` to the DOKS cluster
- Installs or upgrades ingress-nginx
- Installs or upgrades cert-manager
- Creates a `letsencrypt-prod` ClusterIssuer
- Creates the `nvidia-api` Secret in `aiq-system`
- Installs the Helm chart with public Ingress and TLS enabled
- Waits for API, worker, and dashboard rollouts

After ingress-nginx creates a load balancer, point the DNS record at the load
balancer address. TLS may remain pending until DNS resolves correctly.

Check the public resources:

```powershell
kubectl -n ingress-nginx get service ingress-nginx-controller
kubectl -n aiq-system get ingress,certificate,pods
kubectl -n aiq-system describe certificate kuberesearch-tls
```

## Manual Helm equivalent

For a manual deployment, create the NVIDIA Secret:

```powershell
kubectl create namespace aiq-system --dry-run=client -o yaml | kubectl apply -f -
kubectl -n aiq-system create secret generic nvidia-api `
  --from-literal=KRAI_NVIDIA_API_KEY="$env:KRAI_NVIDIA_API_KEY" `
  --dry-run=client -o yaml | kubectl apply -f -
```

Then deploy:

```powershell
helm upgrade --install kuberesearch charts/kube-research-aiq `
  --namespace aiq-system `
  --create-namespace `
  --values charts/kube-research-aiq/values.yaml `
  --values charts/kube-research-aiq/values-kind-nvidia.yaml `
  --set image.tag=latest `
  --set image.pullPolicy=Always `
  --set dashboard.image.tag=latest `
  --set dashboard.image.pullPolicy=Always `
  --set ingress.enabled=true `
  --set ingress.host=research.example.com `
  --set ingress.tls[0].secretName=kuberesearch-tls `
  --set ingress.tls[0].hosts[0]=research.example.com `
  --set-string ingress.annotations.cert-manager\.io/cluster-issuer=letsencrypt-prod `
  --set config.corsOrigins=https://research.example.com
```

## Cleanup

To avoid ongoing cloud costs when the demo is over:

```powershell
helm -n aiq-system uninstall kuberesearch
helm -n ingress-nginx uninstall ingress-nginx
helm -n cert-manager uninstall cert-manager
doctl kubernetes cluster delete kube-research-aiq
```

Before deleting a cluster, verify whether persistent volume data or exported
reports must be retained.

## References

- DigitalOcean DOKS connection guide: https://docs.digitalocean.com/products/kubernetes/how-to/connect-to-cluster/
- `doctl kubernetes cluster kubeconfig save`: https://docs.digitalocean.com/reference/doctl/reference/kubernetes/cluster/kubeconfig/save/
- DigitalOcean ingress-nginx Marketplace guide: https://docs.digitalocean.com/products/marketplace/catalog/nginx-ingress-controller/
- cert-manager Helm install docs: https://cert-manager.io/docs/installation/helm/
