$ErrorActionPreference = "Stop"

$connections = Get-NetTCPConnection -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue
if (-not $connections) {
  Write-Host "Quark transfer is not running on port 8765."
  exit 0
}

$pids = $connections | Select-Object -ExpandProperty OwningProcess -Unique
foreach ($processId in $pids) {
  Stop-Process -Id $processId -Force
  Write-Host "Stopped process on port 8765: $processId"
}
