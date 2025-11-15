"""LLM-gestützte Adressnormalisierung und Vorschläge."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Dict, Optional

try:
    import openai

    OPENAI_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI Paket nicht installiert – LLM-Adressenhilfe deaktiviert.")


@dataclass
class AddressSuggestion:
    raw_response: str
    formatted_address: str
    street: str
    postal_code: str
    city: str
    confidence: float
    notes: Optional[str]
    model_used: Optional[str]

    def as_dict(self) -> Dict[str, object]:
        return {
            "formatted_address": self.formatted_address,
            "street": self.street,
            "postal_code": self.postal_code,
            "city": self.city,
            "confidence": self.confidence,
            "notes": self.notes,
            "model_used": self.model_used,
        }


class LLMAddressHelper:
    """Hilft bei der Normalisierung fehlerhafter Adressen per LLM."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.logger = logging.getLogger(__name__)
        if not api_key:
            try:
                from services.secure_key_manager import get_secure_key  # type: ignore

                api_key = get_secure_key("openai")
            except Exception:  # pragma: no cover - best effort
                api_key = None

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("LLM_ADDRESS_MODEL", os.getenv("LLM_MODEL", "gpt-4o-mini"))
        self.temperature = float(os.getenv("LLM_ADDRESS_TEMPERATURE", "0.1"))
        self.max_tokens = int(os.getenv("LLM_ADDRESS_MAX_TOKENS", "300"))

        self.enabled = False
        self.client = None
        self.cache: Dict[str, AddressSuggestion] = {}

        if OPENAI_AVAILABLE and self.api_key:
            try:
                self.client = openai.OpenAI(api_key=self.api_key)
                self.enabled = True
                self.logger.info("LLMAddressHelper aktiviert (%s)", self.model)
            except Exception as exc:  # pragma: no cover - Netzwerkfehler o.ä.
                self.logger.error("Konnte OpenAI-Client nicht initialisieren: %s", exc)
                self.enabled = False
        else:
            self.enabled = False
            if not OPENAI_AVAILABLE:
                self.logger.info("LLMAddressHelper deaktiviert – OpenAI-Paket fehlt")
            else:
                self.logger.info("LLMAddressHelper deaktiviert – kein API-Key")

    def suggest(self, raw_address: str, *, company_name: Optional[str] = None) -> Optional[AddressSuggestion]:
        """Liefert eine korrigierte Adresse als Vorschlag."""

        key = (raw_address or "").strip()
        if not key:
            return None

        if key in self.cache:
            return self.cache[key]

        if not self.enabled or not self.client:
            return None

        prompt = self._build_prompt(raw_address, company_name)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Du bist ein Assistent für Adressnormalisierung. "
                            "Antworte ausschließlich mit gültigem JSON ohne Markdown."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )

            text = (response.choices[0].message.content or "").strip()
            suggestion = self._parse_response(text)
            if suggestion:
                suggestion.model_used = self.model
                self.cache[key] = suggestion
                return suggestion

            self.logger.warning("LLM lieferte keine verwertbare Adresse: %s", text[:120])
            return None

        except Exception as exc:  # pragma: no cover
            self.logger.error("LLM-Adresse fehlgeschlagen: %s", exc)
            return None

    def _build_prompt(self, address: str, company_name: Optional[str]) -> str:
        company_block = f"\nFirmenname: {company_name}" if company_name else ""
        return (
            "Analysiere die folgende deutsche Adresse und korrigiere Schreibfehler. "
            "Wenn PLZ oder Ort fehlen, versuche sie herzuleiten. "
            "Antworte strikt als JSON mit den Feldern "
            "street, postal_code, city, formatted_address, confidence (0-1) und notes.\n\n"
            f"Adresse: {address}{company_block}\n"
        )

    def _parse_response(self, raw_text: str) -> Optional[AddressSuggestion]:
        text = raw_text.strip()
        if "```" in text:
            # Entferne Code-Fences
            first = text.find("```")
            last = text.rfind("```")
            if first != -1 and last > first:
                text = text[first + 3 : last]
                text = text.replace("json", "", 1).strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return None

        street = str(data.get("street") or "").strip()
        postal_code = str(data.get("postal_code") or "").strip()
        city = str(data.get("city") or "").strip()
        formatted = str(data.get("formatted_address") or "").strip()
        confidence = float(data.get("confidence") or 0.6)
        notes = data.get("notes")

        if not formatted:
            formatted = ", ".join(filter(None, [street, f"{postal_code} {city}".strip()]))
            if not formatted:
                return None

        return AddressSuggestion(
            raw_response=text,
            formatted_address=formatted,
            street=street,
            postal_code=postal_code,
            city=city,
            confidence=min(max(confidence, 0.0), 1.0),
            notes=notes if isinstance(notes, str) else None,
            model_used=None,
        )


_helper_instance: Optional[LLMAddressHelper] = None


def get_address_helper() -> Optional[LLMAddressHelper]:
    """Singleton-Zugriff auf den LLM-Helper."""

    global _helper_instance
    if _helper_instance is None:
        _helper_instance = LLMAddressHelper()
    if not _helper_instance.enabled:
        return None
    return _helper_instance



