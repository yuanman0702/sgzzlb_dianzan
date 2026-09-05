@echo off
setlocal
cd /d "%~dp0"

set "ADB_PATH=%~dp0adb\adb.exe"
set "PATH=%~dp0adb;%PATH%"

if not exist "%ADB_PATH%" (
    echo Bundled adb.exe was not found: %ADB_PATH%
    pause
    exit /b 1
)

if not exist "%~dp0.venv\Scripts\pythonw.exe" (
    call "%~dp0install_dependencies.bat"
    if errorlevel 1 exit /b 1
)

start "" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0remote_app_control\python_server\ui.py" --host 0.0.0.0 --port 8766
exit /b 0
