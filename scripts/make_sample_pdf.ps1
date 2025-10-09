param()

if (!(Test-Path .venv)) {
  Write-Error ".venv nicht gefunden. Bitte erst scripts/setup_venv.ps1 ausführen."
  exit 1
}

$python = Join-Path (Get-Location) ".venv/Scripts/python.exe"
$script = Join-Path (Get-Location) "scripts/generate_sample_pdf.py"

& $python $script


