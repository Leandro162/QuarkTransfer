$ErrorActionPreference = "Stop"

try {
  Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8765/api/shutdown" | Out-Null
  Write-Host "QuarkTransfer shutdown request sent."
}
catch {
  Write-Host "QuarkTransfer is not running on port 8765."
}
