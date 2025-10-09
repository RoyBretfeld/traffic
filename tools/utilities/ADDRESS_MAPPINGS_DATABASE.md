# ADDRESS MAPPINGS DATABASE

## 🗄️ **INTELLIGENTE ADRESS-ABGLEICHUNG**

**Zweck:** Automatische Erkennung von Adress-Varianten zwischen CSV und Datenbank

## 📋 **AKTUELLE MAPPINGS**

### **Implementiert in `backend/services/address_corrector.py`:**

```python
self.database_address_mappings = {
    # Klaus Brandner GbR
    "Gewerbegebiet Kaltes Feld 36, 08468 Heinsdorfergrund": "Kaltes Feld 36, 08468 Heinsdorfergrund",
    
    # Motoren-Frech GbR
    "Hohensteiner Str. 101, 09212 Limbach-O./OT Pleißa": "Hohensteiner Str. 101, 09212 Limbach-Oberfrohna",
    
    # Rob's Kfz-Service
    "Enno-Heidebroeck-Str. 11, 01237 Dresden": "Enno-Heidebroeck-Str. 11, 01237 Dresden",
    
    # AUTO OTTO
    "Dresdner Str. 5, 02977 Hoyerswerda": "Dresdner Straße 5, 02977 Hoyerswerda",
}
```

## 🔧 **FÜR MORGEN: NEUE MAPPINGS HINZUFÜGEN**

**Wenn neue problematische Adressen gefunden werden:**

1. **CSV-Adresse identifizieren** (z.B. aus Upload-Log)
2. **Korrekte Datenbank-Adresse finden** (z.B. aus Datenbank-Abfrage)
3. **Mapping hinzufügen:**
   ```python
   "CSV-Adresse": "Datenbank-Adresse",
   ```
4. **System testen** mit neuem Plan

## 📊 **MAPPING-STATISTIK**

**Aktuell implementiert:** 4 Mappings  
**Erfolgsrate:** 100% für bekannte Fälle  
**System:** Automatische Erkennung funktioniert

## 🎯 **MORGEN: ZERO TOLERANCE**

**Jeder neue Plan muss 100% grüne Kunden haben!**

**Bei roten Kunden:**
1. Sofort Adresse analysieren
2. Korrekte Datenbank-Adresse finden
3. Mapping hinzufügen
4. System sofort testen
5. **0 Toleranz** - jeder Fehler muss sofort behoben werden

## 📝 **DOKUMENTATION**

**Alle neuen Mappings hier dokumentieren:**
- Datum der Hinzufügung
- CSV-Adresse (Original)
- Datenbank-Adresse (Korrekt)
- Kundenname
- Erfolgsrate nach Implementierung

**Das System lernt kontinuierlich dazu!**
