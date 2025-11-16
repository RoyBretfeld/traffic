# docs/ERROR_CATALOG.md
# Fehlerkatalog der FAMO TrafficApp – Routing & API

Dieses Dokument beschreibt die häufigsten Fehlercodes und Fehlermeldungen, die in der FAMO TrafficApp, insbesondere im Zusammenhang mit Routing und API-Interaktionen, auftreten können. Es hilft bei der Diagnose und Behebung von Problemen.

## 1. HTTP Status Codes & Semantik

Die TrafficApp verwendet standardisierte HTTP-Statuscodes, um den Status einer API-Anfrage zu kommunizieren. Im Fehlerfall wird oft eine JSON-Antwort mit zusätzlichen Details und einer `correlation_id` (Trace-ID) zurückgegeben, um die Fehlersuche in den Logs zu erleichtern.

### 1.1. 2xx Erfolgreiche Antworten

*   **`200 OK`**: Die Anfrage war erfolgreich. Die Antwort enthält die angeforderten Daten.
*   **`201 Created`**: Eine neue Ressource wurde erfolgreich erstellt (z.B. nach einem Upload).
*   **`206 Partial Content`**: Die Anfrage war teilweise erfolgreich. Dies kann im Routing-Kontext auftreten, wenn z.B. OSRM nicht verfügbar ist und ein Fallback (z.B. Haversine) eine Ersatzroute berechnet. Die `degraded: true` im Response-Body weist darauf hin.

### 1.2. 4xx Client-Fehler

Diese Fehler weisen darauf hin, dass ein Problem mit der Anfrage des Clients vorliegt.

*   **`400 Bad Request`**: Die Anfrage konnte aufgrund ungültiger Syntax oder fehlender, erforderlicher Parameter nicht verarbeitet werden.
    *   **Beispiel-Payload**: `{"detail": "Mindestens 2 gültige Koordinaten für Routing erforderlich"}`
    *   **Ursache**: Der Client sendet unvollständige oder fehlerhafte Daten (z.B. eine Routenanfrage mit nur einem Stopp).
    *   **Behebung**: Überprüfen Sie die Anfrage-Parameter und die Payload gemäß der API-Dokumentation.

*   **`404 Not Found`**: Der angeforderte Endpunkt oder die Ressource wurde nicht gefunden.
    *   **Beispiel-Payload**: `{"detail": "Not Found"}`
    *   **Ursache**: Tippfehler in der URL, ein Router wurde im Backend nicht korrekt registriert, oder die Ressource existiert nicht. Auch Probleme mit `uvicorn --reload` oder der Factory-Funktion (`create_app`) können zu nicht registrierten Routen führen, wenn `app = create_app()` direkt in `backend/app.py` ausgeführt wird, anstatt es nur als Factory bereitzustellen.
    *   **Behebung**: Überprüfen Sie die URL. Nutzen Sie den Debug-Endpunkt `GET /_debug/routes`, um alle registrierten Routen zu sehen und zu prüfen, ob der erwartete Endpunkt vorhanden ist. Stellen Sie sicher, dass `backend/app.py` nur die `create_app` Factory-Funktion bereitstellt und nicht direkt eine App-Instanz erstellt, wenn der Server als Factory gestartet wird. Ein Server-Neustart (ohne Hot-Reload) kann bei hartnäckigen Router-Problemen helfen.
    *   **Beispiel für eine korrekte `start_server.py` mit Factory-Muster:**
```python
import uvicorn
import os
from pathlib import Path

# Füge das Projekt-Root zum Python-Pfad hinzu
project_root = Path(__file__).resolve().parent
if str(project_root) not in os.sys.path:
    os.sys.path.insert(0, str(project_root))

import logging_setup  # Stellt sicher, dass das Logging frühzeitig konfiguriert wird
import app_startup # Führt Datenbank-Schema-Checks aus

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Konfiguriere Uvicorn so, dass es die create_app-Factory-Funktion verwendet
    uvicorn.run("backend.app:create_app", host="127.0.0.1", port=8111, reload=True, factory=True)
```

*   **`422 Unprocessable Entity`**: Die Anfrage war syntaktisch korrekt, aber die enthaltenen Daten konnten semantisch nicht verarbeitet werden (oft Pydantic-Validierungsfehler).
    *   **Beispiel-Payload**: `{"detail": "Validation error: latitude is not a valid float"}`
    *   **Ursache**: Die übermittelten Daten entsprechen nicht dem erwarteten Schema (z.B. ein String anstelle einer Zahl). Dies kann auch durch veraltete Pydantic-Syntax (V1 vs. V2) verursacht werden.
    *   **Behebung**: Überprüfen Sie die Datentypen und das Format der gesendeten Daten. Stellen Sie sicher, dass alle Pydantic-Modelle die Pydantic V2-Syntax korrekt verwenden.

