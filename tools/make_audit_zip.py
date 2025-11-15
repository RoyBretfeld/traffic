#!/usr/bin/env python3
"""
Audit-ZIP-Pipeline: Erstellt ein ZIP-Archiv mit allen audit-relevanten Dateien.
Format: AUDIT_<YYYYMMDD_HHMMSS>_<shortsha>.zip
Enthält: Manifest (Hashes, Commit, Branch), sanitizierte .env, Logs, OpenAPI, etc.
"""
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
import time
import zipfile
import fnmatch
import sys


ROOT = Path(__file__).resolve().parents[1]
OUTDIR = ROOT / "ZIP"

INCLUDES = [
    "*.md",
    "LICENSE",
    "README*",
    "CHANGELOG*",
    "backend/**",
    "routes/**",
    "services/**",
    "db/**",
    "scripts/**",
    "frontend/**/*.html",
    "frontend/**/*.js",
    "frontend/**/*.css",
    "configs/**",
    ".github/**",
    "*.sql",
    "*.yaml",
    "*.yml",
    "*.toml",
    "*.ini",
    "pyproject.toml",
    "requirements*.txt",
    "openapi.json",
    "route-map.txt",
    "logs/**/*.log",
    "data/samples/**",
]

EXCLUDES = [
    "__pycache__/**",
    "*.pyc",
    "node_modules/**",
    ".venv/**",
    "venv/**",
    ".dist/**",
    "build/**",
    "dist/**",
    "coverage/**",
    ".mypy_cache/**",
    "*.sqlite",
    "*.db-shm",
    "*.db-wal",
    "data/**",
    "!data/samples/**",
    ".env",
    ".env.local",
    ".env.*.secret",
    "secrets/**",
]

SECRET_KEYS = {k.lower() for k in [
    "OPENAI_API_KEY",
    "DATABASE_URL",
    "POSTGRES_PASSWORD",
    "REDIS_URL",
    "SMTP_PASSWORD",
    "API_KEY",
    "SECRET",
    "TOKEN",
]}


# --- helpers ---

