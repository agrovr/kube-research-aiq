param(
    [Parameter(Mandatory = $true)]
    [string]$HostName,

    [Parameter(Mandatory = $true)]
    [string]$LetsEncryptEmail,

    [string]$Namespace = "aiq-system",
    [switch]$SkipCertManager,
    [switch]$SkipNvidiaSecret
)

$ErrorActionPreference = "Stop"

function Require-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command '$Name' was not found on PATH."
    }
}

Require-Command kubectl
Require-Command helm

Write-Host "Using Kubernetes context:"
kubectl config current-context

if (-not $SkipCertManager) {
    Write-Host "Installing or upgrading cert-manager..."
    helm upgrade --install cert-manager oci://quay.io/jetstack/charts/cert-manager `
        --namespace cert-manager `
        --create-namespace `
        --set crds.enabled=true `
        --wait

    $issuer = @"
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: $LetsEncryptEmail
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
      - http01:
          ingress:
            class: traefik
"@

    $issuer | kubectl apply -f -
}

kubectl create namespace $Namespace --dry-run=client -o yaml | kubectl apply -f -

if (-not $SkipNvidiaSecret) {
    if (-not $env:KRAI_NVIDIA_API_KEY) {
        throw "Set KRAI_NVIDIA_API_KEY in this PowerShell session or rerun with -SkipNvidiaSecret."
    }

    kubectl -n $Namespace create secret generic nvidia-api `
        --from-literal=KRAI_NVIDIA_API_KEY="$env:KRAI_NVIDIA_API_KEY" `
        --dry-run=client -o yaml | kubectl apply -f -
}

Write-Host "Deploying KubeResearch AIQ to k3s..."
$helmArgs = @(
    "upgrade",
    "--install",
    "kuberesearch",
    "charts/kube-research-aiq",
    "--namespace",
    $Namespace,
    "--create-namespace",
    "--values",
    "charts/kube-research-aiq/values.yaml",
    "--values",
    "charts/kube-research-aiq/values-kind-nvidia.yaml",
    "--set",
    "image.tag=latest",
    "--set",
    "image.pullPolicy=Always",
    "--set",
    "dashboard.image.tag=latest",
    "--set",
    "dashboard.image.pullPolicy=Always",
    "--set",
    "ingress.enabled=true",
    "--set",
    "ingress.className=traefik",
    "--set",
    "ingress.host=$HostName",
    "--set",
    "ingress.tls[0].secretName=kuberesearch-tls",
    "--set",
    "ingress.tls[0].hosts[0]=$HostName",
    "--set-string",
    "ingress.annotations.cert-manager\.io/cluster-issuer=letsencrypt-prod",
    "--set",
    "config.corsOrigins=https://$HostName"
)

helm @helmArgs

kubectl -n $Namespace rollout status deployment/kuberesearch-kube-research-aiq-api --timeout=180s
kubectl -n $Namespace rollout status deployment/kuberesearch-kube-research-aiq-worker --timeout=180s
kubectl -n $Namespace rollout status deployment/kuberesearch-kube-research-aiq-dashboard --timeout=180s

Write-Host "Deployment submitted. Public URL: https://$HostName"
Write-Host "Check resources with: kubectl -n $Namespace get ingress,certificate,pods"
