# Cursor Leitplanken

## Unantastbar (keine Änderungen durch Prompts ohne explizite Freigabe)
- `./Tourplaene/**` (Originale)
- `tools/orig_integrity.py`, `ingest/reader.py`

## Encoding‑Kontrakt
- **Lesen**: heuristisch (cp850 / utf‑8‑sig / latin‑1)
- **Schreiben/Export/Logs**: **immer UTF‑8**

## Prompt‑Pflicht
- Jede Änderung: Akzeptanzkriterien + Test + minimaler Diff
- Keine neuen Abhängigkeiten ohne Zustimmung
- Prompts, die „nur lesen" sagen → **kein** Schreiben

## Minimal‑Diff
- Nur die im Prompt genannten Dateien ändern

## CI/SLOs (siehe tools/ci_slo_check.py)
- Erkennungsquote ≥ 95 %, Mojibake = 0, Integrität OK

## Branch-Strategie
- Governance-Änderungen: `governance/*`
- Feature-Entwicklung: `feature/*`
- Bugfixes: `fix/*`

## Code-Qualität
- Alle Änderungen müssen Tests haben
- Pre-commit Hooks müssen bestehen
- SLO-Checks müssen grün sein
