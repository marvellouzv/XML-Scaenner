$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"
$log = Join-Path $root "start-local.log"

function Test-PortFree([int]$Port) {
    $listener = New-Object System.Net.Sockets.TcpListener([System.Net.IPAddress]::Loopback, $Port)
    try {
        $listener.Start()
        $listener.Stop()
        return $true
    } catch {
        return $false
    }
}

function Get-FreePort([int[]]$Candidates) {
    foreach ($port in $Candidates) {
        if (Test-PortFree $port) { return $port }
    }
    throw "No free port found in: $($Candidates -join ', ')"
}

$backendPort = Get-FreePort @(8011, 8000, 8020, 8030, 8040)
$frontendPort = Get-FreePort @(5180, 5173, 5190, 5200, 5210)

@"
started_at=$(Get-Date -Format o)
backend_port=$backendPort
frontend_port=$frontendPort
"@ | Set-Content -Path $log

$python = Join-Path $backend "venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "Backend venv not found. Run: cd backend; python -m venv venv; pip install -r requirements.txt"
}

Start-Process -FilePath $python -ArgumentList @(
    "-m", "uvicorn", "main:app",
    "--reload",
    "--port", "$backendPort",
    "--host", "127.0.0.1"
) -WorkingDirectory $backend -WindowStyle Hidden

Start-Sleep -Seconds 2

$frontendCmd = "Set-Location '$frontend'; `$env:VITE_BACKEND_PORT='$backendPort'; npm run dev -- --port $frontendPort --strictPort --host 127.0.0.1"
Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoProfile", "-Command", $frontendCmd) -WindowStyle Hidden

Add-Content -Path $log -Value "backend_url=http://127.0.0.1:$backendPort"
Add-Content -Path $log -Value "frontend_url=http://127.0.0.1:$frontendPort"
Add-Content -Path $log -Value "api_docs=http://127.0.0.1:$backendPort/docs"
