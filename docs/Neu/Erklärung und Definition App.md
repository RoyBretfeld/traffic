Um aus Ihrem bestehenden Prototypen eine vollwertige KI‑Routenplaner‑App zu machen, sollten Sie zwei Dinge parallel entwickeln: eine robuste Routen‑Logik und eine saubere KI‑Integration. Die Fachliteratur beschreibt den Vehicle‑Routing‑Problem‑(VRP‑)Kontext als ein komplexes Optimierungsproblem, das mehrere Fahrzeuge und Kunden mit Restriktionen wie Kapazität, Zeitfenstern und Servicezeiten gleichzeitig berücksichtigt
upperinc.com
. Moderne Software nutzt dazu heuristische Verfahren wie die Sweep‑Methode – man dreht ausgehend vom Depot einen „Strahl“ im Uhrzeigersinn, gruppiert alle Kunden, die in jedem Winkelbereich liegen, und erzeugt so erste Cluster
upperinc.com
. Anschließend berechnet man innerhalb jedes Clusters eine optimale Reihenfolge (TSP‑Problem). Die Sweep‑Heuristik eignet sich besonders für geografisch nah beieinanderliegende Kunden
upperinc.com
.

1. Backend‑Logik erweitern

Routenberechnungs‑API anbinden: Nutzen Sie Google Maps, HERE oder OpenRouteService, um Entfernungen und Fahrzeiten zwischen Depot (FAMO Dresden) und den Kunden sowie zwischen den Kunden zu erhalten. Die VRP‑Literatur empfiehlt für solche Aufgaben die Kombination von „kürzester‑Weg‑Algorithmen“ (etwa Dijkstra) mit höheren Optimierungsverfahren
upperinc.com
.

Koordinaten berechnen: Ihr Skript zum Parsen und Geokodieren der CSV‑Kundenliste ist bereits vorhanden. Nutzen Sie die „ASCII‑normalisierten“ Adressen für das Routing, aber speichern Sie auch die Originaladressen zur Darstellung.

Clustering – „Cluster First, Route Second“:

Sweep‑Heuristik: Berechnen Sie die Winkel aller Kunden relativ zum Depot. Sortieren Sie die Kunden nach diesem Winkel. Legen Sie die maximale Tourdauer als 60 Minuten plus 2 Minuten Verweilzeit pro Kunde fest. Addieren Sie sukzessive die Fahrzeiten und die 2‑Minuten‑Pausen; sobald der 60‑Minuten‑Schwellwert erreicht wird, beginnt ein neuer Cluster.

Alternative K‑Means: Wenn die Kunden in sehr unterschiedlichen Himmelsrichtungen liegen, kann K‑Means‑Clustering auf Basis der GPS‑Koordinaten genutzt werden. Die Anzahl der Cluster wird über die Zeitbedingung (60 Minuten + Servicezeiten) bestimmt.

Feinrouting je Cluster: Für jede Gruppe von Stops lösen Sie das Travel‑Salesman‑Problem (TSP) mit Einschränkungen. Ein einfacher Ansatz ist die Nearest‑Neighbor‑Heuristik, bei der immer der nächstgelegene unbesuchte Kunde gewählt wird, obwohl diese Methode mitunter schlechtere Ergebnisse liefert
upperinc.com
. Bessere Ergebnisse liefern metaheuristische Verfahren wie Simulated Annealing, genetische Algorithmen oder Ant‑Colony‑Optimization
upperinc.com
 – solche Verfahren sind in vielen Routing‑Bibliotheken implementiert.

Bar‑Regel: In Ihren Daten sind BAR‑Kunden besonders markiert. Diese werden im selben Cluster wie die zeitlich zugehörige Haupttour geführt, aber im Frontend orange dargestellt. Das Skript legt eine Spalte bar = True für diese Kunden an.

