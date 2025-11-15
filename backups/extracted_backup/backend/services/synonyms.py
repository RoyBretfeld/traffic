"""Synonym-Store: Persistente Alias-Auflösung (vor Geocoding)"""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import sqlite3
from typing import Optional

from backend.services.text_normalize import normalize_token


@dataclass
class Synonym:
    """Dataclass für ein Synonym-Eintrag"""
    alias: str
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    street: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    country: str = "DE"
    lat: Optional[float] = None
    lon: Optional[float] = None
    priority: int = 0
    active: int = 1
    note: Optional[str] = None


class SynonymStore:
    """Persistenter Store für Adress-Synonyme (Alias → Customer/Address/Coordinates)"""
    
    def __init__(self, db_path: Path | str):
        """
        Args:
            db_path: Pfad zur SQLite-Datenbank (z.B. 'data/address_corrections.sqlite3')
        """
        if isinstance(db_path, str):
            db_path = Path(db_path)
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(db_path))
        self.db.row_factory = sqlite3.Row
        self._ensure_schema()
    
    def _ensure_schema(self):
        """Stellt sicher, dass das Schema existiert"""
        migration_path = Path(__file__).resolve().parents[2] / 'db' / 'migrations' / '003_synonyms.sql'
        if migration_path.exists():
            try:
                self.db.executescript(migration_path.read_text(encoding='utf-8'))
                self.db.commit()
            except sqlite3.OperationalError as e:
                # Tabelle existiert bereits → OK
                if "already exists" not in str(e).lower():
                    raise
    
    def _norm(self, alias: str) -> str:
        """Normalisiert einen Alias für die Suche"""
        return normalize_token(alias).casefold()
    
    def resolve(self, alias: str) -> Optional[Synonym]:
        """
        Löst einen Alias auf (wird VOR Geocoding verwendet).
        
        Args:
            alias: Der zu suchende Alias (z.B. "Roswitha" oder "Hauptstr 1")
            
        Returns:
            Synonym-Objekt oder None wenn nicht gefunden
        """
        an = self._norm(alias)
        row = self.db.execute(
            "SELECT * FROM address_synonyms WHERE alias_norm=? AND active=1 ORDER BY priority DESC LIMIT 1",
            (an,)
        ).fetchone()
        
        if not row:
            return None
        
        # Nutzungsstatistik tracken
        try:
            self.db.execute("INSERT INTO synonym_hits(alias_norm) VALUES (?)", (an,))
            self.db.commit()
        except Exception:
            # Ignorieren wenn Hit-Tabelle noch nicht existiert
            pass
        
        return Synonym(
            alias=row["alias"],
            customer_id=row["customer_id"],
            customer_name=row["customer_name"],
            street=row["street"],
            postal_code=row["postal_code"],
            city=row["city"],
            country=row["country"] or "DE",
            lat=row["lat"],
            lon=row["lon"],
            priority=row["priority"],
            active=row["active"],
            note=row["note"]
        )
    
    def upsert(self, s: Synonym) -> None:
        """
        Fügt ein Synonym hinzu oder aktualisiert es.
        
        Args:
            s: Synonym-Objekt
        """
        an = self._norm(s.alias)
        self.db.execute(
            """
            INSERT INTO address_synonyms(alias,alias_norm,customer_id,customer_name,street,postal_code,city,country,lat,lon,note,active,priority)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(alias) DO UPDATE SET
              alias_norm=excluded.alias_norm,
              customer_id=excluded.customer_id,
              customer_name=excluded.customer_name,
              street=excluded.street,
              postal_code=excluded.postal_code,
              city=excluded.city,
              country=excluded.country,
              lat=excluded.lat,
              lon=excluded.lon,
              note=excluded.note,
              active=excluded.active,
              priority=excluded.priority,
              updated_at=datetime('now')
            """,
            (
                s.alias, an, s.customer_id, s.customer_name,
                s.street, s.postal_code, s.city, s.country,
                s.lat, s.lon, s.note, s.active, s.priority
            )
        )
        self.db.commit()
    
    def list_all(self, limit: int = 200, active_only: bool = True) -> list[dict]:
        """
        Listet alle Synonyme auf.
        
        Args:
            limit: Maximale Anzahl
            active_only: Nur aktive Synonyme
            
        Returns:
            Liste von Dictionaries
        """
        sql = "SELECT * FROM address_synonyms"
        params = []
        if active_only:
            sql += " WHERE active=1"
        sql += " ORDER BY priority DESC, alias LIMIT ?"
        params.append(limit)
        
        rows = self.db.execute(sql, params).fetchall()
        return [dict(row) for row in rows]
    
    def delete(self, alias: str) -> bool:
        """
        Löscht ein Synonym (oder setzt auf inaktiv).
        
        Args:
            alias: Der zu löschende Alias
            
        Returns:
            True wenn gelöscht/deaktiviert
        """
        an = self._norm(alias)
        result = self.db.execute(
            "UPDATE address_synonyms SET active=0 WHERE alias_norm=?", (an,)
        )
        self.db.commit()
        return result.rowcount > 0

