# Free Google Cloud VM Deployment with k3s

This is a best-effort free public demo path that avoids GKE. GKE's free tier
covers the cluster management fee, but the compute that runs your pods is still
billable. For a no-cost Google Cloud path, use Compute Engine's Always Free
`e2-micro` VM and run k3s yourself.

This profile is intentionally tiny:

- One `e2-micro` VM in a Google Cloud Always Free region
- k3s as the Kubernetes runtime
- Traefik Ingress from k3s
- No managed GKE cluster
- No Google Cloud Load Balancer
- No in-cluster Redis or PostgreSQL
- One API pod with file-backed demo storage
- One dashboard pod
- Zero worker replicas

It is less production-like than the full kind or Oracle A1 profiles, but it
still demonstrates Kubernetes, Helm, Ingress, Secrets, public images, and NVIDIA
model integration.

## Free-tier guardrails

According to Google Cloud's Free Program docs, the Compute Engine free tier
includes one non-preemptible `e2-micro` VM per month in one of these US regions:

- `us-west1` Oregon
- `us-central1` Iowa
- `us-east1` South Carolina

The same docs list 30 GB-months of standard persistent disk and 1 GB of outbound
data transfer from North America per month. Google also notes that the GKE free
tier covers one cluster management fee, not the workload compute.

To reduce surprise charges:

- Use `e2-micro`, not `e2-small` or larger.
- Use one of the eligible regions above.
- Use a standard persistent disk no larger than 30 GB.
- Do not create GKE, Cloud SQL, Memorystore, NAT Gateway, or a Google Cloud Load
  Balancer for this path.
- Use an ephemeral external IP rather than reserving static IPs.
- Create a budget alert before deploying.
- Stop or delete the VM when you are done testing.

## Create the VM

In Google Cloud Console, create a Compute Engine VM:

- Name: `kube-research-aiq-free`
- Region: `us-central1`, `us-east1`, or `us-west1`
- Machine type: `e2-micro`
- Boot disk: Ubuntu 24.04 LTS
- Boot disk type: Standard persistent disk
- Boot disk size: 30 GB or less
- Firewall: allow HTTP traffic
- SSH: use browser SSH or your own key

After creation, copy the VM external IP. For a free hostname, use `sslip.io`:

```text
<external-ip>.sslip.io
```

For example:

```text
203.0.113.10.sslip.io
```

## Install k3s and Helm

SSH into the VM:

```bash
sudo apt-get update
sudo apt-get install -y git curl
curl -sfL https://get.k3s.io | sh -
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown "$USER:$USER" ~/.kube/config
export KUBECONFIG=~/.kube/config
kubectl get nodes
```

Install Helm:

```bash
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
helm version
```

Clone the project:

```bash
git clone https://github.com/agrovr/kube-research-aiq.git
cd kube-research-aiq
```

## Deploy the tiny profile

Set the NVIDIA key only in the VM shell:

```bash
export KRAI_NVIDIA_API_KEY="paste-key-here"
```

Deploy with the free micro values file:

```bash
chmod +x scripts/deploy-gce-free-k3s.sh
./scripts/deploy-gce-free-k3s.sh "<external-ip>.sslip.io"
```

Check the resources:

```bash
kubectl -n aiq-system get pods
kubectl -n aiq-system get deploy,svc,ingress
kubectl -n aiq-system logs deploy/kuberesearch-kube-research-aiq-api --tail=50
```

Open:

```text
http://<external-ip>.sslip.io
```

## What this profile proves

This is intentionally not the full production architecture. It proves:

- Kubernetes deployment on a public VM
- Helm chart portability
- Public Ingress through k3s Traefik
- Runtime NVIDIA Secret injection
- Public GHCR image pulls
- Dashboard and API integration

Use the full kind or Oracle A1 profiles when you want Redis, PostgreSQL,
replicated workers, autoscaling, and benchmark CronJobs.

## Cleanup

To remove the app:

```bash
helm -n aiq-system uninstall kuberesearch
kubectl delete namespace aiq-system
```

To stop all possible Google Cloud VM cost, stop or delete the VM from Compute
Engine. Delete unused disks if you no longer need the machine.

## References

- Google Cloud Free Program: https://cloud.google.com/free/docs/gcp-free-tier
- Compute Engine free features: https://cloud.google.com/free/docs/compute-getting-started
- GKE pricing: https://cloud.google.com/kubernetes-engine/pricing
- k3s quick start: https://docs.k3s.io/quick-start
