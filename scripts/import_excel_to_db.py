import argparse
from pathlib import Path

from backend.db.schema import init_db
from backend.db.dao import Kunde, upsert_kunden, insert_tour
from backend.parsers import parse_teha_excel


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Importiert TEHA-Excel in die lokale SQLite-DB"
    )
    parser.add_argument("excel", type=str, help="Pfad zur Excel-Datei")
    parser.add_argument(
        "--date",
        dest="fallback_date",
        type=str,
        default=None,
        help="Optionales Datum (YYYY-MM-DD), wird genutzt, falls kein Datum im Excel steht",
    )
    args = parser.parse_args()

    init_db()

    result = parse_teha_excel(Path(args.excel), fallback_date=args.fallback_date)
    tour_id = str(result.get("tour"))
    datum = str(result.get("datum"))
    kunden_rows = result.get("kunden", [])

    kunden_ids = upsert_kunden(
        Kunde(id=None, name=row["name"], adresse=row["adresse"]) for row in kunden_rows
    )
    tour_db_id = insert_tour(tour_id=tour_id, datum=datum, kunden_ids=kunden_ids)

    print(
        f"Import abgeschlossen. Tour-ID={tour_id} Datum={datum} DB-Tour-Record-ID={tour_db_id}"
    )


if __name__ == "__main__":
    main()
