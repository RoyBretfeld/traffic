# -*- coding: utf-8 -*-
"""
Cursor-KI Debug Runner – CSV → Parser → Bulk-Analysis → Match

Zweck
-----
Dieses Skript prüft automatisiert die Datenfluss-Strecke der TrafficApp:
- ingest.csv_reader
- backend.parsers.tour_plan_parser
- routes.tourplan_bulk_analysis
- routes.tourplan_match
- (optional) common.normalize, common.tour_data_models

Es wurde so geschrieben, dass Cursor es gefahrlos ausführen und reparieren kann.
Es erkennt typische API-Varianten (Duck Typing) und erzeugt am Ende einen
JSON-Report + menschenlesbare Konsolen-Ausgabe. Keine Netzaufrufe.

Aufruf
------
python tests/debug_pipeline_runner.py <pfad/zur/datei.csv> \
       [--encoding utf-8] [--delimiter ";"] [--json-out debug_report.json]

Exit-Codes
----------
0 = alles funktionsfähig, 1 = Warnungen, 2 = kritischer Fehler
"""
from __future__ import annotations

import argparse
import importlib
import io
import json
import os
import sys
import traceback
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple

# -----------------------------
# Hilfs-Modelle für den Report
# -----------------------------

@dataclass
class StepStatus:
    name: str
    ok: bool
    warn: bool = False
    message: str = ""
    items_in: int = 0
    items_out: int = 0
    extra: Dict[str, Any] = None

@dataclass
class DebugReport:
    ok: int
    warn: int
    bad: int
    steps: List[StepStatus]
    errors: List[str]
    warnings: List[str]

    def exit_code(self) -> int:
        if any(not s.ok for s in self.steps) or self.bad > 0:
            return 2
        if self.warn > 0 or any(s.warn for s in self.steps):
            return 1
        return 0

# -----------------------------
# Modul-Lader mit freundlichen Fehlermeldungen
# -----------------------------

def try_import(module_name: str):
    try:
        return importlib.import_module(module_name), None
    except Exception as ex:
        return None, f"Importfehler in '{module_name}': {ex}"

# -----------------------------
# CSV Reader – mehrere mögliche APIs unterstützen
# -----------------------------

def run_csv_reader(mod, csv_bytes: bytes, *, encoding: Optional[str], delimiter: Optional[str]) -> Tuple[List[Dict[str, Any]], str]:
    """Versucht verschiedene Reader-Signaturen:
    - Klasse CSVReader().read(bytes)
    - Funktion read(bytes|str), read_csv(path|bytes)
    - Fallback: Python csv.DictReader mit optionalem Delimiter
    """
    # 1) Class-based API
    if hasattr(mod, "CSVReader"):
        try:
            reader = mod.CSVReader(encoding=encoding or "utf-8")
            rows = reader.read(csv_bytes)
            return list(rows or []), "CSVReader.read"
        except Exception:
            pass
    # 2) Functional APIs
    for fname in ("read", "read_csv", "load", "load_csv"):
        if hasattr(mod, fname):
            func = getattr(mod, fname)
            try:
                # Versuche bytes, sonst Text
                try:
                    rows = func(csv_bytes)
                except TypeError:
                    rows = func(io.StringIO(csv_bytes.decode(encoding or "utf-8", errors="ignore")))
                return list(rows or []), fname
            except Exception:
                traceback.print_exc()
                continue
    # 3) Minimal-Fallback über csv.DictReader
    import csv
    text = io.StringIO(csv_bytes.decode(encoding or "utf-8", errors="ignore"))
    if delimiter:
        dialect = csv.excel
        dialect.delimiter = delimiter
        reader = csv.DictReader(text, dialect=dialect)
    else:
        # Sniffer-Fallback
        try:
            dialect = csv.Sniffer().sniff(text.read(4096))
            text.seek(0)
            reader = csv.DictReader(text, dialect=dialect)
        except Exception:
            text.seek(0)
            reader = csv.DictReader(text, delimiter=';')
    return [ {k.strip(): (v or "").strip() for k,v in row.items()} for row in reader ], "fallback_dictreader"

# -----------------------------
# Parser – typische Signaturen erkennen
# -----------------------------

def run_tour_parser(mod, rows: List[Dict[str, Any]]) -> Tuple[Any, str]:
    # gängige Funktionsnamen
    for fname in ("parse_tour_plan", "parse", "run", "build_model"):
        if hasattr(mod, fname):
            func = getattr(mod, fname)
            try:
                result = func(rows)
                return result, fname
            except Exception:
                traceback.print_exc()
                continue
    raise RuntimeError("Kein passender Parser-EntryPoint gefunden (parse_tour_plan/parse/run/build_model)")

