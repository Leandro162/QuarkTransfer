$ErrorActionPreference = "Stop"

$name = "QuarkTracker"

if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
  throw "Please run this script as Administrator."
}

$existing = Get-Service -Name $name -ErrorAction SilentlyContinue
if ($existing) {
  if ($existing.Status -ne "Stopped") {
    Stop-Service -Name $name -Force
    Start-Sleep -Seconds 2
  }
  sc.exe delete $name | Out-Null
  Write-Host "Service uninstalled: $name"
} else {
  Write-Host "Service is not installed: $name"
}
