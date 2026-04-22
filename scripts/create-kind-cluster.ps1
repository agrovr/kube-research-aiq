param(
  [string]$ClusterName = "kuberesearch"
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command kind -ErrorAction SilentlyContinue)) {
  Write-Error "kind is not installed. Install it from https://kind.sigs.k8s.io/docs/user/quick-start/ and rerun this script."
  exit 1
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
  Write-Error "Docker is not installed or not on PATH."
  exit 1
}

$existing = kind get clusters | Where-Object { $_ -eq $ClusterName }
if (-not $existing) {
  kind create cluster --name $ClusterName --config kind/kind-config.yaml
}
else {
  Write-Host "kind cluster '$ClusterName' already exists."
}

kubectl cluster-info --context "kind-$ClusterName"