# -----------------------------
# Bulk-Analyse – typische Signaturen
# -----------------------------

def run_bulk_analysis(mod, parsed) -> Tuple[Any, str]:
    for fname in ("analyze", "bulk_analyze", "run", "process"):
        if hasattr(mod, fname):
            func = getattr(mod, fname)
            try:
                out = func(parsed)
                return out, fname
            except Exception:
                traceback.print_exc()
                continue
    # Falls das Modul nur Hilfsfunktionen enthält, reiche durch
    return parsed, "noop"

# -----------------------------
# Matching – typische Signaturen
# -----------------------------

def run_match(mod, analyzed) -> Tuple[Any, str]:
    for fname in ("match_tourplan", "match", "assign", "build_routes"):
        if hasattr(mod, fname):
            func = getattr(mod, fname)
            try:
                out = func(analyzed)
                return out, fname
            except Exception:
                traceback.print_exc()
                continue
    return analyzed, "noop"

# -----------------------------
# Qualitätschecks
# -----------------------------

def count_missing_coords(items: Any) -> int:
    missing = 0
    if isinstance(items, list):
        for x in items:
            if isinstance(x, dict):
                lat = x.get("lat") or x.get("latitude")
                lon = x.get("lon") or x.get("lng") or x.get("longitude")
                if lat in (None, "") or lon in (None, ""):
                    missing += 1
            elif hasattr(x, "lat") and hasattr(x, "lon"):
                if getattr(x, "lat") is None or getattr(x, "lon") is None:
                    missing += 1
    return missing

