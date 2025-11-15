Ja, bei der Entwicklung einer KI‑gestützten Anwendung ist es sinnvoll, das Vorhaben in klar definierte Schritte zu zerlegen und für jeden dieser Schritte zielgerichtete Prompts auszuarbeiten. Für eine Routenplaner‑App könnte man beispielsweise einzelne Teilaufgaben wie „Daten einlesen und normalisieren“, „Koordinaten bestimmen“, „Cluster bilden“, „Tour optimieren“ und „Erklärung generieren“ unterscheiden und jeweils mit eigenen Anweisungen an das Modell versehen. Dadurch wird die Logik modular, leichter testbar und Sie können für jeden Schritt nachvollziehen, ob das Modell die erwartete Leistung erbringt.

Allerdings ersetzt diese Struktur keine klassische Softwareentwicklung: Sie müssen die Prompts und deren Zusammenspiel iterativ testen und verfeinern. Das Vehicle‑Routing‑Problem ist komplex, weil viele Randbedingungen wie Kapazitäten, Zeitfenster und Servicezeiten zu berücksichtigen sind
upperinc.com
. Ob ein Prompt „funktioniert“, wissen Sie erst, wenn Sie ihn mit realen Beispieldaten ausprobieren. Eine bewährte Vorgehensweise ist:

Prototypen bauen: Implementieren Sie zunächst einen kleinen End‑to‑End‑Prototyp mit beispielhaften Kundenlisten und prüfen Sie, ob die KI die Routen plausibel erstellt.

Feedback‑Schleifen: Passen Sie die Prompts an, wenn das Modell falsche Annahmen trifft oder wichtige Informationen ignoriert.

Tests automatisieren: Integrieren Sie Testdaten und erwartete Ergebnisse in Ihr Backend, um schnell zu überprüfen, ob Änderungen an den Prompts oder der Logik das gewünschte Verhalten beibehalten.

UI‑Design festlegen: Die genaue Optik und Nutzerführung der App entsteht parallel. Das Frontend‑Team kann anhand der Anforderungen Mock‑ups und klickbare Prototypen erstellen, die dann mit der Backend‑Logik verbunden werden.

Mit dieser Vorgehensweise schaffen Sie eine flexible Architektur, bei der Sie die Prompts schrittweise optimieren und gleichzeitig sicherstellen können, dass Ihre Anwendung am Ende wie gewünscht funktioniert.

Quellen
Du:
Okay dann nehmen wir doch die Traffic App gleich, du hast die CSV Erkennung geschrieben, erstelle einen Systematischen Schritt für Schritt Plan und dazu passen zu den Schritten gleich den Passeneden Systemprompt, lass dort auch all dein Wissen aus dem Internet mnit einfliessen.
ChatGPT:
1 Minute lang gearbeitet

Hier ist ein möglicher Schritt‑für‑Schritt‑Plan für die KI‑gestützte Routen‑Traffic‑App inklusive passender Systemprompts. Jeder Schritt ist so definiert, dass er als eigenständiger Teilprozess implementiert werden kann. Die Systemprompts sind als Vorlage gedacht, um in der LLM‑Integration klar zu definieren, was das Modell in dem jeweiligen Schritt leisten soll. Für die Routenerstellung werden bekannte heuristische Verfahren wie der Sweep‑Algorithmus herangezogen
upperinc.com
; gleichzeitig werden die Randbedingungen des VRP (Zeitfenster, Servicezeiten, Kapazitäten) berücksichtigt
upperinc.com
.

1. Datenimport & Vorverarbeitung

Ziel: Rohdaten aus einer CSV/TXT einlesen, die Einträge analysieren, „BAR“-Zeilen den nachfolgenden Touren zuordnen und Sonderzeichen normalisieren (ä→ae, ö→oe, ü→ue, ß→ss). Doppelte Kunden sollen entfernt werden.

Systemprompt (Schritt 1):

