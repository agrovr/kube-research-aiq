param(
  [string]$ClusterName = "kuberesearch",
  [string]$Namespace = "aiq-system"
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command kind -ErrorAction SilentlyContinue)) {
  Write-Error "kind is not installed."
  exit 1
}

if (-not (Get-Command helm -ErrorAction SilentlyContinue)) {
  Write-Error "helm is not installed."
  exit 1
}

docker build -t kube-research-aiq/research-service:dev apps/research-service
docker build -t kube-research-aiq/dashboard:dev apps/dashboard

kind load docker-image kube-research-aiq/research-service:dev --name $ClusterName
kind load docker-image kube-research-aiq/dashboard:dev --name $ClusterName

helm upgrade --install kuberesearch charts/kube-research-aiq `
  --namespace $Namespace `
  --create-namespace `
  --values charts/kube-research-aiq/values-kind.yaml

kubectl -n $Namespace rollout restart deployment/kuberesearch-kube-research-aiq-api
kubectl -n $Namespace rollout restart deployment/kuberesearch-kube-research-aiq-worker
kubectl -n $Namespace rollout restart deployment/kuberesearch-kube-research-aiq-dashboard

kubectl -n $Namespace rollout status deployment/kuberesearch-kube-research-aiq-api
kubectl -n $Namespace rollout status deployment/kuberesearch-kube-research-aiq-worker
kubectl -n $Namespace rollout status deployment/kuberesearch-kube-research-aiq-dashboard

Write-Host ""
Write-Host "Run this in another terminal to open the dashboard:"
Write-Host "kubectl -n $Namespace port-forward svc/kuberesearch-kube-research-aiq-dashboard 5173:80"
Write-Host ""
Write-Host "Run this in another terminal to open the API:"
Write-Host "kubectl -n $Namespace port-forward svc/kuberesearch-kube-research-aiq-api 8000:80"
