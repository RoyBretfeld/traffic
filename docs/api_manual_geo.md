# API-Dokumentation: Manuelle Koordinaten-Eingabe

## POST /api/tourplan/manual-geo

Speichert manuelle Koordinaten für eine Adresse in der geo_cache Tabelle.

### Request Body
```json
{
  "address": "Teststraße 123, 01234 Dresden",
  "latitude": 51.0504,
  "longitude": 13.7373,
  "by_user": "admin"
}
```

### Parameter
- **address** (string, required): Vollständige Adresse (min. 3 Zeichen)
- **latitude** (number, required): Breitengrad (-90 bis 90)
- **longitude** (number, required): Längengrad (-180 bis 180)  
- **by_user** (string, optional): Benutzer der die Koordinaten eingibt

### Response (200 OK)
```json
{
  "ok": true,
  "message": "Koordinaten für 'Teststraße 123, 01234 Dresden' gespeichert",
  "coordinates": {
    "lat": 51.0504,
    "lon": 13.7373
  }
}
```

### Response (400 Bad Request)
```json
{
  "detail": "Breitengrad muss zwischen -90 und 90 liegen"
}
```

### Response (500 Internal Server Error)
```json
{
  "detail": "Fehler beim Speichern der Koordinaten: [Fehlermeldung]"
}
```

### Verwendung
1. Adresse identifizieren, die keine Koordinaten hat
2. Koordinaten über Karten-Service (z.B. Google Maps) ermitteln
3. API-Aufruf mit korrekten Koordinaten
4. Koordinaten werden in geo_cache gespeichert mit `source="manual"`
5. Adresse wird bei nächster Tourplan-Analyse erkannt

### Beispiel (curl)
```bash
curl -X POST "http://127.0.0.1:8111/api/tourplan/manual-geo" \
  -H "Content-Type: application/json" \
  -d '{
    "address": "Musterstraße 42, 01067 Dresden",
    "latitude": 51.0504,
    "longitude": 13.7373,
    "by_user": "admin"
  }'
```

### Beispiel (Python)
```python
import requests

response = requests.post(
    "http://127.0.0.1:8111/api/tourplan/manual-geo",
    json={
        "address": "Musterstraße 42, 01067 Dresden",
        "latitude": 51.0504,
        "longitude": 13.7373,
        "by_user": "admin"
    }
)

if response.status_code == 200:
    print("Koordinaten erfolgreich gespeichert")
else:
    print(f"Fehler: {response.json()['detail']}")
```
