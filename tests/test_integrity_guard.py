from pathlib import Path
import os
import tempfile

def test_manifest_detects_modification(tmp_path):
    # Setup temporäre Umgebung
    orig = tmp_path/"tourplaene"; orig.mkdir(parents=True)
    (orig/"A.csv").write_text("Kunde;Adresse\nX;Y\n", encoding="utf-8")
    
    # Umgebungsvariablen setzen
    old_orig_dir = os.environ.get("ORIG_DIR")
    old_manifest = os.environ.get("INTEGRITY_MANIFEST")
    
    os.environ["ORIG_DIR"] = str(orig)
    os.environ["INTEGRITY_MANIFEST"] = str(tmp_path/"data"/"orig_manifest.json")
    
    try:
        # Import nach Umgebungsvariablen-Setzung
        from tools.orig_integrity import collect, save_manifest, verify
        
        # build manifest
        save_manifest(collect())
        assert verify()==[]  # ok
        
        # modify file
        (orig/"A.csv").write_text("Kunde;Adresse\nX;Z\n", encoding="utf-8")
        probs = verify()
        assert any(p["issue"]=="modified" for p in probs)
        
    finally:
        # Umgebungsvariablen zurücksetzen
        if old_orig_dir is not None:
            os.environ["ORIG_DIR"] = old_orig_dir
        elif "ORIG_DIR" in os.environ:
            del os.environ["ORIG_DIR"]
            
        if old_manifest is not None:
            os.environ["INTEGRITY_MANIFEST"] = old_manifest
        elif "INTEGRITY_MANIFEST" in os.environ:
            del os.environ["INTEGRITY_MANIFEST"]
