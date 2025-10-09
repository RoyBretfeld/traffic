"""
Unit-Tests für Fuzzy-Suggest Service
"""
import pytest
from services.fuzzy_suggest import suggest_for, get_suggestions_stats
from repositories.geo_repo import canon_addr

def test_canon_addr_basic():
    """Test der kanonischen Adress-Normalisierung."""
    # Grundlegende Normalisierung
    assert canon_addr("Löbtauer Straße 1") == "löbtauer straße 1"
    assert canon_addr("  Mehrfach   Whitespace  ") == "mehrfach whitespace"
    
    # Abkürzungen
    assert canon_addr("Hauptstr. 42") == "hauptstraße 42"
    assert canon_addr("Marktpl. 1") == "marktplatz 1"
    assert canon_addr("Parkallee 5") == "parkallee 5"
    
    # Unicode-Normalisierung
    assert canon_addr("Löbtauer Straße") == "löbtauer straße"

def test_canon_addr_edge_cases():
    """Test der kanonischen Normalisierung bei Edge Cases."""
    # Leere Strings
    assert canon_addr("") == ""
    assert canon_addr(None) == ""
    
    # Nur Whitespace
    assert canon_addr("   ") == ""
    
    # Spezielle Zeichen
    assert canon_addr("Straße-1") == "straße-1"

def test_suggest_for_basic():
    """Test der grundlegenden Fuzzy-Suggest-Funktionalität."""
    pool = [
        "Fröbelstraße 1, Dresden",
        "Löbtauer Straße 2, Heidenau", 
        "Königsbrücker Straße 3, Dresden",
        "Hauptstraße 42, Leipzig",
        "Marktplatz 1, Berlin"
    ]
    
    missing = [
        "Froebelstr. 1, Dresden",  # Abkürzung + Umlaut-Variante
        "Koenigsbruecker Str 3, Dresden",  # Umlaut-Variante + Abkürzung
        "Hauptstr. 42, Leipzig"  # Abkürzung
    ]
    
    result = suggest_for(missing, topk=3, threshold=60, pool=pool)
    
    # Prüfe Struktur
    assert len(result) == 3
    assert all("query" in item for item in result)
    assert all("suggestions" in item for item in result)
    
    # Prüfe erste Adresse (sollte Fröbelstraße finden)
    first_item = result[0]
    assert first_item["query"] == "Froebelstr. 1, Dresden"
    assert len(first_item["suggestions"]) > 0
    
    # Prüfe Score-Struktur
    for suggestion in first_item["suggestions"]:
        assert "address" in suggestion
        assert "score" in suggestion
        assert isinstance(suggestion["score"], float)
        assert suggestion["score"] >= 60

def test_suggest_for_threshold():
    """Test der Threshold-Funktionalität."""
    pool = ["Hauptstraße 1", "Nebenstraße 2", "Seitenstraße 3"]
    missing = ["Hauptstraße 1"]  # Exakte Übereinstimmung
    
    # Hoher Threshold (sollte exakte Übereinstimmung finden)
    result_high = suggest_for(missing, topk=3, threshold=95, pool=pool)
    assert len(result_high[0]["suggestions"]) > 0
    
    # Niedriger Threshold (sollte mehr Vorschläge finden)
    result_low = suggest_for(missing, topk=3, threshold=10, pool=pool)
    assert len(result_low[0]["suggestions"]) >= len(result_high[0]["suggestions"])

def test_suggest_for_empty_inputs():
    """Test bei leeren Eingaben."""
    # Leere fehlende Adressen
    result = suggest_for([], pool=["Test"])
    assert result == []
    
    # Leerer Pool
    result = suggest_for(["Test"], pool=[])
    assert len(result) == 1
    assert result[0]["suggestions"] == []
    
    # Leere Adressen
    result = suggest_for(["", "   ", None], pool=["Test"])
    assert len(result) == 3
    assert all(item["suggestions"] == [] for item in result)

def test_suggest_for_topk_limit():
    """Test der topk-Begrenzung."""
    pool = ["Hauptstraße 1", "Hauptstraße 2", "Hauptstraße 3", "Hauptstraße 4"]
    missing = ["Hauptstraße"]
    
    # topk=2 sollte maximal 2 Vorschläge zurückgeben
    result = suggest_for(missing, topk=2, threshold=50, pool=pool)
    assert len(result[0]["suggestions"]) <= 2

def test_suggest_for_no_matches():
    """Test wenn keine Matches gefunden werden."""
    pool = ["Komplett andere Adresse"]
    missing = ["Hauptstraße 1"]
    
    result = suggest_for(missing, topk=3, threshold=90, pool=pool)
    assert len(result) == 1
    assert result[0]["suggestions"] == []

def test_get_suggestions_stats():
    """Test der Statistiken-Funktion."""
    stats = get_suggestions_stats()
    
    # Prüfe Struktur
    assert "total_cached_addresses" in stats
    assert "fuzzy_engine" in stats
    assert "max_pool_size" in stats
    
    # Prüfe Typen
    assert isinstance(stats["total_cached_addresses"], int)
    assert isinstance(stats["fuzzy_engine"], str)
    assert isinstance(stats["max_pool_size"], int)
    
    # Prüfe gültige Werte
    assert stats["total_cached_addresses"] >= 0
    assert stats["fuzzy_engine"] in ["rapidfuzz", "difflib"]
    assert stats["max_pool_size"] > 0

def test_suggest_for_realistic_scenario():
    """Test mit realistischen deutschen Adressen."""
    pool = [
        "Löbtauer Straße 1, 01809 Heidenau",
        "Hauptstraße 42, 01067 Dresden", 
        "Marktplatz 5, 01069 Dresden",
        "Bahnhofstraße 10, 01099 Dresden",
        "Königsbrücker Straße 15, 01099 Dresden"
    ]
    
    missing = [
        "Löbtauer Str. 1, Heidenau",  # Abkürzung + PLZ fehlt
        "Hauptstr. 42, Dresden",      # Abkürzung + PLZ fehlt
        "Marktpl. 5, Dresden"          # Abkürzung + PLZ fehlt
    ]
    
    result = suggest_for(missing, topk=2, threshold=70, pool=pool)
    
    # Prüfe dass alle fehlenden Adressen verarbeitet wurden
    assert len(result) == 3
    
    # Prüfe dass mindestens eine Adresse Vorschläge hat
    suggestions_found = any(len(item["suggestions"]) > 0 for item in result)
    assert suggestions_found

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
