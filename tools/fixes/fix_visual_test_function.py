#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Repariert die tourplan_visual_test Funktion mit echter Datenbank-Suche
"""

def fix_tourplan_visual_test():
    """Repariert die tourplan_visual_test Funktion"""
    
    # Lese die aktuelle Datei
    with open('backend/app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Finde die tourplan_visual_test Funktion
    start_marker = 'async def tourplan_visual_test(file: UploadFile = File(...)) -> JSONResponse:'
    end_marker = '@app.get("/ui/tourplan-visual-test"'
    
    start_pos = content.find(start_marker)
    end_pos = content.find(end_marker)
    
    if start_pos == -1 or end_pos == -1:
        print("ERROR: tourplan_visual_test Funktion nicht gefunden")
        return False
    
    # Extrahiere den aktuellen Funktionsinhalt
    function_content = content[start_pos:end_pos]
    
    # Erstelle die neue Funktion
    new_function = '''async def tourplan_visual_test(file: UploadFile = File(...)) -> JSONResponse:
    """Lädt eine CSV-Datei hoch und testet die Mojibake-Reparatur visuell."""
    try:
        # Datei temporär speichern
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # CSV mit gehärteter Funktion lesen
            csv_path = Path(tmp_file_path)
            df = read_tourplan_csv(csv_path)
            
            addresses = []
            total_rows = len(df)
            
            # Adressen extrahieren und validieren
            for idx, row in df.iterrows():
                if len(row) >= 5:
                    # Korrekte Spalten-Indizes für Tourplan-CSV
                    # Spalte 0: Kdnr, Spalte 1: Name, Spalte 2: Straße, Spalte 3: PLZ, Spalte 4: Ort
                    customer_id = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
                    customer_name = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
                    street = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ""
                    postal_code = str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else ""
                    city = str(row.iloc[4]).strip() if pd.notna(row.iloc[4]) else ""
                    
                    # Nur verarbeiten wenn alle wichtigen Felder vorhanden sind
                    if customer_id and customer_name and street and city and street != 'nan' and city != 'nan':
                        # Adresse zusammenstellen
                        full_address = f"{street}, {postal_code} {city}".strip()
                        
                        # ECHTE DATENBANK-SUCHE
                        kunde_id = get_kunde_id_by_name_adresse(customer_name, street, city)
                        recognized = kunde_id is not None
                        coordinates = None
                        
                        if recognized:
                            # Lade Kunde-Details mit Koordinaten
                            kunde = get_kunde_by_id(kunde_id)
                            if kunde and 'latitude' in kunde and 'longitude' in kunde:
                                coordinates = {
                                    "lat": float(kunde['latitude']),
                                    "lon": float(kunde['longitude'])
                                }
                        
                        addresses.append({
                            "customer_id": customer_id,
                            "street": street,
                            "postal_code": postal_code,
                            "city": city,
                            "customer_name": customer_name,
                            "full_address": full_address,
                            "recognized": recognized,
                            "coordinates": coordinates,
                            "row": idx + 1
                        })
            
            # UTF-8 JSON Response mit zentraler Konfiguration
            from ingest.http_responses import create_utf8_json_response
            
            # Berechne echte Statistiken
            recognized_count = sum(1 for addr in addresses if addr["recognized"])
            with_coords_count = sum(1 for addr in addresses if addr["coordinates"])
            
            return create_utf8_json_response({
                "success": True,
                "file_name": file.filename,
                "total_rows": total_rows,
                "addresses": addresses,
                "summary": {
                    "total_addresses": len(addresses),
                    "recognized": recognized_count,
                    "unrecognized": len(addresses) - recognized_count,
                    "with_coordinates": with_coords_count
                }
            })
            
        finally:
            # Temporäre Datei löschen
            try:
                os.unlink(tmp_file_path)
            except:
                pass
                
    except Exception as e:
        # Unicode-sichere Fehlerbehandlung
        error_msg = str(e).encode('ascii', errors='replace').decode('ascii')
        print(f"[ERROR] Upload failed: {error_msg}")
        raise HTTPException(status_code=500, detail=f"Fehler beim Verarbeiten der CSV-Datei: {error_msg}")

'''
    
    # Ersetze die Funktion
    new_content = content[:start_pos] + new_function + content[end_pos:]
    
    # Schreibe die neue Datei
    with open('backend/app.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("SUCCESS: tourplan_visual_test Funktion repariert!")
    return True

if __name__ == "__main__":
    fix_tourplan_visual_test()
