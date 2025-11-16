from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pathlib import Path
import pandas as pd
import io
import re
import unicodedata
import os
import asyncio
from ingest.reader import read_tourplan
from repositories.geo_repo import bulk_get
from repositories.geo_alias_repo import resolve_aliases
import unicodedata
import re
from common.normalize import normalize_address

# def _norm(s: str) -> str:
#     """Normalisiert Adressen: Unicode NFC + Whitespace-Bereinigung (wie Bulk-Process)."""
#     s = unicodedata.normalize("NFC", (s or ""))
#     s = re.sub(r"\s+", " ", s).strip()
#     return s
from repositories.manual_repo import is_open as manual_is_open
from services.geocode_fill import fill_missing
from ingest.guards import BAD_MARKERS
from services.stop_dto import build_stop_dto

router = APIRouter()

# Geocoding-Erzwingung Konfiguration
ENFORCE = os.getenv("GEOCODE_ENFORCE", "1") not in ("0","false","False")
BATCH_LIMIT = int(os.getenv("GEOCODE_BATCH_LIMIT", "25"))

# Pydantic-Model für POST-Request
class MatchIn(BaseModel):
    stored_path: str

# Heuristik zur Erkennung der Adressspalte
def _addr_col(df: pd.DataFrame) -> tuple[int, int]:
    """Erkennt die Adressspalte und Header-Offset."""
    header = df.iloc[0].astype(str).str.lower().tolist()
    if any("adresse" in h for h in header):
        return next(i for i,h in enumerate(header) if "adresse" in h), 1
    return (2 if df.shape[1] > 2 else df.shape[1]-1), 0

@router.get("/api/tourplan/match")
async def api_tourplan_match(file: str = Query(..., min_length=3, description="Pfad zur CSV-Datei (absolut oder relativ)")):
    """
    Matcht Adressen aus einem Tourplan gegen die geo_cache Datenbank (GET-Variante).
    
    - Verwendet modernen Tourplan-Parser für vollständige Adressen
    - Normalisiert Adressen mit PLZ und Stadt
    - Führt bulk_get gegen geo_cache aus
    - Gibt Status je Zeile zurück (ok/warn/bad)
    
    Unterstützt:
    - Absolute Pfade (z.B. E:\...\data\staging\...)
    - Relative Pfade unter ./Tourplaene/
    """
    try:
        return await do_match(file)
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"[MATCH ERROR] Unerwarteter Fehler für Datei '{file}': {e}")
        print(f"[MATCH ERROR] Traceback:\n{error_details}")
        error_msg = f"Match-Fehler für '{file}': {str(e)}"
        raise HTTPException(500, detail=error_msg)

@router.post("/api/tourplan/match")
async def api_tourplan_match_post(body: MatchIn):
    """
    Matcht Adressen aus einem Tourplan gegen die geo_cache Datenbank (POST-Variante).
    
    Robuster gegen URL-Encoding-Probleme, da der Pfad im JSON-Body übergeben wird.
    
    Request Body:
    {
        "stored_path": "E:\\...\\data\\staging\\file.csv"
    }
    """
    if not body.stored_path:
        raise HTTPException(422, detail='stored_path fehlt')
    
    if len(body.stored_path) < 3:
        raise HTTPException(422, detail='stored_path zu kurz (min. 3 Zeichen)')
    
    try:
        return await do_match(body.stored_path)
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"[MATCH ERROR] Unerwarteter Fehler für Datei '{body.stored_path}': {e}")
        print(f"[MATCH ERROR] Traceback:\n{error_details}")
        error_msg = f"Match-Fehler für '{body.stored_path}': {str(e)}"
        raise HTTPException(500, detail=error_msg)


