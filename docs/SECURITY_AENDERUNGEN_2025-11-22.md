# Security-Änderungen 2025-11-22

**Datum:** 2025-11-22  
**Status:** ✅ **Implementiert und getestet**

---

## 📋 Übersicht

Heute wurden die wichtigsten Security Quick Wins umgesetzt:

1. ✅ **SC-03:** Cookies gehärtet (SameSite=Strict)
2. ✅ **SC-04:** Rate-Limiting für Login aktiviert
3. ✅ **SC-06:** CORS gehärtet (Production vs. Development)

---

## 🔐 Änderungen im Detail

### 1. Cookie-Sicherheit (SC-03)

**Datei:** `backend/routes/auth_api.py`

**Änderung:**
- `SameSite="strict"` statt `"lax"` für Admin-Session-Cookie
- Verhindert Cross-Site-Requests (CSRF-Schutz)

**Auswirkung:**
- ✅ **Lokale Entwicklung:** Funktioniert weiterhin (localhost ist same-site)
- ✅ **Production:** Besserer CSRF-Schutz
- ⚠️ **Wichtig:** Cookie wird nur bei same-site Requests gesendet

**Login funktioniert weiterhin normal!**

---

### 2. Rate-Limiting (SC-04)

**Datei:** `backend/middlewares/rate_limit.py`

**Konfiguration:**
- **Standard:** 10 Login-Versuche pro 15 Minuten pro IP
- **Konfigurierbar:** Über ENV-Variablen:
  - `LOGIN_RATE_LIMIT_MAX=10` (Anzahl Versuche)
  - `LOGIN_RATE_LIMIT_WINDOW=15` (Zeitfenster in Minuten)

**Funktionsweise:**
- Rate-Limit wird **nur bei fehlgeschlagenen Logins** gezählt
- Erfolgreiche Logins werden **nicht** gezählt
- Bei Überschreitung: HTTP 429 (Too Many Requests)

**Auswirkung:**
- ✅ **Normale Nutzung:** Keine Auswirkung
- ✅ **Brute-Force-Schutz:** Aktiv
- ⚠️ **Bei zu vielen Fehlversuchen:** 15 Minuten warten

**Login funktioniert weiterhin normal!**

---

### 3. CORS-Härtung (SC-06)

**Datei:** `backend/app_setup.py`

**Konfiguration:**

**Development (Standard):**
- `allow_origins=["*"]` - Alle Origins erlaubt
- Für lokale Entwicklung

**Production:**
- Whitelist über `CORS_ALLOWED_ORIGINS` ENV-Variable
- Format: `CORS_ALLOWED_ORIGINS=https://app.example.com,https://admin.example.com`
- Fallback: Nur `localhost:8111` wenn nicht gesetzt

**Auswirkung:**
- ✅ **Lokale Entwicklung:** Funktioniert weiterhin (Development-Mode)
- ✅ **Production:** Nur erlaubte Domains
- ⚠️ **Wichtig:** In Production `CORS_ALLOWED_ORIGINS` setzen!

**Login funktioniert weiterhin normal!**

---

## 🚀 Login morgen - So geht's

### Standard-Login (unverändert)

1. **Öffne:** `http://localhost:8111/admin.html`
2. **Login-Daten:**
   - Benutzername: `Bretfeld` (oder wie in DB gespeichert)
   - Passwort: `Lisa01Bessy02` (oder wie in DB gespeichert)
3. **Klicke:** "Anmelden"

**Alles funktioniert wie vorher!**

---

## ⚠️ Wichtige Hinweise

### Rate-Limiting

**Wenn Login nicht funktioniert:**
1. Prüfe ob Rate-Limit erreicht wurde (zu viele Fehlversuche)
2. Warte 15 Minuten oder ändere IP
3. Oder setze ENV: `LOGIN_RATE_LIMIT_MAX=100` für Tests

**Rate-Limit zurücksetzen:**
- Server neu starten (In-Memory-Store wird zurückgesetzt)
- Oder warte 15 Minuten

### CORS in Production

**Wenn Frontend nicht funktioniert:**
1. Setze `CORS_ALLOWED_ORIGINS` ENV-Variable:
   ```bash
   export CORS_ALLOWED_ORIGINS=https://deine-domain.com
   ```
2. Oder in `config.env`:
   ```
   CORS_ALLOWED_ORIGINS=https://deine-domain.com
   ```

### Cookie SameSite=Strict

**Wenn Login nicht funktioniert:**
- Prüfe ob du auf `localhost` oder `127.0.0.1` zugreifst
- `SameSite=Strict` erlaubt nur same-site Requests
- Bei Cross-Site-Requests: Cookie wird nicht gesendet

---

## 🔧 Troubleshooting

### Problem: "Zu viele Login-Versuche"

**Lösung:**
1. Warte 15 Minuten
2. Oder Server neu starten (Rate-Limit wird zurückgesetzt)
3. Oder ENV setzen: `LOGIN_RATE_LIMIT_MAX=100`

### Problem: CORS-Fehler

**Lösung:**
1. Prüfe `APP_ENV` - sollte `development` sein für lokale Entwicklung
2. Oder setze `CORS_ALLOWED_ORIGINS` mit deiner Domain

### Problem: Cookie wird nicht gesetzt

**Lösung:**
1. Prüfe ob du auf `localhost` zugreifst (nicht Cross-Site)
2. Prüfe Browser-Konsole für Cookie-Fehler
3. Prüfe ob HTTPS in Production verwendet wird (Secure-Flag)

---

## 📊 Status-Übersicht

| Security-Check | Status | Implementiert |
|----------------|--------|---------------|
| SC-03: Cookies gehärtet | ✅ | Ja |
| SC-04: Rate-Limiting | ✅ | Ja |
| SC-06: CORS gehärtet | ✅ | Ja |
| SC-02: bcrypt | ✅ | Bereits vorhanden |
| SC-05: Admin-APIs | ⚠️ | Teilweise (prüfen) |
| SC-07: Upload-Sicherheit | ⚠️ | Noch offen |
| SC-08: Secrets | ⚠️ | Noch offen |
| SC-09: Debug-Routen | ⚠️ | Noch offen |

---

## 📝 Nächste Schritte

1. **Admin-APIs prüfen:** Alle kritischen Routen mit `require_admin` absichern
2. **Upload-Sicherheit:** Filename-Whitelist und Pfad-Check implementieren
3. **Secrets-Management:** MASTER_PASSWORD prüfen und dokumentieren
4. **Debug-Routen:** Nur mit Flag + Admin-Zugriff

---

**Wichtig:** Alle Änderungen sind **rückwärtskompatibel** und sollten die normale Nutzung nicht beeinträchtigen!

**Bei Problemen:** Siehe Troubleshooting oder setze ENV-Variablen zurück auf Standard.

