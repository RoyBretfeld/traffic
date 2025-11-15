import sys
from pathlib import Path

# Projekt-Root zum Python-Pfad hinzufügen
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.services.address_corrections import AddressCorrectionStore

import json, hashlib

DB = Path('data/address_corrections.sqlite3')
CSV = Path('state/address_corrections.csv')
META = Path('state/state.meta.json')
CSV.parent.mkdir(parents=True, exist_ok=True)

store = AddressCorrectionStore(DB)
store.export_csv(CSV)
h = hashlib.sha256(CSV.read_bytes()).hexdigest()
META.write_text(json.dumps({"address_corrections_csv_sha256": h}, indent=2), encoding='utf-8')
print('Export OK:', CSV, h)

