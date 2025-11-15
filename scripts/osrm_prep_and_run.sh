#!/bin/bash
# OSRM Preprocessing & Run Script für Proxmox CT 101
# Port: 5011 (5000 ist belegt durch Frigate)

set -e

OSRM_DIR="/var/lib/osrm"
OSRM_PORT=5011
REGION_FILE="region.osm.pbf"
REGION_URL="https://download.geofabrik.de/europe/germany/sachsen-latest.osm.pbf"

echo "============================================================"
echo "OSRM Setup für Proxmox CT 101"
echo "============================================================"
echo "Port: $OSRM_PORT"
echo "Verzeichnis: $OSRM_DIR"
echo "============================================================"
echo ""

# 1. Verzeichnis erstellen
echo "[1/5] Erstelle Verzeichnis..."
mkdir -p "$OSRM_DIR"
cd "$OSRM_DIR"

# 2. Region-Datei laden (falls noch nicht vorhanden)
if [ ! -f "$REGION_FILE" ]; then
    echo "[2/5] Lade Region-Datei (Sachsen)..."
    echo "      URL: $REGION_URL"
    curl -L -o "$REGION_FILE" "$REGION_URL"
    echo "[OK] Region-Datei geladen: $(du -h $REGION_FILE | cut -f1)"
else
    echo "[2/5] Region-Datei bereits vorhanden: $REGION_FILE"
fi

# 3. Preprocessing
echo "[3/5] Preprocessing (osrm-extract)..."
docker run --rm -t -v "$OSRM_DIR:/data" osrm/osrm-backend:latest \
    osrm-extract -p /opt/car.lua /data/$REGION_FILE

echo "[4/5] Preprocessing (osrm-partition)..."
docker run --rm -t -v "$OSRM_DIR:/data" osrm/osrm-backend:latest \
    osrm-partition /data/region.osrm

echo "[5/5] Preprocessing (osrm-customize)..."
docker run --rm -t -v "$OSRM_DIR:/data" osrm/osrm-backend:latest \
    osrm-customize /data/region.osrm

# 4. Start OSRM (Variante A: Host-Netz)
echo ""
echo "============================================================"
echo "Starte OSRM-Service..."
echo "============================================================"

# Prüfe ob Container bereits läuft
if docker ps | grep -q "osrm"; then
    echo "[INFO] OSRM-Container läuft bereits. Stoppe alten Container..."
    docker stop osrm || true
    docker rm osrm || true
fi

echo "[START] Starte OSRM auf Port $OSRM_PORT (Host-Netz)..."
docker run -d --name osrm \
    --network host \
    -v "$OSRM_DIR:/data" \
    osrm/osrm-backend:latest \
    osrm-routed --algorithm mld --port $OSRM_PORT /data/region.osrm

# 5. Health-Check
echo ""
echo "============================================================"
echo "Health-Check..."
echo "============================================================"

sleep 3  # Warte kurz bis Service startet

# Prüfe ob Port lauscht
if ss -ltnp | grep -q ":$OSRM_PORT"; then
    echo "[OK] Port $OSRM_PORT lauscht"
else
    echo "[WARN] Port $OSRM_PORT lauscht NICHT"
fi

# Test-Route
echo "[TEST] Teste Route-API..."
TEST_RESPONSE=$(curl -s "http://127.0.0.1:$OSRM_PORT/route/v1/driving/13.7373,51.0504;13.7283,51.0615?overview=false" || echo "ERROR")

if echo "$TEST_RESPONSE" | grep -q '"code":"Ok"'; then
    echo "[OK] Route-API funktioniert"
    echo "      Response: $(echo "$TEST_RESPONSE" | head -c 100)..."
else
    echo "[WARN] Route-API-Test fehlgeschlagen"
    echo "      Response: $TEST_RESPONSE"
fi

echo ""
echo "============================================================"
echo "OSRM Setup abgeschlossen"
echo "============================================================"
echo "URL: http://127.0.0.1:$OSRM_PORT"
echo "URL (extern): http://172.16.1.191:$OSRM_PORT"
echo "============================================================"

