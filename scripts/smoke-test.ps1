param(
  [string]$BaseUrl = "http://localhost:8000"
)

$body = @{
  query = "Compare Kubernetes-native deployment strategies for AI research agents."
  depth = "deep"
  tenant = "smoke-test"
} | ConvertTo-Json

$created = Invoke-RestMethod -Method Post -Uri "$BaseUrl/v1/research" -ContentType "application/json" -Body $body
Write-Host "Created job $($created.job_id)"
Start-Sleep -Seconds 3
$job = Invoke-RestMethod -Method Get -Uri "$BaseUrl/v1/research/$($created.job_id)"
$job | ConvertTo-Json -Depth 8
