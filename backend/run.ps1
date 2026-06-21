# Start the API (frees port 8000 if a stale uvicorn instance is still running)
$ErrorActionPreference = "Stop"
$port = if ($env:PORT) { [int]$env:PORT } else { 8000 }

$listener = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
if ($listener) {
    $pid = $listener.OwningProcess
    Write-Host "Port $port is in use by PID $pid — stopping that process..."
    Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}

$env:PYTHONPATH = $PSScriptRoot
Set-Location $PSScriptRoot
Write-Host "Starting API on http://127.0.0.1:$port"
python -m uvicorn app.main:app --host 127.0.0.1 --port $port
