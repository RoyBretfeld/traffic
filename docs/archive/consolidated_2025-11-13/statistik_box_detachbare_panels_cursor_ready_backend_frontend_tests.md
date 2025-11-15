# Statistik-Box & Detachbare Panels — Cursor‑Ready

> Komplettpaket für **Statistik-Unterseite** (mit Pfad-Config & Retention), **Zeitbox-Visualisierung** (rote Unterlage), sowie **abdockbare** Map- & Tourübersicht-Panels. Inklusive **Backend/Frontend-Tests**.

---

## 🚦 Integrationsleitfaden (Kurz)

1) **Backend**: Neue Routen + Writer + Modelle hinzufügen, App registrieren.
2) **Frontend**: Neue Seite `/tourplan/statistik` inkl. Unterseiten, UI-Komponenten und Popout-Mechanik.
3) **Tests**: `pytest` für Backend, `vitest` + `@testing-library/react` für Frontend.
4) **Konfig**: `STATS_STORAGE_PATH` (ENV) & Fallback; Netzpfad/UNC ok.

---

## 🧱 Backend – Dateien

### FILE: `backend/models/stats.py`
```python
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Any, List, Optional
from datetime import date, datetime

class TourLeg(BaseModel):
    from_id: str
    to_id: str
    dist_m: int = Field(ge=0)
    dur_s: int = Field(ge=0)

class TourSnapshot(BaseModel):
    version: int = 1
    date: date
    generated_at: datetime
    tour_id: str
    stops: int = Field(ge=0)
    distance_m: int = Field(ge=0)
    duration_s: int = Field(ge=0)
    timebox_limit_s: int = Field(ge=0)
    timebox_exceeded: bool
    polyline_full: Optional[str] = None
    polyline_simplified: str
    legs: List[TourLeg]
    meta: dict[str, Any] = {}

class DayIndex(BaseModel):
    date: date
    tours: List[str]
    totals: dict[str, Any]  # {"stops":..., "distance_m":..., "duration_s":..., "overruns": ...}

class StoragePathPayload(BaseModel):
    path: str

class DayOverview(BaseModel):
    date: date
    tours: List[dict]
```

---

### FILE: `backend/services/snapshot_writer.py`
```python
from __future__ import annotations
import json, gzip, os
from pathlib import Path
from datetime import date, datetime, timezone
from typing import Iterable
from . import stats_storage
from backend.models.stats import TourSnapshot, DayIndex

ENCODING = "utf-8"

def _day_dir(base: Path, d: date) -> Path:
    return base / f"{d:%Y}" / f"{d:%m}" / f"{d:%d}"

def save_tour_snapshot(base: Path, snap: TourSnapshot) -> Path:
    day = _day_dir(base, snap.date)
    day.mkdir(parents=True, exist_ok=True)
    fp = day / f"tour_{snap.tour_id}.json.gz"
    with gzip.open(fp, "wt", encoding=ENCODING) as f:
        json.dump(snap.model_dump(mode="json"), f, ensure_ascii=False)
    _update_index(day)
    return fp

def _update_index(day_dir: Path) -> None:
    # Sammle Kurzinfos aus allen Tourfiles
    tours = []
    total_distance = 0
    total_duration = 0
    overruns = 0
    for gz in day_dir.glob("tour_*.json.gz"):
        try:
            with gzip.open(gz, "rt", encoding=ENCODING) as f:
                data = json.load(f)
            tours.append({
                "tour_id": data["tour_id"],
                "stops": data["stops"],
                "distance_m": data["distance_m"],
                "duration_s": data["duration_s"],
                "timebox_exceeded": data["timebox_exceeded"],
            })
            total_distance += int(data.get("distance_m", 0))
            total_duration += int(data.get("duration_s", 0))
            overruns += 1 if data.get("timebox_exceeded") else 0
        except Exception:
            continue
    idx = DayIndex(
        date=date.fromisoformat(day_dir.name if len(day_dir.name)==2 else str(date.today())),
        tours=sorted([t["tour_id"] for t in tours]),
        totals={
            "tours": len(tours),
            "distance_m": total_distance,
            "duration_s": total_duration,
            "overruns": overruns,
        },
    )
    idx_path = day_dir / "_index.json"
    idx_path.write_text(idx.model_dump_json(indent=2, ensure_ascii=False), encoding=ENCODING)

# --- Retention --------------------------------------------------------------

def retention_compact(base: Path, keep_full_days: int = 30) -> int:
    """Entfernt 'polyline_full' aus Snapshots, die älter als keep_full_days sind.
    Rückgabe: Zahl der modifizierten Dateien.
    """
    changed = 0
    cutoff = datetime.now(timezone.utc).date().toordinal() - keep_full_days
    for gz in base.rglob("tour_*.json.gz"):
        try:
            with gzip.open(gz, "rt", encoding=ENCODING) as f:
                data = json.load(f)
            d = date.fromisoformat(data["date"]).toordinal()
            if d <= cutoff and data.get("polyline_full"):
                data["polyline_full"] = None
                with gzip.open(gz, "wt", encoding=ENCODING) as f:
                    json.dump(data, f, ensure_ascii=False)
                changed += 1
        except Exception:
            continue
    return changed

# --- Storage Utilities ------------------------------------------------------

def validate_storage_path(p: str) -> tuple[bool, str]:
    try:
        base = Path(p)
        base.mkdir(parents=True, exist_ok=True)
        probe = base / ".write_probe.tmp"
        probe.write_bytes(b"ok")
        assert probe.read_bytes() == b"ok"
        probe.unlink(missing_ok=True)
        return True, "ok"
    except Exception as e:
        return False, str(e)
```

