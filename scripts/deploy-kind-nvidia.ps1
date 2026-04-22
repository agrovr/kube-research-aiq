param(
  [string]$ClusterName = "kuberesearch",
  [string]$Namespace = "aiq-system",
  [string]$Model = "mistralai/mixtral-8x7b-instruct-v0.1"
)

$ErrorActionPreference = "Stop"

if (-not $env:KRAI_NVIDIA_API_KEY) {
  Write-Host "KRAI_NVIDIA_API_KEY is not set in this shell. The secret setup step will prompt for it."
}

.\scripts\set-nvidia-secret.ps1 -Namespace $Namespace

docker build -t kube-research-aiq/research-service:dev apps/research-service
docker build -t kube-research-aiq/dashboard:dev apps/dashboard

kind load docker-image kube-research-aiq/research-service:dev --name $ClusterName
kind load docker-image kube-research-aiq/dashboard:dev --name $ClusterName

helm upgrade --install kuberesearch charts/kube-research-aiq `
  --namespace $Namespace `
  --create-namespace `
  --values charts/kube-research-aiq/values-kind.yaml `
  --values charts/kube-research-aiq/values-kind-nvidia.yaml `
  --set config.shallowModel="$Model" `
  --set config.deepModel="$Model" `
  --set config.classifierModel="$Model"

kubectl -n $Namespace rollout restart deployment/kuberesearch-kube-research-aiq-api
kubectl -n $Namespace rollout restart deployment/kuberesearch-kube-research-aiq-worker
kubectl -n $Namespace rollout restart deployment/kuberesearch-kube-research-aiq-dashboard

kubectl -n $Namespace rollout status deployment/kuberesearch-kube-research-aiq-api
kubectl -n $Namespace rollout status deployment/kuberesearch-kube-research-aiq-worker
kubectl -n $Namespace rollout status deployment/kuberesearch-kube-research-aiq-dashboard

Write-Host "NVIDIA provider mode deployed with model '$Model'."
