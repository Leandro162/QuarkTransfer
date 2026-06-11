$ErrorActionPreference = "Stop"

$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "Quark Transfer Tool.lnk"
$launcher = "\\wsl.localhost\Ubuntu-24.04\home\xuelong\projects\Tools\QuarkTransfer\start_quark_transfer.vbs"
$wscript = Join-Path $env:SystemRoot "System32\wscript.exe"

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $wscript
$shortcut.Arguments = "`"$launcher`""
$shortcut.WorkingDirectory = $desktop
$shortcut.Description = "Start QuarkTransfer from the WSL Home repository"
$shortcut.IconLocation = "$env:SystemRoot\System32\shell32.dll,220"
$shortcut.Save()

Write-Host "Created desktop shortcut: $shortcutPath"
