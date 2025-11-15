# OSRM Docker Setup - Heimisches System

**Ziel:** OSRM im Docker Desktop betreiben

---

## Docker Compose Setup

**Datei:** `docker-compose.yml`

OSRM läuft als separater Service:
- **Container-Name:** `osrm`
- **Port-Mapping:** `5000:5000` (Host:Container)
- **Image:** `osrm/osrm-backend:latest`

---

## Konfiguration

### App läuft lokal (außerhalb Docker)

**Datei:** `config.env`

```env
OSRM_BASE_URL=http://127.0.0.1:5000
```

**Erklärung:** Die App läuft auf dem Host und greift über `localhost:5000` auf den Docker-Container zu.

---

### App läuft auch im Docker

**Datei:** `config.env` (wenn App im Docker-Netzwerk läuft)

```env
OSRM_BASE_URL=http://osrm:5000
```

**Erklärung:** Die App läuft im selben Docker-Netzwerk und kann den OSRM-Service über den Container-Namen `osrm` erreichen.

---

## OSRM Container starten

```bash
# OSRM-Service starten
docker-compose up -d osrm

# Status prüfen
docker ps | grep osrm

# Logs anzeigen
docker logs osrm

# Health-Check
curl http://127.0.0.1:5000/route/v1/driving/13.7373,51.0504;13.7283,51.0615?overview=false
```

---

## Port-Konfiguration

| Umgebung | Port | URL |
|----------|------|-----|
| **Home (Docker Desktop)** | 5000 | `http://127.0.0.1:5000` |
| **Home (Docker-Netzwerk)** | 5000 | `http://osrm:5000` |
| **Work (Proxmox CT 101)** | 5011 | `http://172.16.1.191:5011` |

---

## Troubleshooting

### OSRM nicht erreichbar

1. **Container läuft?**
   ```bash
   docker ps | grep osrm
   ```

2. **Port lauscht?**
   ```bash
   # Windows
   netstat -an | findstr :5000
   
   # Linux/Mac
   ss -ltnp | grep :5000
   ```

3. **Logs prüfen**
   ```bash
   docker logs osrm
   ```

4. **Health-Check**
   ```bash
   curl http://127.0.0.1:5000/route/v1/driving/13.7373,51.0504;13.7283,51.0615?overview=false
   ```

---

## App-Start-Log

Beim Start der App sollte erscheinen:

```
OSRM-Client initialisiert: http://127.0.0.1:5000 (Profil: driving)
```

Oder (wenn im Docker-Netzwerk):

```
OSRM-Client initialisiert: http://osrm:5000 (Profil: driving)
```

---

**Letzte Aktualisierung:** 2025-11-13

