===== START FAMO_TrafficApp_MasterDoku.md =====
# 📦 FAMO TrafficApp – Master-Dokumentation
**Version:** 1.1  
**Stand:** 11.08.2025  

---

## 📑 Inhaltsverzeichnis
1. [Projektbeschreibung](#1-projektbeschreibung)  
2. [Architekturübersicht](#2-architekturübersicht)  
3. [Layout- & Funktionsbeschreibung](#3-layout--funktionsbeschreibung)  
4. [Laufplan / To-Do-Checkliste](#4-laufplan--to-do-checkliste)  
5. [Systemprompt für Cursor](#5-systemprompt-für-cursor)  
6. [Detaillierter Cursor-Umsetzungsplan (GPT-5 ready)](#6-detaillierter-cursor-umsetzungsplan-gpt-5-ready)  

---

## 1. Projektbeschreibung
Die **FAMO TrafficApp** ist eine **lokale, KI-gestützte Routenplanungsanwendung** für den On-Prem-Betrieb unter Proxmox.  
Ziel: **Effiziente, praxisnahe Planung von mindestens 10 Touren täglich** (davon 5 aktiv zu fahren) mit Live-Verkehrsdaten, Zeitfenstern, Tourenstatistik und kontinuierlicher KI-Optimierung.  

**Besonderheiten:**
- Start-/Endpunkt jeder Tour: **Stuttgarter Str. 33, 01189 Dresden**
- TEHA-Tourzusammenfassungen (mehrseitige PDF) als Datenquelle  
- KI-unterstützte Gruppierung der Kunden nach Ort & Zeitlimit  
- Tages-, Wochen- und Jahresstatistiken  
- Sicherer On-Prem-Betrieb ohne externe Datenlecks

---

## 2. Architekturübersicht
**Modularer Aufbau** – jedes Modul unabhängig testbar:

- **01 PDF-Parser** – extrahiert Kunden + Adressen aus TEHA-PDF  
- **02 Geocoding-Service** – wandelt Adressen in GPS-Koordinaten um (mit Cache)  
- **03 KI-Planer** – erstellt Tourengruppen unter Zeit-/Distanzrestriktionen (Werkstatttour ≤ 60 min)  
- **04 Routing-Service** – generiert Strecken mit OpenRouteService (Loop ≤ 60 min, Start=Ende)  
- **05 Touren-Manager** – speichert, versioniert, exportiert Tages- und Wochendaten  
- **06 Statistik-Modul** – wertet Woche/Jahr aus, erstellt Trendberichte  
- **07 Frontend** – zentrale Karte, Tabs (W1–W10), Detailansichten, KI-Kommentare  
- **08 Sicherheitsschicht** – Safety-Guard, Rollen, Audit-Logs  

---

## 3. Layout- & Funktionsbeschreibung
**Hauptansicht**:
- **Zentrale Karte** (Leaflet/OpenStreetMap) als Hauptelement  
- **Horizontale Tabs** (W1–W10) oben, jede Tour eigene Farbe  
- **Aktive Tour** = farbig, andere Routen ausgegraut  
- **Alle Touren** gleichzeitig sichtbar (für Gesamtüberblick)  

**Tab-Detailansicht**:
- Kundenliste mit Adresse, Reihenfolge, Zeitfenster  
- Mini-Karte nur für diese Tour  
- Infozeile: Start/Ziel (immer Stuttgarter Str. 33), Gesamtdauer, km  
- KI-Kommentar zur Planung & Optimierung  

**Zusatzfunktionen**:
- Zeitmanagement (z. B. Werkstatttour ≤ 1 h inkl. Rückfahrt)  
- Automatische Speicherung jeder Tour mit ID:  
  `W1-23.04.25-8K.json` (Tour, Datum, Anzahl Kunden)  
- PDF-Export für Tagesübersicht (alle Touren + Details)  
- Fahrerfeedback-System für KI-Verbesserung  

---

## 4. Laufplan / To-Do-Checkliste
- [ ] **TEHA-Datenimport** (PDF-Parser fertigstellen, Golden-Test anlegen)  
- [ ] **Geocoding** implementieren + SQLite-Cache  
- [ ] **KI-Planung** (Tourengruppierung, Zeitrestriktionen, Start/Ende fix)  
- [ ] **Routing-Integration** mit OpenRouteService  
- [ ] **Tourenspeicherung** im ID-Format (JSON) + PDF-Export  
- [ ] **Frontend** Karte + Tabs + Detailansicht  
- [ ] **Statistik** Tages-, Wochen-, Jahreswerte  
- [ ] **Feedback-Loop** Fahrer → KI  
- [ ] **Tests** Unit, Integration, Golden-File  
- [ ] **Sicherheit** Safety-Guard, Rollen, Logs  

---

## 5. Systemprompt für Cursor
Du bist leitender Systemarchitekt & Senior-Entwickler der FAMO TrafficApp 1.0.
Sprache: Deutsch. Code: modular, getestet, produktionsbereit.

Regeln:

Keine Löschung/Überschreibung von Dateien/Daten ohne Rückfrage + Bestätigungstoken.

Betrieb On-Prem (Proxmox, LAN/VPN), keine unnötigen Cloud-Abhängigkeiten.

Jede Funktion als eigenes Modul mit definiertem Input/Output (JSON-Schema).

Tests first: Unit-, Contract-, E2E-Tests mit Mocks/Fakes.

Self-Check: Konsistenzprüfungen (Loop ≤ 60 min, Start=Ende).

Dokumentation immer aktuell halten (ARCHITECTURE.md, API_DOCS.md, DATA_SCHEMA.md).

UI/UX: Hauptkarte + Tabs, klare Farbkodierung, aktive Tour farbig.

Sicherheit: Rollen, Audit-Logs, Secrets aus .env, keine PII an KI.

yaml
Kopieren
Bearbeiten

---

## 6. Detaillierter Cursor-Umsetzungsplan (GPT-5 ready)
### Modul 01 – PDF-Parser
- Input: TEHA-Tour-PDF  
- Output: JSON `{ tour, datum, kunden: [{name, adresse}] }`  
- Test: Golden-File

### Modul 02 – Geocoding-Service
- Input: Adresse → Output: GPS  
- Cache in SQLite

### Modul 03 – KI-Planer
- Input: Kundenliste, Zeitlimit  
- Output: Tourengruppen  
- LLM: OpenAI GPT-5 API (optimierte Prompts)

### Modul 04 – Routing-Service
- Input: Koordinaten einer Tour  
- Output: Strecken-JSON (km, Dauer, Wegpunkte)  
- API: OpenRouteService, `round_trip=true`

### Modul 05 – Touren-Manager
- Speicherung: `/routen/YYYY-MM-DD/ID.json`  
- Export: Tages-PDF

### Modul 06 – Statistik-Modul
- Input: Tagesdaten → Wochen-/Jahresstatistik  
- Analyse: Trends, Auslastung

### Modul 07 – Frontend
- Hauptkarte: alle Touren sichtbar, aktive Tour farbig  
- Tabs: W1–W10, klickbar  
- Detail: Kundenliste, Mini-Karte, Zeit/km, KI-Kommentar

### Modul 08 – Sicherheitsschicht
- Zugriffskontrolle (Rollen)  
- Audit-Logs  
- Safety-Guard
===== ENDE FAMO_TrafficApp_MasterDoku.md =====