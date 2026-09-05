@echo off
setlocal
cd /d "%~dp0"
set "ADB_PATH=%~dp0adb\adb.exe"
set "PATH=%~dp0adb;%PATH%"

if not exist "%~dp0.venv\Scripts\python.exe" (
    echo Virtual environment not found. Run install_dependencies.bat first.
    pause
    exit /b 1
)

pushd "%~dp0remote_app_control\python_server"
"%~dp0.venv\Scripts\python.exe" -c "from app import registry; print('ADB:', registry.adb_path); print('Devices:', [d['device_id'] for d in registry.scan_devices(force=True)])"
popd
pause
