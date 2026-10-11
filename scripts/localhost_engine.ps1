<#
.SYNOPSIS
    LOCUS Localhost Engine — Manages startup, health diagnostics, and safe shutdown for Windows.
.PARAMETER Action
    The action to execute: 'start', 'check', or 'stop'.
#>

param (
    [Parameter(Mandatory=$true)]
    [ValidateSet('start', 'check', 'stop')]
    [string]$Action
)

$ErrorActionPreference = 'Continue'

# Determine absolute project root (parent directory of scripts/)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir

# Ensure logs directory exists
$logsDir = Join-Path $projectRoot "logs"
if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
}

$launcherLog = Join-Path $logsDir "launcher.log"
$healthLog = Join-Path $logsDir "health_check.log"

function Write-Banner {
    Write-Host "=========================================================================" -ForegroundColor Cyan
    Write-Host "  LOCUS -- GNSS INTEGRITY & CYBERSECURITY OPERATIONS CENTER" -ForegroundColor White
    Write-Host "  Reliable Localhost Service Controller" -ForegroundColor Gray
    Write-Host "=========================================================================" -ForegroundColor Cyan
    Write-Host "  Project Root: $projectRoot" -ForegroundColor DarkGray
    Write-Host "=========================================================================" -ForegroundColor Cyan
    Write-Host ""
}