---

### FILE: `backend/services/stats_storage.py`
```python
from __future__ import annotations
import os, json
from pathlib import Path

# Einfacher Settings-Store (JSON-Datei). Alternativ: DB/Table.
DEFAULT_BASE = Path(os.getenv("STATS_STORAGE_PATH", "C:/Workflow/TrafficApp/data/stats")).resolve()
SETTINGS_FILE = DEFAULT_BASE.parent / "app_settings.json"
KEY = "stats_storage_path"

def get_base_path() -> Path:
    try:
        if SETTINGS_FILE.exists():
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            p = data.get(KEY)
            if p:
                return Path(p)
    except Exception:
        pass
    return DEFAULT_BASE

def set_base_path(p: str) -> None:
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {}
    if SETTINGS_FILE.exists():
        try:
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except Exception:
            data = {}
    data[KEY] = p
    SETTINGS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
```

---

### FILE: `backend/routes/stats_api.py`
```python
from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query
from datetime import date, datetime, timezone
from pathlib import Path
import gzip, json

from backend.models.stats import StoragePathPayload, TourSnapshot, DayOverview
from backend.services.snapshot_writer import (
    save_tour_snapshot, validate_storage_path, retention_compact
)
from backend.services import stats_storage

router = APIRouter(prefix="/api/stats", tags=["Statistics"])

@router.get("/health")
def health():
    base = stats_storage.get_base_path()
    return {"ok": True, "base": str(base)}

# --- Storage Path -----------------------------------------------------------

@router.get("/storage-path")
def get_storage_path():
    return {"path": str(stats_storage.get_base_path())}

@router.post("/storage-path")
def set_storage_path(payload: StoragePathPayload):
    ok, msg = validate_storage_path(payload.path)
    if not ok:
        raise HTTPException(400, detail=f"Pfad ungültig: {msg}")
    stats_storage.set_base_path(payload.path)
    return {"ok": True, "path": payload.path}

# --- Snapshot ---------------------------------------------------------------

@router.post("/snapshot")
def create_snapshot(snap: TourSnapshot):
    base = stats_storage.get_base_path()
    p = save_tour_snapshot(base, snap)
    return {"ok": True, "path": str(p)}

# --- Tagesabfragen ----------------------------------------------------------

@router.get("/dates")
def list_dates(frm: date = Query(None, alias="from"), to: date | None = None):
    base = stats_storage.get_base_path()
    dates = []
    if not base.exists():
        return {"dates": dates}
    for y in sorted({p.name for p in base.iterdir() if p.is_dir()}):
        for m in sorted({p.name for p in (base/ y).iterdir() if p.is_dir()}):
            for d in sorted({p.name for p in (base/ y/ m).iterdir() if p.is_dir()}):
                try:
                    iso = f"{y}-{m}-{d}"
                    di = date.fromisoformat(iso)
                    if frm and di < frm: continue
                    if to and di > to: continue
                    dates.append(iso)
                except Exception:
                    continue
    return {"dates": dates}

@router.get("/day/{day}")
def day_overview(day: date) -> DayOverview:
    base = stats_storage.get_base_path()
    day_dir = base / f"{day:%Y/%m/%d}"
    idx = day_dir / "_index.json"
    if not idx.exists():
        raise HTTPException(404, detail="Kein Index für diesen Tag")
    data = json.loads(idx.read_text(encoding="utf-8"))
    # plus leichtgewichtige Tourliste
    tours = []
    for gz in day_dir.glob("tour_*.json.gz"):
        try:
            with gzip.open(gz, "rt", encoding="utf-8") as f:
                s = json.load(f)
            tours.append({
                "tour_id": s["tour_id"],
                "stops": s["stops"],
                "distance_m": s["distance_m"],
                "duration_s": s["duration_s"],
                "timebox_exceeded": s["timebox_exceeded"],
            })
        except Exception:
            continue
    return {"date": str(day), "tours": sorted(tours, key=lambda t: t["tour_id"]) }

@router.get("/day/{day}/tour/{tour_id}")
def tour_detail(day: date, tour_id: str):
    base = stats_storage.get_base_path()
    day_dir = base / f"{day:%Y/%m/%d}"
    gz = day_dir / f"tour_{tour_id}.json.gz"
    if not gz.exists():
        raise HTTPException(404, detail="Tour nicht gefunden")
    with gzip.open(gz, "rt", encoding="utf-8") as f:
        data = json.load(f)
    return data

@router.get("/overruns")
def overruns(day: date):
    base = stats_storage.get_base_path()
    day_dir = base / f"{day:%Y/%m/%d}"
    res = []
    for gz in day_dir.glob("tour_*.json.gz"):
        try:
            with gzip.open(gz, "rt", encoding="utf-8") as f:
                s = json.load(f)
            if s.get("timebox_exceeded"):
                res.append(s["tour_id"])
        except Exception:
            continue
    return {"date": str(day), "overruns": sorted(res)}

# --- Maintenance ------------------------------------------------------------

@router.post("/retention/compact")
def retention(keep_full_days: int = 30):
    base = stats_storage.get_base_path()
    changed = retention_compact(base, keep_full_days)
    return {"ok": True, "changed": changed}
```

