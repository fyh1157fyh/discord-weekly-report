$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    throw "Virtual environment not found. Run: powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1"
}

Set-Location $ProjectRoot
& $VenvPython -m discord_weekly_report.main
