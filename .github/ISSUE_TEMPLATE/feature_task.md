---
name: Feature/Task
about: Implementiere eine klar umrissene Änderung
labels: enhancement
---

## Kurzbeschreibung
<1–2 Sätze Ziel & Nutzen>

## Scope
- [ ] Backend
- [ ] Frontend (Admin-UI)
- [ ] DB/Migration
- [ ] Infra/DevOps

## Anforderungen / Akzeptanzkriterien
- [ ] Funktional: <…>
- [ ] Nicht-funktional: <Latenz, Sicherheit, Logs, etc.>
- [ ] Tests: <Unit/Integration/Manuell>

## Architektur-Referenz (AR-Checklist)
Wähle die relevanten Punkte aus (oder verlinke Folgetickets):

- [ ] AR-01 Job-Runner & Queues (import/geocode/stats/embeddings)
- [ ] AR-02 Admin-APIs unter `/api/admin/*` + globaler Guard
- [ ] AR-03 Tourplan-Tab (Summen km/Zeiten/Kosten)
- [ ] AR-04 Stats-Aggregator → `stats_daily`/`stats_weekly`
- [ ] AR-05 Geocoding-Cache + Failure-Liste
- [ ] AR-06 OSRM-Cache (Koord-Paar→Distanz/Zeit) mit TTL
- [ ] AR-07 RBAC (Admin/Dispo/ReadOnly)
- [ ] AR-08 Security-Hardening (CORS/Headers/Uploads)
- [ ] AR-09 Admin-Navigation: eine Seite mit Tabs
- [ ] AR-10 Observability (Prometheus/OTel/Health)
- [ ] AR-11 Requirements pinnen + CI-Audits
- [ ] AR-12 Postgres-Migrationspfad dokumentiert

## Security-Referenz (SC-Checklist)
- [ ] SC-01 Keine Default-Admin-Creds im Code
- [ ] SC-02 Passwörter argon2/bcrypt
- [ ] SC-03 Cookies: HttpOnly + Secure (Prod) + SameSite=Strict
- [ ] SC-04 Login-Rate-Limit aktiv
- [ ] SC-05 Admin-APIs mit `require_admin_auth`
- [ ] SC-06 CORS Allowlist (kein `*` mit Credentials)
- [ ] SC-07 Uploads: Whitelist + `resolve()` + Size/MIME-Limits
- [ ] SC-08 Secrets: kein produktiver Default; env/secret-store
- [ ] SC-09 Debug/Test-Routen nur via Flag + Admin
- [ ] SC-10 Logging ohne PII/Secrets; Retention dokumentiert
- [ ] SC-11 Security Headers (CSP/HSTS/XFO/XCTO/Referrer)
- [ ] SC-12 Dependencies gepinnt; CI `pip-audit`/`safety`
- [ ] SC-13 Backups/Restore getestet; Rechte geprüft
- [ ] SC-14 RBAC: Rollen & Rechte durchgezogen
- [ ] SC-15 CSRF bei Cookie-Auth oder Bearer-Token
- [ ] SC-16 DoS/Rate-Limits (Import/Geocoding/Heavy)

## Risiken / Rollback
<Risiken kurz; Rollback-Plan>

## Testplan
<Wie wird geprüft? Daten, Steps, erwartete Resultate>

## Monitoring/Metriken
<Welche Prometheus-Metriken/Logs prüfen wir?>

