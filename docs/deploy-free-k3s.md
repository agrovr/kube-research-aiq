# Free Public Deployment with k3s

This is the recommended public deployment track when the goal is to keep the
project free while still using Kubernetes as the real orchestration layer.

The design is:

- Oracle Cloud Always Free Ampere A1 VM
- k3s as the Kubernetes distribution
- Traefik Ingress and ServiceLB from k3s
- cert-manager and Let's Encrypt for TLS
- GitHub Container Registry images from this repository
- In-cluster Redis and PostgreSQL StatefulSets
- NVIDIA-hosted chat completions through a Kubernetes Secret

This avoids paid managed Kubernetes clusters and paid cloud load balancers.

## Free-tier guardrails

Oracle's Always Free documentation says all OCI accounts include Always Free
resources in the home region for the life of the account. The Ampere A1 Compute
allowance is listed as 3,000 OCPU hours and 18,000 GB hours per month, which is
equivalent to 4 OCPUs and 24 GB of memory for Always Free tenancies. Oracle also
lists 200 GB of Always Free block volume storage.

To keep this deployment free:

- Use an Always Free eligible `VM.Standard.A1.Flex` instance.
- Stay at or below 4 OCPUs and 24 GB RAM total across Ampere A1 instances.
- Keep boot/block volume usage within the Always Free storage allowance.
- Do not create paid managed databases, paid OKE clusters, or extra paid load
  balancers.
- Add a budget alert in OCI before deploying.

Free capacity can be unavailable in some regions. If OCI reports no capacity,
wait, try another availability domain, or choose a different home region before
you build anything around the deployment.

## VM setup

Create one Ubuntu Always Free Ampere A1 VM in OCI:

- Shape: `VM.Standard.A1.Flex`
- OCPU: `2` to `4`
- Memory: `12 GB` to `24 GB`
- Boot volume: keep within Always Free limits
- Public IPv4: enabled

Open inbound ports in the OCI security list or network security group:

- `22/tcp` for SSH from your IP
- `80/tcp` for HTTP
- `443/tcp` for HTTPS
- `6443/tcp` for Kubernetes API from your IP only

## Install k3s on the VM

SSH into the VM and install k3s:

```bash
curl -sfL https://get.k3s.io | sh -
sudo kubectl get nodes
```

k3s includes Traefik Ingress by default and includes ServiceLB, which can expose
LoadBalancer Services through host ports without a cloud load balancer.

Copy kubeconfig to your local machine:

```bash
sudo cat /etc/rancher/k3s/k3s.yaml
```

Save it locally as a kubeconfig file, replace `127.0.0.1` with the VM public IP,
and set `KUBECONFIG`:

```powershell
$env:KUBECONFIG = "C:\Users\ashmi\.kube\kube-research-aiq-free.yaml"
kubectl get nodes
```

## Choose a free DNS name

For a no-cost demo hostname, use a wildcard IP DNS service such as `sslip.io`.
For example, if the VM public IP is `203.0.113.10`, use:

```text
203.0.113.10.sslip.io
```

For a nicer portfolio URL, point a domain you already own at the VM public IP.
The domain itself may not be free, so the `sslip.io` option is the no-cost path.

## Deploy KubeResearch AIQ

Set your NVIDIA key only in the current shell:

```powershell
$env:KRAI_NVIDIA_API_KEY = "paste-key-here"
```

Deploy:

```powershell
.\scripts\deploy-free-k3s.ps1 `
  -HostName "203.0.113.10.sslip.io" `
  -LetsEncryptEmail "you@example.com"
```

The script:

- Installs or upgrades cert-manager using its OCI Helm chart
- Creates a `letsencrypt-prod` ClusterIssuer for Traefik
- Creates the `nvidia-api` Secret
- Installs the Helm chart using the public GHCR images
- Enables Ingress with Traefik and TLS
- Waits for API, worker, and dashboard rollouts

Check the deployment:

```powershell
kubectl -n aiq-system get pods
kubectl -n aiq-system get ingress,certificate
kubectl -n aiq-system describe certificate kuberesearch-tls
```

Open:

```text
https://203.0.113.10.sslip.io
```

## Cleanup

To stop the app:

```powershell
helm -n aiq-system uninstall kuberesearch
helm -n cert-manager uninstall cert-manager
```

To stop all possible OCI usage, terminate the VM and delete unused boot volumes
from the OCI console. This matters because storage can remain after instance
termination depending on how the VM was deleted.

## References

- Oracle Always Free resources: https://docs.oracle.com/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm
- k3s quick start: https://docs.k3s.io/quick-start
- k3s networking services: https://docs.k3s.io/networking/networking-services
- cert-manager Helm install: https://cert-manager.io/docs/installation/helm/