---

### FILE: `backend/app_include_stats.py` (App-Registrierung)
```python
# in eurer main/app.py oder einem Include-Entry verwenden
from fastapi import FastAPI
from backend.routes import stats_api

def register_stats(app: FastAPI):
    app.include_router(stats_api.router)
```

> **Hinweis:** Ruft `register_stats(app)` in eurem FastAPI-Bootstrap auf und achtet darauf, dass der Reload alle Module lädt.

---

## 🧪 Backend-Tests (pytest)

### FILE: `tests/test_stats_api.py`
```python
import json, gzip
from datetime import date, datetime, timezone
from fastapi.testclient import TestClient
from pathlib import Path
from backend.models.stats import TourSnapshot, TourLeg
from backend.routes.stats_api import router
from fastapi import FastAPI

app = FastAPI()
app.include_router(router)
client = TestClient(app)

SAMPLE = TourSnapshot(
    date=date(2025,9,10),
    generated_at=datetime.now(timezone.utc),
    tour_id="W-09.00",
    stops=29,
    distance_m=42153,
    duration_s=7320,
    timebox_limit_s=7200,
    timebox_exceeded=True,
    polyline_full="_p~iF~ps|U_ulLnnqC_mqNvxq`@",
    polyline_simplified="_p~iF~ps|U",
    legs=[TourLeg(from_id="S1", to_id="S2", dist_m=1200, dur_s=300)],
    meta={"profile":"car"},
)

