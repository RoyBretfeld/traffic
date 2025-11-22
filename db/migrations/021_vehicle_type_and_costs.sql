-- Migration 021: Fahrzeugtyp und erweiterte Kostenberechnung
-- Erstellt fahrzeug_typ Spalte in touren Tabelle und erweitert Kostenberechnung
-- Datum: 2025-11-22

-- Füge fahrzeug_typ Spalte hinzu (falls nicht vorhanden)
-- Mögliche Werte: 'diesel', 'e_auto', 'benzin' (Standard: 'diesel')
ALTER TABLE touren ADD COLUMN fahrzeug_typ TEXT DEFAULT 'diesel';

-- Erstelle Index für Fahrzeugtyp (für Statistiken)
CREATE INDEX IF NOT EXISTS idx_touren_fahrzeug_typ ON touren(fahrzeug_typ);

-- Kommentar: Fahrzeugtyp wird verwendet für:
-- - Diesel: Diesel-Kosten + AdBlue-Kosten
-- - E-Auto: Strom-Kosten
-- - Benzin: Benzin-Kosten

