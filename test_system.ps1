# Umfassender System-Test
# Startet Server und testet alle Endpoints

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗"
Write-Host "║          🔍 UMFASSENDER SYSTEM-TEST 🔍                       ║"
Write-Host "╚═══════════════════════════════════════════════════════════════╝"
Write-Host ""

# 1. Alle Python-Prozesse beenden
Write-Host "1️⃣  Beende alle Python-Prozesse..."
$procs = Get-Process python -ErrorAction SilentlyContinue
if ($procs) {
    $procs | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    Write-Host "   ✅ $($procs.Count) Prozess(e) beendet"
} else {
    Write-Host "   ✅ Keine Prozesse gefunden"
}

# 2. Prüfe venv
Write-Host ""
Write-Host "2️⃣  Prüfe venv..."
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "   ✅ Venv vorhanden"
    & "venv\Scripts\Activate.ps1"
} else {
    Write-Host "   ❌ Venv fehlt!"
    exit 1
}

# 3. Teste SQLAlchemy
Write-Host ""
Write-Host "3️⃣  Teste SQLAlchemy..."
try {
    python -c "from sqlalchemy import text; print('OK')" 2>&1 | Out-Null
    Write-Host "   ✅ SQLAlchemy funktioniert"
} catch {
    Write-Host "   ❌ SQLAlchemy-Fehler!"
    exit 1
}

# 4. Starte Server im Hintergrund
Write-Host ""
Write-Host "4️⃣  Starte Server..."
$job = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    & "venv\Scripts\Activate.ps1"
    python start_server.py
}

Write-Host "   ✅ Server-Job gestartet (ID: $($job.Id))"

# 5. Warte auf Server-Start
Write-Host ""
Write-Host "5️⃣  Warte auf Server-Start (max. 15 Sekunden)..."
$maxWait = 15
$waited = 0
$serverReady = $false

while ($waited -lt $maxWait -and -not $serverReady) {
    Start-Sleep -Seconds 2
    $waited += 2
    Write-Host "   Warte... ($waited/$maxWait Sekunden)"
    
    try {
        $r = Invoke-WebRequest -Uri http://127.0.0.1:8111/health -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        $serverReady = $true
        Write-Host "   ✅ Server antwortet!"
    } catch {
        # Server noch nicht bereit
    }
}

if (-not $serverReady) {
    Write-Host "   ❌ Server antwortet nicht nach $maxWait Sekunden"
    Write-Host "   Prüfe Job-Status..."
    Receive-Job $job -ErrorAction SilentlyContinue | Select-Object -Last 10
    Stop-Job $job
    Remove-Job $job
    exit 1
}

# 6. Teste alle Endpoints
Write-Host ""
Write-Host "6️⃣  Teste Endpoints..."

$tests = @(
    @{Name="Backend Health"; Url="http://127.0.0.1:8111/health"},
    @{Name="OSRM Health"; Url="http://127.0.0.1:8111/health/osrm"},
    @{Name="DB Health"; Url="http://127.0.0.1:8111/health/db"},
    @{Name="Frontend"; Url="http://127.0.0.1:8111/"},
    @{Name="KI-Kosten"; Url="http://127.0.0.1:8111/admin/ki-kosten"},
    @{Name="Cost Tracker API"; Url="http://127.0.0.1:8111/api/cost-tracker/stats"}
)

$success = 0
$failed = 0

foreach ($test in $tests) {
    try {
        $r = Invoke-WebRequest -Uri $test.Url -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
        Write-Host "   ✅ $($test.Name): Status $($r.StatusCode)"
        $success++
    } catch {
        Write-Host "   ❌ $($test.Name): $($_.Exception.Message)"
        $failed++
    }
}

# 7. Zusammenfassung
Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗"
Write-Host "║                    ZUSAMMENFASSUNG                            ║"
Write-Host "╚═══════════════════════════════════════════════════════════════╝"
Write-Host ""
Write-Host "✅ Erfolgreich: $success"
Write-Host "❌ Fehlgeschlagen: $failed"
Write-Host ""
Write-Host "Server läuft im Hintergrund (Job ID: $($job.Id))"
Write-Host "Server stoppen: Stop-Job $($job.Id); Remove-Job $($job.Id)"
Write-Host ""

