# -*- coding: utf-8 -*-

"""
FAMO – Adress-Admin (FastAPI) – FIXED/HARDENED 1.0.2

Änderungen ggü. 1.0.1:
- Pydantic v2: lat/lon mit Bereichsgrenzen (lat ∈ [-90,90], lon ∈ [-180,180])
- /api/ping liefert Diagnose (DB-Pfad, Migrationspfad)
- XSS-Schutz im HTML via esc()
- Startup-Hook: WAL+Indizes (idempotent) aus migrations/002_wal_and_indexes.sql oder Fallback
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel, Field, field_validator

# --- Migration 001 sicherstellen (Basis-Schema) ---
MIGR_PATH = Path(__file__).resolve().parents[1] / "migrations" / "001_address_corrections.sql"
MIGR_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS address_corrections (
  key TEXT PRIMARY KEY,
  street_canonical TEXT NOT NULL,
  postal_code TEXT NOT NULL,
  city TEXT NOT NULL,
  country TEXT NOT NULL DEFAULT 'DE',
  lat REAL,
  lon REAL,
  source TEXT NOT NULL DEFAULT 'manual',
  confidence REAL NOT NULL DEFAULT 1.0,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS address_exception_queue (
  key TEXT PRIMARY KEY,
  street TEXT NOT NULL,
  postal_code TEXT NOT NULL,
  city TEXT NOT NULL,
  country TEXT NOT NULL DEFAULT 'DE',
  last_seen TEXT NOT NULL DEFAULT (datetime('now')),
  times_seen INTEGER NOT NULL DEFAULT 1,
  note TEXT,
  status TEXT NOT NULL DEFAULT 'pending',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TRIGGER IF NOT EXISTS trg_address_corrections_updated
AFTER UPDATE ON address_corrections
FOR EACH ROW BEGIN
  UPDATE address_corrections SET updated_at = datetime('now') WHERE key = OLD.key;
END;

CREATE TRIGGER IF NOT EXISTS trg_address_exception_queue_updated
AFTER UPDATE ON address_exception_queue
FOR EACH ROW BEGIN
  UPDATE address_exception_queue SET updated_at = datetime('now') WHERE key = OLD.key;
END;
"""

if not MIGR_PATH.exists():
    MIGR_PATH.parent.mkdir(parents=True, exist_ok=True)
    MIGR_PATH.write_text(MIGR_SQL, encoding="utf-8")

# --- Store import ---
try:
    from backend.services.address_corrections import AddressCorrectionStore, normalize_street
    from backend.services.synonyms import SynonymStore, Synonym
except Exception as ex:  # pragma: no cover
    raise RuntimeError("address_corrections.py wird benötigt.") from ex

# --- App ---
app = FastAPI(title="FAMO – Adress-Admin", version="1.0.2")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

DB_PATH = Path(os.getenv("ADDR_DB_PATH", "data/address_corrections.sqlite3"))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
store = AddressCorrectionStore(DB_PATH)
synonym_store = SynonymStore(DB_PATH)  # Synonym-Store initialisieren

# --- Startup-Hook: WAL+Indizes + Synonym-Migration idempotent anwenden ---
try:
    import sqlite3
    con = sqlite3.connect(DB_PATH)
    p2 = Path(__file__).resolve().parents[1] / "migrations" / "002_wal_and_indexes.sql"
    if p2.exists():
        con.executescript(p2.read_text(encoding="utf-8"))
    # Migration 003: Synonyms
    p3 = Path(__file__).resolve().parents[1] / "db" / "migrations" / "003_synonyms.sql"
    if p3.exists():
        con.executescript(p3.read_text(encoding="utf-8"))
    else:
        con.executescript("""
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
CREATE INDEX IF NOT EXISTS idx_queue_status   ON address_exception_queue(status);
CREATE INDEX IF NOT EXISTS idx_queue_seen     ON address_exception_queue(times_seen, last_seen);
CREATE INDEX IF NOT EXISTS idx_corr_key       ON address_corrections(key);
CREATE INDEX IF NOT EXISTS idx_corr_city_zip  ON address_corrections(city, postal_code);
""")
    con.commit()
    con.close()
except Exception:
    # nicht hart fehlschlagen – Logs reichen
    pass

