from fastapi.testclient import TestClient
from fs.safefs import init_policy
import tempfile
from pathlib import Path
import os

# PathPolicy für Tests initialisieren
def setup_test_policy():
    temp_dir = Path(tempfile.mkdtemp())
    orig_dir = temp_dir / "tourplaene"
    staging_dir = temp_dir / "data" / "staging"
    output_dir = temp_dir / "data" / "output"
    backup_dir = temp_dir / "routen"
    
    for dir_path in [orig_dir, staging_dir, output_dir, backup_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # Umgebungsvariablen setzen
    os.environ["ORIG_DIR"] = str(orig_dir)
    os.environ["STAGING_DIR"] = str(staging_dir)
    os.environ["OUTPUT_DIR"] = str(output_dir)
    os.environ["BACKUP_DIR"] = str(backup_dir)
    
    init_policy(str(orig_dir), str(staging_dir), str(output_dir), str(backup_dir))
    return temp_dir

# Setup vor Tests
test_temp_dir = setup_test_policy()

# App nach PathPolicy-Initialisierung importieren
from backend.app import create_app
app = create_app()
client = TestClient(app)

def test_csv_export_utf8_header():
    r = client.get("/export/tourplan")
    print(f"Status: {r.status_code}")
    print(f"Headers: {r.headers}")
    if r.status_code != 200:
        print(f"Error: {r.text}")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv; charset=utf-8")
    txt = r.content.decode("utf-8")
    assert "ö" in txt or "ß" in txt  # sichtbare Umlaute

def test_csv_export_excel_bom():
    r = client.get("/export/tourplan", params={"excel": True})
    print(f"Status: {r.status_code}")
    if r.status_code != 200:
        print(f"Error: {r.text}")
    assert r.status_code == 200
    # UTF‑8 BOM
    assert r.content[:3] == b"\xef\xbb\xbf"

def test_json_charset_utf8():
    r = client.get("/api/tourplan/status")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/json; charset=utf-8")
    text = r.text
    assert "ö" in text or "ß" in text  # keine \u‑Escapes nötig