def _fallback_customers_from_csv(path: Path) -> list[dict]:
    """Einfacher CSV-Fallback, falls der Tourplan-Parser keine Kunden liefert."""

    try:
        df = pd.read_csv(path, sep=";", dtype=str, keep_default_na=False, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(path, sep=";", dtype=str, keep_default_na=False, encoding="latin-1")

    def _slug(col: str) -> str:
        normalized = unicodedata.normalize("NFKD", col or "").encode("ascii", "ignore").decode("ascii")
        return re.sub(r"[^a-z0-9]", "", normalized.lower())

    slug_map = {_slug(col): col for col in df.columns}

    def _pick(*candidates: str) -> str | None:
        for cand in candidates:
            if cand in slug_map:
                return slug_map[cand]
        return None

    col_name = _pick("kunde", "name", "customer")
    col_street = _pick("strasse", "str", "adresse", "address")
    col_plz = _pick("plz", "postleitzahl", "zip")
    col_city = _pick("stadt", "ort", "city")

    customers: list[dict] = []
    for _, row in df.iterrows():
        name = row.get(col_name, "").strip() if col_name else ""
        street = row.get(col_street, "").strip() if col_street else ""
        postal_code = row.get(col_plz, "").strip() if col_plz else ""
        city = row.get(col_city, "").strip() if col_city else ""

        if not any([name, street, postal_code, city]):
            continue

        raw_address = ", ".join(filter(None, [street, f"{postal_code} {city}".strip()]))
        customers.append(
            {
                "name": name,
                "street": street,
                "postal_code": postal_code,
                "city": city,
                "address": normalize_address(raw_address, name, postal_code),
            }
        )

    return customers

# Gemeinsame Match-Logik (wird von GET und POST verwendet)
async def do_match(file_path: str):
    """
    Führt die Match-Logik für eine CSV-Datei aus.
    
    Args:
        file_path: Pfad zur CSV-Datei (absolut oder relativ)
        
    Returns:
        JSONResponse mit Match-Ergebnissen
    """
    # Pfad-Normalisierung: Unterstütze sowohl absolute als auch relative Pfade
    # WICHTIG: URL-kodierte Pfade dekodieren (Windows-Backslashes)
    import urllib.parse
    
    # Debug: Logge den originalen Parameter
    print(f"[MATCH DEBUG] Original file parameter: {file_path}")
    
    decoded_file = urllib.parse.unquote(file_path)
    print(f"[MATCH DEBUG] Decoded file: {decoded_file}")
    
    # Windows-Pfad: Pathlib sollte Backslashes korrekt handhaben, aber prüfe explizit
    # Verwende direkt den dekodierten Pfad - Pathlib unter Windows unterstützt beide Formate
    p = Path(decoded_file)
    print(f"[MATCH DEBUG] Path object: {p}")
    
    # Wenn relativer Pfad, versuche unter Tourplaene/
    if not p.is_absolute():
        from config.static.app_config import paths
        tourplaene_dir = Path(paths.get("original_csvs", "./Tourplaene"))
        p = tourplaene_dir / decoded_file
    
    # Prüfe ob Datei existiert - verwende os.path.exists() für Windows-Kompatibilität
    file_path_str = str(p)
    
    # WICHTIG: Stelle sicher, dass der Pfad absolut und normalisiert ist
    p = p.resolve()
    file_path_str = str(p)
    
    # Debug: Logge alle Pfad-Varianten
    print(f"[MATCH DEBUG] Prüfe Pfad: {file_path_str}")
    print(f"[MATCH DEBUG] os.path.exists: {os.path.exists(file_path_str)}")
    print(f"[MATCH DEBUG] Path.exists: {p.exists()}")
    
    if not os.path.exists(file_path_str) and not p.exists():
        # Fallback: Versuche verschiedene Pfad-Formate
        test_paths = [
            decoded_file,  # Original dekodierter Pfad
            Path(decoded_file).resolve(),  # Resolved Path
            Path(decoded_file).absolute(),  # Absolute Path
        ]
        existing_path = None
        for test_path in test_paths:
            test_p = Path(test_path) if not isinstance(test_path, Path) else test_path
            test_str = str(test_p.resolve())
            print(f"[MATCH DEBUG] Teste: {test_str} -> {os.path.exists(test_str)}")
            if os.path.exists(test_str) or test_p.exists():
                existing_path = test_str
                p = test_p.resolve()
                print(f"[MATCH DEBUG] Pfad gefunden: {test_str}")
                break
        
        if not existing_path:
            # Letzter Versuch: Suche nach Dateinamen im staging-Verzeichnis
            from config.static.app_config import paths
            staging_dir = Path(paths.get("staging_dir", "./data/staging")).resolve()
            filename_only = p.name
            staging_file = staging_dir / filename_only
            if staging_file.exists():
                p = staging_file.resolve()
                print(f"[MATCH DEBUG] Datei im Staging-Verzeichnis gefunden: {p}")
            else:
                raise HTTPException(404, detail=f"Datei nicht gefunden: {file_path_str} (original: {file_path}, decoded: {decoded_file}, filename: {filename_only})")

    # 1) CSV mit modernem Parser lesen (vollständige Adressen mit PLZ und Stadt)
    from backend.parsers.tour_plan_parser import parse_tour_plan_to_dict
    try:
        tour_data = parse_tour_plan_to_dict(str(p))
    except ValueError as ve:
        # Mojibake-Encoding-Fehler: Versuche Datei zu reparieren
        if "ENCODING-BUG" in str(ve) or "Mojibake" in str(ve):
            print(f"[MATCH WARNING] Mojibake erkannt für {p}, versuche Reparatur...")
            from common.text_cleaner import repair_cp_mojibake
            # Datei neu lesen und reparieren
            try:
                raw_content = p.read_bytes()
                # Versuche verschiedene Encodings
                for enc in ("cp850", "utf-8-sig", "latin-1"):
                    try:
                        decoded = raw_content.decode(enc)
                        repaired = repair_cp_mojibake(decoded)
                        # Reparierte Version temporär speichern
                        temp_path = p.with_suffix('.csv.repaired')
                        temp_path.write_text(repaired, encoding='utf-8')
                        # Versuche erneut mit reparierter Datei
                        tour_data = parse_tour_plan_to_dict(str(temp_path))
                        temp_path.unlink()  # Temporäre Datei löschen
                        print(f"[MATCH] Datei erfolgreich repariert und geparst")
                        break
                    except Exception:
                        continue
                else:
                    # Alle Versuche fehlgeschlagen - Fallback
                    raise ValueError(f"Mojibake-Reparatur fehlgeschlagen: {ve}")
            except Exception as repair_error:
                print(f"[MATCH ERROR] Reparatur fehlgeschlagen: {repair_error}")
                import traceback
                traceback.print_exc()
                # Fallback: Versuche einfaches CSV-Parsing
                try:
                    tour_data = {"customers": _fallback_customers_from_csv(p)}
                except Exception as fallback_error:
                    print(f"[MATCH ERROR] Fallback-Parsing fehlgeschlagen: {fallback_error}")
                    raise HTTPException(500, detail=f"Datei konnte nicht geparst werden: {str(repair_error)}")
        else:
            # Anderer ValueError - keine Mojibake-Reparatur möglich
            import traceback
            error_trace = traceback.format_exc()
            print(f"[MATCH ERROR] ValueError (nicht Mojibake): {ve}\n{error_trace}")
            raise HTTPException(500, detail=f"Parser-Fehler: {str(ve)}")
    except Exception as parse_error:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[MATCH ERROR] Parse-Fehler: {parse_error}\n{error_trace}")
        # Fallback: Versuche einfaches CSV-Parsing
        try:
            tour_data = {"customers": _fallback_customers_from_csv(p)}
        except Exception as fallback_error:
            print(f"[MATCH ERROR] Fallback-Parsing fehlgeschlagen: {fallback_error}")
            raise HTTPException(500, detail=f"Datei konnte nicht geparst werden: {str(parse_error)}")
    
    if not tour_data.get("customers"):
        raise HTTPException(404, detail=f"Keine Kunden in Datei gefunden: {file_path_str}")
    
    # 2) Vollständige Adressen zusammenbauen
    addrs = []
    for customer in tour_data["customers"]:
        # Verwende die bereits normalisierte Adresse aus dem Parser
        if 'address' in customer and customer['address']:
            full_address = customer['address']
        else:
            # Fallback: Vollständige Adresse zusammenbauen: Straße, PLZ Stadt
            full_address = f"{customer['street']}, {customer['postal_code']} {customer['city']}"
        
        # KRITISCH: Synonym-Check VOR Normalisierung
        customer_name = customer.get('name', '')
        synonym_hit = None
        if customer_name:
            from common.synonyms import resolve_synonym
            synonym_hit = resolve_synonym(customer_name)
        
        if synonym_hit:
            # Synonym gefunden - verwende die Synonym-Adresse
            addrs.append(synonym_hit.resolved_address)
        else:
            # Normale Normalisierung
            addrs.append(normalize_address(full_address, customer.get('name', ''), customer.get('postal_code', '')))

    # 3) Alias-Auflösung und DB-Lookup (bulk)
    aliases = resolve_aliases(addrs)  # map: query_norm -> canonical_norm
    geo = bulk_get(addrs + list(aliases.values()))  # beide Mengen laden
    
    # 4) Geocoding-Erzwingung (wenn aktiviert)
    if ENFORCE:
        missing = [i for i, addr in enumerate(addrs) if not geo.get(addr) and not geo.get(aliases.get(addr, ""))]
        if missing:
            print(f"[MATCH] Erzwinge Geocoding für {len(missing)} fehlende Adressen...")
            missing_addrs = [addrs[i] for i in missing]
            filled = await fill_missing(missing_addrs, limit=BATCH_LIMIT)
            for addr, rec in filled.items():
                geo[addr] = rec

    # 5) Status-Bewertung und Output
    out = []
    for i, customer in enumerate(tour_data["customers"]):
        if 'address' in customer and customer['address']:
            full_address = customer['address']
        else:
            full_address = f"{customer['street']}, {customer['postal_code']} {customer['city']}"
        
        customer_name = customer.get('name', '')
        synonym_hit = None
        if customer_name:
            from common.synonyms import resolve_synonym
            synonym_hit = resolve_synonym(customer_name)
        
        if synonym_hit:
            # Synonym gefunden - verwende Synonym-Adresse und Koordinaten
            addr_norm = synonym_hit.resolved_address
            marks = []  # Synonyme haben keine Mojibake-Marker
            rec = {
                'lat': synonym_hit.lat,
                'lon': synonym_hit.lon,
                '_note': 'synonym',
                'address': {'road': synonym_hit.resolved_address}
            }
            has_geo = True
            status = "ok"
        else:
            # Normale Verarbeitung
            addr_norm = normalize_address(full_address, customer.get('name', ''), customer.get('postal_code', ''))
            marks = [m for m in BAD_MARKERS if m in addr_norm]
            
            # Alias-Auflösung
            canon = aliases.get(addr_norm)
            rec = geo.get(addr_norm) or (geo.get(canon) if canon else None)
            
            # KRITISCHE VALIDIERUNG: Nur gültige Adressen mit deutschen Koordinaten akzeptieren
            has_geo = False
            if rec is not None:
                # Prüfe ob Adresse nicht leer ist
                if full_address and full_address.strip() and full_address != "nan, nan nan":
                    # Prüfe ob Koordinaten in Deutschland liegen (grobe Bounding Box)
                    lat, lon = rec.get('lat', 0), rec.get('lon', 0)
                    if lat and lon and 47.0 <= lat <= 55.0 and 5.0 <= lon <= 15.0:
                        has_geo = True
            
            # Status-Logik:
            # ok: hat VALIDE Geo-Daten UND keine Mojibake-Marker UND gültige Adresse
            # warn: keine Geo-Daten ABER keine Mojibake-Marker  
            # bad: Mojibake-Marker vorhanden ODER ungültige Adresse
            if not full_address or not full_address.strip() or full_address == "nan, nan nan":
                status = "bad"  # Ungültige Adresse = immer bad
            elif has_geo:
                status = "ok" if not marks else "bad"
            else:
                status = "warn" if not marks else "bad"
        
        # Bestimme resolved_address und geo_source
        resolved_address = full_address
        geo_source = None
        if synonym_hit:
            resolved_address = synonym_hit.resolved_address
            geo_source = "synonym"
        elif rec:
            if rec.get('_note') == 'manual':
                geo_source = "manual"
            elif rec.get('_note') == 'geocoded':
                geo_source = "geocoded"
            else:
                geo_source = "cache"
        
        # Extra-Felder für DTO
        extra = {}
        if marks:
            extra['mojibake_markers'] = marks
        if synonym_hit:
            extra['synonym'] = synonym_hit.original_name
        
        # DTO mit build_stop_dto erstellen
        stop_dto = build_stop_dto(
            stop_id=str(i + 1),
            display_name=customer.get('name', ''),
            resolved_address=resolved_address,
            lat=rec.get('lat') if rec else None,
            lon=rec.get('lon') if rec else None,
            geo_source=geo_source,
            extra=extra
        )
        
        out.append(stop_dto)

    # Zusammenfassung
    body = {
        "file": str(p), 
        "rows": len(out), 
        "ok": sum(1 for r in out if r["status"]=="ok"), 
        "warn": sum(1 for r in out if r["status"]=="warn"), 
        "bad": sum(1 for r in out if r["status"]=="bad"), 
        "items": out
    }
    
    return JSONResponse(body, media_type="application/json; charset=utf-8")