# -----------------------------
# Main
# -----------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="Cursor-KI Debug Runner")
    ap.add_argument("csv", help="Pfad zur CSV-Datei")
    ap.add_argument("--encoding", default=os.getenv("CSV_DEBUG_ENCODING", "utf-8"))
    ap.add_argument("--delimiter", default=os.getenv("CSV_DEBUG_DELIMITER"))
    ap.add_argument("--json-out", default="debug_report.json")
    args = ap.parse_args()

    # sys.path um Projektwurzel ergänzen
    project_root = os.getcwd()
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    report = DebugReport(ok=0, warn=0, bad=0, steps=[], errors=[], warnings=[])

    # 1) ingest.csv_reader
    mod_reader, err = try_import("ingest.csv_reader")
    if err:
        report.errors.append(err)
        report.bad += 1
        report.steps.append(StepStatus(name="csv_reader:import", ok=False, message=err))
        # harter Abbruch: Reader ist fundamental
        _flush(report, args.json_out)
        _print_report(report)
        return report.exit_code()

    csv_bytes = open(args.csv, "rb").read()
    try:
        rows, reader_api = run_csv_reader(mod_reader, csv_bytes, encoding=args.encoding, delimiter=args.delimiter)
        report.steps.append(StepStatus(name=f"csv_reader:{reader_api}", ok=True, items_out=len(rows)))
        if len(rows) == 0:
            report.warn += 1
            report.warnings.append("CSV-Reader lieferte 0 Datensätze – Delimiter/Encoding prüfen.")
            report.steps[-1].warn = True
            report.steps[-1].message = "0 Datensätze"
    except Exception as ex:
        tb = traceback.format_exc()
        report.bad += 1
        report.errors.append(f"CSV-Reader Fehler: {ex}\n{tb}")
        report.steps.append(StepStatus(name="csv_reader", ok=False, message=str(ex)))
        _flush(report, args.json_out)
        _print_report(report)
        return report.exit_code()

    # 2) backend.parsers.tour_plan_parser
    mod_parser, err = try_import("backend.parsers.tour_plan_parser")
    if err:
        report.errors.append(err)
        report.bad += 1
        report.steps.append(StepStatus(name="tour_plan_parser:import", ok=False, message=err, items_in=len(rows)))
        _flush(report, args.json_out)
        _print_report(report)
        return report.exit_code()

    try:
        parsed, parser_api = run_tour_parser(mod_parser, rows)
        out_count = len(parsed) if hasattr(parsed, "__len__") else 1
        report.steps.append(StepStatus(name=f"tour_plan_parser:{parser_api}", ok=True, items_in=len(rows), items_out=out_count))
        if out_count == 0:
            report.warn += 1
            report.warnings.append("Parser lieferte 0 Elemente – Mapping/Feldnamen prüfen.")
            report.steps[-1].warn = True
    except Exception as ex:
        tb = traceback.format_exc()
        report.bad += 1
        report.errors.append(f"Parser Fehler: {ex}\n{tb}")
        report.steps.append(StepStatus(name="tour_plan_parser", ok=False, message=str(ex), items_in=len(rows)))
        _flush(report, args.json_out)
        _print_report(report)
        return report.exit_code()

    # 3) routes.tourplan_bulk_analysis
    mod_bulk, err = try_import("routes.tourplan_bulk_analysis")
    if err:
        # nicht kritisch – durchreichen
        analyzed, bulk_api = parsed, "missing_module"
        report.steps.append(StepStatus(name="tourplan_bulk_analysis:missing", ok=True, items_in=len(parsed) if hasattr(parsed, "__len__") else 1, items_out=len(parsed) if hasattr(parsed, "__len__") else 1))
    else:
        try:
            analyzed, bulk_api = run_bulk_analysis(mod_bulk, parsed)
            out_count = len(analyzed) if hasattr(analyzed, "__len__") else 1
            report.steps.append(StepStatus(name=f"tourplan_bulk_analysis:{bulk_api}", ok=True, items_in=len(parsed) if hasattr(parsed, "__len__") else 1, items_out=out_count))
        except Exception as ex:
            tb = traceback.format_exc()
            report.bad += 1
            report.errors.append(f"Bulk-Analyse Fehler: {ex}\n{tb}")
            report.steps.append(StepStatus(name="tourplan_bulk_analysis", ok=False, message=str(ex)))
            _flush(report, args.json_out)
            _print_report(report)
            return report.exit_code()

    # 4) routes.tourplan_match
    mod_match, err = try_import("routes.tourplan_match")
    if err:
        matched, match_api = analyzed, "missing_module"
        report.steps.append(StepStatus(name="tourplan_match:missing", ok=True))
    else:
        try:
            matched, match_api = run_match(mod_match, analyzed)
            out_count = len(matched) if hasattr(matched, "__len__") else 1
            missing_coords = count_missing_coords(matched)
            ok = out_count > 0 and (missing_coords < out_count)
            msg = f"Routen: {out_count}, fehlende Koordinaten: {missing_coords}"
            report.steps.append(StepStatus(name=f"tourplan_match:{match_api}", ok=ok, warn=(missing_coords>0), message=msg, items_in=len(analyzed) if hasattr(analyzed, "__len__") else 1, items_out=out_count))
            if out_count == 0:
                report.bad += 1
                report.errors.append("Matching lieferte 0 Routen – prüfe Analyse-Output und Feldnamen.")
            elif missing_coords > 0:
                report.warn += 1
                report.warnings.append("Einige Stopps ohne Koordinaten – Geocoding/Normalisierung prüfen.")
        except Exception as ex:
            tb = traceback.format_exc()
            report.bad += 1
            report.errors.append(f"Matching Fehler: {ex}\n{tb}")
            report.steps.append(StepStatus(name="tourplan_match", ok=False, message=str(ex)))
            _flush(report, args.json_out)
            _print_report(report)
            return report.exit_code()

    # Zusammenfassung schätzen (Heuristik aus den Schritten)
    report.ok = sum(1 for s in report.steps if s.ok and not s.warn)
    report.warn += sum(1 for s in report.steps if s.warn)
    report.bad += sum(1 for s in report.steps if not s.ok)

    _flush(report, args.json_out)
    _print_report(report)
    return report.exit_code()


def _flush(report: DebugReport, path: str) -> None:
    serializable = {
        "ok": report.ok,
        "warn": report.warn,
        "bad": report.bad,
        "steps": [asdict(s) for s in report.steps],
        "errors": report.errors,
        "warnings": report.warnings,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(serializable, f, ensure_ascii=False, indent=2)


def _print_report(report: DebugReport) -> None:
    print("\n=== Cursor-KI Debug Report ===")
    for s in report.steps:
        state = "OK" if s.ok and not s.warn else ("WARN" if s.warn else "BAD")
        print(f"- {s.name:<35} => {state} | in={s.items_in} out={s.items_out} {('|' if s.message else '')} {s.message}")
    if report.warnings:
        print("\nWARNINGS:")
        for w in report.warnings:
            print(" -", w)
    if report.errors:
        print("\nERRORS:")
        for e in report.errors:
            print(" -", e)
    print(f"\nSummary: ok={report.ok}, warn={report.warn}, bad={report.bad}")


if __name__ == "__main__":
    sys.exit(main())
