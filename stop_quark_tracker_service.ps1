Stop-Service -Name "QuarkTracker" -Force
Start-Sleep -Seconds 1
Get-Service -Name "QuarkTracker"
