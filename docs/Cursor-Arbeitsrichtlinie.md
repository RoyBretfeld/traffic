## 🧠 Cursor KI Arbeitsrichtlinie  
**FAMO Dresden – interne Best Practices**

Ziel dieser Richtlinie ist es, reproduzierbare, stabile und nachvollziehbare Arbeit mit der Cursor IDE und ihrer integrierten KI zu gewährleisten.  
Diese Regeln sollen sicherstellen, dass Änderungen konsistent bleiben, Module isoliert funktionieren und keine unbeabsichtigten Seiteneffekte entstehen.

---

### 1. **Verbindliche Grundregeln**
1. **Commit early, commit often**  
   Jeder funktionierende Zwischenstand wird sofort versioniert. So bleibt ein stabiler Kontext für Cursor erhalten.  
   *→ Empfohlen:* `git commit -m "Checkpoint: Modul X funktionsfähig"`  

2. **Keine Mehrfachaufgaben an die KI**  
   Pro Prompt nur **eine** Aufgabe.  
   > ❌ „Erstelle Logging, refactore DB und verbessere Auth.“  
   > ✅ „Erstelle Logging-Service mit File- und Console-Ausgabe.“  

3. **KI-Vorschläge sind Vorschläge, keine Wahrheit**  
   Vorschläge werden als Diff geprüft, nicht blind übernommen. Import- und Typfehler entstehen oft durch „schlaue“ Autovervollständigung.

---

### 2. **Kontextmanagement**
1. **Kontext bewusst auswählen**  
   Cursor nutzt einen begrenzten Kontextbereich. Nur relevante Dateien pinnen oder im Prompt benennen:  
   > „Bearbeite ausschließlich `src/services/authService.ts`“  

2. **Offene Tabs minimieren**  
   Zu viele offene Dateien führen zu veralteten Abhängigkeiten im KI-Kontext.  

3. **Modular arbeiten, aber Schnittstellen definieren**  
   Modularität bedeutet *klare Grenzen*:  
   - TypeScript: `export interface`, keine `export *`-Wildcards  
   - Python: klare `__init__.py`-Strukturen und `TypedDict`/`Protocol`

---

### 3. **Abhängigkeiten & Build-Konsistenz**
1. **Lockfiles nie manuell löschen oder ignorieren**  
   Cursor bezieht API- und Typinformationen direkt aus diesen Dateien.  
   Änderungen an `package.json`, `requirements.txt`, `tsconfig.json` etc. führen zu Kontextverschiebungen.

2. **Lokaler Build ist maßgeblich**  
   Cursor validiert nur Syntax, nicht Laufzeit. Immer lokal prüfen:  
   - JS/TS: `npm run build`  
   - Python: `pytest` / `python -m build`

3. **Keine Silent-Renames**  
   Nach jedem größeren KI-Commit `git diff` prüfen. Cursor benennt gelegentlich automatisch Funktionen oder Klassen um.

---

### 4. **Versionskontrolle & Rückverfolgbarkeit**
1. **Commit vor jedem KI-Refactor**  
   So lassen sich versehentlich zerstörte Module leicht zurückrollen.  

2. **Commit-Messages mit Kontext**  
   > Beispiel: `Refactor: Cursor Vorschlag zu AuthService angewendet`  
   So bleibt nachvollziehbar, woher bestimmte Änderungen stammen.

3. **Branching-Strategie nutzen**  
   Cursor-Experimente immer in eigenen Branches:  
   > `feature/ki-login-refactor`  
   > `experiment/ki-query-optimizer`

---

### 5. **Troubleshooting bei KI-Fehlern**
Wenn nach einer KI-Aktion etwas „nicht mehr geht“:
1. `git diff` prüfen – oft sind Barrel-Exports oder Pfade verändert.  
2. Lokalen Build laufen lassen.  
3. Cursor-Cache löschen (Command Palette → „Clear Editor Context“) und IDE neu starten.  
4. Bei wiederkehrenden Fehlern: Datei explizit ausschließen (`# KI nicht ändern` Kommentar oder `.cursorrules`-Eintrag).

---

### 6. **Erweiterte Hinweise für Teamarbeit**
- **Code Reviews sind Pflicht** bei KI-generierten Änderungen.  
- **Cursor-Änderungen immer kennzeichnen** im Commit (`[AI]` oder `[Cursor]`).  
- **Explizite Imports bevorzugen.** Keine impliziten Abhängigkeiten zwischen Modulen.  

---

### 7. **Philosophie**
Die KI ist kein Autopilot, sondern ein **kollaborativer Assistent**.  
Ziel ist nicht, dass Cursor „den Code schreibt“, sondern dass er Routinearbeit abnimmt, während das Architekturdenken beim Menschen bleibt.  
**KI kann Vorschläge machen – Verantwortung bleibt beim Entwickler.**