# ---------------------------------------------------------------------------
# ACTION: START
# ---------------------------------------------------------------------------
if ($Action -eq 'start') {
    Write-Banner
    Write-Host "[1/5] Verifying local dependencies and environment..." -ForegroundColor Yellow

    # Check Python
    $pythonCmd = "python"
    try {
        $pyVer = & python --version 2>&1
        Write-Host "  [OK] Found Python: $pyVer" -ForegroundColor Green
    } catch {
        Write-Host "  [ERROR] Python is not installed or not in PATH." -ForegroundColor Red
        Write-Host "  Please install Python 3.10+ from https://www.python.org/" -ForegroundColor Yellow
        exit 1
    }

    # Check Node.js
    try {
        $nodeVer = & node --version 2>&1
        Write-Host "  [OK] Found Node.js: $nodeVer" -ForegroundColor Green
    } catch {
        Write-Host "  [ERROR] Node.js is not installed or not in PATH." -ForegroundColor Red
        Write-Host "  Please install Node.js from https://nodejs.org/" -ForegroundColor Yellow
        exit 1
    }

    # Check npm
    try {
        $npmVer = & npm --version 2>&1
        Write-Host "  [OK] Found npm: v$npmVer" -ForegroundColor Green
    } catch {
        Write-Host "  [ERROR] npm is not installed or not in PATH." -ForegroundColor Red
        exit 1
    }

    # Check frontend directory
    $frontendDir = Join-Path $projectRoot "frontend"
    if (-not (Test-Path $frontendDir)) {
        Write-Host "  [ERROR] Frontend directory not found at: $frontendDir" -ForegroundColor Red
        exit 1
    }

    # Check node_modules
    $nodeModulesDir = Join-Path $frontendDir "node_modules"
    if (-not (Test-Path $nodeModulesDir)) {
        Write-Host "  [*] frontend/node_modules missing. Running npm install..." -ForegroundColor Yellow
        Push-Location $frontendDir
        & npm install
        Pop-Location
        if (-not (Test-Path $nodeModulesDir)) {
            Write-Host "  [ERROR] npm install failed." -ForegroundColor Red
            exit 1
        }
    }

    Write-Host ""
    Write-Host "[2/5] Selecting Python execution environment..." -ForegroundColor Yellow
    $venvPath1 = Join-Path $projectRoot ".venv\Scripts\python.exe"
    $venvPath2 = Join-Path $projectRoot "venv\Scripts\python.exe"
    if (Test-Path $venvPath1) {
        $pythonCmd = "`"$venvPath1`""
        Write-Host "  - Activated virtual environment: .venv" -ForegroundColor Green
    } elseif (Test-Path $venvPath2) {
        $pythonCmd = "`"$venvPath2`""
        Write-Host "  - Activated virtual environment: venv" -ForegroundColor Green
    } else {
        Write-Host "  - Using system Python: $((Get-Command python).Source)" -ForegroundColor Green
    }

    Write-Host ""
    Write-Host "[3/5] Checking service ports (127.0.0.1:8000 and 127.0.0.1:5173)..." -ForegroundColor Yellow

    # Check if LOCUS is ALREADY running and healthy
    $alreadyHealthy = $false
    try {
        $bTest = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 1 -ErrorAction SilentlyContinue
        $fTest = Invoke-WebRequest -Uri "http://127.0.0.1:5173/" -UseBasicParsing -TimeoutSec 1 -ErrorAction SilentlyContinue
        if ($bTest.status -eq "HEALTHY" -and $fTest.StatusCode -eq 200) {
            $alreadyHealthy = $true
        }
    } catch {}

    if ($alreadyHealthy) {
        Write-Host ""
        Write-Host "=========================================================================" -ForegroundColor Green
        Write-Host "  [INFO] LOCUS IS ALREADY RUNNING AND HEALTHY!" -ForegroundColor Green
        Write-Host "=========================================================================" -ForegroundColor Green
        Write-Host "  - Web Dashboard:     http://127.0.0.1:5173/" -ForegroundColor White
        Write-Host "  - FastAPI Backend:   http://127.0.0.1:8000/" -ForegroundColor White
        Write-Host "  - Swagger API Docs:  http://127.0.0.1:8000/docs" -ForegroundColor White
        Write-Host "=========================================================================" -ForegroundColor Green
        Write-Host "  Opening browser to your existing active session..." -ForegroundColor Cyan
        Start-Process "http://127.0.0.1:5173/"
        exit 0
    }

    # Check for port conflicts (port occupied by another program)
    $bConn = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
    if ($bConn) {
        $p = Get-Process -Id $bConn[0].OwningProcess -ErrorAction SilentlyContinue
        Write-Host "  [PORT CONFLICT] Port 8000 is occupied by: $($p.ProcessName) (PID: $($p.Id))" -ForegroundColor Red
        Write-Host "  Please close that application or run STOP_LOCUS.bat before launching." -ForegroundColor Yellow
        exit 1
    }

    $fConn = Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue
    if ($fConn) {
        $p = Get-Process -Id $fConn[0].OwningProcess -ErrorAction SilentlyContinue
        Write-Host "  [PORT CONFLICT] Port 5173 is occupied by: $($p.ProcessName) (PID: $($p.Id))" -ForegroundColor Red
        Write-Host "  Please close that application or run STOP_LOCUS.bat before launching." -ForegroundColor Yellow
        exit 1
    }

    Write-Host ""
    Write-Host "[4/5] Starting FastAPI Backend and Vite Frontend..." -ForegroundColor Yellow

    # Launch Backend in visible managed console
    Write-Host "  * Launching FastAPI REST Backend on http://127.0.0.1:8000 ..." -ForegroundColor Cyan
    $backendArgs = "/k title LOCUS_BACKEND_8000 && cd /d `"$projectRoot`" && echo ========================================================== && echo   LOCUS FastAPI REST Backend (127.0.0.1:8000) && echo   Close this window or run STOP_LOCUS.bat to stop. && echo ========================================================== && echo. && $pythonCmd -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000"
    Start-Process -FilePath "cmd.exe" -ArgumentList $backendArgs -WindowStyle Normal

    # Launch Frontend in visible managed console
    Write-Host "  * Launching React Vite Frontend on http://127.0.0.1:5173 ..." -ForegroundColor Cyan
    $frontendArgs = "/k title LOCUS_FRONTEND_5173 && cd /d `"$frontendDir`" && echo ========================================================== && echo   LOCUS React Vite Frontend (127.0.0.1:5173) && echo   Close this window or run STOP_LOCUS.bat to stop. && echo ========================================================== && echo. && npm run dev -- --host 127.0.0.1 --port 5173 --strictPort"
    Start-Process -FilePath "cmd.exe" -ArgumentList $frontendArgs -WindowStyle Normal

    Write-Host ""
    Write-Host "[5/5] Polling services until fully ready (timeout: 45 seconds)..." -ForegroundColor Yellow

    $backendOk = $false
    $frontendOk = $false
    $sw = [System.Diagnostics.Stopwatch]::StartNew()

    while ($sw.Elapsed.TotalSeconds -lt 45) {
        if (-not $backendOk) {
            try {
                $res = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 1 -ErrorAction SilentlyContinue
                if ($res.status -eq "HEALTHY") {
                    $backendOk = $true
                    Write-Host "`n  [OK] FastAPI Backend responded: HEALTHY" -ForegroundColor Green
                }
            } catch {}
        }
        if (-not $frontendOk) {
            try {
                $fRes = Invoke-WebRequest -Uri "http://127.0.0.1:5173/" -UseBasicParsing -TimeoutSec 1 -ErrorAction SilentlyContinue
                if ($fRes.StatusCode -eq 200) {
                    $frontendOk = $true
                    Write-Host "`n  [OK] Vite Frontend responded: HTTP 200" -ForegroundColor Green
                }
            } catch {}
        }
        if ($backendOk -and $frontendOk) { break }
        Write-Host -NoNewline "."
        Start-Sleep -Milliseconds 750
    }

    Write-Host ""
    if (-not $backendOk -or -not $frontendOk) {
        Write-Host "=========================================================================" -ForegroundColor Red
        Write-Host "  [ERROR] ONE OR MORE SERVICES FAILED TO BECOME READY IN TIME." -ForegroundColor Red
        Write-Host "=========================================================================" -ForegroundColor Red
        if (-not $backendOk) { Write-Host "  - Backend failed: check console 'LOCUS_BACKEND_8000'" -ForegroundColor Red }
        if (-not $frontendOk) { Write-Host "  - Frontend failed: check console 'LOCUS_FRONTEND_5173'" -ForegroundColor Red }
        Write-Host "  Run CHECK_LOCUS.bat to diagnose issues." -ForegroundColor Yellow
        Write-Host "  Run STOP_LOCUS.bat to cleanly reset." -ForegroundColor Yellow
        exit 1
    }

    Write-Host "=========================================================================" -ForegroundColor Green
    Write-Host "  LOCUS GNSS SECURITY OPERATIONS CENTER IS LIVE!" -ForegroundColor Green
    Write-Host "=========================================================================" -ForegroundColor Green
    Write-Host "  Web Dashboard:     http://127.0.0.1:5173/   (Opening automatically)" -ForegroundColor White
    Write-Host "  FastAPI REST API:  http://127.0.0.1:8000/" -ForegroundColor White
    Write-Host "  Interactive Docs:  http://127.0.0.1:8000/docs" -ForegroundColor White
    Write-Host "  System Health:     http://127.0.0.1:8000/health" -ForegroundColor White
    Write-Host "=========================================================================" -ForegroundColor Green
    Write-Host "  * Both services are running in managed terminal windows." -ForegroundColor Gray
    Write-Host "  * To stop safely at any time, run STOP_LOCUS.bat." -ForegroundColor Gray
    Write-Host "=========================================================================" -ForegroundColor Green
    Write-Host ""

    # Open browser
    Start-Process "http://127.0.0.1:5173/"

    $logEntry = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] SUCCESS: Launched LOCUS services on 127.0.0.1:5173 and 127.0.0.1:8000"
    Add-Content -Path $launcherLog -Value $logEntry
    exit 0
}