Zwei‑Minuten‑Servicezeiten: Addieren Sie für jeden Kunden 2 Minuten Aufenthalt zum Fahrtzeitwert. Diese Pufferzeit geht in die Cluster‑Zuweisung und später in die ETA‑Berechnung ein.

2. KI‑Integration (GPT)

Die Projektvorgaben verlangen, dass GPT jede Routenanfrage verarbeitet
upperinc.com
. Das bedeutet:

Prompt‑Logik: Das Backend erstellt eine Eingabeaufforderung, die die Kundenliste (mit Koordinaten), die bereits durch die heuristische Clustering‑Logik geordneten Routen und alle Restriktionen (max. 60 Minuten pro Tour, 2 Minuten Servicezeit, Bar‑Kunden markiert) enthält.

Routen‑Optimierung und Erläuterung: GPT kann dabei zwei Aufgaben übernehmen:

Qualitätskontrolle und Feintuning: Das Modell bewertet die vom Heuristik‑Modul vorgeschlagenen Cluster und schlägt bei Bedarf Verbesserungen vor, indem es Stopps verschiebt, um Zeit einzusparen oder Lieferfenster besser auszunutzen.

Erklärende Kommentare: GPT formuliert anschließend für jede Route eine menschlich verständliche Zusammenfassung („KI‑Kommentar“). Zum Beispiel könnte es die Verkehrsverhältnisse erklären oder beschreiben, warum ein bestimmter Kunde ans Ende der Route gestellt wurde.

Prompt‑Versionierung und Logging: Speichern Sie jede Eingabe an GPT zusammen mit der Rückmeldung, um die Nachvollziehbarkeit zu gewährleisten, wie in Ihren Arbeitsprompts gefordert.

3. Frontend‑Umsetzung

UI‑Komponenten: Nutzen Sie die vorhandene Desktop‑GUI als Blaupause und übertragen Sie sie ins Web (React + Leaflet). Jede Tour bekommt einen Tab oder eine Karte, auf der die Stopps nummeriert und farblich (BAR‑Kunden orange) dargestellt sind.

Interaktive Karte: Zeigen Sie die generierten Routen an, markieren Sie den Startpunkt FAMO, und stellen Sie pro Tour ETA, Anzahl Kunden, Gesamtdistanz und Gesamtdauer (inkl. 2‑Minuten‑Pausen) dar.

CSV‑Upload & Export: Lassen Sie den Anwender eine CSV hochladen, parsen Sie die Daten mit Ihrem Skript und zeigen Sie eine Vorschau. Exportieren Sie Ergebnisse als PDF/CSV.

4. Nächste Schritte

API‑Schlüssel beschaffen (Google, HERE oder OpenRouteService) und die notwendigen Routing‑Endpoints anbinden.

Clustering‑Modul implementieren: Beginnen Sie mit der Sweep‑Heuristik; testen Sie K‑Means als Alternative.

GPT‑Integration: Binden Sie die OpenAI‑API im Backend an, implementieren Sie Logging, Prompt‑Versionierung und Tokenkontrolle gemäß Ihrer System‑ und Arbeitsprompts.

Feinkalibrierung: Validieren Sie das Zeitmodell (Reise‑ plus Servicezeiten), passen Sie Schwellenwerte gegebenenfalls an, und testen Sie die Touren mit echten Daten.

Durch diese Kombination aus bewährten heuristischen Verfahren für die Routenberechnung und einer GPT‑basierten Intelligenzschicht, die Erklärung und Finetuning liefert, entsteht eine dynamische, erklärbare Routenplanung. Laut Branchenanalyse können KI‑basierte VRP‑Lösungen die Effizienz um 10–25 % steigern
upperinc.com
; gleichzeitig tragen Methoden wie die Sweep‑Heuristik dazu bei, geografisch nahe Kunden sinnvoll zu gruppieren
upperinc.com
 und damit die 60‑Minuten‑Regel inklusive der 2‑Minuten‑Verweilzeit einzuhalten.