Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

root = fso.GetParentFolderName(WScript.ScriptFullName)
adbPath = root & "\adb\adb.exe"
pythonw = root & "\.venv\Scripts\pythonw.exe"
uiPath = root & "\remote_app_control\python_server\ui.py"

If Not fso.FileExists(pythonw) Then
    shell.Run "cmd.exe /c """ & root & "\install_dependencies.bat""", 1, True
End If

If fso.FileExists(pythonw) And fso.FileExists(adbPath) Then
    shell.Environment("PROCESS")("ADB_PATH") = adbPath
    shell.Environment("PROCESS")("PATH") = root & "\adb;" & shell.Environment("PROCESS")("PATH")
    shell.CurrentDirectory = root
    shell.Run """" & pythonw & """ """ & uiPath & """ --host 0.0.0.0 --port 8766", 0, False
Else
    MsgBox "Missing dependency. Please run install_dependencies.bat first and check adb\adb.exe.", 48, "ADB Emulator Control Server"
End If
