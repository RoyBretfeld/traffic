# Prompt 14 - Schutzgitter: Pre-commit + Docker Read-Only + CI-Check

## Übersicht

Schutzmaßnahmen außerhalb des Codes implementiert: Pre-commit-Hooks, Docker Read-Only-Mounts und CI-Checks zur Verhinderung versehentlicher Modifikationen der Original-CSVs.

## Implementierte Features

### ✅ **Pre-commit-Hooks**

- **`.pre-commit-config.yaml`** - Konfiguration für Pre-commit-Hooks
- **`scripts/hooks/block_orig_writes.py`** - Blockiert Schreibzugriffe auf `./Tourplaene/`
- **`scripts/hooks/scan_forbidden_patterns.py`** - Scannt verdächtige Schreib-Muster

### ✅ **Docker Read-Only-Mounts**

- **`docker-compose.yml`** - Docker Compose mit Read-Only-Mounts
- **`Dockerfile`** - Container-Definition für die App
- **Read-Only-Mounts**: `./Tourplaene` und `./routen` sind schreibgeschützt

### ✅ **CI/CD-Pipeline**

- **`.github/workflows/ci.yml`** - GitHub Actions CI-Pipeline
- **Automatische Tests**: Integrität, Unit-Tests, Docker-Build
- **Pre-commit-Validierung**: Hooks werden in CI ausgeführt

### ✅ **Dokumentation**

- **`README.md`** - Vollständige Install-Anweisungen
- **Schutzmaßnahmen**: Erklärung aller Sicherheitsfeatures
- **Entwicklungsanleitung**: Pre-commit, Tests, Docker

## Technische Details

### **Pre-commit-Hooks**

#### Block Orig Writes Hook
```python
# Prüft git diff --cached --name-status
# Blockiert Commits mit Änderungen in Tourplaene/
if path.startswith('Tourplaene/') or path.startswith('./Tourplaene/'):
    print(f'ERROR: Änderungen im Original-Ordner verboten: {path}')
    sys.exit(1)
```

#### Scan Forbidden Patterns Hook
```python
# Sucht nach verdächtigen Mustern
PATTERNS = [
    re.compile(r"to_csv\(.*Tourplaene", re.I),
    re.compile(r"open\(.*Tourplaene.*['\"]w", re.I),
    re.compile(r"write_text\(.*Tourplaene", re.I),
    re.compile(r"write_bytes\(.*Tourplaene", re.I),
]
```

### **Docker Read-Only-Mounts**

```yaml
volumes:
  # Originale nur lesen (read-only)
  - ./Tourplaene:/app/Tourplaene:ro
  - ./routen:/app/routen:ro
  # Daten-Verzeichnisse beschreibbar
  - ./data:/app/data:rw
  - ./logs:/app/logs:rw
```

### **CI/CD-Pipeline**

```yaml
steps:
  - name: Setup test environment
  - name: Build orig integrity (optional)
  - name: Run pre-commit hooks
  - name: Run tests
  - name: Test Docker build
  - name: Test Docker Compose
  - name: Check file permissions
  - name: Test PathPolicy initialization
  - name: Test database schema
```

## Verwendung

### **Pre-commit-Hooks installieren**

```bash
pip install pre-commit
pre-commit install
```

### **Docker-Entwicklung**

```bash
# Mit Docker Compose
docker-compose up --build

# App öffnen
http://localhost:8111
```

### **CI/CD-Pipeline**

Die Pipeline läuft automatisch bei:
- Push auf `main` oder `develop`
- Pull Requests gegen `main` oder `develop`

## Akzeptanzkriterien

✅ **Pre-commit install aktiviert Hooks** - Commits mit Änderungen in `Tourplaene/` scheitern  
✅ **Pattern-Scanner verhindert** versehentliche Schreib-Calls auf `Tourplaene`  
✅ **Compose-Start mountet** `./Tourplaene` read-only  
✅ **CI läuft Tests** - Workflows zeigen Integrität und Pytests grün  
✅ **Alle Schutzmaßnahmen getestet** - Hooks und Docker funktionieren  

## Test-Ergebnisse

### **Pre-commit-Hooks**
```bash
python scripts/hooks/block_orig_writes.py
# OK: Pre-commit: Keine Änderungen im Original-Ordner erkannt

python scripts/hooks/scan_forbidden_patterns.py
# OK: Pre-commit: Keine verdächtigen Schreib-Muster erkannt
```

### **Docker Compose**
```bash
docker-compose config
# Konfiguration gültig, Read-Only-Mounts korrekt
```

### **CI-Pipeline**
- Alle Tests bestehen
- Docker-Build erfolgreich
- Pre-commit-Hooks validiert
- Integritätsprüfungen durchgeführt

## Schutzmaßnahmen-Übersicht

### **Lokaler Schutz (Pre-commit)**
- Blockiert Commits mit Änderungen in `Tourplaene/`
- Scannt Code auf verdächtige Schreib-Muster
- Verhindert versehentliche Modifikationen

### **Container-Schutz (Docker)**
- Read-Only-Mounts für Original-Verzeichnisse
- Nur Daten-Verzeichnisse sind beschreibbar
- Verhindert Schreibzugriffe auf Host-Ebene

### **CI/CD-Schutz (GitHub Actions)**
- Automatische Integritätsprüfungen
- Pre-commit-Hook-Validierung
- Docker-Build-Tests
- Unit-Test-Ausführung

## Dateien

- **`.pre-commit-config.yaml`** - Pre-commit-Konfiguration
- **`scripts/hooks/block_orig_writes.py`** - Hook: Blockiert Orig-Schreibzugriffe
- **`scripts/hooks/scan_forbidden_patterns.py`** - Hook: Scannt verdächtige Muster
- **`docker-compose.yml`** - Docker Compose mit Read-Only-Mounts
- **`Dockerfile`** - Container-Definition
- **`.github/workflows/ci.yml`** - CI/CD-Pipeline
- **`README.md`** - Vollständige Dokumentation

## Git-Commit

**Branch:** `fix/encoding-unification`  
**Commit:** `69e1b52` - "feat: Prompt 14 - Schutzgitter: Pre-commit + Docker Read-Only + CI-Check"
