$ErrorActionPreference = "Stop"

$taskName = "QuarkTransferAlwaysOn"
$userId = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$wsl = Join-Path $env:WINDIR "System32\wsl.exe"
$arguments = "-d Ubuntu-24.04 -- bash /home/xuelong/projects/Tools/QuarkTransfer/run_home_service_forever.sh"

$action = New-ScheduledTaskAction -Execute $wsl -Argument $arguments
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $userId
$principal = New-ScheduledTaskPrincipal -UserId $userId -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet `
  -AllowStartIfOnBatteries `
  -DontStopIfGoingOnBatteries `
  -StartWhenAvailable `
  -RestartCount 999 `
  -RestartInterval (New-TimeSpan -Minutes 1) `
  -ExecutionTimeLimit ([TimeSpan]::Zero)

$task = New-ScheduledTask `
  -Action $action `
  -Trigger $trigger `
  -Principal $principal `
  -Settings $settings `
  -Description "Keep the Home QuarkTransfer service running on 127.0.0.1:8765."

Register-ScheduledTask -TaskName $taskName -InputObject $task -Force | Out-Null
Start-ScheduledTask -TaskName $taskName

Write-Host "Installed and started scheduled task: $taskName"
Write-Host "QuarkTransfer URL: http://127.0.0.1:8765/"
