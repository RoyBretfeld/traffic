# Security Checklist – TrafficApp 3.0

**Zweck:** Schnell abhakbare Punkte für Reviews/PRs. Jede Zeile ist ein Muss-Kriterium.

**Stand:** 2025-11-22

---

## Authentication & Authorization

- [ ] [SC-01] Keine Default-Admin-Credentials im Code
- [ ] [SC-02] Passwörter mit argon2/bcrypt (kein SHA‑256), Salt & Verify
- [ ] [SC-03] Cookies: HttpOnly + Secure (Prod) + SameSite=Strict
- [ ] [SC-04] Login-Rate-Limit aktiv (z. B. 5–10 Versuche/15 min/IP)
- [ ] [SC-05] Alle Admin-APIs abgesichert: `Depends(require_admin_auth)`
- [ ] [SC-15] CSRF-Schutz (bei Cookie-Auth) **oder** Wechsel auf Bearer-Token

## Network & CORS

- [ ] [SC-06] CORS: nur erlaubte Origins (kein `*` mit Credentials)

## File Uploads

- [ ] [SC-07] Uploads: Dateiname-Whitelist, `resolve()`-Check, Größen- & MIME-Limits

## Secrets & Configuration

- [ ] [SC-08] Secrets: `MASTER_PASSWORD` ohne produktiven Default; `.env`/`secure_keys.json` nicht im Repo

## Debug & Testing

- [ ] [SC-09] Debug-/Test-Routen nur via Flag + Admin; in Prod standardmäßig aus

## Logging & Privacy

- [ ] [SC-10] Logging: keine PII/Secrets; Retention-Policy dokumentiert

## Security Headers

- [ ] [SC-11] Security Headers gesetzt (CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy)

## Dependencies & Build

- [ ] [SC-12] Dependencies gepinnt; CI mit `pip-audit`/`safety`

## Database & Backups

- [ ] [SC-13] Backups & Restore getestet; SQLite-Pfade & -Rechte eingeschränkt

## Role-Based Access Control

- [ ] [SC-14] RBAC: Rollen definiert (Admin/Dispo/Fahrer/ReadOnly); Tabs & APIs rollenbasiert

## Rate Limiting & DoS Protection

- [ ] [SC-16] DoS/Rate-Limits auf Import/Geocoding/Test-Endpunkten & parallele Jobs

---

## Status-Tracking

**Phase A (Quick Wins):** In Bearbeitung  
**Phase B (User/RBAC):** Geplant  
**Phase C (CSRF/Token & Secrets):** Geplant  
**Phase D (Hardening/Monitoring):** Geplant

---

**Siehe auch:** `docs/SECURITY_GUIDE_2025-11-22.md` für detaillierte Anleitung

