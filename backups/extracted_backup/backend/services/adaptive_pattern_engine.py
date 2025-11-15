"""
Adaptive Pattern Engine: Lernt automatisch aus Daten - ohne AI-Kosten

Erkennt Pattern wie:
- OT-Normalisierung
- BAR-Paarungen
- Adress-Varianten
- Routen-Optimierungen

Speichert erkannte Pattern in DB für Wiederverwendung.
"""

import re
import sqlite3
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, asdict
import json
from datetime import datetime

@dataclass
class LearnedPattern:
    """Ein gelerntes Pattern"""
    pattern_id: int
    input_text: str
    normalized_output: str
    pattern_type: str  # 'ot_removal', 'slash_split', 'dash_split', etc.
    confidence: float
    usage_count: int
    created_at: str
    last_used: str

class AdaptivePatternEngine:
    """
    Erkennt und speichert Pattern automatisch - ohne AI
    """
    
    def __init__(self, db_path: str = "data/learned_patterns.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()
    
    def _ensure_schema(self):
        """Erstellt Schema für Pattern-Datenbank"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learned_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                input_text TEXT NOT NULL,
                normalized_output TEXT NOT NULL,
                pattern_type TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                usage_count INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                last_used TEXT NOT NULL,
                UNIQUE(input_text, pattern_type)
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_input_text 
            ON learned_patterns(input_text)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_pattern_type 
            ON learned_patterns(pattern_type)
        """)
        
        conn.commit()
        conn.close()
    
    def learn_pattern(self, input_text: str, normalized: str, pattern_type: str, confidence: float = 1.0):
        """
        Speichert ein neues Pattern oder aktualisiert existierendes
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        # Prüfe ob Pattern bereits existiert
        cursor.execute("""
            SELECT id, usage_count FROM learned_patterns 
            WHERE input_text = ? AND pattern_type = ?
        """, (input_text, pattern_type))
        
        existing = cursor.fetchone()
        
        if existing:
            # Aktualisiere usage_count
            cursor.execute("""
                UPDATE learned_patterns 
                SET usage_count = usage_count + 1,
                    last_used = ?,
                    confidence = ?
                WHERE id = ?
            """, (now, confidence, existing[0]))
        else:
            # Neues Pattern speichern
            cursor.execute("""
                INSERT INTO learned_patterns 
                (input_text, normalized_output, pattern_type, confidence, usage_count, created_at, last_used)
                VALUES (?, ?, ?, ?, 1, ?, ?)
            """, (input_text, normalized, pattern_type, confidence, now, now))
        
        conn.commit()
        conn.close()
    
    def get_pattern(self, input_text: str, pattern_type: Optional[str] = None) -> Optional[Dict]:
        """
        Sucht Pattern in Datenbank
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if pattern_type:
            cursor.execute("""
                SELECT * FROM learned_patterns 
                WHERE input_text = ? AND pattern_type = ?
            """, (input_text, pattern_type))
        else:
            cursor.execute("""
                SELECT * FROM learned_patterns 
                WHERE input_text = ?
                ORDER BY usage_count DESC, confidence DESC
                LIMIT 1
            """, (input_text,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "id": row[0],
                "input_text": row[1],
                "normalized_output": row[2],
                "pattern_type": row[3],
                "confidence": row[4],
                "usage_count": row[5],
                "created_at": row[6],
                "last_used": row[7]
            }
        
        return None
    
    def normalize_with_learning(self, text: str, context: Optional[Dict] = None) -> Tuple[str, str]:
        """
        Normalisiert Text mit automatischem Lernen
        
        Returns:
            (normalized_text, pattern_type)
        """
        # 1. Prüfe ob Pattern bereits gelernt wurde
        learned = self.get_pattern(text)
        if learned:
            # Pattern bekannt: Verwende direkt (kostenlos!)
            self.learn_pattern(text, learned["normalized_output"], learned["pattern_type"])
            return learned["normalized_output"], learned["pattern_type"]
        
        # 2. Wende Standard-Regeln an (kostenlos)
        normalized, pattern_type = self._apply_rules(text, context)
        
        # 3. Speichere Pattern für nächstes Mal
        if normalized != text:
            self.learn_pattern(text, normalized, pattern_type)
        
        return normalized, pattern_type
    
    def _apply_rules(self, text: str, context: Optional[Dict] = None) -> Tuple[str, str]:
        """
        Wendet kostenlose Python-Regeln an
        """
        # OT-Entfernung
        from repositories.geo_repo import has_ot_part, remove_ot_part
        if has_ot_part(text):
            normalized = remove_ot_part(text).strip().rstrip(',').strip()
            return normalized, "ot_removed"
        
        # Slash-Split
        if '/' in text:
            normalized = text.split('/')[0].strip()
            return normalized, "slash_split"
        
        # Dash-Split
        if ' - ' in text or ' -' in text:
            normalized = text.split(' -')[0].strip().split('-')[0].strip()
            return normalized, "dash_split"
        
        # Keine Änderung
        return text, "unchanged"
    
    def get_statistics(self) -> Dict:
        """Gibt Statistiken über gelernte Pattern zurück"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM learned_patterns")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(usage_count) FROM learned_patterns")
        total_usage = cursor.fetchone()[0] or 0
        
        cursor.execute("""
            SELECT pattern_type, COUNT(*) 
            FROM learned_patterns 
            GROUP BY pattern_type
        """)
        by_type = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            "total_patterns": total,
            "total_usage": total_usage,
            "by_type": by_type
        }

# Singleton-Instanz
_pattern_engine: Optional[AdaptivePatternEngine] = None

def get_pattern_engine() -> AdaptivePatternEngine:
    """Gibt globale Pattern-Engine-Instanz zurück"""
    global _pattern_engine
    if _pattern_engine is None:
        _pattern_engine = AdaptivePatternEngine()
    return _pattern_engine

