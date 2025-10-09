# CSV-Analyse Prompt für KI

## Problem
Die FAMO TrafficApp hat 21 CSV-Dateien im `tourplaene/` Verzeichnis, aber der CSV Bulk Processor zeigt nur 182 Kunden an. Das ist viel zu wenig!

## Erwartung
- **21 CSV-Dateien** sollten **1000+ Kunden** ergeben
- Jede CSV-Datei enthält **mehrere Touren** (W-07.00 Uhr BAR, W-07.00 Uhr Tour, PIR Anlief. 7.45 Uhr, etc.)
- Jede Tour hat **10-20 Kunden**

## CSV-Struktur
```
Tourenübersicht;;;;;
Lieferdatum: 14.08.25;;;;;
;;;;;
Kdnr;Name;Straße;PLZ;Ort;Gedruckt
;W-07.00 Uhr BAR;;;;
5023;Stockmann KFZ-Service;Cowaplast 28;01640;Coswig;1
4590;Fahrzeugservice u.;Grenzstr. 9;01640;Coswig;1
;;;;;
;W-07.00 Uhr Tour;;;;
4772;Dresdner Klassiker Handel GmbH;Königsbrücker Straße 96;01099;Dresden;1
5119;Gomodrom Automobile;Kesselsdorfer Str. 99;01159;Dresden;1
...
;;;;;
;PIR Anlief. 7.45 BAR;;;;
40179;Bauservice Tilo Richter;Bielatalstraße 34;01824;Königstein;1
...
```

## Was die KI tun soll
1. **Alle CSV-Dateien analysieren** und **jede Zeile zählen**
2. **Tour-Header erkennen** (W-.*Uhr, PIR.*Uhr, PIR.*BAR, etc.)
3. **Kunden zählen** (Zeilen mit Name + Straße, aber nicht Header)
4. **Eindeutige Kunden** erkennen (keine Duplikate)
5. **Detaillierte Statistiken** ausgeben

## Gewünschte Ausgabe
```
📊 CSV-ANALYSE ERGEBNIS
========================
📁 CSV-Dateien: 21
📄 Gesamte Zeilen: 2.500+
👥 Gesamte Kunden: 1.200+
🔄 Eindeutige Kunden: 800+
🚗 Touren: 100+
📈 Durchschnitt: 60 Kunden pro Datei
```

## Code-Ansatz
```python
# 1. Alle CSV-Dateien finden
csv_files = list(Path("tourplaene").glob("*.csv"))

# 2. Jede Datei analysieren
for csv_file in csv_files:
    df = pd.read_csv(csv_file, encoding='utf-8')
    
    # 3. Tour-Header finden
    tour_headers = df[df['Name'].str.contains('W-.*Uhr|PIR.*Uhr|PIR.*BAR', na=False, regex=True)]
    
    # 4. Kunden zählen
    customers = df[(df['Name'].notna()) & (df['Straße'].notna()) & 
                   (~df['Name'].str.contains('W-.*Uhr|PIR.*Uhr|PIR.*BAR', na=False, regex=True))]
```

## Ziel
**Schnelle, genaue Analyse** aller CSV-Daten ohne Umwege!
