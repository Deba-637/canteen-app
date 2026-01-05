Set fso = CreateObject("Scripting.FileSystemObject")
currentDir = fso.GetParentFolderName(WScript.ScriptFullName)

Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = oWS.ExpandEnvironmentStrings("%USERPROFILE%\Desktop\Canteen App.lnk")

Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = currentDir & "\start_server.bat"
oLink.WorkingDirectory = currentDir
oLink.IconLocation = "shell32.dll, 17"
oLink.Save

MsgBox "Shortcut created successfully on your Desktop!", 64, "Canteen App"
