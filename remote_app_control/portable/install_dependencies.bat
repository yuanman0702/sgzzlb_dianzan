@echo off
setlocal
cd /d "%~dp0"

set "PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple"
set "PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn"
set "REQ=%~dp0remote_app_control\python_server\requirements.txt"

echo [1/4] Checking Python...
set "PYTHON_CMD=python"
python --version >nul 2>nul
if errorlevel 1 (
    py -3 --version >nul 2>nul
    if errorlevel 1 (
        echo Python was not found. Please install Python 3.10+ and tick "Add python.exe to PATH".
        pause
        exit /b 1
    )
    set "PYTHON_CMD=py -3"
)

echo [2/4] Creating virtual environment...
if not exist "%~dp0.venv\Scripts\python.exe" (
    %PYTHON_CMD% -m venv "%~dp0.venv"
    if errorlevel 1 (
        echo Failed to create virtual environment.
        pause
        exit /b 1
    )
)

echo [3/4] Upgrading pip from Tsinghua mirror...
"%~dp0.venv\Scripts\python.exe" -m pip install --upgrade pip -i "%PIP_INDEX_URL%" --trusted-host "%PIP_TRUSTED_HOST%"
if errorlevel 1 (
    echo Failed to upgrade pip.
    pause
    exit /b 1
)

echo [4/4] Installing dependencies from Tsinghua mirror...
"%~dp0.venv\Scripts\python.exe" -m pip install -r "%REQ%" -i "%PIP_INDEX_URL%" --trusted-host "%PIP_TRUSTED_HOST%"
if errorlevel 1 (
    echo Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo Dependencies installed successfully.
pause
