#!/usr/bin/env python3
"""Dienstprogramm zum Testen des CSV-Bulk-Prozessors."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any


try:  # Sicherstellen, dass Unicode-Ausgabe unter Windows klappt
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except AttributeError:
    pass


LOG_FILE = Path("logs/csv_import_debug.log")
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


def configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
        ],
    )


def process_files(
    tour_dir: Path,
    db_path: Path,
    max_files: int | None,
    skip_geocoding: bool,
    save_to_db: bool,
) -> Dict[str, Any]:
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

    from backend.services.csv_bulk_processor import CSVBulkProcessor

    processor = CSVBulkProcessor(str(tour_dir), str(db_path))

    csv_files = processor.find_all_csv_files()
    if max_files is not None:
        csv_files = csv_files[:max_files]

    if not csv_files:
        logging.warning("Keine CSV-Dateien gefunden im Verzeichnis %s", tour_dir)
        return {
            "files_processed": 0,
            "total_customers": 0,
            "total_tours": 0,
            "database_path": str(db_path),
        }

    processed: List[Dict[str, Any]] = []
    for csv_file in csv_files:
        logging.info("Verarbeite Datei: %s", csv_file.name)
        result = processor.process_csv_file(csv_file)
        if result.get("customers") and not skip_geocoding and "error" not in result:
            try:
                result["customers"] = processor.calculate_geopoints(result["customers"])
            except Exception as exc:  # pragma: no cover - Debug-Ausgabe
                logging.exception("Geocoding fehlgeschlagen für %s", csv_file.name)
                result["error"] = f"geocoding failed: {exc}"
        processed.append(result)

    if save_to_db:
        processor.create_database()
        processor.save_to_database(processed)

    total_customers = sum(item.get("total_customers", 0) for item in processed)
    total_tours = sum(item.get("total_tours", 0) for item in processed)
    errors = [item for item in processed if "error" in item]

    summary = {
        "files_processed": len(processed),
        "total_customers": total_customers,
        "total_tours": total_tours,
        "database_path": str(db_path),
        "errors": errors,
    }

    logging.info(
        "Zusammenfassung: Dateien=%s, Touren=%s, Kunden=%s, Fehler=%s",
        summary["files_processed"],
        summary["total_tours"],
        summary["total_customers"],
        len(errors),
    )

    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CSV-Bulk-Prozessor testen")
    parser.add_argument(
        "--tour-dir",
        type=Path,
        default=Path("tourplaene"),
        help="Verzeichnis mit Tour-CSV-Dateien",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=Path("data/customers.db"),
        help="SQLite-Zieldatei",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=None,
        help="Maximale Anzahl Dateien, 0 bedeutet alle",
    )
    parser.add_argument(
        "--skip-geocoding",
        action="store_true",
        help="Geocoding überspringen, nur Parsing testen",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Ergebnis in die Datenbank schreiben",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Detailiertere Debug-Ausgaben aktivieren",
    )

    args = parser.parse_args(argv)
    configure_logging(args.verbose)

    max_files = args.max_files if args.max_files not in (None, 0) else None

    summary = process_files(
        tour_dir=args.tour_dir,
        db_path=args.db_path,
        max_files=max_files,
        skip_geocoding=args.skip_geocoding,
        save_to_db=args.save,
    )

    if summary.get("errors"):
        logging.warning("Es sind Fehler aufgetreten. Details siehe Logdatei.")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

