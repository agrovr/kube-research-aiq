param(
  [string]$ClusterName = "kuberesearch",
  [string]$Namespace = "aiq-system",
  [int]$ApiPort = 8000,
  [int]$DashboardPort = 5173,
  [switch]$SkipDeploy,
  [switch]$SkipSmoke,
  [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot

function Require-Command {
  param([string]$Name)

  if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
    throw "$Name is required but was not found on PATH."
  }
}

function Test-PortListening {
  param([int]$Port)

  $listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
  return $null -ne $listener
}

function Wait-HttpReady {
  param(
    [string]$Url,
    [int]$TimeoutSeconds = 45
  )

  $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
  do {
    try {
      Invoke-RestMethod -Uri $Url -TimeoutSec 3 | Out-Null
      return $true
    }
    catch {
      Start-Sleep -Seconds 2
    }
  } while ((Get-Date) -lt $deadline)

  return $false
}

function Start-LocalPortForward {
  param(
    [string]$Service,
    [int]$LocalPort,
    [int]$RemotePort
  )

  if (Test-PortListening -Port $LocalPort) {
    Write-Host "Port $LocalPort is already listening; leaving it as-is."
    return
  }

  $pwsh = Get-Command pwsh -ErrorAction SilentlyContinue
  if (-not $pwsh) {
    $pwsh = Get-Command powershell -ErrorAction Stop
  }

  $escapedRoot = $repoRoot.Replace("'", "''")
  $command = "Set-Location -LiteralPath '$escapedRoot'; kubectl -n $Namespace port-forward svc/$Service $LocalPort`:$RemotePort"
  $process = Start-Process $pwsh.Source -WindowStyle Minimized -PassThru -ArgumentList @("-NoExit", "-Command", $command)
  Write-Host "Started port-forward for svc/$Service on localhost:$LocalPort (pid=$($process.Id))."
}

Require-Command docker
Require-Command kind
Require-Command kubectl
Require-Command helm

Set-Location $repoRoot

if (-not $SkipDeploy) {
  & "$PSScriptRoot\create-kind-cluster.ps1" -ClusterName $ClusterName
  & "$PSScriptRoot\deploy-kind.ps1" -ClusterName $ClusterName -Namespace $Namespace
}

Start-LocalPortForward `
  -Service "kuberesearch-kube-research-aiq-api" `
  -LocalPort $ApiPort `
  -RemotePort 80

Start-LocalPortForward `
  -Service "kuberesearch-kube-research-aiq-dashboard" `
  -LocalPort $DashboardPort `
  -RemotePort 80

$readyUrl = "http://127.0.0.1:$ApiPort/readyz"
$dashboardUrl = "http://127.0.0.1:$DashboardPort"

if (-not (Wait-HttpReady -Url $readyUrl)) {
  throw "API did not become ready at $readyUrl. Check the port-forward window and pod logs."
}

if (-not $SkipSmoke) {
  & "$PSScriptRoot\smoke-test.ps1" -BaseUrl "http://127.0.0.1:$ApiPort"
}

if (-not $NoBrowser) {
  Start-Process $dashboardUrl
}

Write-Host ""
Write-Host "KubeResearch AIQ is running locally."
Write-Host "Dashboard: $dashboardUrl"
Write-Host "API readyz: $readyUrl"
Write-Host ""
Write-Host "To stop local access, close the minimized port-forward PowerShell windows."
