import sys
from pathlib import Path

# Projektverzeichnis zum Python-Pfad hinzufügen
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from db.core import db_health
import json

if __name__ == "__main__":
    print(json.dumps(db_health(), ensure_ascii=False, indent=2))
