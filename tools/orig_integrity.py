from __future__ import annotations
from pathlib import Path
import hashlib, json, os, sys

ORIG_DIR = Path(os.getenv("ORIG_DIR", "./tourplaene")).resolve()
MANIFEST = Path(os.getenv("INTEGRITY_MANIFEST", "./data/orig_manifest.json")).resolve()

def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1<<20), b''):
            h.update(chunk)
    return h.hexdigest()

def collect() -> dict:
    files = sorted([p for p in ORIG_DIR.rglob("*.csv") if p.is_file()])
    entries = []
    for p in files:
        st = p.stat()
        entries.append({
            "path": str(p.relative_to(ORIG_DIR)),
            "size": st.st_size,
            "mtime": int(st.st_mtime),
            "sha256": sha256(p),
        })
    return {"root": str(ORIG_DIR), "count": len(entries), "files": entries}

def save_manifest(data: dict):
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))

def verify() -> list[dict]:
    ref = load_manifest()
    problems = []
    seen = set()
    for e in ref["files"]:
        p = ORIG_DIR / e["path"]
        seen.add(e["path"])
        if not p.exists():
            problems.append({"path": e["path"], "issue": "missing"})
            continue
        cur = {"size": p.stat().st_size, "sha256": sha256(p)}
        if cur["size"] != e["size"] or cur["sha256"] != e["sha256"]:
            problems.append({"path": e["path"], "issue": "modified"})
    # neue Dateien, die nicht im Manifest stehen
    for p in ORIG_DIR.rglob("*.csv"):
        rel = str(p.relative_to(ORIG_DIR))
        if rel not in seen:
            problems.append({"path": rel, "issue": "unexpected_new"})
    return problems

def main(argv=None):
    cmd = (argv or sys.argv[1:]) or ["verify"]
    if cmd[0] == "build":
        save_manifest(collect()); print(f"manifest written: {MANIFEST}")
    elif cmd[0] == "verify":
        probs = verify()
        if probs:
            print(json.dumps({"ok": False, "problems": probs}, ensure_ascii=False, indent=2)); sys.exit(2)
        print(json.dumps({"ok": True}, ensure_ascii=False))
    else:
        print("usage: python -m tools.orig_integrity [build|verify]"); sys.exit(1)

if __name__ == "__main__":
    main()
