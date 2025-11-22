"""
HT-05: CSV-Export mit CSV-Injection-Schutz.
Entschärft Felder, die mit =, +, -, @ beginnen.
"""
import csv
import io
from typing import List, Dict, Any, Optional


def escape_csv_cell(value: Any) -> str:
    """
    HT-05: Entschärft CSV-Injection (Excel-Formeln).
    
    Felder, die mit =, +, -, @ beginnen, werden mit ' geprefixt.
    Dies verhindert, dass Excel sie als Formeln interpretiert.
    
    Args:
        value: Zell-Wert (wird zu String konvertiert)
    
    Returns:
        Escapeter String
    """
    if value is None:
        return ""
    
    str_value = str(value).strip()
    
    # CSV-Injection-Schutz: Präfix ' für gefährliche Zeichen
    if str_value and str_value[0] in ['=', '+', '-', '@']:
        return "'" + str_value
    
    return str_value


def export_to_csv(
    data: List[Dict[str, Any]],
    fieldnames: Optional[List[str]] = None,
    delimiter: str = ','
) -> str:
    """
    Exportiert Daten zu CSV mit CSV-Injection-Schutz (HT-05).
    
    Args:
        data: Liste von Dicts (Zeilen)
        fieldnames: Spalten-Namen (falls None, werden Keys aus erstem Dict verwendet)
        delimiter: CSV-Delimiter (Standard: Komma)
    
    Returns:
        CSV-String
    """
    if not data:
        return ""
    
    # Spalten-Namen bestimmen
    if fieldnames is None:
        fieldnames = list(data[0].keys())
    
    # CSV in Memory-StringIO schreiben
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=fieldnames,
        delimiter=delimiter,
        quoting=csv.QUOTE_MINIMAL,
        escapechar=None
    )
    
    # Header schreiben
    writer.writeheader()
    
    # Daten schreiben (mit CSV-Injection-Schutz)
    for row in data:
        escaped_row = {
            key: escape_csv_cell(row.get(key))
            for key in fieldnames
        }
        writer.writerow(escaped_row)
    
    return output.getvalue()


def export_to_csv_file(
    data: List[Dict[str, Any]],
    filename: str,
    fieldnames: Optional[List[str]] = None,
    delimiter: str = ','
) -> bytes:
    """
    Exportiert Daten zu CSV-Datei (Bytes) mit CSV-Injection-Schutz (HT-05).
    
    Args:
        data: Liste von Dicts (Zeilen)
        filename: Dateiname (nur für Info)
        fieldnames: Spalten-Namen
        delimiter: CSV-Delimiter
    
    Returns:
        CSV als Bytes (UTF-8)
    """
    csv_string = export_to_csv(data, fieldnames, delimiter)
    return csv_string.encode('utf-8-sig')  # BOM für Excel-Kompatibilität