def test_storage_path_roundtrip(tmp_path, monkeypatch):
    # set custom path
    resp = client.post("/api/stats/storage-path", json={"path": str(tmp_path)})
    assert resp.status_code == 200
    assert resp.json()["ok"] is True

    # create snapshot
    resp = client.post("/api/stats/snapshot", json=json.loads(SAMPLE.model_dump_json()))
    assert resp.status_code == 200

    # day overview
    resp = client.get("/api/stats/day/2025-09-10")
    assert resp.status_code == 200
    tours = resp.json()["tours"]
    assert any(t["tour_id"] == "W-09.00" for t in tours)

    # detail
    resp = client.get("/api/stats/day/2025-09-10/tour/W-09.00")
    assert resp.status_code == 200
    assert resp.json()["timebox_exceeded"] is True

    # overruns
    resp = client.get("/api/stats/overruns", params={"day":"2025-09-10"})
    assert resp.status_code == 200
    assert "W-09.00" in resp.json()["overruns"]
```

### FILE: `tests/test_retention.py`
```python
from datetime import date, datetime, timezone, timedelta
import json, gzip
from pathlib import Path
from backend.models.stats import TourSnapshot, TourLeg
from backend.services.snapshot_writer import save_tour_snapshot, retention_compact

def _snap(d: date, with_full=True):
    return TourSnapshot(
        date=d,
        generated_at=datetime.now(timezone.utc),
        tour_id=f"T-{d:%H%M}",
        stops=2,
        distance_m=1000,
        duration_s=600,
        timebox_limit_s=1200,
        timebox_exceeded=False,
        polyline_full=("abc" if with_full else None),
        polyline_simplified="abc",
        legs=[TourLeg(from_id="A", to_id="B", dist_m=1000, dur_s=600)],
        meta={},
    )

def test_retention(tmp_path):
    old_day = date(2025, 1, 1)
    new_day = date(2025, 10, 10)
    save_tour_snapshot(tmp_path, _snap(old_day))
    save_tour_snapshot(tmp_path, _snap(new_day))

    changed = retention_compact(tmp_path, keep_full_days=10)  # sehr klein fürs Testen
    assert changed >= 1
```

---

## 🖥️ Frontend – Seiten & Komponenten

> Annahmen: React + React Router, Tailwind aktiv. Optional: `shadcn/ui` & `lucide-react` (Icons). Recharts für kleine Stat-Kacheln.

### FILE: `src/components/StoragePathCard.tsx`
```tsx
import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button"; // falls shadcn installiert, sonst <button>
import { Input } from "@/components/ui/input";

export default function StoragePathCard() {
  const [path, setPath] = useState("");
  const [status, setStatus] = useState<null | { ok: boolean; msg: string }>(null);

  useEffect(() => {
    fetch("/api/stats/storage-path").then(r => r.json()).then(d => setPath(d.path || ""));
  }, []);

  const onSave = async () => {
    setStatus(null);
    const res = await fetch("/api/stats/storage-path", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path })
    });
    if (res.ok) {
      setStatus({ ok: true, msg: "Gespeichert & getestet" });
    } else {
      const j = await res.json().catch(() => ({}));
      setStatus({ ok: false, msg: j.detail || "Fehler" });
    }
  };

  return (
    <div className="p-4 rounded-2xl shadow bg-white border">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-semibold">Speicherpfad für Statistik</h3>
      </div>
      <div className="grid gap-3 md:grid-cols-[1fr_auto] items-center">
        <Input value={path} onChange={e => setPath(e.target.value)} placeholder="C:\\Workflow\\TrafficApp\\data\\stats oder \\server\\share\\stats" />
        <Button onClick={onSave}>Test & Speichern</Button>
      </div>
      {status && (
        <div className={`mt-2 text-sm ${status.ok ? "text-green-700" : "text-red-700"}`}>
          {status.ok ? "OK:" : "Fehler:"} {status.msg}
        </div>
      )}
    </div>
  );
}
```

---

### FILE: `src/components/StatsTiles.tsx`
```tsx
import { useEffect, useState } from "react";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from "recharts";

