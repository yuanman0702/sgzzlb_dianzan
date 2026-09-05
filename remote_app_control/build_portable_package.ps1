$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$PackageName = "sgzz_adb_control_portable_$Timestamp"
$DistRoot = Join-Path $RepoRoot "dist"
$PackageDir = Join-Path $DistRoot $PackageName
$ZipPath = Join-Path $DistRoot "$PackageName.zip"

function Copy-CleanDirectory {
    param(
        [Parameter(Mandatory=$true)][string]$Source,
        [Parameter(Mandatory=$true)][string]$Destination
    )
    New-Item -ItemType Directory -Force $Destination | Out-Null
    robocopy $Source $Destination /E /XD __pycache__ .pytest_cache .mypy_cache .venv build android logs /XF *.pyc *.pyo | Out-Null
    if ($LASTEXITCODE -le 7) {
        $global:LASTEXITCODE = 0
    } else {
        throw "robocopy failed: $Source -> $Destination"
    }
}

function Find-Adb {
    $candidates = @()
    if ($env:ADB_PATH) {
        $candidates += $env:ADB_PATH
    }
    $sdk = $env:ANDROID_HOME
    if (-not $sdk) {
        $sdk = $env:ANDROID_SDK_ROOT
    }
    if ($sdk) {
        $candidates += (Join-Path $sdk "platform-tools\adb.exe")
    }
    $whereAdb = Get-Command adb.exe -ErrorAction SilentlyContinue
    if ($whereAdb) {
        $candidates += $whereAdb.Source
    }
    $candidates += @(
        "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe",
        "C:\leidian\LDPlayer14\adb.exe",
        "D:\leidian\LDPlayer14\adb.exe",
        "E:\leidian\LDPlayer14\adb.exe",
        "C:\Program Files\dnplayerext2\adb.exe",
        "D:\Program Files\dnplayerext2\adb.exe",
        "E:\Program Files\dnplayerext2\adb.exe"
    )
    foreach ($path in $candidates) {
        if ($path -and (Test-Path $path)) {
            return (Resolve-Path $path).Path
        }
    }
    throw "adb.exe was not found."
}

New-Item -ItemType Directory -Force $DistRoot | Out-Null
if (Test-Path $PackageDir) {
    Remove-Item -LiteralPath $PackageDir -Recurse -Force
}
New-Item -ItemType Directory -Force $PackageDir | Out-Null

Copy-CleanDirectory -Source (Join-Path $RepoRoot "remote_app_control\python_server") -Destination (Join-Path $PackageDir "remote_app_control\python_server")
Copy-CleanDirectory -Source (Join-Path $RepoRoot "emulator_bot") -Destination (Join-Path $PackageDir "emulator_bot")
Copy-CleanDirectory -Source (Join-Path $RepoRoot "assets\templates") -Destination (Join-Path $PackageDir "assets\templates")

Copy-Item -LiteralPath (Join-Path $RepoRoot "remote_app_control\README.md") -Destination (Join-Path $PackageDir "remote_app_control\README.md") -Force
Copy-Item -LiteralPath (Join-Path $RepoRoot "remote_app_control\portable\install_dependencies.bat") -Destination (Join-Path $PackageDir "install_dependencies.bat") -Force
Copy-Item -LiteralPath (Join-Path $RepoRoot "remote_app_control\portable\start_server_ui.bat") -Destination (Join-Path $PackageDir "start_server_ui.bat") -Force
Copy-Item -LiteralPath (Join-Path $RepoRoot "remote_app_control\portable\start_server_ui_silent.vbs") -Destination (Join-Path $PackageDir "start_server_ui_silent.vbs") -Force
Copy-Item -LiteralPath (Join-Path $RepoRoot "remote_app_control\portable\health_check.bat") -Destination (Join-Path $PackageDir "health_check.bat") -Force
Copy-Item -LiteralPath (Join-Path $RepoRoot "remote_app_control\portable\README_PORTABLE.md") -Destination (Join-Path $PackageDir "README_PORTABLE.md") -Force

$accountFile = Join-Path $RepoRoot "sgzz_accounts.txt"
if (Test-Path $accountFile) {
    Copy-Item -LiteralPath $accountFile -Destination (Join-Path $PackageDir "sgzz_accounts.txt") -Force
} else {
    New-Item -ItemType File -Path (Join-Path $PackageDir "sgzz_accounts.txt") | Out-Null
}

$likeTargetFile = Join-Path $RepoRoot "sgzz_like_target.txt"
if (Test-Path $likeTargetFile) {
    Copy-Item -LiteralPath $likeTargetFile -Destination (Join-Path $PackageDir "sgzz_like_target.txt") -Force
} else {
    New-Item -ItemType File -Path (Join-Path $PackageDir "sgzz_like_target.txt") | Out-Null
}

@"
[adb]
path = ""
device_serial = ""

[connect]
auto_connect_hosts = ["127.0.0.1"]
auto_connect_ports = [5555, 5557, 5559, 5561, 5563, 5565]

[paths]
screenshot_dir = "logs/screenshots"
debug_dir = "logs/debug"
template_dir = "assets/templates"

[vision]
default_timeout_seconds = 8.0
poll_interval_seconds = 0.35
click_jitter_pixels = 3
"@ | Set-Content -Path (Join-Path $PackageDir "config.toml") -Encoding UTF8

$adb = Find-Adb
$adbDir = Split-Path -Parent $adb
$targetAdbDir = Join-Path $PackageDir "adb"
New-Item -ItemType Directory -Force $targetAdbDir | Out-Null
foreach ($name in @("adb.exe", "AdbWinApi.dll", "AdbWinUsbApi.dll", "libwinpthread-1.dll", "NOTICE.txt", "source.properties")) {
    $source = Join-Path $adbDir $name
    if (Test-Path $source) {
        Copy-Item -LiteralPath $source -Destination (Join-Path $targetAdbDir $name) -Force
    }
}
if (-not (Test-Path (Join-Path $targetAdbDir "adb.exe"))) {
    throw "Failed to copy adb.exe."
}

New-Item -ItemType Directory -Force (Join-Path $PackageDir "logs") | Out-Null
if (Test-Path $ZipPath) {
    Remove-Item -LiteralPath $ZipPath -Force
}
Compress-Archive -Path (Join-Path $PackageDir "*") -DestinationPath $ZipPath -Force

Write-Host "Package directory: $PackageDir"
Write-Host "Package zip:       $ZipPath"
