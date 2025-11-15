"""
File Parser Service - Modul 1
Aufgabe: CSV/Excel-Dateien einlesen und rohe Daten extrahieren
Verantwortlichkeit: Nur Datei-Parsing, keine Geschäftslogik
"""

from __future__ import annotations
from pathlib import Path
from typing import Union, Optional, List, Dict, Any
import pandas as pd
from io import BytesIO
import tempfile
from backend.parsers import parse_tour_plan_to_dict, parse_tour_plan


class FileParserService:
    """Service zum Einlesen von CSV/Excel-Dateien"""
    
    def __init__(self):
        self.supported_formats = ['.csv', '.xlsx', '.xls']
    
    def parse_file(self, file_path: Union[str, Path, BytesIO], 
                   filename: Optional[str] = None) -> pd.DataFrame:
        """
        DEPRECATED: Verwende ingest.csv_reader.read_csv_unified() stattdessen
        
        Parst eine Datei und gibt ein Pandas DataFrame zurück
        """
        from ingest.csv_reader import read_csv_unified
        
        # Verwende den zentralen CSV-Reader für CSV-Dateien
        if isinstance(file_path, BytesIO):
            if not filename:
                raise ValueError("Filename muss bei BytesIO-Objekten angegeben werden")
            
            if filename.endswith('.csv'):
                return read_csv_unified(file_path, sep=';', header=None, dtype=str)
            elif filename.endswith(('.xlsx', '.xls')):
                return pd.read_excel(file_path)
            else:
                raise ValueError(f"Unsupported Dateiformat: {filename}")
        else:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"Datei nicht gefunden: {file_path}")
            
            if file_path.suffix.lower() == '.csv':
                return read_csv_unified(file_path, sep=';', header=None, dtype=str)
            elif file_path.suffix.lower() in ['.xlsx', '.xls']:
                return pd.read_excel(file_path)
            else:
                raise ValueError(f"Unsupported Dateiformat: {file_path.suffix}")
    
    def parse_teha_format(self, file_path: Union[str, Path, BytesIO], 
                          filename: Optional[str] = None) -> Dict[str, Any]:
        """Wrapper für parse_tour_plan_to_dict; SPDX: Schritt 1 der neuen Pipeline."""
        try:
            if isinstance(file_path, BytesIO):
                with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.csv') as tmp:
                    file_path.seek(0)
                    tmp.write(file_path.read())
                    tmp_path = Path(tmp.name)
                try:
                    return parse_tour_plan_to_dict(tmp_path)
                finally:
                    tmp_path.unlink(missing_ok=True)
            else:
                return parse_tour_plan_to_dict(file_path)
        except Exception as e:
            raise ValueError(f"Fehler beim Parsen mit neuem Tourplan-Parser: {str(e)}")
    
    def validate_file_format(self, filename: str) -> bool:
        """Prüft ob das Dateiformat unterstützt wird"""
        return any(filename.lower().endswith(fmt) for fmt in self.supported_formats)
    
    def get_file_info(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Gibt Informationen über die geparste Datei zurück"""
        return {
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": list(df.columns),
            "file_size": "N/A",  # Könnte implementiert werden
            "parsing_method": "pandas_standard"
        }
