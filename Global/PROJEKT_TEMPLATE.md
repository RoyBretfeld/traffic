# 📋 Projekt-Template für neue Projekte

**Version:** 1.0  
**Stand:** 2025-11-14  
**Zweck:** Vorlage zum schnellen Setup neuer Projekte mit Cursor-Standards

---

## 🚀 Quick-Start für neues Projekt

### **Schritt 1: Basis-Struktur erstellen**

```bash
# Neues Projekt initialisieren
mkdir mein-neues-projekt
cd mein-neues-projekt
git init

# Standard-Ordner erstellen
mkdir -p Regeln audits/zip docs src tests

# .gitignore erstellen
cat > .gitignore << 'EOF'
# Audits
audits/zip/*.zip

# Secrets
.master.key
.env.local
*.pem
*.key

# Datenbanken
*.db
*.db-shm
*.db-wal

# Python
__pycache__/
*.pyc
*.pyo
venv/
.venv/

# Node
node_modules/
.npm/

# IDEs
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db
EOF
```

---

### **Schritt 2: Standards kopieren**

```bash
# Aus Referenz-Projekt (z.B. FAMO TrafficApp)
REFERENCE_PROJECT="/path/to/famo-trafficapp"

# Kopiere globale Standards
cp "$REFERENCE_PROJECT/Regeln/GLOBAL_STANDARDS.md" Regeln/

# Kopiere Template-Dateien
cp "$REFERENCE_PROJECT/Regeln/STANDARDS.md" Regeln/
cp "$REFERENCE_PROJECT/Regeln/STANDARDS_QUICK_REFERENCE.md" Regeln/
cp "$REFERENCE_PROJECT/Regeln/REGELN_AUDITS.md" Regeln/
cp "$REFERENCE_PROJECT/Regeln/AUDIT_CHECKLISTE.md" Regeln/
cp "$REFERENCE_PROJECT/Regeln/CURSOR_PROMPT_TEMPLATE.md" Regeln/
cp "$REFERENCE_PROJECT/Regeln/CURSOR_WORKFLOW.md" Regeln/

# Leere LESSONS_LOG.md erstellen
cat > Regeln/LESSONS_LOG.md << 'EOF'
# Lessons Learned – <Projektname>

**Projekt:** <Projektname>  
**Zweck:** Dokumentation aller kritischen Fehler und deren Lösungen

---

## Einleitung

Dieses Dokument sammelt alle echten Störungen und Fehler. Format:

- **Symptom:** Was wurde beobachtet?
- **Ursache:** Was war die Root Cause?
- **Fix:** Wie wurde es behoben?
- **Was die KI künftig tun soll:** Welche Lehren ziehen wir daraus?

---

## Template für neue Einträge

```md
## YYYY-MM-DD – [Kurzbeschreibung]

**Kategorie:** Backend/Frontend/DB/Infrastruktur  
**Schweregrad:** 🔴 KRITISCH / 🟡 MEDIUM / 🟢 LOW  
**Dateien:** [Liste]

### Symptom
- [Was wurde beobachtet?]

### Ursache
- [Root Cause]

### Fix
- [Konkrete Codeänderungen]

### Was die KI künftig tun soll
1. [Lehre 1]
2. [Lehre 2]
```

---

**Statistiken:**
- Gesamt-Audits: 0
- Kritische Fehler: 0
- Medium Fehler: 0
- Low Fehler: 0
EOF

# README für Regeln/-Ordner
cp "$REFERENCE_PROJECT/Regeln/README.md" Regeln/
```

---

### **Schritt 3: PROJECT_PROFILE.md erstellen**

```bash
cat > PROJECT_PROFILE.md << 'EOF'
# Projekt-Profil: <Projektname>

**Version:** 1.0  
**Stand:** YYYY-MM-DD  
**Zweck:** Projektspezifische Details für Cursor AI

---

## 🎯 Projekt-Übersicht

**Name:** <Projektname>  
**Beschreibung:** [Kurzbeschreibung des Projekts]  
**Status:** In Entwicklung / Production  
**Team:** [Namen]

---

## 🛠️ Technologie-Stack

**Backend:**
- Sprache: [Python 3.10 / Node.js 18 / ...]
- Framework: [FastAPI / Django / Express / ...]
- Datenbank: [SQLite / PostgreSQL / MongoDB / ...]

**Frontend:**
- Framework: [Vanilla JS / React / Vue / ...]
- Build-Tool: [Vite / Webpack / ...]
- UI-Library: [Bootstrap / Tailwind / ...]

**Infrastruktur:**
- Deployment: [Docker / Kubernetes / ...]
- CI/CD: [GitHub Actions / GitLab CI / ...]
- Monitoring: [Self-Hosted / ...]

---

## 🏗️ Architektur

**Typ:** [Monolith / Microservices / Serverless]  
**API:** [REST / GraphQL / gRPC]  
**Auth:** [JWT / Session / OAuth]

**Ordner-Struktur:**
```
<Projektname>/
├── Regeln/           ← Standards & Audit-Regeln
├── src/              ← Quellcode
├── tests/            ← Tests
├── docs/             ← Dokumentation
└── audits/           ← Audit-ZIPs
```

---

## ⚙️ Kritische Features

1. [Feature 1]
2. [Feature 2]
3. [Feature 3]

**Abhängigkeiten:**
- [Externe APIs: ...]
- [Services: ...]

---

## ⚠️ Bekannte Schwachstellen

1. [Problem 1]
2. [Problem 2]

**Mitigations:**
- [Lösung 1]
- [Lösung 2]

---

## 📚 Lessons Learned

**Siehe:** `Regeln/LESSONS_LOG.md`

**Häufigste Fehlertypen:**
- [Noch keine]

---

## 👥 Ansprechpartner

- **Backend:** [Name]
- **Frontend:** [Name]
- **DevOps:** [Name]
- **Projekt-Lead:** [Name]

---

## 🔗 Links

- **Repository:** [URL]
- **Staging:** [URL]
- **Production:** [URL]
- **Dokumentation:** `docs/`

---

**Version:** 1.0  
**Letzte Aktualisierung:** YYYY-MM-DD
EOF
```

