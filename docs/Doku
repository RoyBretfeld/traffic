===== START FAMO_TrafficApp_EntwicklerMap.md =====
# 🗺️ FAMO TrafficApp – Entwickler-Map
**Version:** 1.0  
**Stand:** 11.08.2025  

---

## 📌 1. Architekturübersicht
Die FAMO TrafficApp ist modular aufgebaut, jedes Modul ist eigenständig testbar und kommuniziert über klar definierte JSON-Schnittstellen.

**Module:**
1. **PDF-Parser** – TEHA-PDF → Kundenliste (JSON)
2. **Geocoding-Service** – Adressen → GPS-Koordinaten
3. **KI-Planer** – Kunden + Zeitlimit → Tourengruppen
4. **Routing-Service** – Koordinaten → Streckenplanung (OpenRouteService)
5. **Touren-Manager** – Speichern, Versionieren, Export
6. **Statistik-Modul** – Woche/Jahr auswerten
7. **Frontend** – Karte + Tabs, Detailansichten
8. **Sicherheitsschicht** – Rollen, Logging, Safety-Guard

---

## 📌 2. Modultabelle
| Modul | Beschreibung | Input | Output | Status |
|-------|--------------|-------|--------|--------|
| PDF-Parser | Extrahiert Kunden aus TEHA-PDF | PDF | JSON | geplant |
| Geocoding | Wandelt Adressen in GPS um | Adresse | Lat/Lon | geplant |
| KI-Planer | Gruppiert Kunden in Touren | JSON (Kunden) | JSON (Touren) | geplant |
| Routing | Berechnet Routen | JSON (Touren) | GeoJSON | geplant |
| Touren-Manager | Speichert & exportiert Touren | JSON (Route) | JSON/PDF | geplant |
| Statistik | Aggregiert Tourdaten | JSON | Statistik | geplant |
| Frontend | UI mit Karte/Tabs | API-Daten | UI | geplant |
| Sicherheit | Zugriffskontrolle & Logging | Request | Zugriff/Log | geplant |

---

## 📌 3. Systemprompt für Cursor
Du bist leitender Systemarchitekt der FAMO TrafficApp.
Sprache: Deutsch. Ziel: Modularer, getesteter, produktionsreifer Code.

Regeln:

Keine Löschung von Dateien/Daten ohne Rückfrage + Bestätigungstoken.

On-Premises (Proxmox, LAN/VPN), keine unnötigen Cloud-Abhängigkeiten.

Jede Funktion als eigenes Modul mit klarem Input/Output (JSON-Schema).

Tests-first: Unit-, Integration-, Golden-File-Tests.

Self-Check: Konsistenz (Loop ≤ 60 Min, Start=Ende).

Dokumentation immer aktuell halten (ARCHITECTURE.md, API_DOCS.md).

UI/UX: Hauptkarte mit Tabs; aktive Tour farbig, andere ausgegraut.

Sicherheit: Rollen, Audit-Logs, .env-Secrets, keine PII an KI.

yaml
Kopieren
Bearbeiten

---

## 📌 4. API-Endpunkt-Übersicht
| Endpoint | Methode | Beschreibung | Input | Output |
|----------|---------|--------------|-------|--------|
| `/api/parser/pdf` | POST | PDF verarbeiten | Datei | JSON (Kunden) |
| `/api/geocode` | POST | Adressen geokodieren | JSON (Adresse) | JSON (Lat/Lon) |
| `/api/routes/plan` | POST | Touren berechnen | JSON (Kunden) | JSON (Routen) |
| `/api/routes/save` | POST | Route speichern | JSON (Route) | Status |
| `/api/routes/day/{datum}` | GET | Tagesrouten laden | Datum | JSON (Routen) |
| `/api/stats/weekly` | GET | Wochenstatistik | – | JSON |
| `/api/stats/yearly` | GET | Jahresstatistik | – | JSON |

---

## 📌 5. Datenbankschema (SQLite/PostgreSQL)
**Tabelle `kunden`**
- id (PK)
- name (Text)
- adresse (Text)
- lat (Float)
- lon (Float)

**Tabelle `touren`**
- id (PK)
- tour_id (Text)
- datum (Date)
- kunden_ids (JSON)
- dauer_min (Int)
- distanz_km (Float)
- fahrer (Text)

**Tabelle `feedback`**
- id (PK)
- tour_id (Text)
- datum (Date)
- kommentar (Text)
- bewertung (Int)

---

## 📌 6. Teststrategie
- **Unit-Tests**: Jede Funktion einzeln testen.
- **Integrationstests**: Modul-übergreifende Abläufe prüfen.
- **Golden-File-Tests**: Parser-Ausgabe mit Referenz vergleichen.
- **E2E-Tests**: Gesamtablauf vom PDF bis zur gespeicherten Route.

---

## 📌 7. Entwicklungs-Workflow
1. **Branch anlegen** (`feature/<modul>`)
2. Code + Tests schreiben
3. Lokale Tests (`pytest`) laufen lassen
4. Doku anpassen
5. Commit + Push
6. Merge in `main` nach Review

---

## 📌 8. Sicherheitskonzept
- Rollenmodell: Admin, Dispatcher, Fahrer
- Zugriffskontrolle pro API-Route
- Safety-Guard: Keine Löschung ohne Bestätigung
- Audit-Logs für jede Änderung
- API-Keys in `.env`, nicht in Git

===== ENDE FAMO_TrafficApp_EntwicklerMap.md =====