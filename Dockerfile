FROM python:3.11-slim

# Arbeitsverzeichnis setzen
WORKDIR /app

# System-Abhängigkeiten installieren
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python-Abhängigkeiten kopieren und installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Zusätzliche Pakete für Tests und Hooks
RUN pip install --no-cache-dir pytest respx httpx pre-commit

# App-Code kopieren
COPY . .

# Verzeichnisse erstellen
RUN mkdir -p /app/data/staging /app/data/output /app/logs

# Port freigeben
EXPOSE 8111

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8111/health/db || exit 1

# App starten
CMD ["python", "backend/app.py"]