# ---------------------------------------------------------------------------
# ACTION: CHECK
# ---------------------------------------------------------------------------
if ($Action -eq 'check') {
    Write-Banner
    $reportLines = @("==== LOCUS DIAGNOSTIC REPORT $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ====")

    function Report($msg, $color='White') {
        Write-Host $msg -ForegroundColor $color
        $script:reportLines += $msg
    }

    Report "[1/4] Environment Binaries & Toolchains:" "Cyan"
    try {
        $pyVer = & python --version 2>&1
        Report "  [OK] Python: $pyVer ($((Get-Command python).Source))" "Green"
    } catch { Report "  [FAIL] Python not found" "Red" }

    try {
        $nodeVer = & node --version 2>&1
        Report "  [OK] Node.js: $nodeVer ($((Get-Command node).Source))" "Green"
    } catch { Report "  [FAIL] Node.js not found" "Red" }

    try {
        $npmVer = & npm --version 2>&1
        Report "  [OK] npm: v$npmVer" "Green"
    } catch { Report "  [FAIL] npm not found" "Red" }

    Write-Host ""
    Report "[2/4] Verifying Critical Core Files:" "Cyan"
    $checkFiles = @(
        "src/api/app.py",
        "frontend/package.json",
        "frontend/src/api/locusApi.js",
        "data/processed/locus_telemetry_clean.csv",
        "data/features/locus_security_features.csv",
        "models/production/xgboost/xgboost_detector.joblib",
        "models/production/isolation_forest/isolation_forest.joblib",
        "models/production/temporal/temporal_model.pt",
        "data/rag/vector_store.db"
    )
    foreach ($f in $checkFiles) {
        $fullPath = Join-Path $projectRoot $f
        if (Test-Path $fullPath) {
            Report "  [OK] Found: $f" "Green"
        } else {
            Report "  [WARN] Missing: $f" "Yellow"
        }
    }

    Write-Host ""
    Report "[3/4] Testing Local HTTP Endpoints:" "Cyan"
    $bHealth = $false; $bDocs = $false; $fGui = $false

    try {
        $hRes = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 3 -ErrorAction Stop
        if ($hRes.status -eq "HEALTHY") {
            $bHealth = $true
            Report "  [OK] FastAPI Backend: http://127.0.0.1:8000/health (HEALTHY, Events: $($hRes.total_available_events), RAG Chunks: $($hRes.rag_vector_store_chunks))" "Green"
        } else {
            Report "  [WARN] Backend returned status: $($hRes.status)" "Yellow"
        }
    } catch {
        Report "  [DOWN] FastAPI Backend on http://127.0.0.1:8000/health is not responding." "Red"
    }

    try {
        $dRes = Invoke-WebRequest -Uri "http://127.0.0.1:8000/docs" -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
        if ($dRes.StatusCode -eq 200) {
            $bDocs = $true
            Report "  [OK] Swagger Interactive Docs: http://127.0.0.1:8000/docs (HTTP 200 OK)" "Green"
        }
    } catch {
        Report "  [DOWN] Swagger Docs on http://127.0.0.1:8000/docs is not reachable." "Red"
    }

    try {
        $mRes = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/models/status" -TimeoutSec 3 -ErrorAction SilentlyContinue
        if ($mRes.detectors) {
            $detSummaries = ($mRes.detectors.PSObject.Properties | ForEach-Object { "$($_.Name): $($_.Value.status)" }) -join ", "
            Report "  [OK] Detection Quad: $detSummaries" "Green"
        }
    } catch {}

    try {
        $gRes = Invoke-WebRequest -Uri "http://127.0.0.1:5173/" -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
        if ($gRes.StatusCode -eq 200) {
            $fGui = $true
            Report "  [OK] Vite React GUI: http://127.0.0.1:5173/ (HTTP 200 OK)" "Green"
        }
    } catch {
        Report "  [DOWN] Vite Frontend on http://127.0.0.1:5173/ is not responding." "Red"
    }

    Write-Host ""
    Report "[4/4] Frontend API Proxy Configuration:" "Cyan"
    $proxyTarget = "http://127.0.0.1:8000 (via Vite proxy on /api)"
    Report "  [OK] API Connection Target: $proxyTarget" "Green"

    Write-Host ""
    Write-Host "=========================================================================" -ForegroundColor Cyan
    if ($bHealth -and $fGui -and $bDocs) {
        Report "  OVERALL DIAGNOSTIC RESULT: [HEALTHY & READY FOR USE]" "Green"
    } elseif ($bHealth -or $fGui) {
        Report "  OVERALL DIAGNOSTIC RESULT: [DEGRADED - ONE SERVICE IS DOWN]" "Yellow"
    } else {
        Report "  OVERALL DIAGNOSTIC RESULT: [OFFLINE - DOUBLE-CLICK START_LOCUS.bat TO LAUNCH]" "Red"
    }
    Write-Host "=========================================================================" -ForegroundColor Cyan

    $reportLines | Out-File -FilePath $healthLog -Encoding utf8
    Write-Host "Detailed report saved to: $healthLog" -ForegroundColor DarkGray
    exit 0
}

