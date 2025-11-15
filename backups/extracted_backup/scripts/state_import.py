import sys
from pathlib import Path

# Projekt-Root zum Python-Pfad hinzufügen
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.services.address_corrections import AddressCorrectionStore

DB = Path('data/address_corrections.sqlite3')
CSV = Path('state/address_corrections.csv')

store = AddressCorrectionStore(DB)
if CSV.exists():
    n = store.import_csv(CSV)
    print('Import OK:', n, 'Einträge')
else:
    print('Kein CSV gefunden:', CSV)

