"""API-Routen für KI-gestützte Adresshilfe."""

from __future__ import annotations

import asyncio
import logging
from typing import List, Optional

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from common.normalize import normalize_address
from ingest.guards import assert_no_mojibake
from repositories import manual_repo
from repositories.geo_repo import upsert
from repositories.geo_fail_repo import clear as clear_fail
from services.geocode_fill import HEADERS, TIMEOUT, _geocode_variant
from services.geocode_persist import write_result
from services.llm_address_helper import get_address_helper

router = APIRouter()


class ManualAssistEntry(BaseModel):
    id: int
    raw_address: str
    reason: Optional[str]
    created_at: Optional[str]
    llm_suggestion: Optional[dict]


class ManualAssistResponse(BaseModel):
    entries: List[ManualAssistEntry]
    llm_enabled: bool


class ManualAssistGeocodeRequest(BaseModel):
    raw_address: str = Field(..., min_length=3, description="Originale Adresse aus dem Tourplan")
    formatted_address: str = Field(..., min_length=3, description="Bereinigte Adresse zum Geokodieren")
    by_user: Optional[str] = Field(None, description="Optionaler Benutzername")


@router.get("/api/manual/assist", tags=["manual"], response_model=ManualAssistResponse)
async def manual_assist_overview(limit: int = 20):
    """Liste offener Manual-Queue Einträge mit optionaler LLM-Unterstützung."""

    entries = manual_repo.list_open(limit=limit)
    helper = get_address_helper()
    llm_enabled = helper is not None

    results: List[ManualAssistEntry] = []

    if entries and helper:
        tasks = [asyncio.to_thread(helper.suggest, entry["raw_address"]) for entry in entries]
        suggestions = await asyncio.gather(*tasks, return_exceptions=True)
    else:
        suggestions = [None] * len(entries)

    for entry, suggestion in zip(entries, suggestions):
        suggestion_dict = None
        if suggestion and not isinstance(suggestion, Exception):
            suggestion_dict = suggestion.as_dict()
        elif isinstance(suggestion, Exception):  # pragma: no cover - Logging für Fehlerfälle
            logging.warning("LLM-Suggestion Fehler: %s", suggestion)

        results.append(
            ManualAssistEntry(
                id=entry.get("id"),
                raw_address=entry.get("raw_address", ""),
                reason=entry.get("reason"),
                created_at=str(entry.get("created_at")) if entry.get("created_at") else None,
                llm_suggestion=suggestion_dict,
            )
        )

    return ManualAssistResponse(entries=results, llm_enabled=llm_enabled)


@router.post("/api/manual/assist/geocode", tags=["manual"])
async def manual_assist_geocode(body: ManualAssistGeocodeRequest):
    """Geokodiert eine manuell bestätigte Adresse und speichert das Ergebnis."""

    formatted = body.formatted_address.strip()
    if not formatted:
        raise HTTPException(status_code=400, detail="Formatierte Adresse darf nicht leer sein")

    try:
        assert_no_mojibake(formatted)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Ungültige Zeichen in Adresse: {exc}")

    async with httpx.AsyncClient(timeout=TIMEOUT, headers=HEADERS) as client:
        result = await _geocode_variant(formatted, client, is_fallback=True)

    if not result:
        raise HTTPException(status_code=422, detail="Keine Koordinaten für den Vorschlag gefunden")

    result.setdefault("_note", "manual_assist")
    persisted = write_result(body.raw_address, [result])

    try:
        lat = float(result.get("lat"))
        lon = float(result.get("lon"))
        upsert(body.raw_address, lat, lon, source="manual_assist", by_user=body.by_user)
    except (TypeError, ValueError) as exc:  # pragma: no cover
        logging.warning("Konnte Koordinaten nicht als float speichern: %s", exc)

    manual_repo.close(normalize_address(body.raw_address))
    clear_fail(body.raw_address)

    return JSONResponse(
        {
            "ok": True,
            "formatted_address": formatted,
            "lat": float(result.get("lat")),
            "lon": float(result.get("lon")),
            "persisted": persisted,
        },
        media_type="application/json; charset=utf-8",
    )