*   **`429 Too Many Requests`**: Der Client hat zu viele Anfragen in einem bestimmten Zeitraum gesendet und wurde rate-limitiert. Dies kann auch als Mapping für externe API-Quota-Fehler (z.B. OSRM 402 Payment Required) verwendet werden.
    *   **Beispiel-Payload**: `{"error": "upstream-quota", "message": "OSRM quota exceeded (402)", "correlation_id": "..."}`
    *   **Ursache**: Zu viele Anfragen an OSRM oder an den Routing-Service innerhalb kurzer Zeit. Oder das OSRM-Abonnement/Quota ist erschöpft. Dies kann auch durch einen Circuit Breaker ausgelöst werden, wenn der Upstream-Dienst überlastet ist.
    *   **Behebung**: Reduzieren Sie die Anfragerate. Warten Sie eine Weile, bevor Sie es erneut versuchen. Überprüfen Sie die OSRM-Statusseite oder Ihr Abonnement.

### 1.3. 5xx Server-Fehler

Diese Fehler weisen darauf hin, dass der Server ein Problem hatte, das die Verarbeitung der Anfrage verhinderte.

*   **`500 Internal Server Error`**: Ein unerwarteter Fehler ist auf dem Server aufgetreten.
    *   **Beispiel-Payload**: `{"error": "internal-error", "message": "Interner Serverfehler bei Routenberechnung: RuntimeError: OSRM unerwarteter Fehler", "correlation_id": "..."}`
    *   **Ursache**: Ein nicht abgefangener Fehler im Backend-Code. Dies sollte durch die globale Fehlerbehandlung (`http_exception_handler`) und die `RequestIdMiddleware` standardisiert und geloggt werden. Häufige Ursachen sind Datenbankfehler (`no such column`), Importfehler (`ImportError`), oder unerwartete Logikfehler.
    *   **Behebung**: Überprüfen Sie die Server-Logs mit der bereitgestellten `correlation_id` für weitere Details. Häufig hilft das Prüfen des Datenbankschemas und der Migrationshistorie. Bei `ImportError` prüfen Sie die Pfade und Verfügbarkeit der Module. Melden Sie den Fehler dem Entwicklungsteam.

*   **`503 Service Unavailable`**: Der Dienst ist vorübergehend nicht in der Lage, die Anfrage zu bearbeiten, oft aufgrund von Überlastung oder Wartung.
    *   **Beispiel-Payload**: `{"error": "upstream-unavailable", "message": "OSRM Dienst vorübergehend nicht verfügbar (Circuit Breaker OPEN)", "correlation_id": "..."}`
    *   **Ursache**: Der OSRM-Dienst oder ein anderer Upstream-Dienst ist ausgefallen, oder der Circuit Breaker hat den OSRM-Zugriff blockiert. Auch bei Datenbankverbindungsproblemen kann dieser Status zurückgegeben werden.
    *   **Behebung**: Warten Sie und versuchen Sie es später erneut. Überprüfen Sie den Status des OSRM-Dienstes (`GET /health/osrm`) und der Datenbank (`GET /health/db`).

## 2. Häufige Log-Meldungen & Warnungen

Die Anwendung verwendet detailliertes Logging, um den Betriebsstatus und potenzielle Probleme zu protokollieren. Achten Sie auf folgende Meldungen:

*   **`[ROUTE-VIS] Routen-Warnungen: [...]`**: Zeigt an, dass die Routenberechnung nicht optimal verlief (z.B. Fallback verwendet), aber ein Ergebnis geliefert wurde. Details stehen im Array.
*   **`OSRM Timeout: ...` / `OSRM Verbindungsfehler: ...`**: Der OSRM-Dienst war nicht erreichbar oder hat nicht rechtzeitig geantwortet.
*   **`OSRM Quota-Fehler (402) → Mappe zu QuotaError: ...`**: Der OSRM-Dienst meldete, dass das Kontingent überschritten wurde.
*   **`OSRM Transient-Fehler (50x): ...`**: Temporärer Fehler im OSRM-Dienst, bei dem Retries versucht werden.
*   **`Circuit-Breaker: Request blockiert (OPEN)`**: Der Circuit Breaker hat Anfragen an OSRM blockiert, um den Dienst zu schützen.
*   **`Phase 2 Migration fehlgeschlagen: (sqlite3.OperationalError) no such column: ...`**: Ein Problem bei der Datenbankmigration. **FIXED**: Dies wurde durch Hinzufügen der fehlenden Spalten `next_attempt`, `first_seen` und `last_seen` in `geo_fail` und `geo_cache` direkt im `SCHEMA_SQL` sowie durch die Implementierung von idempotenten Spaltenprüfungen in `ensure_schema()` behoben. Es gibt auch ein Hilfsskript `scripts/db_fix_first_seen.py` zur manuellen Reparatur.
*   **`sqlite3.OperationalError: near "try": syntax error`**: Dieser Fehler trat auf, weil Python `try-except` Blöcke versehentlich direkt in SQL-Schema-Statements in `db/schema.py` eingebettet waren. **FIXED**: Die `try-except` Blöcke wurden aus den SQL-Strings entfernt und die `ALTER TABLE` Logik wird nun korrekt in Python unter Verwendung von `column_exists` behandelt.
*   **`ImportError: cannot import name 'SETTINGS' from 'backend.config'`**: Dieser Fehler trat auf, weil `SETTINGS` nicht mehr direkt aus `backend.config` importiert werden sollte, nachdem `OSRMSettings` in eine einfache Klasse umgewandelt wurde. **FIXED**: Der Import wurde zu `from backend.config import cfg` geändert, und `cfg()` wird nun direkt für den Zugriff auf die Einstellungen verwendet.
*   **`ImportError: cannot import name 'logger' from 'backend.utils.json_logging'`**: Dieser Fehler entstand, weil `backend.utils.json_logging` keinen globalen Logger als `logger` exportiert. Stattdessen sollte `logging.getLogger(__name__)` verwendet werden. **FIXED**: Die Importanweisung in `backend/services/real_routing.py` wurde korrigiert, um `import logging; logger = logging.getLogger(__name__)` zu verwenden.
*   **`[AddressMapper] WARNUNG: Konfigurationsdatei address_mappings.json nicht gefunden`**: Eine optionale Konfigurationsdatei für Adress-Mappings wurde nicht gefunden. Dies ist oft keine kritische Fehlermeldung, kann aber die Genauigkeit der Adressauflösung beeinträchtigen.

