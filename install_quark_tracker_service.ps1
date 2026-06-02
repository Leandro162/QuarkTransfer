$ErrorActionPreference = "Stop"

$name = "QuarkTracker"
$displayName = "Quark Tracker"
$port = 8765
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$source = Join-Path $root "QuarkTrackerService.cs"
$exe = Join-Path $root "QuarkTrackerService.exe"
$compiler = "$env:WINDIR\Microsoft.NET\Framework64\v4.0.30319\csc.exe"

if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
  throw "Please run this script as Administrator."
}

& $compiler /nologo /target:exe /out:$exe /reference:System.ServiceProcess.dll $source
if ($LASTEXITCODE -ne 0) {
  throw "Failed to compile QuarkTrackerService.exe."
}

$existing = Get-Service -Name $name -ErrorAction SilentlyContinue
if ($existing) {
  if ($existing.Status -ne "Stopped") {
    Stop-Service -Name $name -Force
    Start-Sleep -Seconds 2
  }
  sc.exe delete $name | Out-Null
  Start-Sleep -Seconds 2
}

$listeners = netstat -ano -p tcp | Select-String ":$port\s+.*LISTENING"
foreach ($listener in $listeners) {
  $parts = ($listener.Line -split "\s+") | Where-Object { $_ }
  $pid = [int]$parts[-1]
  Write-Host "Stopping existing process on port $port, PID $pid"
  taskkill /PID $pid /F | Out-Null
  Start-Sleep -Seconds 1
}

sc.exe create $name binPath= "`"$exe`"" start= auto DisplayName= "$displayName" | Out-Null
sc.exe description $name "Runs the local Quark share tracker at http://127.0.0.1:8765/tracker" | Out-Null
Start-Service -Name $name
Start-Sleep -Seconds 2

$status = Get-Service -Name $name
Write-Host "Service installed: $($status.Name) $($status.Status)"
Write-Host "Tracker page: http://127.0.0.1:8765/tracker"