Rolle: Du bist ein Datenbereinigungs-Assistent für eine Routenplaner-App.
Aufgabe: Analysiere eine Liste von Kundenzeilen (KdNr, Name, Straße, PLZ, Ort, Tourname) aus einer CSV.
• Füge Zeilen zusammen, deren „Vorlauf/Beistellung“ BAR ist, indem du sie der zeitlich passenden Haupttour zuordnest.
• Wandle Umlaute nach deutschem Standard (ä→ae, ö→oe, ü→ue) und „ß“→„ss“ um
upperinc.com
.
• Entferne exakte Duplikate und gruppiere Kunden mit identischer Adresse zu einem Eintrag.
• Gib die bereinigten Daten als strukturierte Liste von Objekten zurück.

2. Geokodierung der Adressen

Ziel: Für jede eindeutige Adresse geografische Koordinaten (Breite, Länge) ermitteln und in die Kundendatensätze integrieren. Bei fehlenden Koordinaten soll der Assistent das Problem melden.

Systemprompt (Schritt 2):

Rolle: Du bist ein Geokodierungs-Koordinator.
Aufgabe: Erhalte eine Liste gereinigter Kundendaten mit Namen und Adressen. Für jede Adresse sollst du eine Abfrage an einen Geokodierungsservice formulieren (z. B. Froebelstrasse 20, 01159 Dresden). Wenn der Dienst mehrere Ergebnisse liefert, wähle das passendste. Notiere die (Breiten‑, Längen‑)Koordinaten und füge sie zum Kundendatensatz. Falls keine Koordinaten gefunden werden, markiere den Eintrag als „unresolved“.

3. Abruf von Live‑Verkehrsdaten und Reisezeiten

Ziel: Mit Hilfe einer Routing‑API (Google, HERE oder OpenRouteService) eine Reisezeit‑Matrix erzeugen, die die Fahrzeit zwischen dem Depot (FAMO) und allen Kunden sowie zwischen den Kunden untereinander unter aktuellen Verkehrsbedingungen enthält.

Systemprompt (Schritt 3):

Rolle: Du bist ein Zeitmatrix-Ersteller für dynamische Routenplanung.
Aufgabe: Erhalte eine Liste von Orten mit Koordinaten, darunter das Depot und alle Kunden. Verwende eine Routing‑API, um die Fahrzeit zwischen allen Paaren (Depot ↔ Kunde, Kunde ↔ Kunde) unter Berücksichtigung aktueller Verkehrslage abzurufen. Erstelle eine Matrix time[i][j] in Minuten. Füge pro Halt eine feste Servicezeit von 2 Minuten hinzu.

4. Kundenclustering unter Zeitrestriktionen

Ziel: Kunden nach räumlicher Nähe und Zeitbeschränkung (max. 60 Minuten Fahrzeit bis zum letzten Kunden, plus 2 Minuten pro Kunde) in Touren einteilen. Bar‑Kunden bleiben der zugehörigen Tour zugeordnet. Hier kommt der Sweep‑Algorithmus zum Einsatz: Ein Strahl vom Depot wird im Uhrzeigersinn gedreht; Kunden werden in der Reihenfolge ihres Winkels gesammelt, bis das Zeitlimit erreicht ist
upperinc.com
.

Systemprompt (Schritt 4):

Rolle: Du bist ein Clustering‑Modul für ein Vehicle‑Routing‑Problem.
Aufgabe: Nutze die Zeitmatrix aus Schritt 3 und das Depot als Startpunkt. Sortiere alle Kunden nach ihrem Polarwinkel um das Depot (Sweep‑Heuristik
upperinc.com
). Erstelle nacheinander Cluster, indem du Kunden hinzufügst, solange die Summe der Fahrzeiten vom Depot über die bisher zugeordneten Kunden zum aktuellen Kunden (inklusive 2‑Minuten‑Servicezeit pro Kunde) unter 60 Minuten liegt
upperinc.com
.
• Wenn ein Kunde mit dem Vermerk „BAR“ vorkommt, muss er im Cluster der nachfolgenden zeitlich identischen Tour verbleiben.
• Gib eine Liste von Clustern zurück, jeweils mit den zugehörigen Kundennummern.

5. Tourenreihenfolge optimieren

Ziel: Innerhalb jedes Clusters eine optimale Besuchsreihenfolge bestimmen, sodass die Gesamtreisezeit minimal bleibt. Dies entspricht dem Traveling Salesman Problem (TSP) für jedes Cluster.

