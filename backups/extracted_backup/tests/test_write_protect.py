import os, pytest
from pathlib import Path
from fs.safefs import init_policy, safe_write_text

def setup_module():
    init_policy(
        os.getenv("ORIG_DIR","./tourplaene"), 
        os.getenv("STAGING_DIR","./data/staging"), 
        os.getenv("OUTPUT_DIR","./data/output"),
        os.getenv("BACKUP_DIR","./routen")
    )

def test_write_blocked_in_orig(tmp_path):
    orig = Path(os.getenv("ORIG_DIR","./tourplaene"))
    (orig/"probe.csv").write_text("x;y\n", encoding="utf-8")  # erlaubt: manueller Drop
    with pytest.raises(PermissionError):
        safe_write_text(orig/"new.csv", "a;b\n")

def test_write_blocked_in_backup(tmp_path):
    backup = Path(os.getenv("BACKUP_DIR","./routen"))
    with pytest.raises(PermissionError):
        safe_write_text(backup/"new.csv", "a;b\n")

def test_write_allowed_in_staging(tmp_path):
    stag = Path(os.getenv("STAGING_DIR","./data/staging"))
    safe_write_text(stag/"ok.csv", "a;b\n")
    assert (stag/"ok.csv").exists()
