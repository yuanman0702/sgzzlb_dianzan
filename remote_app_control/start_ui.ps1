$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$ServerDir = Join-Path $Root "python_server"
$Python = Join-Path $ServerDir ".venv\Scripts\python.exe"
$Pythonw = Join-Path $ServerDir ".venv\Scripts\pythonw.exe"
$LogDir = Join-Path $Root "..\logs\remote_app_control"
$Stdout = Join-Path $LogDir "ui_stdout.log"
$Stderr = Join-Path $LogDir "ui_stderr.log"

if (-not (Test-Path $Python)) {
    python -m venv (Join-Path $ServerDir ".venv")
    & $Python -m pip install -r (Join-Path $ServerDir "requirements.txt")
}

New-Item -ItemType Directory -Force $LogDir | Out-Null

if (Test-Path $Pythonw) {
    Start-Process `
        -FilePath $Pythonw `
        -ArgumentList @("ui.py", "--host", "0.0.0.0", "--port", "8766") `
        -WorkingDirectory $ServerDir `
        -RedirectStandardOutput $Stdout `
        -RedirectStandardError $Stderr
} else {
    Start-Process `
        -FilePath $Python `
        -ArgumentList @("ui.py", "--host", "0.0.0.0", "--port", "8766") `
        -WorkingDirectory $ServerDir `
        -WindowStyle Hidden `
        -RedirectStandardOutput $Stdout `
        -RedirectStandardError $Stderr
}
