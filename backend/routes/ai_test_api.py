"""API für AI Test - Adress-Analyse mit LLM"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import tempfile
import pandas as pd
from typing import List, Dict, Any
import re

from ingest.http_responses import create_utf8_json_response
from repositories.geo_repo import has_ot_part, remove_ot_part
from common.normalize import normalize_address

router = APIRouter(prefix="/api/ai-test", tags=["ai-test"])


def normalize_city_with_adaptive_engine(city: str, postal_code: str = None) -> Dict[str, Any]:
    """
    Normalisiert Stadt mit Adaptive Pattern Engine (kostenlos, lernt automatisch)
    
    Ersetzt AI durch selbstlernende Regel-Engine:
    - Prüft gelernte Pattern (kostenlos)
    - Wendet Python-Regeln an (kostenlos)
    - Speichert neue Pattern für nächstes Mal (kostenlos)
    """
    try:
        from backend.services.adaptive_pattern_engine import get_pattern_engine
        engine = get_pattern_engine()
        
        # Verwende Pattern-Engine (kostenlos, lernt automatisch)
        normalized, pattern_type = engine.normalize_with_learning(city, {"postal_code": postal_code})
        
        return {
            "original": city,
            "normalized": normalized,
            "method": pattern_type
        }
    except ImportError:
        # Fallback auf bestehende Logik
        pass

def normalize_city_with_ai(city: str, postal_code: str = None) -> Dict[str, Any]:
    """
    Normalisiert Stadtnamen mit AI-Logik:
    - "Bannewitz, OT Posen" → "Bannewitz"
    - "Kreischer OT Wittgensdorf" → "Kreischer"
    - "Byrna / Bürkewitz" → "Byrna" (oder Hauptort basierend auf PLZ)
    
    Args:
        city: Original Stadtname
        postal_code: Postleitzahl (optional)
        
    Returns:
        Dict mit original, normalized, method
    """
    if not city:
        return {"original": city, "normalized": "", "method": "empty"}
    
    original = city.strip()
    
    # OT-Entfernung
    if has_ot_part(original):
        normalized = remove_ot_part(original).strip()
        # Komma am Ende entfernen falls vorhanden
        normalized = normalized.rstrip(',').strip()
        return {
            "original": original,
            "normalized": normalized,
            "method": "ot_removed"
        }
    
    # "/" Behandlung (z.B. "Byrna / Bürkewitz")
    if '/' in original:
        parts = [p.strip() for p in original.split('/')]
        # Ersten Teil nehmen (häufig der Hauptort)
        normalized = parts[0]
        return {
            "original": original,
            "normalized": normalized,
            "method": "slash_split"
        }
    
    # "-" Behandlung (z.B. "Bad Gottloiba - Berghübel")
    if ' - ' in original or ' -' in original or '- ' in original:
        parts = [p.strip() for p in re.split(r'\s*-\s*', original)]
        # Ersten Teil nehmen
        normalized = parts[0].strip()
        return {
            "original": original,
            "normalized": normalized,
            "method": "dash_split"
        }
    
    return {
        "original": original,
        "normalized": original,
        "method": "unchanged"
    }


def detect_bar_pairing(df: pd.DataFrame) -> Dict[int, Dict[str, Any]]:
    """
    Erkennt BAR-Kunden und paart sie mit normalen Touren.
    
    Sucht nach:
    - Spalte 5: "-07:00 URBAR" (BAR-Kunde)
    - Spalte 9: "7-07:00" (normale Tour)
    - Beide gehören zusammen (gleiche Zeit)
    
    Returns:
        Dict: row_index → {is_bar_customer: bool, bar_paired: bool, tour_time: str}
    """
    result = {}
    
    for idx, row in df.iterrows():
        info = {
            "is_bar_customer": False,
            "bar_paired": False,
            "tour_time": None
        }
        
        # Prüfe Spalte 5 (Index 4) für BAR-Kunden
        col5 = str(row.iloc[4]) if len(row) > 4 else ""
        if "URBAR" in col5.upper() or "BAR" in col5.upper():
            info["is_bar_customer"] = True
            # Zeit extrahieren
            time_match = re.search(r'(\d+)[:.]00', col5)
            if time_match:
                info["tour_time"] = time_match.group(1)
        
        # Prüfe Spalte 9 (Index 8) für normale Tour
        col9 = str(row.iloc[8]) if len(row) > 8 else ""
        if info["tour_time"] and info["tour_time"] in col9:
            info["bar_paired"] = True
        
        result[idx] = info
    
    return result


@router.post("/analyze")
async def analyze_csv_ai(file: UploadFile = File(...)) -> JSONResponse:
    """
    Analysiert CSV mit AI-Unterstützung:
    - Normalisiert OT-Adressen
    - Erkennt BAR-Paarungen
    - Identifiziert Orte basierend auf PLZ
    """
    try:
        print(f"[AI-TEST] Upload gestartet: {file.filename}")
        
        # Temporäre Datei
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        print(f"[AI-TEST] Datei gespeichert: {tmp_file_path}")
        
        try:
            # CSV lesen
            csv_path = Path(tmp_file_path)
            df = pd.read_csv(csv_path, sep=';', header=None, dtype=str, encoding='utf-8-sig')
            
            # Fallback für andere Encodings
            if df.empty:
                for encoding in ['cp850', 'latin-1', 'iso-8859-1']:
                    try:
                        df = pd.read_csv(csv_path, sep=';', header=None, dtype=str, encoding=encoding)
                        print(f"[AI-TEST] CSV mit {encoding} gelesen")
                        break
                    except:
                        continue
            
            print(f"[AI-TEST] CSV geparst: {len(df)} Zeilen, {len(df.columns)} Spalten")
            
            # BAR-Paarung erkennen
            bar_info = detect_bar_pairing(df)
            
            # Zeilen verarbeiten
            rows = []
            for idx, row in df.iterrows():
                if len(row) < 5:
                    continue
                
                # Spalten extrahieren (Typische Tourplan-Struktur)
                customer_id = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
                customer_name = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
                street = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ""
                postal_code = str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else ""
                city = str(row.iloc[4]).strip() if pd.notna(row.iloc[4]) else ""
                
                # Weitere Spalten (falls vorhanden)
                col5 = str(row.iloc[5]).strip() if len(row) > 5 and pd.notna(row.iloc[5]) else ""
                col6 = str(row.iloc[6]).strip() if len(row) > 6 and pd.notna(row.iloc[6]) else ""
                col7 = str(row.iloc[7]).strip() if len(row) > 7 and pd.notna(row.iloc[7]) else ""
                col8 = str(row.iloc[8]).strip() if len(row) > 8 and pd.notna(row.iloc[8]) else ""
                col9 = str(row.iloc[9]).strip() if len(row) > 9 and pd.notna(row.iloc[9]) else ""
                
                # Stadt normalisieren mit Adaptive Pattern Engine (kostenlos, lernt automatisch)
                city_norm = normalize_city_with_adaptive_engine(city, postal_code)
                
                # Adresse normalisieren
                normalized_address = normalize_address(f"{street}, {postal_code} {city_norm['normalized']}")
                
                # BAR-Info
                bar_data = bar_info.get(idx, {})
                
                row_data = {
                    "row": idx + 1,
                    "customer_id": customer_id,
                    "customer_name": customer_name,
                    "street": street,
                    "postal_code": postal_code,
                    "original_city": city,
                    "normalized_city": city_norm['normalized'],
                    "normalization_method": city_norm['method'],
                    "normalized_address": normalized_address,
                    "col5": col5,
                    "col6": col6,
                    "col7": col7,
                    "col8": col8,
                    "col9": col9,
                    "is_bar_customer": bar_data.get("is_bar_customer", False),
                    "bar_paired": bar_data.get("bar_paired", False),
                    "tour_time": bar_data.get("tour_time"),
                }
                
                rows.append(row_data)
            
            # Header für Tabelle
            headers = [
                "Zeile", "Kdnr", "Name", "Straße", "PLZ", "Ort (Original)", "Ort (Normalisiert)", 
                "Normalisierung", "Adresse (Normalisiert)", "Spalte 5", "Spalte 6", "Spalte 7", 
                "Spalte 8", "Spalte 9", "BAR", "BAR gepaart", "Tour Zeit"
            ]
            
            result = {
                "success": True,
                "file_name": file.filename,
                "total_rows": len(rows),
                "headers": headers,
                "rows": rows,
                "summary": {
                    "bar_customers": sum(1 for r in rows if r["is_bar_customer"]),
                    "bar_paired": sum(1 for r in rows if r["bar_paired"]),
                    "ot_normalized": sum(1 for r in rows if r["normalization_method"] != "unchanged"),
                }
            }
            
            print(f"[AI-TEST] Verarbeitet: {len(rows)} Zeilen, {result['summary']['bar_customers']} BAR-Kunden")
            return create_utf8_json_response(result)
            
        finally:
            try:
                import os
                os.unlink(tmp_file_path)
            except:
                pass
                
    except Exception as e:
        import traceback
        error_msg = str(e)
        error_trace = traceback.format_exc()
        print(f"[AI-TEST ERROR] {error_msg}\n{error_trace}")
        
        return create_utf8_json_response({
            "success": False,
            "error": error_msg
        }, status_code=500)

