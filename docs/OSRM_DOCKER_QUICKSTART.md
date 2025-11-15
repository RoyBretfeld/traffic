# OSRM Docker Quickstart

## Problem: 503 Service Unavailable bei `/health/osrm`

**Ursache:** OSRM-Container läuft nicht.

---

## Lösung

### 1. Docker Desktop starten

- Docker Desktop öffnen
- Warten bis Docker läuft (Icon in der Taskleiste)

### 2. OSRM-Container starten

```bash
# Im Projektverzeichnis
docker-compose up -d osrm
```

### 3. Status prüfen

```bash
# Container läuft?
docker ps | grep osrm

# Port lauscht?
netstat -ano | findstr :5000

# Health-Check
curl http://127.0.0.1:5000/nearest/v1/driving/13.7373,51.0504?number=1
```

---

## Automatischer Start

Falls Docker Desktop beim Systemstart nicht automatisch startet:

1. Docker Desktop öffnen
2. Settings → General → "Start Docker Desktop when you log in" aktivieren

---

## Troubleshooting

### Docker Desktop läuft nicht

**Fehler:** `open //./pipe/dockerDesktopLinuxEngine: Das System kann die angegebene Datei nicht finden`

**Lösung:**
1. Docker Desktop manuell starten
2. Warten bis vollständig geladen (Icon grün)
3. Container neu starten: `docker-compose up -d osrm`

### OSRM-Container startet nicht

```bash
# Logs prüfen
docker-compose logs osrm

# Container neu erstellen
docker-compose up -d --force-recreate osrm
```

### Port 5000 bereits belegt

```bash
# Prüfen was Port 5000 nutzt
netstat -ano | findstr :5000

# In docker-compose.yml Port ändern (z.B. 5001:5000)
```

---

**Letzte Aktualisierung:** 2025-11-13

