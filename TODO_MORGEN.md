# TODO für morgen (19. November 2025)

## ✅ Route-Linien schmaler machen - ERLEDIGT (20. November 2025)

**Problem:** Routen-Linien sind zu dick/fett

**Aktuelle Einstellungen:**
- OSRM-Routen: `weight: 6`, `opacity: 0.9`
- Fallback-Linien: `weight: 3`, `opacity: 0.7`

**Zu ändern:**
- OSRM-Routen: `weight: 4` (statt 6)
- Fallback-Linien: `weight: 2` (statt 3)

**Dateien:**
- `frontend/index.html` (mehrere Stellen)

**Zu ändernde Stellen:**

1. **OSRM-Routen (JavaScript):**
   - Zeile 4425: `weight: 6` → `weight: 4`
   - Zeile 4426: `opacity: 0.9` → `opacity: 0.8` (optional, für bessere Sichtbarkeit)

2. **CSS für OSRM-Routen:**
   - Zeile 61: `stroke-width: 6px !important;` → `stroke-width: 4px !important;`
   - Zeile 66: `stroke-width: 6px !important;` → `stroke-width: 4px !important;`

3. **Fallback-Linien (JavaScript):**
   - Zeile 4844: `weight: 3` → `weight: 2`

4. **CSS für Fallback-Linien:**
   - Zeile 72: `stroke-width: 3px !important;` → `stroke-width: 2px !important;`
   - Zeile 76: `stroke-width: 3px !important;` → `stroke-width: 2px !important;`

**Schritte:**
1. Öffne `frontend/index.html`
2. Ändere JavaScript `weight`-Werte (Zeile 4425)
3. Ändere CSS `stroke-width`-Werte (Zeilen 61, 66, 72, 76)
4. Teste im Browser: Routen sollten schmaler, aber noch sichtbar sein

---

**Erstellt:** 2025-11-18 21:20  
**Erledigt:** 2025-11-20  
**Status:** ✅ Alle Änderungen umgesetzt und getestet