---

### **Schritt 4: README.md erstellen**

```bash
cat > README.md << 'EOF'
# <Projektname>

[Kurzbeschreibung des Projekts]

---

## 📘 Standards & Regeln

**⭐ Zentrale Dokumentation:** [`Regeln/`](Regeln/)

**Für Entwickler:**
- 🚀 [STANDARDS_QUICK_REFERENCE.md](Regeln/STANDARDS_QUICK_REFERENCE.md) - Tägliche Arbeit
- 🔄 [CURSOR_WORKFLOW.md](Regeln/CURSOR_WORKFLOW.md) - 6-Schritt-Prozess für Änderungen

**Für Cursor-KI:**
- 🤖 [CURSOR_PROMPT_TEMPLATE.md](Regeln/CURSOR_PROMPT_TEMPLATE.md) - Bug-Fix-Templates
- 🔍 [REGELN_AUDITS.md](Regeln/REGELN_AUDITS.md) - 7 unverhandelbare Audit-Regeln
- 📝 [LESSONS_LOG.md](Regeln/LESSONS_LOG.md) - Bekannte Fehler & Lösungen

**Globale Standards:**
- 🌍 [GLOBAL_STANDARDS.md](Regeln/GLOBAL_STANDARDS.md) - Projektübergreifende Regeln

---

## 🚀 Schnellstart

[Setup-Anleitung]

---

## 📊 Projektstatus

[Status-Informationen]

---

## 🛠️ Technologie-Stack

[Stack-Details, siehe PROJECT_PROFILE.md]

---

## 📖 Weitere Dokumentation

- [PROJECT_PROFILE.md](PROJECT_PROFILE.md) - Projektspezifisches Profil
- `docs/` - Weitere Dokumentation
- `Regeln/` - Standards & Audit-Regeln

---

**Version:** 1.0  
**Letzte Aktualisierung:** YYYY-MM-DD
EOF
```

---

### **Schritt 5: Ersten Commit erstellen**

```bash
git add .
git commit -m "docs: Projekt-Struktur mit Standards & Regeln initialisiert

- Regeln/-Ordner mit globalen Standards erstellt
- GLOBAL_STANDARDS.md (projektübergreifend)
- STANDARDS.md, REGELN_AUDITS.md, CURSOR_WORKFLOW.md
- PROJECT_PROFILE.md (projektspezifisch)
- README.md mit Verweis auf Standards
- audits/zip/ für Audit-Pakete
- .gitignore mit Standard-Excludes

Basis für strukturierte Entwicklung mit Cursor AI"
```

---

## ✅ Checkliste

Nach Setup prüfen:

```markdown
[ ] Regeln/-Ordner existiert (8 Dateien)
[ ] PROJECT_PROFILE.md ausgefüllt (Technologie-Stack, etc.)
[ ] README.md aktualisiert (Projekt-Beschreibung)
[ ] .gitignore vorhanden
[ ] audits/zip/ erstellt
[ ] Erster Commit durchgeführt
[ ] Remote-Repository verlinkt (git remote add origin ...)
[ ] Entwickler-Team informiert (README lesen!)
```

---

## 📦 Optionale Erweiterungen

### **Python-Projekt:**

```bash
# requirements.txt
cat > requirements.txt << 'EOF'
# Self-Hosted Essentials
cryptography==41.0.7  # Secrets-Vault
python-dotenv==1.0.0  # .env.local support

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0

# Code Quality
black==23.11.0
flake8==6.1.0
pre-commit==3.5.0
EOF

# Virtuelle Umgebung
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder: venv\Scripts\activate  # Windows

pip install -r requirements.txt

# Pre-Commit Hooks
pre-commit install
```

### **Node.js-Projekt:**

```bash
# package.json (minimal)
npm init -y

# Dependencies
npm install --save-dev \
  eslint \
  prettier \
  jest \
  husky

# ESLint Config
npx eslint --init
```

---

## 🎯 Nächste Schritte

Nach Setup:

1. **Passe PROJECT_PROFILE.md an** (Technologie-Stack, Team, etc.)
2. **Passe Regeln/STANDARDS.md an** (projektspezifische Regeln)
3. **Lies Regeln/CURSOR_WORKFLOW.md** (6-Schritt-Prozess)
4. **Starte Entwicklung** (mit Cursor + Standards)

---

**🎉 Projekt-Setup abgeschlossen! Viel Erfolg! 🚀**

