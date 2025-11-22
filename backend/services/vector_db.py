"""
Chroma-Vektordatenbank-Integration für Tour-Embeddings.
Speichert Tour-Metadaten als Embeddings für KI-Learning.
"""
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# ChromaDB wird lazy importiert (nur wenn benötigt)
_chroma_client = None
_chroma_collection = None


def get_chroma_client():
    """
    Gibt den ChromaDB-Client zurück (lazy initialization).
    
    Returns:
        chromadb.Client oder None wenn ChromaDB nicht verfügbar ist
    """
    global _chroma_client
    
    if _chroma_client is not None:
        return _chroma_client
    
    try:
        import chromadb
        from chromadb.config import Settings
        
        # ChromaDB-Pfad aus Umgebungsvariable oder Standard
        chroma_path = os.getenv("CHROMA_DB_PATH", "./data/chroma_db")
        chroma_path_obj = Path(chroma_path)
        chroma_path_obj.mkdir(parents=True, exist_ok=True)
        
        # Persistent Client erstellen
        _chroma_client = chromadb.PersistentClient(
            path=str(chroma_path_obj),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        logger.info(f"ChromaDB-Client initialisiert: {chroma_path}")
        return _chroma_client
        
    except ImportError:
        logger.warning("ChromaDB nicht installiert. Installiere mit: pip install chromadb")
        return None
    except Exception as e:
        logger.error(f"Fehler beim Initialisieren von ChromaDB: {e}", exc_info=True)
        return None


def get_tours_collection():
    """
    Gibt die ChromaDB-Collection für Touren zurück.
    
    Returns:
        chromadb.Collection oder None wenn ChromaDB nicht verfügbar ist
    """
    global _chroma_collection
    
    if _chroma_collection is not None:
        return _chroma_collection
    
    client = get_chroma_client()
    if client is None:
        return None
    
    try:
        # Collection erstellen oder abrufen
        collection_name = "tours"
        _chroma_collection = client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Tour-Embeddings für KI-Learning"}
        )
        
        logger.info(f"ChromaDB-Collection '{collection_name}' bereit")
        return _chroma_collection
        
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der ChromaDB-Collection: {e}", exc_info=True)
        return None


def add_tour_embedding(
    tour_id: str,
    datum: str,
    embedding: List[float],
    metadata: Dict[str, Any]
) -> bool:
    """
    Fügt ein Tour-Embedding zur ChromaDB hinzu.
    
    Args:
        tour_id: Tour-Identifikator
        datum: Tour-Datum (YYYY-MM-DD)
        embedding: Embedding-Vektor (Liste von Floats)
        metadata: Metadaten (tour_id, datum, stops_count, distance_km, etc.)
    
    Returns:
        True wenn erfolgreich, False bei Fehler
    """
    collection = get_tours_collection()
    if collection is None:
        logger.warning("ChromaDB-Collection nicht verfügbar - Embedding nicht gespeichert")
        return False
    
    try:
        # Eindeutige ID: tour_id + datum
        doc_id = f"{tour_id}_{datum}"
        
        # Text für Embedding (wird für Similarity-Search verwendet)
        text = metadata.get("text", f"Tour {tour_id} am {datum}")
        
        # Metadaten vorbereiten (nur skalare Werte, keine Listen)
        clean_metadata = {
            "tour_id": str(tour_id),
            "datum": str(datum),
            "stops_count": int(metadata.get("stops_count", 0)),
            "distance_km": float(metadata.get("distance_km", 0.0)),
            "total_time_min": int(metadata.get("total_time_min", 0)),
            "sector": str(metadata.get("sector", "")) if metadata.get("sector") else "",
            "tour_type": str(metadata.get("tour_type", "")) if metadata.get("tour_type") else "",
        }
        
        # Embedding hinzufügen (upsert: aktualisiert falls bereits vorhanden)
        collection.upsert(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[clean_metadata]
        )
        
        logger.debug(f"Tour-Embedding gespeichert: {doc_id}")
        return True
        
    except Exception as e:
        logger.error(f"Fehler beim Speichern des Tour-Embeddings: {e}", exc_info=True)
        return False


def search_similar_tours(
    query_embedding: List[float],
    n_results: int = 5,
    filter_metadata: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Sucht ähnliche Touren basierend auf Embedding.
    
    Args:
        query_embedding: Query-Embedding-Vektor
        n_results: Anzahl der Ergebnisse
        filter_metadata: Optional: Filter-Metadaten (z.B. {"tour_type": "W"})
    
    Returns:
        Liste von ähnlichen Touren mit Metadaten
    """
    collection = get_tours_collection()
    if collection is None:
        logger.warning("ChromaDB-Collection nicht verfügbar - Suche nicht möglich")
        return []
    
    try:
        # ChromaDB where-Filter vorbereiten
        where_filter = None
        if filter_metadata:
            where_filter = {}
            for key, value in filter_metadata.items():
                where_filter[key] = value
        
        # Suche durchführen
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter
        )
        
        # Ergebnisse formatieren
        similar_tours = []
        if results["ids"] and len(results["ids"]) > 0:
            for i in range(len(results["ids"][0])):
                similar_tours.append({
                    "tour_id": results["metadatas"][0][i].get("tour_id", ""),
                    "datum": results["metadatas"][0][i].get("datum", ""),
                    "distance": results["distances"][0][i] if results.get("distances") else None,
                    "metadata": results["metadatas"][0][i]
                })
        
        return similar_tours
        
    except Exception as e:
        logger.error(f"Fehler bei der Similarity-Suche: {e}", exc_info=True)
        return []


def get_collection_stats() -> Dict[str, Any]:
    """
    Gibt Statistiken über die ChromaDB-Collection zurück.
    
    Returns:
        Dict mit count, collection_name, etc.
    """
    collection = get_tours_collection()
    if collection is None:
        return {
            "available": False,
            "count": 0,
            "error": "ChromaDB nicht verfügbar"
        }
    
    try:
        # Zähle Dokumente (peek mit großem Limit)
        peek_result = collection.peek(limit=10000)
        count = len(peek_result["ids"]) if peek_result.get("ids") else 0
        
        return {
            "available": True,
            "count": count,
            "collection_name": collection.name
        }
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Collection-Statistiken: {e}", exc_info=True)
        return {
            "available": False,
            "count": 0,
            "error": str(e)
        }

