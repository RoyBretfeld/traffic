# PowerShell-Script zum Erstellen eines Windows Task Scheduler Jobs
# für tägliches Datenbank-Backup um 16:00 Uhr

$scriptPath = Join-Path $PSScriptRoot "db_backup.py"
$pythonPath = (Get-Command python).Path
$taskName = "FAMO_TrafficApp_DB_Backup"
$description = "Tägliches Backup der traffic.db Datenbank um 16:00 Uhr"

# Prüfe ob Task bereits existiert
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue

if ($existingTask) {
    Write-Host "Task existiert bereits. Aktualisiere..."
    # Task löschen
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

# Task erstellen
$action = New-ScheduledTaskAction -Execute $pythonPath -Argument "`"$scriptPath`""
$trigger = New-ScheduledTaskTrigger -Daily -At "4:00 PM"
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Task registrieren
Register-ScheduledTask -TaskName $taskName -Description $description -Action $action -Trigger $trigger -Settings $settings -RunLevel Highest

Write-Host "Task erfolgreich erstellt: $taskName"
Write-Host "Backup wird täglich um 16:00 Uhr ausgeführt."
Write-Host ""
Write-Host "Task anzeigen: Get-ScheduledTask -TaskName '$taskName'"
Write-Host "Task löschen: Unregister-ScheduledTask -TaskName '$taskName' -Confirm:`$false"

