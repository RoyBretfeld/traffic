# ROOT-CAUSE-ANALYSE: Wie ist das Mojibake entstanden?

## 🔍 **Der Mojibake-Entstehungsprozess**

### **Schritt 1: CSV-Export aus TEHA-System**
```
TEHA-System → CSV-Export → "Löbtauer Straße"
                    ↓
            Windows CP850 Encoding
                    ↓
            Bytes: 4C F6 62 74 61 75 65 72 20 53 74 72 61 DF 65
```

### **Schritt 2: Erste Fehlinterpretation**
```
CSV-Datei wird mit UTF-8 gelesen (falsch!)
                    ↓
            UTF-8 Decoder interpretiert CP850-Bytes als UTF-8
                    ↓
            Resultat: "L├Âbtauer Stra├üe" (Mojibake!)
```

### **Schritt 3: Doppelte Korruption**
```
Mojibake-String wird erneut mit CP850 gespeichert
                    ↓
            CP850 Encoder konvertiert Mojibake zu Bytes
                    ↓
            Bytes: 4C E2 94 AC C3 96 62 74 61 75 65 72 20 53 74 72 61 E2 94 AC C3 BC 65
```

### **Schritt 4: Endgültige Korruption**
```
Diese Bytes werden wieder mit UTF-8 gelesen
                    ↓
            UTF-8 Decoder interpretiert korrupte Bytes
                    ↓
            Resultat: "L┬btauer Stra┬ße" (Doppeltes Mojibake!)
```

## 🚨 **Warum ist das passiert?**

### **1. Fehlende Encoding-Standards**
- **Keine einheitliche Encoding-Policy**
- **Jeder Entwickler hat sein eigenes Encoding gewählt**
- **Keine Dokumentation der Encoding-Anforderungen**

### **2. Ad-hoc-Reparaturen statt Prävention**
- **Symptome werden behandelt, nicht die Ursache**
- **Reparatur-Funktionen verschleiern das Problem**
- **Keine Guards gegen Mojibake**

### **3. Fehlende Tests**
- **Keine Encoding-Roundtrip-Tests**
- **Keine Mojibake-Detection**
- **Keine Monitoring der Encoding-Qualität**

### **4. Windows/Linux Encoding-Konflikte**
- **Windows: CP850/CP1252 Standard**
- **Linux: UTF-8 Standard**
- **Keine plattformübergreifende Strategie**

## 🔧 **Wie verhindern wir das in Zukunft?**

### **1. Encoding-Policy etablieren**
```python
# EINZIGE Encoding-Policy für das gesamte System:
# 1. CSV-Eingang: CP850 (Windows-Standard)
# 2. Interne Verarbeitung: UTF-8 (Unicode-Standard)
# 3. Ausgabe: UTF-8 (Unicode-Standard)
# 4. Keine Ad-hoc-Reparaturen!
```

### **2. Zentraler CSV-Reader**
```python
# backend/utils/csv_reader.py
def read_csv_hardened(file_path):
    """EINZIGER CSV-Reader für das gesamte System"""
    # 1. CP850-Decodierung (einmalig)
    # 2. UTF-8-Normalisierung
    # 3. Mojibake-Guards
    # 4. Keine Reparaturen!
```

### **3. Encoding-Guards überall**
```python
# Nach jedem CSV-Ingest:
assert_no_mojibake(text)
trace_text("CSV_INGEST", text[:200])

# Vor jedem Geocoding:
assert_no_mojibake(address)
preview_geocode_url(address)
```

### **4. Automatische Tests**
```python
# tests/test_encoding_policy.py
def test_encoding_roundtrip():
    """Testet, dass Encoding-Roundtrip funktioniert"""
    # "Löbtauer Straße" → UTF-8 → UTF-8 = "Löbtauer Straße"
    
def test_no_mojibake_anywhere():
    """Testet, dass nirgendwo Mojibake entsteht"""
    # Simuliert gesamten Flow und prüft auf Mojibake
```

### **5. Monitoring und Alerting**
```python
# Logge alle Mojibake-Funde
# Zähle reparierte Adressen
# Überwache Geocoding-Erfolg
# Alert bei Encoding-Problemen
```

## 📋 **Konkrete Präventionsmaßnahmen**

### **1. Code-Review-Checkliste**
- [ ] Wird ein einheitlicher CSV-Reader verwendet?
- [ ] Sind Encoding-Guards implementiert?
- [ ] Werden Ad-hoc-Reparaturen vermieden?
- [ ] Sind Tests für Encoding-Roundtrip vorhanden?

### **2. CI/CD-Pipeline**
- [ ] Automatische Encoding-Tests
- [ ] Mojibake-Detection in jedem Build
- [ ] Encoding-Policy-Compliance-Check

### **3. Dokumentation**
- [ ] Encoding-Policy dokumentiert
- [ ] CSV-Reader-Usage dokumentiert
- [ ] Troubleshooting-Guide für Encoding-Probleme

### **4. Monitoring**
- [ ] Encoding-Qualität überwachen
- [ ] Geocoding-Erfolg messen
- [ ] Mojibake-Inzidenz tracken

## 🎯 **Fazit**

**Das Mojibake ist entstanden durch:**
1. **Fehlende Encoding-Standards**
2. **Ad-hoc-Reparaturen statt Prävention**
3. **Fehlende Tests und Guards**
4. **Plattform-spezifische Encoding-Konflikte**

**Die Lösung ist:**
1. **Einheitliche Encoding-Policy**
2. **Zentraler CSV-Reader**
3. **Encoding-Guards überall**
4. **Automatische Tests**
5. **Monitoring und Alerting**

**So verhindern wir das in Zukunft!**