export function StatsTiles({ from, to }: { from?: string; to?: string }) {
  const [dates, setDates] = useState<string[]>([]);

  useEffect(() => {
    const params = new URLSearchParams();
    if (from) params.set("from", from);
    if (to) params.set("to", to);
    fetch(`/api/stats/dates?${params.toString()}`).then(r => r.json()).then(d => setDates(d.dates || []));
  }, [from, to]);

  return (
    <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <div className="p-4 rounded-2xl shadow bg-white border">
        <div className="text-sm text-gray-500">Verfügbare Tage</div>
        <div className="text-2xl font-semibold">{dates.length}</div>
      </div>
      <div className="p-4 rounded-2xl shadow bg-white border col-span-3">
        <div className="h-36">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={dates.map(d => ({ d, v: 1 }))}>
              <XAxis dataKey="d" hide />
              <YAxis hide />
              <Tooltip />
              <Bar dataKey="v" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
```

---

### FILE: `src/pages/statistik/StatistikPage.tsx`
```tsx
import { useState } from "react";
import StoragePathCard from "@/components/StoragePathCard";
import { StatsTiles } from "@/components/StatsTiles";
import { Link } from "react-router-dom";

export default function StatistikPage() {
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  return (
    <div className="p-4 md:p-6 space-y-6">
      <h1 className="text-2xl font-bold">Statistik</h1>

      <StoragePathCard />

      <div className="p-4 rounded-2xl shadow bg-white border">
        <div className="flex gap-3 items-end">
          <div>
            <label className="text-sm text-gray-600">Von</label>
            <input className="border rounded p-2 w-44" type="date" value={from} onChange={e => setFrom(e.target.value)} />
          </div>
          <div>
            <label className="text-sm text-gray-600">Bis</label>
            <input className="border rounded p-2 w-44" type="date" value={to} onChange={e => setTo(e.target.value)} />
          </div>
          <Link to={`/tourplan/statistik/${from || new Date().toISOString().slice(0,10)}`} className="ml-auto underline">Tag öffnen</Link>
        </div>
      </div>

      <StatsTiles from={from} to={to} />
    </div>
  );
}
```

---

### FILE: `src/pages/statistik/DayView.tsx`
```tsx
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

export default function DayView() {
  const { date } = useParams();
  const [tours, setTours] = useState<any[]>([]);

  useEffect(() => {
    if (!date) return;
    fetch(`/api/stats/day/${date}`).then(r => r.json()).then(d => setTours(d.tours || []));
  }, [date]);

  return (
    <div className="p-4 md:p-6 space-y-4">
      <h2 className="text-xl font-semibold">Tag {date}</h2>
      <div className="grid gap-3">
        {tours.map(t => (
          <Link key={t.tour_id} to={`/tourplan/statistik/${date}/${encodeURIComponent(t.tour_id)}`} className="p-3 rounded-xl border bg-white shadow flex items-center justify-between">
            <div className="font-mono">{t.tour_id}</div>
            <div className="text-sm text-gray-600">Stops {t.stops} · {(t.distance_m/1000).toFixed(1)} km · {(t.duration_s/60).toFixed(0)} min</div>
            {t.timebox_exceeded && <span className="text-red-600 text-xs font-semibold">Zeitbox überschritten</span>}
          </Link>
        ))}
      </div>
    </div>
  );
}
```

---

### FILE: `src/pages/statistik/TourDetail.tsx`
```tsx
import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import polyline from "@mapbox/polyline";

// Primitive Leaflet-Integration wird vorausgesetzt; hier zeichnen wir nur die Daten auf eine Canvas/Leaflet-Map.

export default function TourDetail() {
  const { date, tourId } = useParams();
  const [snap, setSnap] = useState<any | null>(null);

  useEffect(() => {
    if (!date || !tourId) return;
    fetch(`/api/stats/day/${date}/tour/${tourId}`).then(r => r.json()).then(setSnap);
  }, [date, tourId]);

  const coords = useMemo(() => {
    if (!snap?.polyline_simplified) return [] as [number, number][];
    try { return polyline.decode(snap.polyline_simplified) as [number, number][]; } catch { return []; }
  }, [snap]);

  return (
    <div className="p-4 md:p-6 space-y-4">
      <h3 className="text-xl font-semibold">{tourId} – {date}</h3>
      <div className="text-sm text-gray-600">{(snap?.distance_m||0)/1000} km · {(snap?.duration_s||0)/60} min</div>

      <div className="relative rounded-2xl overflow-hidden border bg-white shadow h-[420px]">
        {/* Beispiel: Zwei Layer; Unterlage rot, wenn Zeitbox überschritten */}
        <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="absolute inset-0">
          {coords.length > 1 && (
            <>
              {snap?.timebox_exceeded && (
                <polyline points={coords.map(([a,b])=>`${b},${100-a}`).join(" ")} stroke="red" strokeOpacity="0.18" strokeWidth="4" fill="none" />
              )}
              <polyline points={coords.map(([a,b])=>`${b},${100-a}`).join(" ")} stroke="black" strokeWidth="1.5" fill="none" />
            </>
          )}
        </svg>
        {coords.length === 0 && <div className="p-4 text-sm">Keine Geometrie</div>}
      </div>
    </div>
  );
}
```

> In eurer echten Map (Leaflet/Mapbox) bitte zwei Polylines rendern: **Unterlage rot (opacity~0.18, dicker)** + reguläre Route darüber.

---

## 🪟 Abdockbare Panels (Popout Windows)

### Konzept
- **DetachablePanel** rendert seinen Inhalt in ein **neues Browserfenster** via Portal (ReactDOM.createPortal).
- **usePopoutWindow** kapselt `window.open`, Lifecycle und `postMessage`-Sync (optional für Live-Updates).
- Buttons an **Karte** und **Tourübersicht**: „Abdocken“ öffnet Popout; „Andocken“ schließt es wieder.

### FILE: `src/components/hooks/usePopoutWindow.ts`
```tsx
import { useEffect, useRef, useState } from "react";

export function usePopoutWindow(title = "Panel", features = "width=900,height=700") {
  const [opened, setOpened] = useState<Window | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    return () => { if (opened && !opened.closed) opened.close(); };
  }, [opened]);

  const open = () => {
    if (opened && !opened.closed) { opened.focus(); return opened; }
    const win = window.open("", title, features);
    if (!win) return null;
    win.document.title = title;
    const el = win.document.createElement("div");
    el.id = "popout-root";
    win.document.body.appendChild(el);
    containerRef.current = el as HTMLDivElement;
    setOpened(win);
    // Basic styles
    const style = win.document.createElement("style");
    style.textContent = `html,body,#popout-root{height:100%;margin:0} body{font-family:system-ui,Segoe UI,Roboto,Arial}`;
    win.document.head.appendChild(style);
    return win;
  };

  const close = () => { if (opened && !opened.closed) opened.close(); setOpened(null); };

  return { open, close, containerRef, opened };
}
```

---

### FILE: `src/components/DetachablePanel.tsx`
```tsx
import { useEffect, useMemo } from "react";
import ReactDOM from "react-dom";
import { usePopoutWindow } from "@/components/hooks/usePopoutWindow";

