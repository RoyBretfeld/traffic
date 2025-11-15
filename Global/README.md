# 🌍 Globale Standards & Templates

**Version:** 1.0  
**Stand:** 2025-11-14  
**Zweck:** Projektübergreifende Standards für alle Cursor-Projekte

---

## 📁 Inhalt dieses Ordners

### **1. GLOBAL_STANDARDS.md** 🌍
**Universelle Entwicklungs-Standards mit Cursor**

Gilt für **alle Projekte**, unabhängig von:
- Programmiersprache (Python, JavaScript, Go, etc.)
- Framework (FastAPI, Django, React, Vue, etc.)
- Infrastruktur (Docker, Kubernetes, Bare Metal, etc.)

**Inhalt:**
- 7 Arbeitsregeln für Cursor
- 6-Schritt-Audit-Prozess
- Standard-Ordnerstruktur (Regeln/, audits/zip/)
- Safety & Robustheit (Defensive Programmierung)
- Anleitung für neue Projekte

**→ [GLOBAL_STANDARDS.md](GLOBAL_STANDARDS.md)**

---

### **2. PROJEKT_TEMPLATE.md** 📋
**Quick-Start-Guide für neue Projekte**

Copy & Paste Bash-Scripts zum Setup:
- Ordner-Struktur erstellen
- Standards kopieren
- `.gitignore` generieren
- `PROJECT_PROFILE.md` Template
- `README.md` Template
- Ersten Commit vorbereiten

**Aufwand:** ~10 Minuten pro neuem Projekt

**→ [PROJEKT_TEMPLATE.md](PROJEKT_TEMPLATE.md)**

---

## 🎯 Verwendung

### **Für neue Projekte:**

```bash
# Schritt 1: Neues Projekt erstellen
mkdir mein-neues-projekt
cd mein-neues-projekt
git init

# Schritt 2: Globale Standards kopieren
cp /path/to/famo-trafficapp/Global/GLOBAL_STANDARDS.md Regeln/
cp /path/to/famo-trafficapp/Global/PROJEKT_TEMPLATE.md ./

# Schritt 3: Template folgen
# Siehe PROJEKT_TEMPLATE.md für Details
```

### **Für bestehende Projekte:**

```bash
# Globale Standards nachträglich hinzufügen
mkdir -p Regeln audits/zip
cp /path/to/famo-trafficapp/Global/GLOBAL_STANDARDS.md Regeln/

# PROJECT_PROFILE.md erstellen (siehe PROJEKT_TEMPLATE.md)
# README.md anpassen (Verweis auf Regeln/)
```

---

## 📖 Projektspezifische Standards

**Jedes Projekt hat zusätzlich:**
- `PROJECT_PROFILE.md` - Projektspezifisches Profil (Technologie, Team, etc.)
- `Regeln/STANDARDS.md` - Projektspezifische Standards
- `Regeln/LESSONS_LOG.md` - Projekt-spezifische Fehler & Learnings

**Siehe:** `../PROJECT_PROFILE.md` (Beispiel: FAMO TrafficApp)

---

## 🔗 Verwandte Dokumente

**Im Projekt (FAMO TrafficApp):**
- `../PROJECT_PROFILE.md` - Projektspezifisches Profil
- `../Regeln/` - Projekt-Standards & Audit-Regeln

**Global (hier):**
- `GLOBAL_STANDARDS.md` - Universelle Regeln
- `PROJEKT_TEMPLATE.md` - Quick-Start für neue Projekte

---

## 🌍 Philosophie

**Diese Standards sind:**
- ✅ Projektübergreifend (wiederverwendbar)
- ✅ Technologie-unabhängig (Python, Node.js, Go, etc.)
- ✅ Framework-unabhängig (FastAPI, Django, Express, etc.)
- ✅ Copy & Paste ready (für neue Projekte)

**Ziel:** Reproduzierbare, nachvollziehbare Entwicklung mit Cursor AI

---

**Version:** 1.0  
**Letzte Aktualisierung:** 2025-11-14

🌍 **Universell. Reproduzierbar. Nachvollziehbar.**

