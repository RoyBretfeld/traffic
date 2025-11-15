# TrafficApp – Performance-Fix (für Cursor)

Ziel: Die gestartete App läuft weiter, ist aber **sehr langsam**. Hier sind präzise Änderungen & Skripte, die du direkt in Cursor anwenden kannst. Fokus: Reload-Bremsen abstellen, kaputte SQLite-Queue reparieren, Geocoding/OSRM beschleunigen, Logging drosseln.

> Umgebung: Windows, Pfadbeispiele wie `C:\Workflow\TrafficApp` aus den Logs. Passe ggf. Pfade an.

---

## 1) **Reload-Bremse entfernen** (WatchFiles/Autoreload)

### Option A – Start ohne Reload (CLI)
```powershell
# im Projektordner
uvicorn backend.app:app --host 127.0.0.1 --port 8111 --log-level info --no-access-log
```

### Option B – Programmatisch steuern (`start_server.py`)
**Patch-Vorschlag:**
```diff
@@
-import uvicorn
-import os
+import uvicorn
+import os
@@
-if __name__ == "__main__":
-    uvicorn.run("backend.app:app", host="127.0.0.1", port=8111, reload=True)
+if __name__ == "__main__":
+    reload = os.getenv("DEV", "0") == "1"
+    uvicorn.run(
+        "backend.app:app",
+        host="127.0.0.1",
+        port=8111,
+        reload=reload,
+        # optional: Zugriff-Logs abklemmen (weniger I/O)
+        log_level=os.getenv("UVICORN_LOG_LEVEL", "info"),
+    )
```

### Option C – Wenn Reload nötig: Daten/Logs ausschließen
```powershell
uvicorn backend.app:app --reload \
  --reload-dir backend --reload-dir routes --reload-dir services \
  --reload-exclude "data/*" --reload-exclude "logs/*" --reload-exclude "*.csv"
```

> **Warum?** Deine App schreibt CSV/Temp/Logs → WatchFiles löst ständig Reloads aus („1/5 changes detected“), das bremst massiv.

---

## 2) **Kaputte `manual_queue`-DB reparieren**
_Log-Auszug:_ `(sqlite3.DatabaseError) database disk image is malformed`

### Schnellreparatur (PowerShell)
```powershell
# Pfad zur Queue-DB anpassen, z.B.:
$queue = "C:\\Workflow\\TrafficApp\\data\\manual_queue.sqlite"
if (Test-Path $queue) { Rename-Item $queue "$($queue).bak_$(Get-Date -Format yyyyMMdd_HHmmss)" }
```
Beim nächsten Start wird die DB neu erstellt.

### Automatische Integritätsprüfung beim Start (`backend/startup_checks.py`)
```diff
@@
+import sqlite3, os, logging
+
+def _sqlite_integrity_or_recreate(path: str, recreate_cb=None):
+    if not os.path.exists(path):
+        return True
+    try:
+        con = sqlite3.connect(path)
+        ok = con.execute("PRAGMA integrity_check;").fetchone()[0]
+        con.close()
+        if ok != "ok":
+            raise sqlite3.DatabaseError(ok)
+        return True
+    except Exception as e:
+        logging.error("[MANUAL_QUEUE] integrity_check failed: %s", e)
+        if recreate_cb:
+            recreate_cb(path)
+        return False
+
+def _recreate_queue(path: str):
+    try:
+        if os.path.exists(path):
+            os.replace(path, f"{path}.broken")
+    except Exception:
+        pass
+
+def check_manual_queue_db():
+    path = os.getenv("MANUAL_QUEUE_DB", os.path.join("data", "manual_queue.sqlite"))
+    _sqlite_integrity_or_recreate(path, recreate_cb=_recreate_queue)
@@
 def run_startup_checks():
@@
     logging.info("✅ 5 Endpoints registriert")
+    # zusätzliche DB-Health
+    try:
+        check_manual_queue_db()
+        logging.info("✅ Manual-Queue DB: OK")
+    except Exception:
+        logging.warning("[MANUAL_QUEUE] Konnte Integritätscheck nicht ausführen")
```