export default function DetachablePanel({
  title,
  docked,
  onDockChange,
  children,
}: {
  title: string;
  docked: boolean;
  onDockChange: (docked: boolean) => void;
  children: React.ReactNode;
}) {
  const { open, close, containerRef, opened } = usePopoutWindow(title);

  useEffect(() => {
    if (!docked) {
      const win = open();
      if (!win) onDockChange(true);
      const intv = setInterval(() => { if (opened && opened.closed) onDockChange(true); }, 1000);
      return () => clearInterval(intv);
    } else {
      close();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [docked]);

  if (docked) return <>{children}</>;
  if (!containerRef.current) return null;
  return ReactDOM.createPortal(<div style={{ padding: 8 }}>{children}</div>, containerRef.current);
}
```

---

### Map- und Tourlisten-Integration

#### FILE: `src/pages/tourplan/MapPanelWithPopout.tsx`
```tsx
import { useState } from "react";
import DetachablePanel from "@/components/DetachablePanel";
import { Maximize2, Minimize2 } from "lucide-react";

export default function MapPanelWithPopout() {
  const [docked, setDocked] = useState(true);
  return (
    <div className="rounded-2xl border bg-white shadow overflow-hidden">
      <div className="flex items-center justify-between p-2 border-b bg-gray-50">
        <div className="font-medium">Karte</div>
        <button className="p-1 rounded hover:bg-gray-200" onClick={() => setDocked(!docked)}>
          {docked ? <Maximize2 size={18}/> : <Minimize2 size={18}/>} {docked ? "Abdocken" : "Andocken"}
        </button>
      </div>
      <DetachablePanel title="Karte" docked={docked} onDockChange={setDocked}>
        <div className="h-[520px]">{/* Hier eure echte Map-Komponente einfügen */}
          <div className="h-full grid place-items-center text-sm text-gray-600">Map Placeholder</div>
        </div>
      </DetachablePanel>
    </div>
  );
}
```

#### FILE: `src/pages/tourplan/TourListWithPopout.tsx`
```tsx
import { useState } from "react";
import DetachablePanel from "@/components/DetachablePanel";
import { Maximize2, Minimize2 } from "lucide-react";

export default function TourListWithPopout() {
  const [docked, setDocked] = useState(true);
  return (
    <div className="rounded-2xl border bg-white shadow overflow-hidden">
      <div className="flex items-center justify-between p-2 border-b bg-gray-50">
        <div className="font-medium">Tourübersicht</div>
        <button className="p-1 rounded hover:bg-gray-200" onClick={() => setDocked(!docked)}>
          {docked ? <Maximize2 size={18}/> : <Minimize2 size={18}/>} {docked ? "Abdocken" : "Andocken"}
        </button>
      </div>
      <DetachablePanel title="Tourübersicht" docked={docked} onDockChange={setDocked}>
        <div className="p-3">
          {/* Eure echte Tourliste hier rein (Tabelle/Accordion) */}
          <ul className="space-y-2">
            <li className="p-2 border rounded-xl">W-07.00 (17 Stops)</li>
            <li className="p-2 border rounded-xl">W-09.00 (29 Stops)</li>
            <li className="p-2 border rounded-xl">W-11.00 (22 Stops)</li>
          </ul>
        </div>
      </DetachablePanel>
    </div>
  );
}
```

---

## 🔗 Routing-Setup (Frontend)

### FILE: `src/AppRoutes.tsx` (Ausschnitt)
```tsx
import { RouteObject } from "react-router-dom";
import StatistikPage from "@/pages/statistik/StatistikPage";
import DayView from "@/pages/statistik/DayView";
import TourDetail from "@/pages/statistik/TourDetail";

export const routes: RouteObject[] = [
  // ...
  { path: "/tourplan/statistik", element: <StatistikPage/> },
  { path: "/tourplan/statistik/:date", element: <DayView/> },
  { path: "/tourplan/statistik/:date/:tourId", element: <TourDetail/> },
];
```

---

## 🧪 Frontend-Tests (Vitest + RTL)

### FILE: `src/__tests__/StoragePathCard.test.tsx`
```tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import StoragePathCard from "@/components/StoragePathCard";

describe("StoragePathCard", () => {
  it("lädt und speichert Pfad", async () => {
    // mock fetch
    global.fetch = vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => ({ path: "C:/tmp" }) })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ ok: true }) }) as any;

    render(<StoragePathCard/>);
    expect(await screen.findByDisplayValue("C:/tmp")).toBeInTheDocument();

    fireEvent.change(screen.getByRole("textbox"), { target: { value: "C:/stats" } });
    fireEvent.click(screen.getByText("Test & Speichern"));

    await waitFor(() => screen.getByText(/Gespeichert/));
    expect(screen.getByText(/Gespeichert/)).toBeInTheDocument();
  });
});
```

### FILE: `src/__tests__/DetachablePanel.test.tsx`
```tsx
import { describe, it, expect, vi } from "vitest";
import { render } from "@testing-library/react";
import DetachablePanel from "@/components/DetachablePanel";

