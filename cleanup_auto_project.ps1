param(
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path $PSScriptRoot).Path
$RepoPrefix = $RepoRoot.TrimEnd("\") + "\"
$FreedBytes = 0L

function Get-PathSizeBytes {
    param([Parameter(Mandatory=$true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        return 0L
    }
    $item = Get-Item -LiteralPath $Path -Force
    if (-not $item.PSIsContainer) {
        return [long]$item.Length
    }
    $sum = (Get-ChildItem -LiteralPath $Path -Recurse -Force -File -ErrorAction SilentlyContinue |
        Measure-Object -Property Length -Sum).Sum
    if ($null -eq $sum) {
        return 0L
    }
    return [long]$sum
}

function Assert-InRepo {
    param([Parameter(Mandatory=$true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        return $false
    }
    $resolved = (Resolve-Path -LiteralPath $Path).Path
    if ($resolved -eq $RepoRoot) {
        throw "Refusing to remove repo root: $resolved"
    }
    if (-not ($resolved.StartsWith($RepoPrefix, [System.StringComparison]::OrdinalIgnoreCase))) {
        throw "Refusing to remove path outside repo: $resolved"
    }
    return $true
}

function Remove-CleanTarget {
    param([Parameter(Mandatory=$true)][string]$Path)
    if (-not (Assert-InRepo -Path $Path)) {
        return
    }
    $size = Get-PathSizeBytes -Path $Path
    if ($DryRun) {
        Write-Host ("DRYRUN {0:N2} MB  {1}" -f ($size / 1MB), $Path)
    } else {
        Remove-Item -LiteralPath $Path -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host ("REMOVED {0:N2} MB  {1}" -f ($size / 1MB), $Path)
    }
    $script:FreedBytes += $size
}

$activeRunDirs = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
try {
    $status = Invoke-RestMethod -Uri "http://127.0.0.1:8766/sgzz/status" -TimeoutSec 2
    foreach ($job in @($status.jobs.jobs)) {
        if ($job.state -in @("running", "stopping") -and $job.record_path) {
            $runDir = Split-Path -Parent ([string]$job.record_path)
            if (Test-Path -LiteralPath $runDir) {
                [void]$activeRunDirs.Add((Resolve-Path -LiteralPath $runDir).Path)
            }
        }
    }
} catch {
    Write-Host "WARN could not read active job status; only static cleanup will run."
}

$legacyRuns = Join-Path $RepoRoot "logs\sgzz_runs"
Remove-CleanTarget -Path $legacyRuns

$legacyScreenshots = Join-Path $RepoRoot "logs\screenshots"
Remove-CleanTarget -Path $legacyScreenshots

$logsRoot = Join-Path $RepoRoot "logs"
if (Test-Path -LiteralPath $logsRoot) {
    Get-ChildItem -LiteralPath $logsRoot -Force -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Extension -in @(".png", ".jpg", ".jpeg", ".webp") } |
        ForEach-Object { Remove-CleanTarget -Path $_.FullName }
}

$remoteRunsRoot = Join-Path $RepoRoot "logs\remote_app_control\devices"
if (Test-Path -LiteralPath $remoteRunsRoot) {
    Get-ChildItem -LiteralPath $remoteRunsRoot -Recurse -Directory -Force -ErrorAction SilentlyContinue |
        Where-Object { $_.Parent.Name -eq "sgzz_runs" -and $_.Name -match "^\d{8}_\d{6}$" } |
        ForEach-Object {
            $resolved = (Resolve-Path -LiteralPath $_.FullName).Path
            if (-not $activeRunDirs.Contains($resolved)) {
                Remove-CleanTarget -Path $resolved
            } else {
                Write-Host "KEEP active run $resolved"
            }
        }
}

$distRoot = Join-Path $RepoRoot "dist"
if (Test-Path -LiteralPath $distRoot) {
    $latestZip = Get-ChildItem -LiteralPath $distRoot -Force -File -Filter "*.zip" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    Get-ChildItem -LiteralPath $distRoot -Force -ErrorAction SilentlyContinue |
        ForEach-Object {
            if ($latestZip -and -not $_.PSIsContainer -and $_.FullName -eq $latestZip.FullName) {
                Write-Host "KEEP latest package $($_.FullName)"
            } else {
                Remove-CleanTarget -Path $_.FullName
            }
        }
}

$oldOverlayVenv = Join-Path $RepoRoot "android_overlay_bridge\python_server\.venv"
Remove-CleanTarget -Path $oldOverlayVenv

Get-ChildItem -LiteralPath $RepoRoot -Recurse -Force -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -in @("__pycache__", ".pytest_cache", ".mypy_cache") } |
    ForEach-Object { Remove-CleanTarget -Path $_.FullName }

Write-Host ("Total freed estimate: {0:N2} MB" -f ($FreedBytes / 1MB))
