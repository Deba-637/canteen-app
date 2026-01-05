$TargetFile = "$PSScriptRoot\start_server.bat"
$ShortcutFile = "$env:USERPROFILE\Desktop\Canteen App.lnk"
$WScriptShell = New-Object -ComObject WScript.Shell
$Shortcut = $WScriptShell.CreateShortcut($ShortcutFile)
$Shortcut.TargetPath = $TargetFile
$Shortcut.WorkingDirectory = $PSScriptRoot
$Shortcut.IconLocation = "shell32.dll, 17"
$Shortcut.Save()

Write-Host "Shortcut created successfully on Desktop!" -ForegroundColor Green
Start-Sleep -Seconds 3