# --- Optional: Auto-Import beim Start (CSV → SQLite) ---
CSV = Path('state/address_corrections.csv')
try:
    if CSV.exists():
        store.import_csv(CSV)
        print('[Auto-Import] state/address_corrections.csv angewendet')
except Exception as ex:
    print('[Auto-Import] Warnung:', ex)

# ---------- Models ----------

class ResolveIn(BaseModel):
    key: str = Field(..., description="Schlüssel: norm(street)|postal_code|city|country")
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    street: Optional[str] = Field(None, description="Optional: bereinigter Straßenname")
    source: str = Field("manual", description="Quelle der Korrektur")
    confidence: float = Field(1.0, ge=0.0, le=1.0)

    @field_validator("street")
    @classmethod
    def _clean_street(cls, v: Optional[str]):
        return normalize_street(v) if v else v

# ---------- Page ----------

INDEX_HTML = """
<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>FAMO – Adress-Admin</title>
  <style>
    body { font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, 'Helvetica Neue', Arial; margin: 20px; }
    h1 { font-size: 20px; margin-bottom: 10px; }
    .controls { display: flex; gap: 12px; align-items: center; margin-bottom: 12px; flex-wrap: wrap; }
    input[type="text"], input[type="number"] { padding: 6px 8px; border: 1px solid #ddd; border-radius: 6px; }
    button { padding: 6px 10px; border-radius: 6px; border: 1px solid #999; background: #f6f6f6; cursor: pointer; }
    button:hover { background: #eee; }
    table { border-collapse: collapse; width: 100%; }
    th, td { border-bottom: 1px solid #eee; padding: 8px; text-align: left; }
    th { background: #fafafa; font-weight: 600; }
    .badge { padding: 2px 6px; border-radius: 10px; background: #eef; border: 1px solid #ccd; font-size: 12px; }
    .muted { color: #666; font-size: 12px; }
    .row { display: flex; gap: 6px; }
  </style>
</head>
<body>
  <h1>FAMO – Adress-Admin</h1>
  <div class="controls">
    <label>Filter Stadt <input id="fCity" type="text" placeholder="z. B. Dresden" /></label>
    <label>Filter PLZ <input id="fZip" type="text" placeholder="01067" /></label>
    <button onclick="loadPending()">Neu laden</button>
    <button onclick="exportCSV()">Korrekturen exportieren (CSV)</button>
  </div>
  <div id="stat" class="muted">Lade…</div>
  <table>
    <thead>
      <tr>
        <th>Key</th>
        <th>Straße</th>
        <th>PLZ</th>
        <th>Stadt</th>
        <th>Land</th>
        <th>Gesehen</th>
        <th>Koordinaten</th>
        <th>Aktion</th>
      </tr>
    </thead>
    <tbody id="tb"></tbody>
  </table>

<script>
function esc(t){ return String(t).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

async function fetchJSON(url, opts={}) {
  const res = await fetch(url, Object.assign({headers: {'Content-Type':'application/json'}}, opts));
  if (!res.ok) throw new Error(await res.text());
  return await res.json();
}

async function loadStats() {
  try {
    const st = await fetchJSON('/api/stats');
    const s = document.getElementById('stat');
    s.innerText = `Ausstehend: ${st.pending} | Korrekturen: ${st.corrections}`;
  } catch (e) { console.error(e); }
}

async function loadPending() {
  await loadStats();
  const city = document.getElementById('fCity').value.trim().toLowerCase();
  const zip = document.getElementById('fZip').value.trim();
  const data = await fetchJSON('/api/pending?limit=200');
  const tb = document.getElementById('tb');
  tb.innerHTML = '';
  data.forEach(row => {
    if (city && !row.city.toLowerCase().includes(city)) return;
    if (zip && String(row.postal_code) !== zip) return;
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td class="muted">${esc(row.key)}</td>
      <td>${esc(row.street)}</td>
      <td>${esc(row.postal_code)}</td>
      <td>${esc(row.city)}</td>
      <td>${esc(row.country)}</td>
      <td><span class="badge">${esc(row.times_seen)}</span><div class="muted">${esc(row.last_seen)}</div></td>
      <td>
        <div class="row">
          <input type="number" step="0.000001" placeholder="lat" style="width:120px" />
          <input type="number" step="0.000001" placeholder="lon" style="width:120px" />
        </div>
        <div class="row" style="margin-top:4px">
          <input type="text" placeholder="Straße korrigiert (optional)" style="width:250px" />
        </div>
      </td>
      <td><button>Speichern</button></td>
    `;
    const btn = tr.querySelector('button');
    btn.addEventListener('click', async () => {
      const [latEl, lonEl] = tr.querySelectorAll('input[type="number"]');
      const streetEl = tr.querySelector('input[type="text"]');
      const lat = parseFloat(latEl.value);
      const lon = parseFloat(lonEl.value);
      if (Number.isNaN(lat) || Number.isNaN(lon)) { alert('Bitte gültige Lat/Lon eingeben.'); return; }
      const payload = { key: row.key, lat, lon, street: streetEl.value || null, source: 'manual', confidence: 1.0 };
      try {
        await fetchJSON('/api/resolve', { method: 'POST', body: JSON.stringify(payload) });
        tr.style.opacity = 0.5; tr.querySelector('button').disabled = true;
      } catch (e) { alert('Fehler beim Speichern: ' + e.message); }
      await loadStats();
    });
    tb.appendChild(tr);
  });
}

async function exportCSV() {
  const res = await fetch('/api/export');
  if (!res.ok) { alert('Export fehlgeschlagen'); return; }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = 'address_corrections.csv'; a.click();
  URL.revokeObjectURL(url);
}

loadPending();
</script>
</body>
</html>
"""

