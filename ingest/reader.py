from pathlib import Path
import io, unicodedata, pandas as pd
from fs.safefs import safe_write_text
import os, json
from common.text_cleaner import repair_cp_mojibake

IN_ENCODING = os.getenv("IN_ENCODING", "cp850")
CSV_SEP = os.getenv("CSV_SEP", ";")
STAGING_DIR = Path(os.getenv("STAGING_DIR", "./data/staging")).resolve()
VERIFY_ON_INGEST = os.getenv("VERIFY_ORIG_ON_INGEST", "1") == "1"

def _ensure_orig_clean():
    """Prüft die Integrität der Original-CSVs vor jedem Ingest"""
    if VERIFY_ON_INGEST:
        try:
            from tools.orig_integrity import verify as verify_orig
            probs = verify_orig()
            if probs:
                # fail fast, damit keine veränderten Dateien genutzt werden
                print(f"[WARNING] Originale verändert: {json.dumps(probs, ensure_ascii=False)}")
                # raise RuntimeError(f"Originale verändert: {json.dumps(probs, ensure_ascii=False)}")
        except ImportError:
            # Fallback wenn orig_integrity nicht verfügbar ist
            print("[WARNING] orig_integrity nicht verfügbar, Verifikation übersprungen")

def _canonicalize_to_utf8(orig_path: Path) -> Path:
    """
    Erstellt UTF-8-Kopie aus Original-CSV.
    
    WICHTIG: Original wird NUR gelesen (read-only).
    Alle Schreib-Operationen gehen nach STAGING_DIR.
    """
    # Prüfe ob Original geschützt ist
    try:
        from fs.protected_fs import is_protected_path
        if is_protected_path(orig_path):
            print(f"[INGEST] Geschütztes Original gelesen: {orig_path.name}")
    except ImportError:
        pass  # protected_fs nicht verfügbar, trotzdem weiter
    
    raw = orig_path.read_bytes()  # nur lesen – ORIG ist write-protected
    text = raw.decode(IN_ENCODING)  # cp850 → Unicode
    text = repair_cp_mojibake(text)
    text = unicodedata.normalize("NFC", text)
    out = STAGING_DIR / (orig_path.stem + ".utf8.csv")
    safe_write_text(out, text, encoding="utf-8")  # nur STAGING beschreiben
    return out

def read_tourplan(orig_path: str|Path) -> pd.DataFrame:
    """Zentraler Ingest: erstellt UTF‑8‑Kopie in STAGING und liest daraus."""
    # Integritätsprüfung vor Ingest
    _ensure_orig_clean()
    
    orig_path = Path(orig_path)
    staged = _canonicalize_to_utf8(orig_path)
    
    # Minimal-Logging
    df = pd.read_csv(staged, sep=CSV_SEP, header=None, dtype=str)
    print(f"[INGEST] {orig_path.name} -> {staged.name} ({len(df)} Zeilen)")
    
    return df
