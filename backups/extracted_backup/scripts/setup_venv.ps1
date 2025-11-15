# scripts/setup_venv.ps1
if (!(Test-Path .venv)) { py -3 -m venv .venv }
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
if (Test-Path requirements.txt) { pip install -r requirements.txt } else { Write-Host "Keine requirements.txt gefunden." }
pre-commit install
Write-Host "venv aktiv. Pakete & pre-commit installiert."