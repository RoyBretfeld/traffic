# Admin-Login Anleitung

**Stand:** 2025-11-22  
**Status:** ✅ **Aktuell und funktionsfähig**

---

## 🚀 Schnellstart

### 1. Admin-Bereich öffnen

```
http://localhost:8111/admin.html
```

### 2. Login-Daten

**Standard-Admin (falls erstellt):**
- **Benutzername:** `Bretfeld`
- **Passwort:** `Lisa01Bessy02`

**Oder:** Eigene Admin-Benutzer aus der Datenbank

---

## 📋 Login-Schritte

1. **Öffne Admin-Seite:**
   - URL: `http://localhost:8111/admin.html`
   - Oder über Navigation: Klicke auf "Admin" im Hauptmenü

2. **Login-Formular:**
   - Benutzername eingeben
   - Passwort eingeben
   - "Anmelden" klicken

3. **Bei erfolgreichem Login:**
   - Du wirst zum Admin-Dashboard weitergeleitet
   - Session-Cookie wird gesetzt (24 Stunden gültig)

---

## ⚠️ Wichtige Hinweise

### Rate-Limiting

**Neu seit 2025-11-22:**
- Max. **10 Login-Versuche** pro **15 Minuten** pro IP
- Bei zu vielen Fehlversuchen: HTTP 429 (Too Many Requests)
- **Erfolgreiche Logins werden NICHT gezählt!**

**Wenn Rate-Limit erreicht:**
- Warte 15 Minuten
- Oder Server neu starten (Rate-Limit wird zurückgesetzt)
- Oder ENV setzen: `LOGIN_RATE_LIMIT_MAX=100` für Tests

### Cookie SameSite=Strict

**Neu seit 2025-11-22:**
- Cookie wird nur bei same-site Requests gesendet
- **Lokale Entwicklung:** Funktioniert normal (localhost ist same-site)
- **Cross-Site:** Cookie wird nicht gesendet (Sicherheit)

### CORS

**Neu seit 2025-11-22:**
- **Development:** Alle Origins erlaubt (lokale Entwicklung)
- **Production:** Nur erlaubte Domains (über `CORS_ALLOWED_ORIGINS`)

---

## 🔧 Admin-Benutzer erstellen

### Initialen Admin erstellen

```bash
python scripts/create_initial_admin_user.py
```

**Standard-Credentials:**
- Benutzername: `Bretfeld`
- Passwort: `Lisa01Bessy02`

**Oder über ENV:**
```bash
export INITIAL_ADMIN_USERNAME=MeinAdmin
export INITIAL_ADMIN_PASSWORD=MeinPasswort
python scripts/create_initial_admin_user.py
```

### Weitere Admin-Benutzer

**Über Admin-Interface:**
1. Als Admin einloggen
2. Tab "Benutzerverwaltung" öffnen
3. "Neuen Benutzer erstellen" klicken
4. Benutzerdaten eingeben
5. Rolle: "Admin" wählen

---

## 🐛 Troubleshooting

### Problem: "Ungültiger Benutzername oder Passwort"

**Lösung:**
1. Prüfe ob Benutzer existiert:
   ```bash
   python scripts/debug_user_login.py
   ```
2. Prüfe Passwort-Hash in Datenbank
3. Erstelle neuen Admin-Benutzer falls nötig

### Problem: "Zu viele Login-Versuche"

**Lösung:**
1. Warte 15 Minuten
2. Oder Server neu starten
3. Oder ENV setzen: `LOGIN_RATE_LIMIT_MAX=100`

### Problem: Cookie wird nicht gesetzt

**Lösung:**
1. Prüfe Browser-Konsole für Fehler
2. Prüfe ob du auf `localhost` zugreifst (nicht Cross-Site)
3. Prüfe Browser-Einstellungen (Cookies erlauben)
4. Prüfe ob HTTPS in Production verwendet wird

### Problem: CORS-Fehler

**Lösung:**
1. Prüfe `APP_ENV` - sollte `development` sein für lokale Entwicklung
2. Oder setze `CORS_ALLOWED_ORIGINS` mit deiner Domain

---

## 📊 Session-Verwaltung

### Session-Dauer

**Standard:** 24 Stunden

**Konfigurierbar:**
```bash
export ADMIN_SESSION_DURATION_HOURS=8
```

### Session prüfen

**Über API:**
```bash
curl http://localhost:8111/api/auth/status
```

**Response:**
```json
{
  "authenticated": true,
  "user": {
    "id": 1,
    "username": "Bretfeld",
    "role": "admin"
  }
}
```

### Session beenden

**Über Admin-Interface:**
- Klicke auf "Abmelden"

**Über API:**
```bash
curl -X POST http://localhost:8111/api/auth/logout
```

---

## 🔐 Sicherheit

### Passwort ändern

**Über Admin-Interface:**
1. Tab "Benutzerverwaltung"
2. Benutzer auswählen
3. "Passwort ändern" klicken
4. Neues Passwort eingeben

### Passwort zurücksetzen

**Falls Passwort vergessen:**
1. Neuen Admin-Benutzer erstellen
2. Oder Passwort direkt in Datenbank ändern (nicht empfohlen)

---

## 📝 Checkliste für morgen

- [ ] Server starten: `python start_server.py`
- [ ] Admin-Seite öffnen: `http://localhost:8111/admin.html`
- [ ] Login-Daten eingeben (siehe oben)
- [ ] Bei Problemen: Siehe Troubleshooting

---

**Wichtig:** Alle Security-Änderungen sind **rückwärtskompatibel** und sollten die normale Nutzung nicht beeinträchtigen!

**Bei Problemen:** Siehe `docs/SECURITY_AENDERUNGEN_2025-11-22.md` für Details.

