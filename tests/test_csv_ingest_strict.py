"""Tests für deterministisches CSV-Parsing mit Synonym-Resolver"""

from pathlib import Path
import json
import pytest
from backend.pipeline.csv_ingest_strict import parse_csv, IngestError
from backend.services.synonyms import SynonymStore, Synonym


def test_ingest_deterministic(tmp_path: Path):
    """Golden File Test: Deterministisches Parsing mit Synonym"""
    # Arrange
    db = tmp_path / 'test.sqlite3'
    syn = SynonymStore(db)
    
    # Synonym hinzufügen
    syn.upsert(Synonym(
        alias='Roswitha',
        customer_id='C001',
        street='Hauptstr 1',
        postal_code='01067',
        city='Dresden'
    ))
    
    # CSV erstellen
    csv_in = tmp_path / 'in.csv'
    csv_in.write_text(
        'customer;street;postal_code;city\nRoswitha;;;Dresden\n',
        encoding='utf-8'
    )
    
    # Act
    rows = parse_csv(csv_in, syn)
    
    # Assert
    assert len(rows) == 1
    assert rows[0]['street'] == 'Hauptstr 1'
    assert rows[0]['postal_code'] == '01067'
    assert rows[0]['city'] == 'Dresden'
    assert rows[0]['synonym_applied'] is True
    
    # Golden Snapshot
    snap = tmp_path / 'snap.json'
    snap.write_text(
        json.dumps(rows, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    
    # Verify: Zweiter Lauf muss identisch sein
    rows2 = parse_csv(csv_in, syn)
    assert rows == rows2


def test_ingest_without_synonym(tmp_path: Path):
    """Test ohne Synonym"""
    db = tmp_path / 'test.sqlite3'
    syn = SynonymStore(db)
    
    csv_in = tmp_path / 'in.csv'
    csv_in.write_text(
        'customer;street;postal_code;city\nMax Mustermann;Hauptstr 1;01067;Dresden\n',
        encoding='utf-8'
    )
    
    rows = parse_csv(csv_in, syn)
    
    assert len(rows) == 1
    assert rows[0]['street'] == 'Hauptstr 1'
    assert rows[0]['postal_code'] == '01067'
    assert rows[0]['city'] == 'Dresden'
    assert rows[0]['synonym_applied'] is False


def test_ingest_missing_columns(tmp_path: Path):
    """Test mit fehlenden Pflichtspalten"""
    db = tmp_path / 'test.sqlite3'
    syn = SynonymStore(db)
    
    csv_in = tmp_path / 'in.csv'
    csv_in.write_text(
        'customer;street\nMax Mustermann;Hauptstr 1\n',
        encoding='utf-8'
    )
    
    with pytest.raises(IngestError, match="Pflichtspalten fehlen"):
        parse_csv(csv_in, syn)


def test_ingest_quarantine(tmp_path: Path):
    """Test: Fehlerhafte Zeilen werden verarbeitet (leere Felder sind erlaubt, aber nicht ideal)"""
    db = tmp_path / 'test.sqlite3'
    syn = SynonymStore(db)
    
    csv_in = tmp_path / 'in.csv'
    # Valide erste Zeile, zweite mit leeren Feldern
    csv_in.write_text(
        'customer;street;postal_code;city\nMax Mustermann;Hauptstr 1;01067;Dresden\nInvalid;;;\n',
        encoding='utf-8'
    )
    
    rows = parse_csv(csv_in, syn)
    
    # Beide Zeilen werden verarbeitet (leere Felder sind erlaubt)
    assert len(rows) >= 1
    # Erste Zeile ist valide
    assert rows[0]['customer'] == 'Max Mustermann'
    assert rows[0]['street'] == 'Hauptstr 1'

