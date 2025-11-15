#!/usr/bin/env python3
"""
Safe Print Utility - Verhindert UnicodeEncodeError in der Konsole
"""

import sys
from typing import Any


def safe_print(*args: Any, **kwargs: Any) -> None:
    """
    Sicherer Print, der UnicodeEncodeError verhindert.
    Ersetzt nicht darstellbare Zeichen durch '?'.
    """
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # Konvertiere alle Args zu ASCII-sicheren Strings
        safe_args = []
        for arg in args:
            try:
                arg_str = str(arg)
                # Ersetze nicht darstellbare Zeichen durch '?'
                safe_str = arg_str.encode('ascii', errors='replace').decode('ascii')
                safe_args.append(safe_str)
            except Exception:
                safe_args.append('?')
        
        try:
            print(*safe_args, **kwargs)
        except Exception:
            # Letzter Fallback: Ignoriere komplett
            pass


def configure_console_utf8() -> bool:
    """
    Versucht, die Konsole auf UTF-8 umzustellen.
    Gibt True zurück wenn erfolgreich, sonst False.
    """
    try:
        # Versuche stdout/stderr auf UTF-8 umzustellen
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
            return True
        else:
            return False
    except Exception:
        return False


# Automatisch beim Import versuchen, Konsole umzustellen
_utf8_configured = configure_console_utf8()

if __name__ == "__main__":
    print(f"UTF-8 Konfiguration: {'Erfolgreich' if _utf8_configured else 'Fehlgeschlagen'}")
    print(f"stdout encoding: {sys.stdout.encoding}")
    print(f"stderr encoding: {sys.stderr.encoding}")
    
    # Test
    safe_print("Test: Umlaute öäü → sollte funktionieren")
    safe_print("Test: Spezialzeichen ← → ✓ → sollte funktionieren")

