# TrafficApp 3.0 – Admin-Navigation & Layout-Standards für KIs

## 1. Ziel

Dieses Dokument legt **verbindliche Regeln** fest, wie der Admin-Bereich der TrafficApp aufgebaut und erweitert wird – insbesondere durch externe KIs (z.B. Cursor, ChatGPT).

Kernpunkte:

* Der Admin-Bereich soll **eindeutig navigierbar** sein.
* Es darf **nicht gemischt** werden zwischen:
  * einem zentralen Admin-Dokument mit Tabs/Registern **und**
  * vielen separaten Admin-HTML-Seiten ohne konsistente Navigation.
* KIs müssen sich an eine **einheitliche Strategie** halten.

---

## 2. Begriffe

* **Admin-Hauptseite**: zentrales Admin-HTML-Dokument, z.B. `admin.html`.
* **Tab / Register**: Navigations-Elemente innerhalb der Admin-Hauptseite (z.B. Bootstrap-Tabs, Sidebar-Links, etc.).
* **Admin-Modul**: inhaltlicher Bereich wie „DB-Verwaltung", „Statistik", „Tour-Import", „Datenfluss & KI".

---

## 3. Grundentscheidung für TrafficApp 3.0

Für den Admin-Bereich der TrafficApp 3.0 gilt verbindlich:

> **Es gibt genau EINE Admin-Hauptseite (z.B. `admin.html`) mit Tabs/Registern.**
>
> Alle Admin-Module werden als **Sektionen/Views innerhalb dieser Seite** umgesetzt.

Das bedeutet konkret:

* Keine neuen separaten Admin-HTML-Seiten wie `admin_stats.html`, `admin_db.html`, etc.
* Neue Admin-Funktionen werden in der bestehenden Admin-Seite integriert:
  * neue Tabs / neue Sektionen
  * Wiederverwendung bestehender Layout-Komponenten

Wenn es ausnahmsweise eine separate Seite geben muss (z.B. Spezial-Tool), dann:

* Muss diese Seite **explizit** über einen Tab/Link aus der Admin-Hauptseite aufrufbar sein.
* Darf die Hauptnavigation **nicht dupliziert** werden.

---

## 4. Struktur der Admin-Hauptseite

### 4.1 Layout-Grundstruktur

Die Admin-Hauptseite folgt dem Muster:

* Kopfbereich: Titel / Logo / ggf. globale Aktionen
* Navigation: Tabs oder Sidebar mit den Admin-Modulen
* Inhaltsbereich: `tab-pane` / Content-Div, in dem das aktive Modul gerendert wird

Beispiel (vereinfacht):

```html
<ul class="nav nav-tabs" id="adminTabs" role="tablist">
  <li class="nav-item"><a class="nav-link active" data-bs-toggle="tab" href="#tab-db">DB-Verwaltung</a></li>
  <li class="nav-item"><a class="nav-link" data-bs-toggle="tab" href="#tab-stats">Statistik</a></li>
  <li class="nav-item"><a class="nav-link" data-bs-toggle="tab" href="#tab-import">Tour-Import</a></li>
</ul>

<div class="tab-content" id="adminTabContent">
  <div class="tab-pane fade show active" id="tab-db" role="tabpanel"></div>
  <div class="tab-pane fade" id="tab-stats" role="tabpanel"></div>
  <div class="tab-pane fade" id="tab-import" role="tabpanel"></div>
</div>
```

KIs müssen dieses Muster respektieren und erweitern, **nicht ersetzen**.

### 4.2 Regeln für Tabs/Sektionen

* Jeder Admin-Bereich bekommt **einen klar benannten Tab** (z.B. `DB-Verwaltung`, `Statistik`, `Tour-Import & Vorladen`, `Datenfluss & KI`).
* Pro Tab gibt es genau **eine zugehörige Content-Sektion** (`div.tab-pane` o.ä.).
* Klassen-Kombinationen (z.B. bei Bootstrap) müssen konsistent eingehalten werden:
  * `tab-pane fade` + `show active` für das aktuell sichtbare Tab.

KIs dürfen:

* neue Tabs hinzufügen
* bestehende Tabs um Inhalt erweitern

KIs dürfen NICHT:

* das Navigationsschema wechseln (z.B. von Tabs zu komplett neuer Sidebar) ohne ausdrückliche Anweisung
* mehrere unabhängige Navigationssysteme in derselben Seite einführen.

---

## 5. Wann separate HTML-Seiten erlaubt sind

