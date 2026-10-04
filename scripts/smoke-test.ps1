param(
  [string]$BaseUrl = "http://localhost:8000",
  [int]$TimeoutSeconds = 120
)

# Sends one deep dive and waits for it to surface with a cited report.
$body = @{
  query = "Compare Kubernetes deployment strategies for AI research agents."
  depth = "deep"
  tenant = "smoke-test"
  tags = @("smoke")
} | ConvertTo-Json

$created = Invoke-RestMethod -Method Post -Uri "$BaseUrl/v1/research" -ContentType "application/json" -Body $body
Write-Host "Dive $($created.job_id): $($created.message)"

$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
do {
  Start-Sleep -Seconds 2
  $job = Invoke-RestMethod -Method Get -Uri "$BaseUrl/v1/research/$($created.job_id)"
  Write-Host ("  {0,-9} {1,-8} {2:P0}" -f $job.status, $job.stage, $job.progress)
} while ($job.status -in @("queued", "running") -and (Get-Date) -lt $deadline)

if ($job.status -ne "succeeded") {
  throw "Dive ended as '$($job.status)': $($job.error)"
}
Write-Host "Surfaced: $($job.title) with $($job.sources.Count) sources across $($job.sections.Count) sections."
