# TrafficApp 3.0 – DB- und Zugriffsübersicht für Adminbereich

## 1. Ziel dieses Dokuments

Dieses Dokument beschreibt:

* Welche Datenbanken aktuell existieren
* Wofür sie genutzt werden
* Wer (Rolle, nicht Person) wie darauf zugreift
* Technische Basics (Ort, Technik, Backup, Rechte)

Es ist für den **Adminbereich** gedacht, damit klar ist:

* Wo Daten liegen
* Wer wofür verantwortlich ist
* Welche Risiken bestehen, wenn etwas ausfällt oder falsch benutzt wird

---

## 2. Aktuelle Datenbanken (Stand: 2025-11-19)

### 2.1 TrafficApp-Hauptdatenbank

* **Typ:** SQLite
* **Ort:** Lokale Datei auf dem TrafficApp-Server/LXC
* **Funktion:**

  * Speichert Kern-Daten der Anwendung (z.B. Touren-Metadaten, Nutzerkonfigurationen etc.)

* **Zugriff:**

  * **Backend-Service (FastAPI):** Vollzugriff (Lesen/Schreiben)
  * **Adminbereich (Web-UI):** Nur über Backend-API, kein Direktzugriff auf Datei

* **Rechte:**

  * Schreibzugriff nur über Anwendung / Backend
  * Direktzugriff auf Datei nur für Server-Admins (z.B. root / technischer Betreiber)

* **Backups:**

  * Geplante regelmäßige Dateisicherungen (z.B. per Cron, Proxmox-Snapshots, oder Backup-Script)

*(Details werden später ergänzt: Tabellen, genaue Pfade, Backup-Intervall)*

---

### 2.2 OSRM (Routing-Daten)

* **Typ:** Dateien / Routing-Profile im OSRM-Dockercontainer
* **Ort:** Docker-Volume / gemountetes Verzeichnis auf dem OSRM-Host
* **Funktion:**

  * Bereitstellung der Routinginformationen für Straßen (Routenberechnung)

* **Zugriff:**

  * **TrafficApp-Backend:** Per HTTP-Anfrage an OSRM-API (Lesend – Routen anfragen)
  * **Adminbereich:** Indirekt über Health-Checks und Status-Seiten

* **Rechte:**

  * Konfiguration / Updates nur durch System-Admin / Infrastruktur-Admin

* **Backups:**

  * Hängt von Setup ab: Rebuild über OSM-Daten möglich / oder Snapshot des Volumes

---

### 2.3 (Geplant) Routen- & Historien-Datenbank

* **Typ:** SQLite (oder später ggf. andere DB)
* **Status:** Geplant – noch in Umsetzung
* **Funktion (Ziel):**

  * Persistent speichern von Routen, Sub-Routen, Optimierungen
  * Historie von Touren, Auswertungen, Statistikgrundlage

* **Zugriff (geplant):**

  * **Backend-Service:** Vollzugriff
  * **Adminbereich:** Lesender Zugriff (Statistik, Historie, Auswertungen)
  * **Option:** Exportfunktionen (z.B. CSV, JSON)

---

### 2.4 (Geplant) Vektordatenbank für KI

* **Typ:** Noch zu definieren (z.B. SQLite + Vektor-Extension, oder externer Dienst)
* **Status:** Noch Konzeptphase
* **Funktion (Ziel):**

  * Speichern von Embeddings (Vektoren) zu Touren, Routen, Fehlern
  * Grundlage für KI-Lernen und Empfehlungen

* **Zugriff (geplant):**

  * **KI-Services / Backend-Worker:** Vollzugriff
  * **Adminbereich:** Einsehen von Statistiken, ggfs. Fehler-Clustering

---

## 3. Rollen & Zugriffsrechte

### 3.1 Rollenübersicht

* **Fahrer / Nutzer der TrafficApp-UI**

  * Kein direkter DB-Zugriff
  * Arbeiten ausschließlich über die Weboberfläche (Haupt-UI)

* **Disponent / Adminbereich-Nutzer**

  * Zugriff auf Admin-Weboberfläche
  * Darf:

    * Tourenübersichten ansehen
    * Statistiken abrufen
    * Systeme prüfen (Health-Checks)
  * Darf NICHT:

    * Direkt SQL-Abfragen ausführen
    * Datenbankdateien bearbeiten/löschen

* **System-Admin / Infrastruktur-Admin**

  * Zugriff auf Server / LXC / Docker
  * Darf:

    * DB-Dateien sichern (Backups)
    * OSRM-Container neu starten / aktualisieren
    * Updates der TrafficApp einspielen

* **Entwickler / KI-Entwickler**

  * Zugriff auf Codebasis (Git/ZIP)
  * Arbeiten primär lokal oder in Dev-Umgebungen
  * Kein direkter Zugriff auf Produktiv-DB ohne Freigabe

---

## 4. Sicht im Adminbereich

Im Adminbereich sollte es eine eigene Sektion **„Datenbanken & Zugriffe"** geben, die folgendes anzeigt:

1. **Übersicht aller relevanten Datenquellen**

   * TrafficApp-Hauptdatenbank (Status: erreichbar? Größe?)
   * OSRM (Status: online? Antwortzeiten?)
   * Geplante Routen-DB (Status: aktiv, in Planung, inaktiv)
   * Geplante Vektordatenbank (Status: Konzept / aktiv)

2. **Zugriffsebenen (Rollen)**

   * Kurzbeschreibung, welche Rolle auf welche Ebene zugreifen kann

3. **Wichtige Hinweise / Risiken**

   * Hinweis, dass direkte Manipulation der DB-Dateien zu Datenverlust führen kann
   * Empfehlung: Änderungen nur über die Anwendung / definierte Schnittstellen

4. **Dokulinks**

   * Link auf: `STATUS_AKTUELL.md`
   * Link auf: ggf. `docs/db_routes.md` (sobald vorhanden)
   * Link auf: Backup- / Restore-Anleitung

---

## 5. Nächste Schritte für diese Doku

* Konkrete Tabellenstruktur der SQLite-DB eintragen (Tabellen, Spalten, Beziehungen)
* Exakte Pfade und Backup-Scripte ergänzen
* Im Adminbereich die Anzeige dieser Infos technisch anbinden (Health-Endpunkte, Größenabfrage, Statusflags)

