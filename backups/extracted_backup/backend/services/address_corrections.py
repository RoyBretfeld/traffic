# -*- coding: utf-8 -*-
"""
FAMO – AddressCorrectionStore

Speichert manuelle Adresskorrekturen und verwaltet die Exception-Queue.
"""

from __future__ import annotations

import csv
import re
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict


def normalize_street(street: Optional[str]) -> Optional[str]:
    """Normalisiert einen Straßennamen für konsistente Speicherung."""
    if not street:
        return None
    s = street.strip()
    # Einfache Normalisierung: Whitespace normalisieren
    s = re.sub(r"\s+", " ", s)
    # Häufige Abkürzungen vereinheitlichen
    low = s.lower()
    if low.endswith("str"):
        s = s[:-3] + "straße"
    elif low.endswith("strasse"):
        s = s[:-6] + "straße"
    return s


class AddressCorrectionStore:
    """Verwaltet Adresskorrekturen in einer SQLite-Datenbank."""
    
    def __init__(self, db_path: Path | str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()
    
    def _ensure_schema(self) -> None:
        """Stellt sicher, dass die Tabellen existieren."""
        with sqlite3.connect(self.db_path) as con:
            # address_corrections Tabelle
            con.execute("""
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
                )
            """)
            
            # address_exception_queue Tabelle
            con.execute("""
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
                )
            """)
            
            # Trigger für updated_at
            con.execute("""
                CREATE TRIGGER IF NOT EXISTS trg_address_corrections_updated
                AFTER UPDATE ON address_corrections
                FOR EACH ROW BEGIN
                    UPDATE address_corrections SET updated_at = datetime('now') WHERE key = OLD.key;
                END
            """)
            
            con.execute("""
                CREATE TRIGGER IF NOT EXISTS trg_address_exception_queue_updated
                AFTER UPDATE ON address_exception_queue
                FOR EACH ROW BEGIN
                    UPDATE address_exception_queue SET updated_at = datetime('now') WHERE key = OLD.key;
                END
            """)
            
            con.commit()
    
    def list_pending(self, limit: int = 100) -> List[Dict]:
        """Listet ausstehende Adressen aus der Exception-Queue."""
        with sqlite3.connect(self.db_path) as con:
            con.row_factory = sqlite3.Row
            cur = con.execute("""
                SELECT key, street, postal_code, city, country, last_seen, times_seen, note
                FROM address_exception_queue
                WHERE status = 'pending'
                ORDER BY times_seen DESC, last_seen DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cur.fetchall()]
    
    def resolve(self, key: str, lat: float, lon: float, 
                street_canonical: Optional[str] = None,
                source: str = "manual", 
                confidence: float = 1.0) -> None:
        """Löst eine Adresse auf (speichert Korrektur und entfernt aus Queue)."""
        # Parse key: norm(street)|postal_code|city|country
        parts = key.split("|")
        if len(parts) < 3:
            raise KeyError(f"Ungültiger Key-Format: {key}")
        
        street = parts[0]
        postal_code = parts[1]
        city = parts[2]
        country = parts[3] if len(parts) > 3 else "DE"
        
        street_canonical = street_canonical or normalize_street(street) or street
        
        with sqlite3.connect(self.db_path) as con:
            # In Korrekturen speichern
            con.execute("""
                INSERT OR REPLACE INTO address_corrections 
                (key, street_canonical, postal_code, city, country, lat, lon, source, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (key, street_canonical, postal_code, city, country, lat, lon, source, confidence))
            
            # Aus Queue entfernen
            con.execute("""
                UPDATE address_exception_queue 
                SET status = 'resolved'
                WHERE key = ?
            """, (key,))
            
            con.commit()
    
    def export_csv(self, output_path: Path | str) -> None:
        """Exportiert alle Korrekturen als CSV."""
        output_path = Path(output_path)
        with sqlite3.connect(self.db_path) as con:
            con.row_factory = sqlite3.Row
            cur = con.execute("""
                SELECT key, street_canonical, postal_code, city, country, 
                       lat, lon, source, confidence, created_at, updated_at
                FROM address_corrections
                ORDER BY created_at DESC
            """)
            
            rows = cur.fetchall()
            
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            if not rows:
                return
            
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            for row in rows:
                writer.writerow(dict(row))
    
    def import_csv(self, csv_path: Path | str) -> int:
        """Importiert Korrekturen aus CSV (key-basiert, INSERT OR REPLACE)."""
        csv_path = Path(csv_path)
        if not csv_path.exists():
            return 0
        
        count = 0
        with open(csv_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            with sqlite3.connect(self.db_path) as con:
                for row in reader:
                    key = row.get("key", "")
                    if not key:
                        continue
                    
                    con.execute("""
                        INSERT OR REPLACE INTO address_corrections
                        (key, street_canonical, postal_code, city, country, lat, lon, source, confidence, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        key,
                        row.get("street_canonical", ""),
                        row.get("postal_code", ""),
                        row.get("city", ""),
                        row.get("country", "DE"),
                        float(row["lat"]) if row.get("lat") else None,
                        float(row["lon"]) if row.get("lon") else None,
                        row.get("source", "manual"),
                        float(row.get("confidence", 1.0)),
                        row.get("created_at", ""),
                        row.get("updated_at", "")
                    ))
                    count += 1
                
                con.commit()
        
        return count

