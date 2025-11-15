from pathlib import Path
import pandas as pd
from ingest.reader import read_tourplan
from fs.safefs import init_policy
import os

# Test‑CSV mit Umlauten erzeugen (als CP850 gespeichert)
SAMPLE = "Kunde;Adresse\nMüller;Löbtauer Straße 1, 01809 Heidenau\n"

def test_read_tourplan_cp850(tmp_path, monkeypatch):
    # Arrange Pfade
    orig_dir = tmp_path / "tourplaene"; orig_dir.mkdir(parents=True)
    stag_dir = tmp_path / "data" / "staging"; stag_dir.mkdir(parents=True)
    
    # PathPolicy initialisieren
    init_policy(str(orig_dir), str(stag_dir), str(tmp_path / "data" / "output"))
    
    # Schreibe CP850‑Datei ins ORIG (simuliert Original‑Drop)
    src = orig_dir / "Plan.csv"
    src.write_bytes(SAMPLE.encode("cp850"))

    # Act - Direkter Aufruf mit expliziten Parametern
    from ingest.reader import _canonicalize_to_utf8
    staged = _canonicalize_to_utf8(src)
    df = pd.read_csv(staged, sep=";", header=None, dtype=str)

    # Assert – Umlaute korrekt, Kopie existiert, Spalten stimmen
    assert staged.exists()
    assert df.shape[0] >= 1 and df.shape[1] >= 2
    row = df.iloc[1 if df.iloc[0,0].lower()=="kunde" else 0]
    assert "Müller" in " ".join(row.astype(str))
    assert "Löbtauer Straße" in " ".join(row.astype(str))
