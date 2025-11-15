"""Test für Parser ohne Latin-1 Hardcode."""
from importlib import reload
from pathlib import Path
import tempfile
import sys

# Füge das Projekt-Root-Verzeichnis zum Python-Pfad hinzu
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_header_parsing_keeps_umlauts(tmp_path):
    """Test dass Header-Parsing Umlaute intakt lässt."""
    p = tmp_path/"t.csv"
    content = "Lieferdatum: 04.09.2025\nKunde;Straße;PLZ;Stadt\nA;Fröbelstraße 1;01234;Dresden\n".encode('utf-8')
    p.write_bytes(content)
    
    import backend.parsers.tour_plan_parser as tp; reload(tp)
    
    # Test der Heuristik-Funktion
    raw = p.read_bytes()
    txt, enc = tp._heuristic_decode(raw)
    assert 'Fröbelstraße' in txt, f"Umlaute nicht erhalten: {txt}"
    assert enc in ('utf-8-sig','utf-8*replace','cp850','latin-1'), f"Unerwartetes Encoding: {enc}"
    
    # Test der parse_tour_plan Funktion
    plan = tp.parse_tour_plan(p)
    assert plan.delivery_date == "2025-09-04", f"Delivery date nicht korrekt: {plan.delivery_date}"
    assert len(plan.tours) > 0, "Keine Touren gefunden"
    
    # Prüfe dass Umlaute in den Kunden-Daten erhalten bleiben
    for tour in plan.tours:
        for customer in tour.customers:
            if 'Fröbelstraße' in customer.street:
                assert 'ö' in customer.street, f"Umlaut verloren: {customer.street}"
                print(f"✓ Umlaut erhalten: {customer.street}")

def test_heuristic_decode_variants():
    """Test verschiedene Encoding-Varianten."""
    import backend.parsers.tour_plan_parser as tp; reload(tp)
    
    # UTF-8 Test
    utf8_content = "Fröbelstraße 1, Dresden".encode('utf-8')
    txt, enc = tp._heuristic_decode(utf8_content)
    assert 'Fröbelstraße' in txt
    assert enc == 'utf-8-sig' or enc == 'utf-8*replace'
    
    # CP850 Test
    cp850_content = "Fröbelstraße 1, Dresden".encode('cp850')
    txt, enc = tp._heuristic_decode(cp850_content)
    assert 'Fröbelstraße' in txt
    assert enc == 'cp850'
    
    # Latin-1 Test
    latin1_content = "Fröbelstraße 1, Dresden".encode('latin-1')
    txt, enc = tp._heuristic_decode(latin1_content)
    assert 'Fröbelstraße' in txt
    assert enc == 'latin-1'

if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmp_dir:
        print("=== Parser Encoding Test ===")
        test_header_parsing_keeps_umlauts(Path(tmp_dir))
        test_heuristic_decode_variants()
        print("✓ Alle Tests erfolgreich!")
