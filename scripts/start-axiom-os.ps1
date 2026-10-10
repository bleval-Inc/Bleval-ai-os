param(
    [switch]$Build
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $repoRoot "backend"
$dashboardDir = Join-Path $repoRoot "dashboard"

function Stop-PortProcess {
    param([int]$Port)

    $connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    if ($null -eq $connections) {
        return
    }

    $procIds = $connections | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($procId in $procIds) {
        if ($procId) {
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        }
    }
}

Stop-PortProcess -Port 3000
Stop-PortProcess -Port 8000

$backendPython = Join-Path $backendDir ".venv\Scripts\python.exe"
if (-not (Test-Path $backendPython)) {
    throw "Backend venv not found at $backendPython. Activate or recreate the backend virtual environment first."
}

$backendLogsDir = Join-Path $backendDir "logs"
if (-not (Test-Path $backendLogsDir)) {
    New-Item -ItemType Directory -Path $backendLogsDir -Force | Out-Null
}

$backendStdOut = Join-Path $backendLogsDir "backend-stdout.log"
$backendStdErr = Join-Path $backendLogsDir "backend-stderr.log"
$dashboardLogsDir = Join-Path $dashboardDir "logs"
if (-not (Test-Path $dashboardLogsDir)) {
    New-Item -ItemType Directory -Path $dashboardLogsDir -Force | Out-Null
}
$dashboardStdOut = Join-Path $dashboardLogsDir "dashboard-stdout.log"
$dashboardStdErr = Join-Path $dashboardLogsDir "dashboard-stderr.log"

Write-Host "Starting Axiom OS backend on http://localhost:8000"
Start-Process -FilePath $backendPython -ArgumentList "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000" -WorkingDirectory $backendDir -NoNewWindow -RedirectStandardOutput $backendStdOut -RedirectStandardError $backendStdErr

if ($Build) {
    Write-Host "Building dashboard..."
    Push-Location $dashboardDir
    npm run build
    Pop-Location
}

Write-Host "Starting Axiom OS dashboard on http://localhost:3000"
Start-Process -FilePath "npm.cmd" -ArgumentList "run", "start", "--", "--hostname", "127.0.0.1", "--port", "3000" -WorkingDirectory $dashboardDir -NoNewWindow -RedirectStandardOutput $dashboardStdOut -RedirectStandardError $dashboardStdErr

Write-Host "AXIOM OS is starting."
Write-Host "Backend: http://localhost:8000"
Write-Host "Dashboard: http://localhost:3000"
