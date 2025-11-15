from __future__ import annotations
import re


_MOJIBAKE_MARKERS = {
    "Ã",
    "Â",
    "ƒ",
    "╞",
    "╚",
    "╔",
    "╩",
    "╦",
    "╠",
    "╬",
    "╧",
    "╤",
    "═",
    "║",
    "╣",
    "┬",
    "┼",
    "┤",
    "┴",
    "┐",
    "┌",
    "┘",
    "└",
    "┼",
    "├",
}


def repair_cp_mojibake(text: str | None) -> str | None:
    """Behebt typische CP437/CP850-Mojibake-Artefakte."""

    if not text or not isinstance(text, str):
        return text

    if not any(marker in text for marker in _MOJIBAKE_MARKERS):
        return text

    for codec in ("cp437", "cp850"):
        try:
            repaired = text.encode(codec).decode("utf-8")
            if not any(marker in repaired for marker in _MOJIBAKE_MARKERS):
                return repaired
            text = repaired
        except UnicodeEncodeError:
            continue
        except UnicodeDecodeError:
            continue

    return text

# Intelligente ?? Zeichen-Korrektur basierend auf Kontext
def _fix_question_marks(text: str) -> str:
    """Korrigiert ?? Zeichen basierend auf Kontext."""
    if not text or "??" not in text:
        return text
    
    # Kontext-basierte Korrekturen für häufige Fälle
    context_fixes = {
        # Straße/Straße-Korrekturen
        "Stra??e": "Straße",
        "stra??e": "straße", 
        "Stra??": "Straße",
        "stra??": "straße",
        
        # Häufige Straßennamen mit ?? 
        "Burgker Stra??e": "Burgker Straße",
        "Cosch??tzer": "Coschützer",
        "Cosch??tzer Stra??e": "Coschützer Straße",
        "Wilsdruffer Stra??e": "Wilsdruffer Straße",
        "Dresdner Stra??e": "Dresdner Straße",
        "Tharandter Stra??e": "Tharandter Straße",
        "L??btauer": "Löbtauer",
        "L??btauer Stra??e": "Löbtauer Straße",
        "Fr??belstra??e": "Fröbelstraße",
        "Morgenr??the": "Morgenröthe",
        "Nieder m??hle": "Niedermühle",
        "B??renstein": "Bärenstein",
        "Gro??opitz": "Großopitz",
        "Berggie??h??bel": "Berggießhübel",
        "Gottleuba-Berggie??h??bel": "Gottleuba-Berggießhübel",
        "Bad Gottleuba-Berggie??h??bel": "Bad Gottleuba-Berggießhübel",
        
        # Allgemeine ?? Zeichen-Korrekturen (nach spezifischen Fällen)
        # "??": "ö",  # Fallback entfernt - zu unspezifisch
        
        # Weitere häufige Fälle
        "H??se": "Häse",  # Häufig in Namen
        "H??hnel": "Höhnel",
        "M??ller": "Müller",
        "M??glitztalstra??e": "Müglitztalstraße",
        "Pratzschwitzer Stra??e": "Pratzschwitzer Straße",
        "Herbert-Liebsch- Str.": "Herbert-Liebsch-Straße",
        "Stra??e des Friedens": "Straße des Friedens",
        "Stra??e der MTS": "Straße der MTS",
        "Dresdner Landstrasse": "Dresdner Landstraße",
        "Kleine Basch??tzer": "Kleine Baschützer",
        "Kleine Basch??tzer Str.": "Kleine Baschützer Straße",
        
        # Zusätzliche Mojibake-Fälle aus den verbleibenden Warnungen
        "S??gewerk": "Sägewerk",
        "Sch??nfeld": "Schönfeld",
        "Glash??tte": "Glashütte",
        "haftungsbeschr??nkt": "haftungsbeschränkt",
        "Altnossener Stra??e": "Altnossener Straße",
        "Dorfstra??e": "Dorfstraße",
        "Stolpener Strasse": "Stolpener Straße",
        
        # Weitere spezifische Fälle
        "Am S??gewerk": "Am Sägewerk",
        "OT Sch??nfeld": "OT Schönfeld",
        "OT Luchau": "OT Luchau",  # Bereits korrekt
        "OT Sehma": "OT Sehma",    # Bereits korrekt
    }
    
    # Wende Kontext-Fixes an
    for corrupt, correct in context_fixes.items():
        text = text.replace(corrupt, correct)
    
    return text
