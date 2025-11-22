"""
Tour-Embedder: Erstellt Embeddings aus Tour-Metadaten.
Verwendet OpenAI-Embeddings oder lokales Modell.
"""
import os
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# OpenAI-Client wird lazy importiert
_openai_client = None


def get_openai_client():
    """
    Gibt den OpenAI-Client zurück (lazy initialization).
    
    Returns:
        openai.OpenAI oder None wenn OpenAI nicht verfügbar ist
    """
    global _openai_client
    
    if _openai_client is not None:
        return _openai_client
    
    try:
        from openai import OpenAI
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY nicht gesetzt - Embeddings nicht möglich")
            return None
        
        _openai_client = OpenAI(api_key=api_key)
        logger.info("OpenAI-Client initialisiert")
        return _openai_client
        
    except ImportError:
        logger.warning("OpenAI-Package nicht installiert. Installiere mit: pip install openai")
        return None
    except Exception as e:
        logger.error(f"Fehler beim Initialisieren von OpenAI: {e}", exc_info=True)
        return None


def create_tour_text(tour_metadata: Dict[str, Any]) -> str:
    """
    Erstellt einen Text-String aus Tour-Metadaten für Embedding.
    
    Args:
        tour_metadata: Dict mit tour_id, datum, stops_count, distance_km, etc.
    
    Returns:
        Text-String für Embedding
    """
    tour_id = tour_metadata.get("tour_id", "Unbekannt")
    datum = tour_metadata.get("datum", "")
    stops_count = tour_metadata.get("stops_count", 0)
    distance_km = tour_metadata.get("distance_km", 0.0)
    total_time_min = tour_metadata.get("total_time_min", 0)
    sector = tour_metadata.get("sector", "")
    tour_type = tour_metadata.get("tour_type", "")
    
    # Erstelle beschreibenden Text
    parts = [f"Tour {tour_id}"]
    
    if datum:
        parts.append(f"am {datum}")
    
    if stops_count > 0:
        parts.append(f"{stops_count} Stops")
    
    if distance_km > 0:
        parts.append(f"{distance_km:.1f} km")
    
    if total_time_min > 0:
        parts.append(f"{total_time_min} Minuten")
    
    if sector:
        parts.append(f"{sector}-Sektor")
    
    if tour_type:
        parts.append(f"Typ {tour_type}")
    
    return ", ".join(parts)


def create_tour_embedding(tour_metadata: Dict[str, Any]) -> Optional[List[float]]:
    """
    Erstellt ein Embedding aus Tour-Metadaten.
    
    Args:
        tour_metadata: Dict mit tour_id, datum, stops_count, distance_km, etc.
    
    Returns:
        Embedding-Vektor (Liste von Floats) oder None bei Fehler
    """
    # Erstelle Text aus Metadaten
    text = create_tour_text(tour_metadata)
    
    # Versuche OpenAI-Embeddings
    client = get_openai_client()
    if client is not None:
        try:
            response = client.embeddings.create(
                model="text-embedding-3-small",  # Günstiges Modell
                input=text
            )
            
            embedding = response.data[0].embedding
            logger.debug(f"OpenAI-Embedding erstellt für Tour {tour_metadata.get('tour_id')}")
            return embedding
            
        except Exception as e:
            logger.warning(f"Fehler bei OpenAI-Embedding: {e}, verwende Fallback")
    
    # Fallback: Einfaches Feature-Vector (normalisiert)
    # Konvertiere Metadaten zu numerischem Vektor
    try:
        # Normalisierte Features (für einfache Similarity)
        features = [
            float(tour_metadata.get("stops_count", 0)) / 50.0,  # Normalisiert auf 0-1 (max 50 Stops)
            float(tour_metadata.get("distance_km", 0.0)) / 100.0,  # Normalisiert auf 0-1 (max 100 km)
            float(tour_metadata.get("total_time_min", 0)) / 120.0,  # Normalisiert auf 0-1 (max 120 min)
        ]
        
        # Sektor-Encoding (one-hot-ähnlich)
        sector = tour_metadata.get("sector", "").upper()
        sector_features = [
            1.0 if sector == "N" else 0.0,
            1.0 if sector == "O" else 0.0,
            1.0 if sector == "S" else 0.0,
            1.0 if sector == "W" else 0.0,
        ]
        
        # Tour-Typ-Encoding
        tour_type = tour_metadata.get("tour_type", "").upper()
        type_features = [
            1.0 if "W" in tour_type else 0.0,
            1.0 if "PIR" in tour_type else 0.0,
            1.0 if "T" in tour_type else 0.0,
        ]
        
        # Kombiniere alle Features
        embedding = features + sector_features + type_features
        
        logger.debug(f"Fallback-Embedding erstellt für Tour {tour_metadata.get('tour_id')} (10 Features)")
        return embedding
        
    except Exception as e:
        logger.error(f"Fehler beim Erstellen des Fallback-Embeddings: {e}", exc_info=True)
        return None


def embed_and_store_tour(
    tour_id: str,
    datum: str,
    tour_metadata: Dict[str, Any]
) -> bool:
    """
    Erstellt Embedding und speichert es in ChromaDB.
    
    Args:
        tour_id: Tour-Identifikator
        datum: Tour-Datum (YYYY-MM-DD)
        tour_metadata: Dict mit stops_count, distance_km, total_time_min, etc.
    
    Returns:
        True wenn erfolgreich, False bei Fehler
    """
    from backend.services.vector_db import add_tour_embedding
    
    # Erstelle Embedding
    embedding = create_tour_embedding(tour_metadata)
    if embedding is None:
        logger.warning(f"Konnte kein Embedding für Tour {tour_id} erstellen")
        return False
    
    # Füge Text zur Metadaten hinzu
    tour_metadata["text"] = create_tour_text(tour_metadata)
    
    # Speichere in ChromaDB
    success = add_tour_embedding(
        tour_id=tour_id,
        datum=datum,
        embedding=embedding,
        metadata=tour_metadata
    )
    
    if success:
        logger.info(f"Tour-Embedding gespeichert: {tour_id} ({datum})")
    else:
        logger.warning(f"Tour-Embedding konnte nicht gespeichert werden: {tour_id} ({datum})")
    
    return success