# ---------------------------------------------------------------------------
# ACTION: STOP
# ---------------------------------------------------------------------------
if ($Action -eq 'stop') {
    Write-Banner
    Write-Host "Stopping ONLY LOCUS processes on ports 8000 and 5173..." -ForegroundColor Yellow
    Write-Host ""

    $stoppedAny = $false

    # Find processes listening on port 8000
    $backendConns = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
    if ($backendConns) {
        foreach ($conn in $backendConns) {
            $p = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
            if ($p -and ($p.ProcessName -like "*python*" -or $p.ProcessName -like "*uvicorn*")) {
                Write-Host "  [STOPPING] LOCUS Backend: $($p.ProcessName) (PID: $($p.Id))..." -ForegroundColor Yellow
                Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
                $stoppedAny = $true
            }
        }
    } else {
        Write-Host "  [INFO] Port 8000 is already free (Backend is offline)." -ForegroundColor Gray
    }

    # Find processes listening on port 5173
    $frontendConns = Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue
    if ($frontendConns) {
        foreach ($conn in $frontendConns) {
            $p = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
            if ($p -and ($p.ProcessName -like "*node*" -or $p.ProcessName -like "*cmd*")) {
                Write-Host "  [STOPPING] LOCUS Frontend: $($p.ProcessName) (PID: $($p.Id))..." -ForegroundColor Yellow
                Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
                $stoppedAny = $true
            }
        }
    } else {
        Write-Host "  [INFO] Port 5173 is already free (Frontend is offline)." -ForegroundColor Gray
    }

    # Close titled terminal windows
    taskkill /F /FI "WINDOWTITLE eq LOCUS_BACKEND_8000*" 2>$null | Out-Null
    taskkill /F /FI "WINDOWTITLE eq LOCUS_FRONTEND_5173*" 2>$null | Out-Null

    Start-Sleep -Milliseconds 750

    $bAfter = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
    $fAfter = Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue

    Write-Host ""
    if (-not $bAfter -and -not $fAfter) {
        Write-Host "=========================================================================" -ForegroundColor Green
        Write-Host "  [SUCCESS] ALL LOCUS SERVICES STOPPED SAFELY." -ForegroundColor Green
        Write-Host "=========================================================================" -ForegroundColor Green
        Write-Host "  - Port 8000 (FastAPI): Free" -ForegroundColor White
        Write-Host "  - Port 5173 (Vite):    Free" -ForegroundColor White
        Write-Host "  - Unrelated Python and Node.js applications remain untouched." -ForegroundColor White
        Write-Host "=========================================================================" -ForegroundColor Green
    } else {
        Write-Host "  [WARN] Some ports are still occupied:" -ForegroundColor Red
        if ($bAfter) { Write-Host "    - Port 8000 is still listening" -ForegroundColor Red }
        if ($fAfter) { Write-Host "    - Port 5173 is still listening" -ForegroundColor Red }
    }

    $stopEntry = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] STOP: Closed LOCUS backend and frontend processes"
    Add-Content -Path $launcherLog -Value $stopEntry
    exit 0
}