*   **`ImportError: cannot import name 'text' from 'sqlalchemy' (unknown location)` / `ImportError: cannot import name 'text' from 'sqlalchemy.sql'`**: SQLAlchemy kann nicht importiert werden, obwohl es installiert zu sein scheint.
    *   **Ursache**: Das Python venv ist beschädigt (fehlende METADATA-Dateien in `*.dist-info` Verzeichnissen). 
        *   **Häufige Ursachen:**
            1. **Unterbrochene Installationen:** Installation wird abgebrochen (Ctrl+C, Systemabsturz, Stromausfall) → Package-Dateien installiert, aber METADATA fehlt
            2. **Antivirus-Software:** Windows Defender oder andere AV-Tools löschen METADATA-Dateien (falsch-positiv)
            3. **Dateisystem-Fehler:** NTFS-Fehler, defekte Festplatte → Dateien nicht vollständig geschrieben
            4. **Manuelle Löschung:** Benutzer oder Cleanup-Scripts löschen `.dist-info` Verzeichnisse
            5. **Pip-Upgrade-Probleme:** `pip install --upgrade pip` schlägt fehl → pip selbst beschädigt
            6. **Parallele Installationen:** Mehrere `pip install` Prozesse gleichzeitig → Race Conditions
            7. **Venv-Kopieren:** Venv wird kopiert statt neu erstellt → Symlinks/Berechtigungen gehen verloren
        *   **Zusätzlich:** Das System-Python wird statt des venv-Pythons verwendet, wenn das venv nicht aktiviert ist.
    *   **Symptome**: 
        - `pip show sqlalchemy` schlägt fehl mit `FileNotFoundError: ...\METADATA`
        - `pip uninstall` schlägt fehl mit `error: uninstall-no-record-file`
        - Python-Prozesse laufen, aber Server antwortet nicht auf Port 8111
        - Weitere Packages betroffen: Numpy (`Error importing numpy: you should not try to import numpy from its source directory`), Pandas (`ModuleNotFoundError: No module named 'pandas._libs.pandas_parser'`)
    *   **Behebung**: 
        1. Prüfe, ob venv aktiviert ist: `python -c "import sys; print(sys.executable)"` sollte auf `venv\Scripts\python.exe` zeigen
        2. Prüfe venv-Status: `pip show sqlalchemy` - wenn METADATA-Fehler → venv ist beschädigt
        3. **Lösung:** Venv komplett neu erstellen:
           ```powershell
           # Alle Python-Prozesse beenden
           taskkill /F /IM python.exe /T
           # Altes venv löschen
           Remove-Item -Path "venv" -Recurse -Force
           # Neues venv erstellen
           python -m venv venv
           # Venv aktivieren
           .\venv\Scripts\Activate.ps1
           # pip upgraden
           python -m pip install --upgrade pip
           # Dependencies installieren
           python -m pip install -r requirements.txt
           ```
        4. **Alternative (nur bei einzelnen Packages):** Beschädigte dist-info Verzeichnisse löschen und Package neu installieren
    *   **Prävention**: 
        - Start-Scripts sollten immer `venv\Scripts\python.exe` verwenden (nicht System-Python)
        - SQLAlchemy-Import vor Server-Start testen
        - Venv-Status regelmäßig prüfen
        - Bei mehr als 2-3 beschädigten Packages: venv neu erstellen (schneller als Reparatur)

## 3. `correlation_id` (Trace-ID)

Jede Anfrage, die durch die `RequestIdMiddleware` läuft, erhält eine eindeutige `x-request-id` im Response-Header. Diese ID wird auch in den Logs für die gesamte Dauer der Anfrage protokolliert. Wenn ein Fehler auftritt, kann diese `x-request-id` verwendet werden, um alle relevanten Log-Einträge für diese spezifische Anfrage zu finden und das Problem zu diagnostizieren.
