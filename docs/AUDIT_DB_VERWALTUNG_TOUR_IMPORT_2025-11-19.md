# Audit – DB-Verwaltung & Tour-Import (Stand 2025-11-19)

## 1. DB-Verwaltung – Problem & Ursache

### 1.1 Beobachtung (aus AUDIT_FEHLER_DB_VERWALTUNG_2025-11-19)

* API-Endpunkte `/api/db/info` und `/api/db/tables` liefern **korrekte Daten**.
* JavaScript setzt `innerHTML` für die Content-Elemente (Längen ~1.6k / ~15k Zeichen).
* Console-Logs zeigen:
  * Tab-Element vorhanden
  * `innerHTML` wurde gesetzt
  * Tab „sichtbar: true" laut Code
* Trotzdem ist im UI **kein Inhalt sichtbar**.

### 1.2 Wahrscheinliche Root Cause

Bootstrap-Tabs mit `fade` verhalten sich so:

```css
.tab-pane.fade {
  opacity: 0;
}
.tab-pane.fade.show {
  opacity: 1;
}
```

Laut Audit besitzt der DB-Verwaltungs-Tab die Klassen-Kombi:

* `tab-pane fade active`

**Problem:**

* Es fehlt die Klasse `show`.
* Ergebnis: `opacity` bleibt 0 → Inhalt bleibt unsichtbar, egal was in den Kind-Elementen steht.

Dieses Verhalten erklärt, warum:

* JS / API / innerHTML alle korrekt sind
* aber der Nutzer trotzdem „leere Fläche" sieht.

### 1.3 Fix-Vorschläge

#### Option A – Markup anpassen (empfohlen)

DB-Verwaltungs-Tab so markieren, dass er wirklich sichtbar ist:

```html
<div class="tab-pane fade show active" id="db-tab" role="tabpanel">
    ...
</div>
```

* `fade show active` statt nur `fade active`.
* Alternativ: `fade` entfernen, wenn keine Fade-Animation nötig ist.

#### Option B – Aktivierung per JavaScript

Beim Umschalten der Tabs sicherstellen, dass **`show` und `active`** gesetzt werden:

```javascript
function activateTab(tabId) {
    document.querySelectorAll('.tab-pane').forEach(pane => {
        pane.classList.remove('show', 'active');
    });
    const target = document.getElementById(tabId);
    if (target) {
        target.classList.add('show', 'active');
    }
}
```

#### Option C – CSS-Fallback (Hotfix)

Wenn das Tab-Handling nicht sofort angepasst werden kann:

```css
.tab-pane.fade.active {
    opacity: 1 !important;
}
```

* Notlösung/harter Override, bis das Tab-System sauber geregelt ist.

---

## 2. Tour-Import & Vorladen – Audit-Status

### 2.1 Bereits umgesetzt (laut AUDIT_TOUR_IMPORT_FEATURE_2025-11-19)

**Datenbank / Migrationen:**

* Migration `020_import_batches.sql` angelegt.
* Tabellen:
  * `import_batches`
  * `import_batch_items`
  * `customers`

**Backend-API:**

* Routen vorhanden für:
  * `POST /api/import/batch` – Batch anlegen
  * `GET /api/import/batches` – Übersicht
  * `GET /api/import/batch/{id}` – Details
  * `GET /api/import/stats` – Füllstände/Statistiken
* Router in `app_setup.py` registriert.

Damit ist die **Basis-Infrastruktur** für das Feature vorhanden.

### 2.2 Noch offene Punkte

1. **Upload-Handling & Parsing**
   * Es fehlt ein Endpoint wie `POST /api/import/upload`, der:
     * Dateien entgegennimmt (CSV/ZIP)
     * sie einem `import_batch` zuordnet
     * Parsing/Verarbeitung startet.

2. **CSV-Parser & Datenanlage**
   * Aus den CSV-Dateien müssen:
     * neue `customers` (falls noch nicht vorhanden)
     * neue `tours` (Status z.B. `preloaded`)
     * passende `tour_stops`
   * erzeugt und gespeichert werden.

3. **Geocoding-Worker**
   * Hintergrundprozess, der:
     * Kunden/Stops mit `geocode_status = 'pending'` holt
     * Geocoding-Service aufruft
     * `lat/lon` + `geocode_status` (`ok` / `failed`) setzt.

4. **Admin-Frontend „Tour-Import & Vorladen"**
   * Eigene Sektion/Seite im Admin-Bereich mit:
     * Upload-Feld + Import-Button
     * Tabelle der `import_batches` inkl. Status / Touren / Stops
     * Anzeige von Füllständen (z.B. `GET /api/import/stats`).

5. **Import-Profile (optional)**
   * Mapping von CSV-Spalten → Felder (Kunde/Tour/Stopp) je Kunde/Format.
   * Eigene Tabelle `import_profiles` denkbar.

---

## 3. Empfohlene Next Steps

### 3.1 Kurzfristig: DB-Verwaltung reparieren

1. Tab-Markup prüfen:
   * Hat der DB-Tab aktuell `class="tab-pane fade active"`?
2. Anpassen auf:
   * `class="tab-pane fade show active"` (oder `tab-pane show active`).
3. In Dev-Tools prüfen:
   * `opacity` des Tab-Panels = 1
   * Inhalt sichtbar.

Damit ist die DB-Verwaltung im Adminbereich wieder nutzbar, ohne Backend- oder API-Code ändern zu müssen.

### 3.2 Mittelfristig: Tour-Import auf MVP heben

1. **Upload-Endpoint implementieren**
   * `POST /api/import/upload`
   * Speichert Datei(en), verknüpft mit `import_batches` / `import_batch_items`.

2. **CSV-Parser integrieren**
   * Bestehende Parser-Logik verwenden oder neu anlegen.
   * Für jede Datei:
     * Kunden anlegen/suchen (`customers`)
     * `tours` mit Status `preloaded` anlegen
     * `tour_stops` pro Tour anlegen

3. **Geocoding-Prozess aktivieren**
   * Job/Worker, der regelmäßig `customers` mit `geocode_status = 'pending'` verarbeitet.

4. **Minimal-UI bauen**
   * Admin-Ansicht für:
     * Upload
     * Batch-Liste (Status, Touren, Stops)
     * Füllstände (z.B. Kunden gesamt, geocoded, failed).

Später erweiterbar um:

* Import-Profile
* Simulation-Imports
* detailiertes Logging/Monitoring.

---

Dieses Dokument fasst den Audit-Stand für **DB-Verwaltung** und **Tour-Import** zusammen und definiert klare, umsetzbare nächste Schritte für Bugfixing und Feature-Vervollständigung.

