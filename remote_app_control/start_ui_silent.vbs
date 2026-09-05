Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

root = fso.GetParentFolderName(WScript.ScriptFullName)
serverDir = root & "\python_server"
pythonw = serverDir & "\.venv\Scripts\pythonw.exe"
uiPath = serverDir & "\ui.py"

If fso.FileExists(pythonw) Then
    shell.CurrentDirectory = serverDir
    shell.Run """" & pythonw & """ """ & uiPath & """ --host 0.0.0.0 --port 8766", 0, False
Else
    scriptPath = root & "\start_ui.ps1"
    shell.Run "powershell.exe -WindowStyle Hidden -NoProfile -ExecutionPolicy Bypass -File """ & scriptPath & """", 0, False
End If
