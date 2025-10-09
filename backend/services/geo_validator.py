"""
Geografischer Validator für FAMO TrafficApp
Validiert Kundenadressen auf das FAMO-Geschäftsgebiet:
- Sachsen, Brandenburg, Sachsen-Anhalt, Thüringen
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Tuple, List
from enum import Enum


class ValidationResult(Enum):
    VALID = "valid"
    OUTSIDE_SERVICE_AREA = "outside_service_area"
    GEOCODING_FAILED = "geocoding_failed"
    INVALID_COORDINATES = "invalid_coordinates"


@dataclass
class GeoValidationError:
    result: ValidationResult
    message: str
    suggested_action: str
    detected_region: Optional[str] = None


@dataclass
class BundeslandBounds:
    """Geografische Grenzen der Bundesländer"""

    name: str
    min_lat: float
    max_lat: float
    min_lon: float
    max_lon: float


class GeoValidator:
    """Validiert Kundenadressen auf FAMO-Geschäftsgebiet"""

    def __init__(self):
        # Definiere die geografischen Grenzen der relevanten Bundesländer
        self.service_areas = [
            # Sachsen (Hauptgeschäftsgebiet)
            BundeslandBounds(
                name="Sachsen",
                min_lat=50.171,
                max_lat=51.685,  # Vogtland bis Lausitz
                min_lon=11.872,
                max_lon=15.038,  # Plauen bis Görlitz
            ),
            # Brandenburg
            BundeslandBounds(
                name="Brandenburg",
                min_lat=51.359,
                max_lat=53.558,  # Süd bis Nord-Brandenburg
                min_lon=11.268,
                max_lon=14.766,  # West bis Ost-Brandenburg
            ),
            # Sachsen-Anhalt
            BundeslandBounds(
                name="Sachsen-Anhalt",
                min_lat=50.937,
                max_lat=53.042,  # Harz bis Altmark
                min_lon=10.565,
                max_lon=13.182,  # Harz bis Elbe
            ),
            # Thüringen
            BundeslandBounds(
                name="Thüringen",
                min_lat=50.204,
                max_lat=51.649,  # Rhön bis Hainich
                min_lon=9.877,
                max_lon=12.653,  # Wartburg bis Altenburger Land
            ),
        ]

        # Bekannte problematische Regionen für bessere Fehlermeldungen
        self.known_outside_regions = {
            "Bayern": (48.0, 50.5, 8.5, 13.8),
            "Baden-Württemberg": (47.5, 49.8, 7.5, 10.5),
            "Hessen": (49.4, 51.7, 7.8, 10.2),
            "Niedersachsen": (51.3, 53.9, 6.6, 11.6),
            "Nordrhein-Westfalen": (50.3, 52.5, 5.9, 9.5),
            "Mecklenburg-Vorpommern": (53.1, 54.7, 10.6, 14.4),
            "Schleswig-Holstein": (53.4, 55.1, 7.9, 11.3),
            "Ostsee-Region": (53.8, 55.0, 10.0, 15.0),
            "Nordsee-Region": (53.3, 55.0, 6.0, 9.0),
        }

    def validate_coordinates(
        self, lat: float, lon: float, address: str = ""
    ) -> Tuple[ValidationResult, Optional[GeoValidationError]]:
        """Validiert Koordinaten gegen FAMO-Geschäftsgebiet"""

        # Basis-Koordinaten-Check
        if not self._are_valid_coordinates(lat, lon):
            return ValidationResult.INVALID_COORDINATES, GeoValidationError(
                result=ValidationResult.INVALID_COORDINATES,
                message=f"Ungültige Koordinaten: {lat}, {lon}",
                suggested_action="Adresse erneut geocodieren oder manuell korrigieren",
            )

        # Prüfe ob in einem der Service-Gebiete
        for area in self.service_areas:
            if self._is_in_bounds(lat, lon, area):
                return ValidationResult.VALID, None

        # Außerhalb des Service-Gebiets - ermittle wo
        detected_region = self._detect_region(lat, lon)

        return ValidationResult.OUTSIDE_SERVICE_AREA, GeoValidationError(
            result=ValidationResult.OUTSIDE_SERVICE_AREA,
            message="Adresse liegt außerhalb des FAMO-Geschäftsgebiets",
            suggested_action=self._get_suggestion_for_region(detected_region),
            detected_region=detected_region,
        )

    def validate_address_batch(
        self, addresses_with_coords: List[Tuple[str, float, float]]
    ) -> List[Tuple[str, ValidationResult, Optional[GeoValidationError]]]:
        """Validiert mehrere Adressen auf einmal"""
        results = []

        for address, lat, lon in addresses_with_coords:
            result, error = self.validate_coordinates(lat, lon, address)
            results.append((address, result, error))

        return results

    def get_service_area_summary(self) -> dict:
        """Gibt Übersicht über das Service-Gebiet zurück"""
        return {
            "bundeslaender": [area.name for area in self.service_areas],
            "total_area_bounds": {
                "min_lat": min(area.min_lat for area in self.service_areas),
                "max_lat": max(area.max_lat for area in self.service_areas),
                "min_lon": min(area.min_lon for area in self.service_areas),
                "max_lon": max(area.max_lon for area in self.service_areas),
            },
            "hauptstandort": {
                "name": "FAMO Dresden",
                "address": "Stuttgarter Str. 33, 01189 Dresden",
                "lat": 51.0111988,
                "lon": 13.7016485,
            },
        }

    def _are_valid_coordinates(self, lat: float, lon: float) -> bool:
        """Prüft ob Koordinaten grundsätzlich gültig sind"""
        return (
            -90 <= lat <= 90
            and -180 <= lon <= 180
            and
            # Deutschland liegt etwa zwischen diesen Koordinaten
            47 <= lat <= 55
            and 5 <= lon <= 16
        )

    def _is_in_bounds(self, lat: float, lon: float, bounds: BundeslandBounds) -> bool:
        """Prüft ob Koordinaten in einem Bundesland liegen"""
        return (
            bounds.min_lat <= lat <= bounds.max_lat
            and bounds.min_lon <= lon <= bounds.max_lon
        )

    def _detect_region(self, lat: float, lon: float) -> Optional[str]:
        """Versucht zu erkennen in welcher Region die Koordinaten liegen"""
        for region_name, (
            min_lat,
            max_lat,
            min_lon,
            max_lon,
        ) in self.known_outside_regions.items():
            if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
                return region_name

        # Grobe Himmelsrichtung wenn keine spezifische Region erkannt
        if lat < 50:
            return "Süddeutschland"
        elif lat > 52.5:
            return "Norddeutschland"
        elif lon < 10:
            return "Westdeutschland"
        else:
            return "Unbekannte Region"

    def _get_suggestion_for_region(self, detected_region: Optional[str]) -> str:
        """Gibt regionsspezifische Korrekturvorschläge"""
        if not detected_region:
            return "Adresse prüfen - liegt außerhalb von Sachsen, Brandenburg, Sachsen-Anhalt, Thüringen"

        suggestions = {
            "Bayern": "Adresse liegt in Bayern - zu weit südlich für FAMO-Touren",
            "Baden-Württemberg": "Adresse liegt in Baden-Württemberg - außerhalb des Service-Gebiets",
            "Ostsee-Region": "Adresse an der Ostsee erkannt - zu weit nördlich",
            "Nordsee-Region": "Adresse an der Nordsee erkannt - zu weit westlich",
            "Süddeutschland": "Adresse zu weit südlich - FAMO liefert nur in Mitteldeutschland",
            "Norddeutschland": "Adresse zu weit nördlich - außerhalb des Geschäftsgebiets",
            "Westdeutschland": "Adresse zu weit westlich - außerhalb des Service-Radius",
        }

        return suggestions.get(
            detected_region,
            f"Adresse liegt in {detected_region} - außerhalb des FAMO-Geschäftsgebiets",
        )


# Globaler Validator
geo_validator = GeoValidator()


# Convenience-Funktionen
def validate_customer_location(
    lat: float, lon: float, address: str = ""
) -> Tuple[bool, Optional[str]]:
    """Einfache Validierung - True wenn im Service-Gebiet"""
    result, error = geo_validator.validate_coordinates(lat, lon, address)

    if result == ValidationResult.VALID:
        return True, None
    else:
        return False, error.message if error else "Unbekannter Validierungsfehler"


def get_validation_stats_for_batch(
    addresses_with_coords: List[Tuple[str, float, float]],
) -> dict:
    """Statistiken für Batch-Validierung"""
    results = geo_validator.validate_address_batch(addresses_with_coords)

    stats = {
        "total": len(results),
        "valid": 0,
        "outside_area": 0,
        "invalid_coords": 0,
        "detected_regions": {},
    }

    for address, result, error in results:
        if result == ValidationResult.VALID:
            stats["valid"] += 1
        elif result == ValidationResult.OUTSIDE_SERVICE_AREA:
            stats["outside_area"] += 1
            if error and error.detected_region:
                region = error.detected_region
                stats["detected_regions"][region] = (
                    stats["detected_regions"].get(region, 0) + 1
                )
        elif result == ValidationResult.INVALID_COORDINATES:
            stats["invalid_coords"] += 1

    return stats


if __name__ == "__main__":
    # Test-Beispiele
    validator = GeoValidator()

    test_locations = [
        ("FAMO Dresden", 51.0111988, 13.7016485),
        ("Leipzig", 51.3397, 12.3731),  # Sachsen - Valid
        ("Potsdam", 52.3906, 13.0645),  # Brandenburg - Valid
        ("Magdeburg", 52.1205, 11.6276),  # Sachsen-Anhalt - Valid
        ("Erfurt", 50.9848, 11.0299),  # Thüringen - Valid
        ("Hamburg", 53.5511, 9.9937),  # Zu weit nördlich
        ("München", 48.1351, 11.5820),  # Zu weit südlich
        ("Rügen/Ostsee", 54.5260, 13.3890),  # Ostsee
    ]

    print("🔍 FAMO Geo-Validator Test:")
    print(
        f"📍 Service-Gebiet: {', '.join(area.name for area in validator.service_areas)}"
    )
    print()

    for name, lat, lon in test_locations:
        result, error = validator.validate_coordinates(lat, lon, name)
        status = "✅" if result == ValidationResult.VALID else "❌"
        print(f"{status} {name}: {result.value}")
        if error:
            print(f"   → {error.message}")
            print(f"   → {error.suggested_action}")
        print()
