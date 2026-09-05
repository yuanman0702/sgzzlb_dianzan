$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$ServerDir = Join-Path $Root "python_server"
$Python = Join-Path $ServerDir ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    python -m venv (Join-Path $ServerDir ".venv")
    & $Python -m pip install -r (Join-Path $ServerDir "requirements.txt")
}

Set-Location $ServerDir
& $Python app.py --host 0.0.0.0 --port 8766
