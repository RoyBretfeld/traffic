# 🔐 Secrets-Management – FAMO TrafficApp 3.0

**Version:** 1.0  
**Stand:** 2025-11-14  
**Zweck:** Sichere Verwaltung von API-Keys und Secrets

---

## 🎯 Überblick

**Problem:** API-Keys im Klartext in `config.env` (wird in Git committed).

**Lösung:** Trennung zwischen:
- **`env.example`** - Template mit Platzhaltern (IN Git)
- **`.env.local`** - Echte Secrets (NICHT in Git, siehe `.gitignore`)
- **Production:** Secrets-Manager (AWS, Azure, HashiCorp Vault)

---

## 📋 Setup für Entwickler

### **Schritt 1: `.env.local` erstellen**

```bash
# Kopiere Template
cp env.example .env.local
```

### **Schritt 2: Secrets eintragen**

Öffne `.env.local` und fülle die Werte aus:

```bash
# .env.local - Lokale Secrets (NICHT in Git!)

# OpenAI API Key (hole von: https://platform.openai.com/api-keys)
OPENAI_API_KEY=sk-proj-DEIN_ECHTER_KEY_HIER

# Optional: Andere lokale Overrides
OSRM_BASE_URL=http://127.0.0.1:5000
DATABASE_URL=sqlite:///data/traffic_dev.db
```

### **Schritt 3: Backend-Code anpassen**

**Datei:** `backend/config.py`

```python
import os
from pathlib import Path
from dotenv import load_dotenv

# Lade .env.local (priorität) und dann config.env (fallback)
env_local = Path(".env.local")
env_default = Path("config.env")

if env_local.exists():
    load_dotenv(env_local, override=True)
    print("[CONFIG] .env.local geladen")
elif env_default.exists():
    load_dotenv(env_default)
    print("[CONFIG] config.env geladen")
else:
    print("[CONFIG] Keine ENV-Datei gefunden, nutze Defaults")

# Nutze Secrets
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY fehlt in .env.local!")
```

### **Schritt 4: Installiere `python-dotenv`**

```bash
pip install python-dotenv
echo "python-dotenv==1.0.0" >> requirements.txt
```

---

## 🏢 Production-Setup (AWS Secrets Manager)

### **Schritt 1: Secret erstellen**

```bash
# AWS CLI
aws secretsmanager create-secret \
    --name famo-trafficapp/prod/openai-key \
    --secret-string '{"OPENAI_API_KEY":"sk-proj-..."}'
```

### **Schritt 2: Backend-Code erweitern**

```python
import boto3
import json

def load_secrets_from_aws():
    """Lädt Secrets aus AWS Secrets Manager"""
    if os.getenv("APP_ENV") != "production":
        return  # Nur in Production
    
    client = boto3.client('secretsmanager', region_name='eu-central-1')
    
    try:
        response = client.get_secret_value(
            SecretId='famo-trafficapp/prod/openai-key'
        )
        secrets = json.loads(response['SecretString'])
        
        # Setze ENV-Variablen
        for key, value in secrets.items():
            os.environ[key] = value
        
        print("[CONFIG] AWS Secrets geladen")
    except Exception as e:
        print(f"[CONFIG] Fehler beim Laden von AWS Secrets: {e}")
        raise

# In config.py vor allen anderen Imports
if os.getenv("APP_ENV") == "production":
    load_secrets_from_aws()
```

### **Schritt 3: IAM-Policy**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:eu-central-1:ACCOUNT_ID:secret:famo-trafficapp/*"
    }
  ]
}
```

---

## 🔒 Security Best Practices

### **1. `.gitignore` prüfen**

Stelle sicher, dass `.env.local` in `.gitignore` ist:

```bash
# .gitignore
.env.local
config.env  # Nur wenn du altes config.env deprecaten willst
*.key
*.pem
```

### **2. Secrets rotieren**

- **OpenAI API Key:** Alle 90 Tage
- **DB-Passwörter:** Alle 180 Tage
- **Bei Verdacht auf Leak:** SOFORT

### **3. Least Privilege**

- Nur notwendige Permissions
- Separate Keys für Dev/Staging/Prod

### **4. Monitoring**

- CloudWatch Logs für Secrets-Zugriffe
- Alerts bei verdächtigen Zugriffen

---

## 📝 Migration von `config.env` zu `.env.local`

### **Schritt 1: Backup**

```bash
cp config.env config.env.backup
```

### **Schritt 2: Secrets extrahieren**

```bash
# Nur die sensiblen Zeilen in .env.local kopieren
grep "OPENAI_API_KEY" config.env > .env.local
```

### **Schritt 3: `config.env` bereinigen**

Entferne alle sensiblen Daten aus `config.env`, lasse nur nicht-sensible Defaults:

```bash
# config.env (öffentlich, in Git)
LLM_MODEL=gpt-4o
LLM_MAX_TOKENS=1000
DATABASE_URL=sqlite:///data/traffic.db
OSRM_BASE_URL=http://127.0.0.1:5000
```

### **Schritt 4: Umbenennen**

```bash
# Optional: config.env → env.example umbenennen
mv config.env env.example
```

---

## ✅ Checkliste

**Vor Deployment:**
- [ ] `.env.local` erstellt und Secrets eingetragen
- [ ] `.env.local` in `.gitignore`
- [ ] `python-dotenv` installiert
- [ ] `backend/config.py` angepasst (load_dotenv)
- [ ] Alte `config.env` bereinigt (keine Secrets mehr)
- [ ] Production: AWS Secrets Manager konfiguriert
- [ ] IAM-Policy erstellt und zugewiesen
- [ ] README.md aktualisiert (Setup-Anleitung)

---

## 🆘 Troubleshooting

### **Problem: `OPENAI_API_KEY` nicht gefunden**

```
ValueError: OPENAI_API_KEY fehlt in .env.local!
```

**Lösung:**
1. Prüfe, ob `.env.local` existiert: `ls -la .env.local`
2. Prüfe Inhalt: `cat .env.local | grep OPENAI`
3. Stelle sicher, dass `load_dotenv()` VOR den Imports aufgerufen wird

### **Problem: Production lädt keine Secrets**

**Lösung:**
1. Prüfe ENV: `echo $APP_ENV` (muss "production" sein)
2. Prüfe IAM-Role: Hat Instance die richtige Policy?
3. Prüfe CloudWatch Logs: Fehler bei `get_secret_value()`?

---

**Version:** 1.0  
**Letzte Aktualisierung:** 2025-11-14  
**Projekt:** FAMO TrafficApp 3.0

🔐 **Sichere Secrets = Sicheres Projekt!**