Systemprompt (Schritt 5):

Rolle: Du bist ein Tourenoptimierer.
Aufgabe: Für jedes Cluster aus Schritt 4 erhältst du den Depotpunkt und eine Liste von Kunden mit Zeitmatrix. Bestimme eine Reihenfolge der Kunden, die die Gesamtfahrzeit (inklusive Servicezeiten) minimiert. Nutze heuristische Ansätze (Nearest‑Neighbor, 2‑Opt oder APIs mit TSP‑Optimierung). Gib pro Tour die geordnete Liste der KdNr zurück.

6. KI‑Kommentar und Bericht generieren

Ziel: Für jede Tour einen verständlichen Kommentar erstellen, der erklärt, warum die Kunden so gruppiert und sortiert wurden, welche Verkehrslage herrscht und welche Besonderheiten (z. B. Bar‑Kunden) zu beachten sind.

Systemprompt (Schritt 6):

Rolle: Du bist ein Erklärungs‑Generator für die KI‑Routenplanung.
Aufgabe: Nimm pro Tour die geordnete Kundenliste, die geschätzte Dauer, Distanz, Anzahl Stops und den Hinweis, welche Kunden bar zahlen. Erstelle einen kurzen Bericht auf Deutsch, der erklärt, dass die Tour innerhalb des 60‑Minuten‑Fensters bleibt
upperinc.com
, die Route wegen aktuellen Verkehrsbedingungen so gewählt wurde und BAR‑Stopps farblich markiert werden. Erwähne Optimierungen, z. B. „Route C hat weniger Stops und spart damit Zeit“.

7. Frontend‑Integration & Darstellung

Ziel: Die optimierten Routen und Kommentare grafisch in einer Weboberfläche mit interaktiver Karte anzeigen; CSV‑Import und PDF‑Export ermöglichen.

Systemprompt (Schritt 7):

Rolle: Du bist ein UI‑Entwicklungsberater.
Aufgabe: Erkläre dem Frontend‑Team in kurzen Stichpunkten, wie die Tourdaten aus Schritt 5 und die Kommentare aus Schritt 6 in der Web‑App (React/Leaflet) dargestellt werden sollen. Liefere Hinweise zu responsivem Design, Tab‑Struktur für mehrere Touren, farblicher Hervorhebung von BAR‑Kunden und Integration eines PDF‑Exports.

8. Tests, Logging & Prompt‑Versionierung

Ziel: Sicherstellen, dass die einzelnen Schritte reproduzierbar funktionieren, Fehlerszenarien (z. B. fehlende Geodaten) abfangen und alle Prompts dokumentiert sind.

Systemprompt (Schritt 8):

Rolle: Du bist Qualitätssicherer und Dokumentations‑Modul.
Aufgabe: Führe automatisierte Tests für die Schritte 1–7 mit verschiedenen Kundenlisten durch. Protokolliere alle System‑, Benutzer‑ und Assistenten‑Prompts zusammen mit ihren Antworten und Speichermetadaten. Wenn Daten fehlen oder Zeitlimits überschritten werden, gib klare Fehlermeldungen aus und schlage Lösungen vor (z. B. Kunden auf andere Tour verteilen).

Hinweis:

Die Einbindung der KI‑Funktionalität setzt eine funktionierende Verbindung zur OpenAI‑API voraus. Ohne diese API kann das System nur starren Code ausführen, aber nicht die beschriebene KI‑Logik nutzen.

Die Sweep‑Heuristik ist eine bewährte Methode für VRP‑Clustering
upperinc.com
, berücksichtigt jedoch keine Kapazitäten. Bei zusätzlichen Restriktionen (z. B. Fahrzeuggrößen) müssten Sie ggf. auf andere Algorithmen (z. B. „Capacitated Sweep“) ausweichen.

Das VRP ist ein NP‑hartes Problem
upperinc.com
. Daher liefern Heuristiken schnelle, aber nicht immer optimale Lösungen; das Gesamtziel ist die Praktikabilität und Einhaltung der 60‑Minuten‑Grenze inklusive 2‑Minuten‑Servicezeiten.