Grundsatz: **Standard ist EIN Admin-Dokument.** Separate Seiten sind Ausnahmefälle.

Erlaubt sind separate HTML-Seiten nur, wenn:

1. Es sich um ein spezielles Tool/Feature handelt, das einen **eigenen Fullscreen-Workflow** braucht (z.B. komplexer Editor, Vollbild-Viewer).
2. Die Seite **nicht** als generische Admin-Steuerzentrale dient.
3. Sie über die Admin-Hauptseite aufgerufen wird, z.B.:
   * Button/Link in einem Tab (`target="_blank"` oder modaler Frame).
4. Die globale Admin-Navigation **nicht** dupliziert oder abweichend nachgebaut wird.

KIs müssen in solchen Fällen im Code klar markieren:

* Zweck der separaten Seite
* Zusammenhang zur Admin-Hauptseite

---

## 6. Anforderungen an KIs (Cursor / ChatGPT / andere)

Wenn eine KI Code für den Admin-Bereich erzeugt oder ändert, gelten folgende Regeln:

1. **Navigationsstrategie nicht ändern**
   * Bestehende Admin-Hauptseite weiterverwenden.
   * Keine neue alternative „Admin-Startseite" erzeugen.

2. **Neue Funktionen integrieren, nicht isolieren**
   * Neue Module als neue Tabs/Sektionen in der vorhandenen Admin-Struktur anlegen.
   * APIs/Endpunkte, die Admin-Funktionalität liefern, müssen einem Tab zugeordnet sein.

3. **Konsistente Benennung**
   * Tab-Titel müssen mit Dokumentation und Code-Bezeichnungen übereinstimmen.
   * Beispiel: Tab „DB-Verwaltung" ↔ Doku-Abschnitt „DB-Verwaltung" ↔ JS-Modul `db_admin.js`.

4. **Keine Navigations-Duplikate**
   * Kein zweites Menü innerhalb eines Tabs einführen, das aussieht wie eine „Mini-Admin-Startseite".
   * Untergliederungen innerhalb eines Tabs sind okay (z.B. Sub-Tabs oder Accordion), aber als **Teil des Moduls**, nicht als neue globale Navigation.

5. **Dokumentationspflicht**
   * Wenn neue Tabs oder Module angelegt werden, muss in der Projekt-Doku ein Hinweis ergänzt werden (z.B. in `STATUS_AKTUELL.md` oder einem Admin-spezifischen Dokument).

---

## 7. Beispiele – erlaubt vs. nicht erlaubt

### 7.1 Erlaubt

* KI fügt einen neuen Tab „Tour-Import & Vorladen" in `admin.html` hinzu und nutzt dort bestehendes Layout.
* KI erweitert im Tab „Statistik" die Charts, ohne neue HTML-Seiten zu erzeugen.
* KI erstellt eine Spezialseite `route_simulator.html`, die nur über einen Button im Admin-Tab „Tools" geöffnet wird.

### 7.2 Nicht erlaubt

* KI legt `admin_db.html` und `admin_stats.html` an und verlinkt diese getrennt, ohne zentrale Admin-Hauptnavigation.
* KI erzeugt innerhalb eines Tabs eine zweite Tab-Navigation, die so aussieht wie die Hauptnavigation, aber andere Inhalte zeigt.
* KI baut einen alternativen Admin-Einstiegspunkt (`admin2.html`), ohne die bestehende Struktur zu benutzen.

---

## 8. Checkliste für Änderungen im Admin-Bereich (für KIs)

Vor jedem Commit / Vorschlag:

* [ ] Wird **nur** die bestehende Admin-Hauptseite (`admin.html`) erweitert?
* [ ] Sind neue Bereiche als **Tabs/Sektionen** innerhalb dieser Seite umgesetzt?
* [ ] Gibt es keine neue, konkurrierende Admin-Startseite?
* [ ] Werden vorhandene Navigationsmuster (Tabs, Klassen, IDs) wiederverwendet?
* [ ] Ist die neue Funktion in der Doku referenziert (z.B. im Admin-/Status-Dokument)?

Nur wenn alle Punkte mit **Ja** beantwortet werden, entspricht die Änderung diesem Standard.

---

**Dieses Dokument ist verbindlich für alle zukünftigen KI-gestützten Änderungen im Admin-Bereich der TrafficApp 3.0. Ziel ist ein klarer, erweiterbarer und für Menschen UND KIs verständlicher Admin-Bereich, ohne Navigations-Chaos.**

**Erstellt:** 2025-11-19  
**Version:** 1.0  
**Status:** Verbindlich

