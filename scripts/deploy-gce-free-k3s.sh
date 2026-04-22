#!/usr/bin/env bash
set -euo pipefail

HOST_NAME="${1:-}"
NAMESPACE="${NAMESPACE:-aiq-system}"

if [[ -z "$HOST_NAME" ]]; then
  echo "Usage: ./scripts/deploy-gce-free-k3s.sh <host-name>"
  echo "Example: ./scripts/deploy-gce-free-k3s.sh 203.0.113.10.sslip.io"
  exit 1
fi

if ! command -v kubectl >/dev/null 2>&1; then
  echo "kubectl was not found on PATH."
  exit 1
fi

if ! command -v helm >/dev/null 2>&1; then
  echo "helm was not found on PATH."
  exit 1
fi

if [[ -z "${KRAI_NVIDIA_API_KEY:-}" ]]; then
  echo "Set KRAI_NVIDIA_API_KEY before deploying."
  exit 1
fi

echo "Using Kubernetes context:"
kubectl config current-context || true

kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
kubectl -n "$NAMESPACE" create secret generic nvidia-api \
  --from-literal=KRAI_NVIDIA_API_KEY="$KRAI_NVIDIA_API_KEY" \
  --dry-run=client -o yaml | kubectl apply -f -

helm upgrade --install kuberesearch charts/kube-research-aiq \
  --namespace "$NAMESPACE" \
  --create-namespace \
  --values charts/kube-research-aiq/values.yaml \
  --values charts/kube-research-aiq/values-free-micro.yaml \
  --set ingress.host="$HOST_NAME" \
  --set config.corsOrigins="http://$HOST_NAME"

kubectl -n "$NAMESPACE" rollout status deployment/kuberesearch-kube-research-aiq-api --timeout=180s
kubectl -n "$NAMESPACE" rollout status deployment/kuberesearch-kube-research-aiq-dashboard --timeout=180s

echo "KubeResearch AIQ deployed."
echo "Open: http://$HOST_NAME"
