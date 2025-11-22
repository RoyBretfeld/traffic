# ========================================
# FAMO TrafficApp - Robuster Start (PowerShell)
# Rechtsklick -> "Mit PowerShell ausführen"
# ========================================

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath
& "$scriptPath\tools\scripts\start_robust.ps1"

