# docs/RUNBOOK_ROUTING.md
# Routing Runbook für FAMO TrafficApp

Dieses Dokument beschreibt die Routing-Architektur, Start-/Stopp-Prozeduren, Fehlerbehebung und wichtige Konfigurationsdetails für den OSRM-Dienst.

## 1. Architektur Überblick

Die FAMO TrafficApp nutzt eine mehrstufige Routing-Logik:

1.  **OSRM-Client (`services/osrm_client.py`)**: Primärer Routing-Dienst (Standard: `http://localhost:5011` oder konfigurierte `OSRM_BASE_URL`). Dieser Client implementiert:
    *   **Timeouts & Retries**: Für robuste Anfragen.
    *   **Circuit Breaker**: (`backend/utils/circuit_breaker.py`) Schützt vor überlasteten oder ausgefallenen OSRM-Servern. Bei Fehlern wechselt der Zustand von `CLOSED` zu `OPEN`, blockiert weitere Anfragen für eine bestimmte Zeit und versucht dann, sich im `HALF_OPEN`-Zustand zu erholen.
    *   **Rate Limiting**: (`backend/utils/rate_limit.py`) Verhindert eine Überlastung des OSRM-Dienstes durch zu viele Anfragen.
    *   **Cache**: (`backend/cache/osrm_cache.py`) Speichert Routing-Ergebnisse in der SQLite-Datenbank, um wiederkehrende Anfragen zu beschleunigen und die OSRM-Last zu reduzieren.

2.  **Real Routing Service (`backend/services/real_routing.py`)**: Kapselt die Logik für die Routenberechnung. Versucht zuerst den OSRM-Client. Bei Fehlern (z.B. OSRM nicht erreichbar, Circuit Breaker OPEN, Quota-Fehler) fällt es auf eine Haversine-Berechnung zurück. Bei weniger als zwei gültigen Stopps wird ein `400 Bad Request` zurückgegeben, bei unerwarteten Fehlern ein `500 Internal Server Error`.

3.  **Fehlerbehandlung (`backend/core/error_handlers.py`)**: Eine globale Middleware (`RequestIdMiddleware`) versieht jede Anfrage mit einer `x-request-id` und loggt die Anfragedauer. Die `http_exception_handler` Funktion fängt alle `HTTPException`s ab und gibt eine standardisierte JSON-Fehlermeldung zurück. Spezifische OSRM-Fehler (z.B. `402 Payment Required`) werden intern in `QuotaError` oder `TransientError` umgewandelt und von der globalen Fehlerbehandlung zu entsprechenden HTTP-Statuscodes (z.B. `429 Too Many Requests`, `503 Service Unavailable`) gemappt.

## 2. OSRM Dienst bereitstellen (Port 5011)

Der OSRM-Dienst läuft idealerweise in einem separaten Docker-Container, um Isolation und einfache Bereitstellung zu gewährleisten. Der Standard-Port im Backend ist **5011** (anstelle des OSRM-Standard-Ports 5000, um Konflikte zu vermeiden).

### A) Docker (empfohlen)

Navigieren Sie zum Verzeichnis `deploy/osrm/`:

```bash
cd deploy/osrm/
```

