---
name: Security Fix
about: Härtung/Absicherung mit klarer SC-Checklist
labels: security
---

## Problem
<Kurzbeschreibung + betroffene Komponenten>

## Fix-Ansatz
<Geplante Änderung>

## SC-Checklist (Pflicht)
- [ ] SC-01 Keine Default-Admin-Creds
- [ ] SC-02 Passwörter argon2/bcrypt
- [ ] SC-03 Cookies sicher (Prod) + SameSite=Strict
- [ ] SC-04 Login-Rate-Limit
- [ ] SC-05 Admin-Auth-Guard auf Endpoints
- [ ] SC-06 CORS Allowlist
- [ ] SC-07 Upload-Whitelists + `resolve()`
- [ ] SC-11 Security Headers
- [ ] SC-12 Dependency-Audit in CI

## Tests / Verifikation
<Wie wird Sicherheit verifiziert? (negative Tests, Scans, Manuell)>

## Rollout
<Feature-Flag/ENV/Steps>