// JSDOM kann window.open nicht real öffnen; wir mocken es minimal.

describe("DetachablePanel", () => {
  it("rendert angedockt", () => {
    const { getByText } = render(
      <DetachablePanel title="Test" docked={true} onDockChange={()=>{}}>
        <div>CONTENT</div>
      </DetachablePanel>
    );
    expect(getByText("CONTENT")).toBeInTheDocument();
  });

  it("öffnet Popout bei undocked (mock)", () => {
    // mock window.open
    const fakeWin: any = { document: { body: document.body, head: document.head, createElement: (t: string)=>document.createElement(t) }, closed: false, close: vi.fn(), focus: vi.fn(), };
    const openSpy = vi.spyOn(window, "open").mockReturnValue(fakeWin);

    render(
      <DetachablePanel title="Test" docked={false} onDockChange={()=>{}}>
        <div>CONTENT</div>
      </DetachablePanel>
    );
    expect(openSpy).toHaveBeenCalled();
  });
});
```

---

## 🧩 UX-Regeln – Zeitbox (rote Unterlage)

- Backend liefert `timebox_exceeded` je Tour.
- Frontend: **immer dieselbe Route doppelt zeichnen**, wenn `true` →
  - Untere Polyline: `rgba(255,0,0,0.18)`, größerer `strokeWidth` (z. B. 9)
  - Obere Polyline: regulär (z. B. 5) — so entsteht die „leicht rote Unterlegung“.

---

## ⚙️ Konfiguration

- ENV: `STATS_STORAGE_PATH=C:\\Workflow\\TrafficApp\\data\\stats` (oder `\\\\server\\share\\stats`)
- Fallback ist oben im `stats_storage.py` implementiert.

---

## ✅ Akzeptanz-Checkliste

- [ ] Pfad in UI ändern → **OK-Badge** nach Testschreibprobe.
- [ ] Snapshot-API speichert unter `{base}/YYYY/MM/DD/` und aktualisiert `_index.json`.
- [ ] Tagansicht listet Touren mit Kennzahlen & Overrun-Badge.
- [ ] Tourdetail zeigt Route; bei Overrun **rote Unterlage**.
- [ ] Retention entfernt `polyline_full` nach N Tagen (API `/api/stats/retention/compact`).
- [ ] **Abdocken** der Karte & Tourliste funktioniert (separate Fenster).

---

## 📝 Nächste Schritte (Empfohlen)

- Echte Map (Leaflet/Mapbox) einhängen; Polylines dort doppelt rendern.
- OSRM-Snapshots automatisieren (Hook am Ende der Tourberechnung / Tagesabschluss-Task 19:00 Uhr).
- Extra-Dash: Summen/Ø je Woche/Monat, Heatmap Stundenlast, Top‑Overruns.
- Optional: Index-DB (SQLite) für schnelle Filter — Snapshots bleiben JSON‑Quelle.
```