1.  **OSM PBF-Datei vorbereiten**: Laden Sie eine `.osm.pbf`-Datei für Ihre gewünschte Region herunter (z.B. von [Geofabrik](https://download.geofabrik.de/)). Legen Sie diese Datei im `deploy/osrm/data/` Ordner ab und benennen Sie sie in `region.osrm.osm.pbf` um (oder passen Sie den `command` in `docker-compose.yml` entsprechend an).
    *Beispiel: `deploy/osrm/data/germany-latest.osm.pbf` umbenennen in `region.osrm.osm.pbf`.*

2.  **OSRM Container starten**: Führen Sie den Docker Compose Befehl aus. Dieser Befehl baut das Image, extrahiert die Daten, partitioniert und customized sie und startet den OSRM-Routing-Dienst.

```bash
docker-compose up -d --build
```

Der OSRM-Dienst wird nun auf `http://localhost:5011` verfügbar sein.

### B) Nativ (manuelle Installation)

Falls Sie Docker nicht verwenden möchten, können Sie OSRM auch nativ installieren. Dies ist komplexer und hängt stark von Ihrem Betriebssystem ab. Details finden Sie in der [OSRM-Dokumentation](https://project-osrm.org/docs/)

## 3. Start/Stopp der FAMO TrafficApp

Stellen Sie sicher, dass der OSRM-Dienst läuft, bevor Sie die TrafficApp starten.

### Starten

```bash
python start_server.py
```

### Stoppen

Drücken Sie `Ctrl+C` in der Konsole, in der der Server läuft.

## 4. Fehlerbehebung & Monitoring

### API Endpunkte

*   **`GET /health/live`**: Schneller Liveness-Check der FastAPI-Anwendung.
*   **`GET /health/osrm`**: Überprüft den OSRM-Dienst (siehe Details unten).
*   **`GET /health/db`**: Überprüft die Datenbankverbindung.
*   **`GET /_debug/routes`**: Zeigt alle registrierten API-Routen an. Nützlich, um 404-Fehler bei Endpunkten zu debuggen.
*   **`GET /api/osrm/metrics`**: Zeigt OSRM-Metriken (Latenz, Fehler, Circuit Breaker Status) an.

### OSRM Health Check (`GET /health/osrm`)

Dieser Endpunkt gibt detaillierte Informationen über den OSRM-Dienst zurück:

```json
{
  "base_url": "http://localhost:5011",
  "reachable": true,
  "sample_ok": true,
  "status_code": 200,
  "message": "OSRM erreichbar",
  "circuit_breaker_state": "CLOSED",
  "circuit_breaker_failures": 0,
  "circuit_breaker_open_since": null
}
```

*   `reachable`: Zeigt an, ob der OSRM-Server auf der konfigurierten URL antwortet.
*   `sample_ok`: Zeigt an, ob eine Testroute erfolgreich berechnet werden konnte.
*   `circuit_breaker_state`: Der aktuelle Zustand des Circuit Breakers (`CLOSED`, `OPEN`, `HALF_OPEN`).
*   `circuit_breaker_failures`: Anzahl der aufeinanderfolgenden Fehler, die zum Öffnen des Circuit Breakers führen können.
*   `circuit_breaker_open_since`: Zeitstempel, wann der Circuit Breaker zuletzt in den `OPEN`-Zustand gewechselt ist.

### `/_debug/routes` Endpunkt

Zeigt eine Liste aller in der FastAPI-Anwendung registrierten Routen an. Dies ist nützlich, um zu überprüfen, ob ein erwarteter Endpunkt tatsächlich vom Server geladen wurde (z.B. wenn Sie einen 404-Fehler erhalten). Beachten Sie, dass der Endpunkt direkt unter `/_debug/routes` erreichbar ist, nicht unter `/api/_debug/routes`.

### Fehler-Codes (HTTP-Status)

*   **`400 Bad Request`**: Ungültige Eingabedaten (z.B. zu wenige Koordinaten).
*   **`404 Not Found`**: Endpunkt nicht gefunden (überprüfen Sie `/_debug/routes`).
*   **`429 Too Many Requests`**: OSRM-Quota überschritten (intern von 402 gemappt).
*   **`500 Internal Server Error`**: Unerwarteter Serverfehler. Im Body finden Sie eine `x-request-id` zur Nachverfolgung in den Logs.
*   **`503 Service Unavailable`**: OSRM-Dienst vorübergehend nicht verfügbar (Circuit Breaker OPEN oder Transient-Fehler). Dies kann auch bei Datenbankverbindungsproblemen auftreten.

### Logs

Die Anwendung generiert strukturierte JSON-Logs (falls `USE_JSON_LOGGING=True` in `.env` gesetzt ist), die wichtige Informationen wie `x-request-id` und `duration_ms` (Anfragedauer) enthalten. Diese sind entscheidend für die Fehlersuche.

## 5. Konfiguration (`.env`)

Erstellen Sie eine `.env`-Datei im Projekt-Root (falls noch nicht vorhanden) und konfigurieren Sie die folgenden Variablen:

```env
OSRM_BASE_URL=http://127.0.0.1:5011
OSRM_PROFILE=driving
OSRM_TIMEOUT_SEC=10 # Gesamtes Timeout für OSRM-Anfrage in Sekunden
OSRM_RETRY_MAX=2    # Maximale Anzahl der Retries bei transienten Fehlern

# Circuit Breaker Einstellungen
OSRM_BREAKER_MAX_FAILS=5    # Anzahl der Fehler, bevor der Circuit offen ist
OSRM_BREAKER_RESET_SEC=60   # Zeit in Sekunden, nach der ein OPEN-Circuit in HALF-OPEN wechselt

# OSRM Cache Einstellungen
ROUTING_CACHE_TTL_SEC=3600 # Cache-TTL in Sekunden (1 Stunde)
DATABASE_URL=sqlite:///./app.db

# Logging
USE_JSON_LOGGING=True # Aktiviert JSON-formatiertes Logging
LOG_LEVEL=INFO # Log-Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
```

## 6. Frontend Degradationssignale

Wenn der OSRM-Dienst degradiert ist (`degraded=True` im `/api/tour/route-details`-Response):

*   **Gestrichelte Route**: Die Routenlinie auf der Karte wird gestrichelt dargestellt.
*   **Rote Farbe**: Die Routenlinie wird rot gefärbt, um den degradationszustand sofort sichtbar zu machen.
*   **Warnbanner**: Ein gelber oder oranger Banner wird oben im Frontend angezeigt, der auf den degradierte Routing-Dienst und die Verwendung von Ersatzrouten (Haversine-Fallback) hinweist.

## 7. SQLite "database disk image is malformed" – Reparatur

Falls die SQLite-Datenbank korrupt wird, können Sie das `db_repair.sh`-Skript verwenden:

```bash
bash scripts/db_repair.sh
```

Dieses Skript sichert die aktuelle `app.db`, erstellt einen SQL-Dump, erstellt eine neue Datenbank aus dem Dump und ersetzt die korrupte Datei.