### Fail-Open im Enqueue (`repositories/manual_repo.py`)
```diff
@@
-def enqueue_address(address_norm: str, raw_address: str, reason: str):
-    with get_conn() as con:
-        con.execute(
-            """
-            INSERT INTO manual_queue(address_norm, raw_address, reason)
-            VALUES (?, ?, ?)
-            """,
-            (address_norm, raw_address, reason),
-        )
+def enqueue_address(address_norm: str, raw_address: str, reason: str):
+    try:
+        with get_conn() as con:
+            con.execute(
+                """
+                INSERT INTO manual_queue(address_norm, raw_address, reason)
+                VALUES (?, ?, ?)
+                """,
+                (address_norm, raw_address, reason),
+            )
+    except Exception as e:
+        # Fail-Open: Verarbeitung nicht blockieren
+        logging.warning("[MANUAL_REPO] enqueue skipped (%s) for %s", e, raw_address)
```

---

## 3) **SQLite schneller machen (WAL + Index)**
Beim Verbindungsaufbau PRAGMAs setzen und Index anlegen (z. B. im `repositories/common.py`).
```diff
@@
 import sqlite3, os
@@
 def get_conn():
     path = os.getenv("DB_PATH", os.path.join("data", "app.sqlite"))
     con = sqlite3.connect(path, check_same_thread=False)
+    con.execute("PRAGMA journal_mode=WAL;")
+    con.execute("PRAGMA synchronous=NORMAL;")
+    con.execute("PRAGMA temp_store=MEMORY;")
+    con.execute("PRAGMA mmap_size=134217728;")  # 128MB
     return con
@@
 def ensure_schema(con):
     con.executescript(
         """
         CREATE TABLE IF NOT EXISTS geocode_cache (
             address_norm TEXT PRIMARY KEY,
             lat REAL,
             lon REAL,
             ts  TEXT
         );
+        CREATE INDEX IF NOT EXISTS idx_gc_addr ON geocode_cache(address_norm);
         """
     )
```

---

## 4) **Geocoding: Parallel & robust**
Nutze `httpx.AsyncClient` + Semaphore, DB-Hits zuerst, Misses bündeln.
```python
# services/geocode_batch.py
import asyncio, httpx, logging
from .cache import get_coords_from_cache, put_coords

SEM = asyncio.Semaphore(int(os.getenv("GEOCODE_CONCURRENCY", 8)))

async def _geocode_one(client, addr: str):
    if hit := get_coords_from_cache(addr):
        return addr, hit
    url = f"https://nominatim.openstreetmap.org/search?q={addr}&format=json&limit=1"
    async with SEM:
        r = await client.get(url, headers={"User-Agent": "TrafficApp/1.0"}, timeout=20)
        r.raise_for_status()
        js = r.json()
        if js:
            lat, lon = float(js[0]["lat"]), float(js[0]["lon"])
            put_coords(addr, lat, lon)
            return addr, (lat, lon)
        return addr, None

async def geocode_batch(addresses):
    async with httpx.AsyncClient() as client:
        tasks = [asyncio.create_task(_geocode_one(client, a)) for a in addresses]
        return await asyncio.gather(*tasks)
```

> **Hinweis:** Zeichenersetzungen (z. B. `Strasse`→`Straße`) **vorher** anwenden (siehe Mapping unten), um Misses zu reduzieren.

---

