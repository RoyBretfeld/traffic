from pathlib import Path
import hashlib, json

CSV = Path('state/address_corrections.csv')
META = Path('state/state.meta.json')

if CSV.exists():
    h = hashlib.sha256(CSV.read_bytes()).hexdigest()
    print('CSV SHA256:', h)
    try:
        print('META:', json.loads(META.read_text()))
    except Exception:
        pass
else:
    print('CSV fehlt')