# ---------- Routes (API) ----------

@app.get("/", response_class=HTMLResponse)
async def index_page():
    return HTMLResponse(INDEX_HTML)

@app.get("/api/ping")
async def ping():
    return {"status": "ok", "db": str(DB_PATH), "migrations": str(MIGR_PATH)}

@app.get("/api/pending")
async def api_pending(limit: int = 100):
    items = store.list_pending(limit=limit)
    return items

@app.get("/api/stats")
async def api_stats():
    try:
        import sqlite3
        con = sqlite3.connect(DB_PATH)
        cur = con.execute("SELECT COUNT(*) FROM address_exception_queue WHERE status='pending'")
        pending = cur.fetchone()[0]
        cur = con.execute("SELECT COUNT(*) FROM address_corrections")
        corr = cur.fetchone()[0]
        con.close()
    except Exception:
        pending, corr = 0, 0
    return {"pending": pending, "corrections": corr}

@app.post("/api/resolve")
async def api_resolve(payload: ResolveIn):
    try:
        store.resolve(payload.key, payload.lat, payload.lon,
                      street_canonical=payload.street, source=payload.source, confidence=payload.confidence)
        return {"ok": True}
    except KeyError as ex:
        raise HTTPException(status_code=404, detail=str(ex))
    except Exception as ex:  # pragma: no cover
        raise HTTPException(status_code=400, detail=str(ex))

# --- Synonym-API ---
class SynIn(BaseModel):
    alias: str
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    street: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    country: str = "DE"
    lat: Optional[float] = Field(None, ge=-90, le=90)
    lon: Optional[float] = Field(None, ge=-180, le=180)
    priority: int = 0
    active: int = 1
    note: Optional[str] = None


@app.get("/api/synonyms")
async def list_synonyms(limit: int = 200, active_only: bool = True):
    """Listet alle Synonyme"""
    rows = synonym_store.list_all(limit=limit, active_only=active_only)
    return rows


@app.post("/api/synonyms/upsert")
async def upsert_synonym(s: SynIn):
    """Fügt ein Synonym hinzu oder aktualisiert es"""
    syn = Synonym(**s.dict())
    synonym_store.upsert(syn)
    return {"ok": True, "message": f"Synonym '{s.alias}' gespeichert"}


@app.post("/api/synonyms/delete")
async def delete_synonym(alias: str):
    """Löscht/Deaktiviert ein Synonym"""
    success = synonym_store.delete(alias)
    if success:
        return {"ok": True, "message": f"Synonym '{alias}' deaktiviert"}
    else:
        raise HTTPException(status_code=404, detail=f"Synonym '{alias}' nicht gefunden")


@app.get("/api/export")
async def api_export():
    import tempfile
    tmp = Path(tempfile.gettempdir()) / "address_corrections_export.csv"
    try:
        store.export_csv(tmp)
        data = tmp.read_bytes()
    finally:
        try:
            tmp.unlink()
        except Exception:
            pass
    return StreamingResponse(iter([data]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=address_corrections.csv"})
