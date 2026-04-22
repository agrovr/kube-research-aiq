param(
  [string]$Namespace = "aiq-system",
  [int]$LocalPort = 18080,
  [int]$TimeoutSeconds = 90
)

$ErrorActionPreference = "Stop"

$portForward = $null
$startedPortForward = $false

New-Item -ItemType Directory -Force -Path ".tmp" | Out-Null

function Test-ApiReady {
  try {
    $ready = Invoke-RestMethod -Uri "http://127.0.0.1:$LocalPort/readyz" -TimeoutSec 3
    return $ready.status -eq "ready"
  }
  catch {
    return $false
  }
}

if (-not (Test-ApiReady)) {
  $portForward = Start-Process -FilePath kubectl `
    -ArgumentList @(
      "-n",
      $Namespace,
      "port-forward",
      "svc/kuberesearch-kube-research-aiq-api",
      "$($LocalPort):80"
    ) `
    -PassThru `
    -WindowStyle Hidden `
    -RedirectStandardOutput ".tmp\smoke-nvidia-port-forward.log" `
    -RedirectStandardError ".tmp\smoke-nvidia-port-forward.err"
  $startedPortForward = $true
  Start-Sleep -Seconds 3
}

try {
  $ready = Invoke-RestMethod -Uri "http://127.0.0.1:$LocalPort/readyz"
  if ($ready.status -ne "ready") {
    throw "API is not ready: $($ready | ConvertTo-Json -Compress)"
  }
  if ($ready.provider -ne "nvidia") {
    throw "Cluster is still using provider '$($ready.provider)'. Run .\scripts\deploy-kind-nvidia.ps1 before the NVIDIA smoke test."
  }

  $body = @{
    query = "In one short paragraph, explain why Kubernetes is useful for orchestrating AI research agents."
    depth = "shallow"
    tenant = "nvidia-smoke"
    tags = @("nvidia", "smoke-test")
  } | ConvertTo-Json

  $created = Invoke-RestMethod -Method Post `
    -Uri "http://127.0.0.1:$LocalPort/v1/research" `
    -ContentType "application/json" `
    -Body $body

  $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
  $job = $null
  do {
    Start-Sleep -Seconds 2
    $job = Invoke-RestMethod -Uri "http://127.0.0.1:$LocalPort/v1/research/$($created.job_id)"
    Write-Host "job=$($job.id) status=$($job.status)"
  } while ($job.status -in @("queued", "running") -and (Get-Date) -lt $deadline)

  if ($job.status -ne "succeeded") {
    throw "NVIDIA smoke job did not succeed. Status=$($job.status) Error=$($job.error)"
  }

  if ($job.report -match "Mock response") {
    throw "NVIDIA smoke job succeeded but still used the mock provider."
  }

  Write-Host "NVIDIA smoke test succeeded."
  Write-Host ""
  Write-Host ($job.report.Substring(0, [Math]::Min(800, $job.report.Length)))
}
finally {
  if ($startedPortForward -and $portForward -and -not $portForward.HasExited) {
    Stop-Process -Id $portForward.Id -Force
  }
}
