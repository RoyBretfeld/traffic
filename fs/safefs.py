from __future__ import annotations
from pathlib import Path
import pandas as pd

def safe_to_csv(df, path: str|Path, *, excel: bool=False, sep: str=';', index: bool=False):
    """Schreibt CSV sicher (kein Schreiben in ORIG). Standard UTF‑8; mit excel=True -> UTF‑8 mit BOM."""
    if POLICY is None:
        raise RuntimeError("PathPolicy not initialized")
    p = Path(path)
    POLICY.assert_writable(p)
    enc = 'utf-8-sig' if excel else 'utf-8'
    return df.to_csv(p, encoding=enc, sep=sep, index=index)

class PathPolicy:
    def __init__(self, orig: Path, staging: Path, output: Path, backup: Path = None):
        self.orig, self.staging, self.output = orig.resolve(), staging.resolve(), output.resolve()
        self.backup = backup.resolve() if backup else None
        for p in (self.orig, self.staging, self.output):
            p.mkdir(parents=True, exist_ok=True)
        if self.backup:
            self.backup.mkdir(parents=True, exist_ok=True)
    def assert_writable(self, path: Path):
        rp = path.resolve()
        if str(rp).startswith(str(self.orig) + os.sep):
            raise PermissionError(f"Write blocked in ORIG_DIR: {rp}")
        if self.backup and str(rp).startswith(str(self.backup) + os.sep):
            raise PermissionError(f"Write blocked in BACKUP_DIR: {rp}")

POLICY: PathPolicy|None = None

def init_policy(orig: str, staging: str, output: str, backup: str = None):
    global POLICY; POLICY = PathPolicy(Path(orig), Path(staging), Path(output), Path(backup) if backup else None)

def safe_write_text(path: str|Path, text: str, encoding: str = "utf-8"):
    if POLICY is None:
        raise RuntimeError("PathPolicy not initialized")
    p = Path(path); POLICY.assert_writable(p); p.write_text(text, encoding=encoding)