## 5) **OSRM: Table-API + Session**
Statt viele Einzelrouten: in Batches `/table` abfragen.
```python
# services/osrm_matrix.py
import itertools, requests

OSRM = os.getenv("OSRM_URL", "http://router.project-osrm.org")
session = requests.Session()

def _chunk(seq, size):
    it = iter(seq)
    while True:
        block = list(itertools.islice(it, size))
        if not block:
            return
        yield block

def osrm_table(coords):  # coords: [(lon,lat), ...]
    results = {}
    for batch in _chunk(coords, 100):
        coord_str = ";".join(f"{x},{y}" for x, y in batch)
        url = f"{OSRM}/table/v1/driving/{coord_str}?annotations=duration"
        r = session.get(url, timeout=30)
        r.raise_for_status()
        data = r.json()
        # map zurück in ein Dictionary (i,j) -> duration
        for i, row in enumerate(data.get("durations", [])):
            for j, val in enumerate(row):
                results[(i, j)] = val
    return results
```

---

## 6) **Logging drosseln & HEX-Dumps nur bei DEBUG**
```diff
@@
 import logging, os
@@
 LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
 logging.basicConfig(level=LEVEL, ...)
@@
-for noisy in ("watchfiles.main", "uvicorn.access"):
-    logging.getLogger(noisy).setLevel(logging.WARNING)
+for noisy in ("watchfiles.main", "uvicorn.access", "httpx", "urllib3"):
+    logging.getLogger(noisy).setLevel(logging.WARNING)
@@
-def hex_dump(label, data):
-    logging.info("[%s] %s", label, data.hex(" "))
+def hex_dump(label, data):
+    if logging.getLogger().isEnabledFor(logging.DEBUG):
+        logging.debug("[%s] %s", label, data.hex(" "))
```

> Stelle `LOG_LEVEL=WARNING` im `.env`, wenn du maximale Ruhe willst.

---

## 7) **Address-Mapping-Datei anlegen**
Lege `config/address_mappings.json` an (Warnung in Logs: *nicht gefunden*). Beispiel:
```json
{
  "replacements": [
    ["Strasse", "Straße"],
    ["Str.", "Straße"],
    ["-OT ", " "],
    ["OT ", " "],
    ["ß", "ß"],
    ["oe", "ö"],
    ["ue", "ü"],
    ["ae", "ä"]
  ]
}
```
Lade das bei Startup und normalisiere Adressen **vor** Geocoding.

---

## 8) **.env Beispiel (ins Projektwurzelverzeichnis)**
```ini
# .env
DEV=0                   # 1 = Reload an, 0 = aus
LOG_LEVEL=INFO          # oder WARNING
OSRM_URL=http://router.project-osrm.org
GEOCODE_CONCURRENCY=8
MANUAL_QUEUE_DB=data/manual_queue.sqlite
```

---

## 9) **Einmalige Admin-Schritte (PowerShell)**
```powershell
# 1) Queue-DB sichern/entfernen (falls korrupt)
$queue = "C:\\Workflow\\TrafficApp\\data\\manual_queue.sqlite"
if (Test-Path $queue) { Rename-Item $queue "$($queue).bak_$(Get-Date -Format yyyyMMdd_HHmmss)" }

# 2) .env anlegen
@"
DEV=0
LOG_LEVEL=INFO
OSRM_URL=http://router.project-osrm.org
GEOCODE_CONCURRENCY=8
MANUAL_QUEUE_DB=data/manual_queue.sqlite
"@ | Set-Content -NoNewline .env -Encoding UTF8

# 3) Start ohne Reload
uvicorn backend.app:app --host 127.0.0.1 --port 8111 --log-level info --no-access-log
```

---

## 10) **Checkliste (Kurzfassung)**
- [ ] Reload aus oder Datenordner vom Watch ausschließen.
- [ ] Manual-Queue-DB prüfen/neu erstellen; Enqueue **fail-open**.
- [ ] SQLite: WAL + `synchronous=NORMAL` + Index auf `geocode_cache(address_norm)`.
- [ ] Adressen **vorher** normalisieren (Mapping-Datei).
- [ ] Geocoding parallelisieren (Semaphore ~8).
- [ ] OSRM `/table` in Batches + `requests.Session()`.
- [ ] Logging-Level senken, HEX-Dumps nur bei DEBUG.

> Das bringt erfahrungsgemäß den größten Sprung von **„kriechend“** zu **„flott“**.