def git(cmd):
    """Führt einen Git-Befehl aus und gibt das Ergebnis zurück."""
    try:
        return subprocess.check_output(
            ["git", *cmd], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return ""


def shortsha():
    """Gibt den kurzen SHA des aktuellen Commits zurück."""
    s = git(["rev-parse", "--short", "HEAD"]) or "nogit"
    return s


def match(path: Path, pattern: str) -> bool:
    """Prüft, ob ein Pfad einem Pattern entspricht (unterstützt **)."""
    path_str = path.as_posix()
    
    # Konvertiere ** zu einem rekursiven Match
    if "**" in pattern:
        # Pattern wie "backend/**" - matcht alles unter backend/
        if pattern.endswith("/**"):
            prefix = pattern[:-3]  # Entferne "/**"
            return path_str.startswith(prefix + "/") or path_str == prefix
        # Pattern wie "**/*.log" - matcht alle .log Dateien rekursiv
        elif pattern.startswith("**/"):
            suffix = pattern[3:]  # Entferne "**/"
            # Prüfe ob der Pfad mit dem Suffix endet (mit fnmatch für Wildcards)
            if "/" in suffix:
                # Komplexeres Pattern wie "**/subdir/*.log"
                parts = suffix.split("/")
                if len(parts) > 1:
                    # Matcht rekursiv: irgendwo im Pfad muss das Pattern vorkommen
                    return fnmatch.fnmatch(path_str, f"*/{suffix}") or fnmatch.fnmatch(path_str, suffix)
            return fnmatch.fnmatch(path_str, f"*/{suffix}") or fnmatch.fnmatch(path_str, suffix)
        # Pattern wie "logs/**/*.log"
        elif "/**/" in pattern:
            parts = pattern.split("/**/")
            if len(parts) == 2:
                prefix, suffix = parts
                # Der Pfad muss mit prefix beginnen und irgendwo suffix enthalten
                if path_str.startswith(prefix + "/"):
                    # Prüfe ob suffix irgendwo im Rest des Pfads vorkommt
                    rest = path_str[len(prefix) + 1:]
                    return fnmatch.fnmatch(rest, f"*/{suffix}") or fnmatch.fnmatch(rest, suffix)
    
    # Standard fnmatch für einfache Patterns
    return fnmatch.fnmatch(path_str, pattern)


def collect():
    """Sammelt alle Dateien basierend auf Include/Exclude-Regeln."""
    files = set()
    
    # Sammle alle Dateien, die Include-Patterns entsprechen
    for pat in INCLUDES:
        for p in ROOT.rglob("*"):
            if p.is_file():
                rel = p.relative_to(ROOT)
                if match(rel, pat):
                    files.add(p)
    
    # Wende Excludes an
    keep = set()
    for p in files:
        rel = p.relative_to(ROOT)
        excluded = False
        for ex in EXCLUDES:
            if ex.startswith("!"):
                continue
            if match(rel, ex):
                excluded = True
                break
        if not excluded:
            keep.add(p)
    
    # Re-apply negative excludes (!pattern)
    for ex in EXCLUDES:
        if ex.startswith("!"):
            pat = ex[1:]
            for p in ROOT.rglob("*"):
                if p.is_file():
                    rel = p.relative_to(ROOT)
                    if match(rel, pat):
                        keep.add(p)
    
    return sorted(keep)


def sha256(p: Path) -> str:
    """Berechnet den SHA256-Hash einer Datei."""
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def make_env_audit():
    """Erstellt eine sanitizierte .env.audit aus .env oder config.env."""
    # Prüfe zuerst .env, dann config.env
    src = ROOT / ".env"
    if not src.exists():
        src = ROOT / "config.env"
    if not src.exists():
        return None
    
    dst = ROOT / ".env.audit"
    lines = src.read_text(encoding="utf-8", errors="ignore").splitlines()
    out = []
    
    for line in lines:
        # Ignoriere Kommentare und leere Zeilen
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            out.append(line)
            continue
        
        # Parse KEY=VALUE
        m = re.match(r"\s*([A-Za-z0-9_]+)\s*=\s*(.*)\s*$", line)
        if m and m.group(1).lower() in SECRET_KEYS:
            out.append(f"{m.group(1)}=<REDACTED>")
        else:
            out.append(line)
    
    dst.write_text("\n".join(out) + "\n", encoding="utf-8")
    return dst


def main():
    """Hauptfunktion: Erstellt das Audit-ZIP."""
    OUTDIR.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    name = f"AUDIT_{ts}_{shortsha()}.zip"
    zpath = OUTDIR / name
    
    print(f"Erstelle Audit-ZIP: {name}")
    print(f"Suche Dateien...")
    
    env_audit = make_env_audit()
    files = collect()
    
    if env_audit:
        files.append(env_audit)
        print(f"  -> .env.audit hinzugefuegt")
    
    print(f"  -> {len(files)} Dateien gefunden")
    
    manifest = {
        "created": ts,
        "git": {
            "commit": git(["rev-parse", "HEAD"]) or "",
            "branch": git(["rev-parse", "--abbrev-ref", "HEAD"]) or "",
            "dirty": bool(git(["status", "--porcelain"])),
        },
        "files": []
    }
    
    print(f"Erstelle ZIP-Archiv...")
    with zipfile.ZipFile(
        zpath, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as z:
        # Füge Dateien hinzu
        for p in files:
            rel = p.relative_to(ROOT)
            try:
                z.write(p, rel.as_posix())
                manifest["files"].append({
                    "path": rel.as_posix(),
                    "sha256": sha256(p),
                    "size": p.stat().st_size,
                })
            except Exception as e:
                print(f"  [WARN] {rel} konnte nicht hinzugefuegt werden: {e}")
        
        # Schreibe Manifest ins ZIP
        mbytes = json.dumps(manifest, indent=2, ensure_ascii=False).encode("utf-8")
        z.writestr("audit_manifest.json", mbytes)
    
    # Berechne ZIP-Groesse
    size_mb = zpath.stat().st_size / (1024 * 1024)
    print(f"[OK] Fertig: {zpath}")
    print(f"  Groesse: {size_mb:.2f} MB")
    print(f"  Dateien: {len(manifest['files'])}")
    print(f"  Git-Commit: {manifest['git']['commit'][:12]} ({manifest['git']['branch']})")
    
    # Aufräumen: .env.audit löschen
    if env_audit and env_audit.exists():
        env_audit.unlink()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

