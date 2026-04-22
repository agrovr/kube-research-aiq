param(
  [string]$BaseUrl = "https://integrate.api.nvidia.com/v1",
  [string]$ChatModel = "",
  [switch]$Chat
)

if (-not $env:KRAI_NVIDIA_API_KEY) {
  Write-Error "Set KRAI_NVIDIA_API_KEY in your current shell before running this script."
  exit 1
}

$headers = @{
  Authorization = "Bearer $env:KRAI_NVIDIA_API_KEY"
}

try {
  $response = Invoke-RestMethod -Method Get -Uri "$($BaseUrl.TrimEnd('/'))/models" -Headers $headers
  Write-Host "NVIDIA API key accepted. Models endpoint returned successfully."
  if ($response.data) {
    $response.data | Select-Object -First 8 -Property id, owned_by | Format-Table -AutoSize
  }

  if ($Chat) {
    if (-not $ChatModel) {
      $ChatModel = $response.data[0].id
    }

    $payload = @{
      model = $ChatModel
      messages = @(
        @{
          role = "user"
          content = "Reply with one short sentence confirming this NVIDIA API key can call chat completions."
        }
      )
      temperature = 0.1
      max_tokens = 80
    } | ConvertTo-Json -Depth 6

    $chatResponse = Invoke-RestMethod `
      -Method Post `
      -Uri "$($BaseUrl.TrimEnd('/'))/chat/completions" `
      -Headers $headers `
      -ContentType "application/json" `
      -Body $payload

    Write-Host ""
    Write-Host "Chat completion succeeded with model '$ChatModel'."
    Write-Host $chatResponse.choices[0].message.content
  }
}
catch {
  Write-Error "NVIDIA API key validation failed: $($_.Exception.Message)"
  if ($_.ErrorDetails.Message) {
    Write-Error $_.ErrorDetails.Message
  }
  exit 1
}
