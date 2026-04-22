param(
  [string]$Namespace = "aiq-system",
  [string]$SecretName = "nvidia-api"
)

$ErrorActionPreference = "Stop"

if (-not $env:KRAI_NVIDIA_API_KEY) {
  $secureKey = Read-Host "Paste NVIDIA API key for this session" -AsSecureString
  $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)
  try {
    $env:KRAI_NVIDIA_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
  }
  finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
  }
}

kubectl get namespace $Namespace | Out-Null
if ($LASTEXITCODE -ne 0) {
  kubectl create namespace $Namespace
}

kubectl -n $Namespace create secret generic $SecretName `
  --from-literal=KRAI_NVIDIA_API_KEY="$env:KRAI_NVIDIA_API_KEY" `
  --dry-run=client `
  -o yaml | kubectl apply -f -

Write-Host "Secret '$SecretName' is configured in namespace '$Namespace'."
