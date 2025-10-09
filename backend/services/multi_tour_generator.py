"""
Multi-Tour-Generator für FAMO TrafficApp
Teilt große Kundenlisten automatisch in optimierte Einzeltouren auf
Beispiel: 40 Kunden → 6 Touren mit je 6-7 Kunden
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Tuple
import math

try:
    from .geo_validator import geo_validator, ValidationResult
    from .optimization_rules import OptimizationRules, default_rules
    from .ai_optimizer import AIOptimizer, Stop
except ImportError:
    # Fallback für direktes Ausführen
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).parent.parent))
    from services.geo_validator import geo_validator, ValidationResult
    from services.optimization_rules import OptimizationRules, default_rules
    from services.ai_optimizer import AIOptimizer, Stop
import asyncio


@dataclass
class Customer:
    id: int
    name: str
    address: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    priority: int = 1  # 1=normal, 2=wichtig, 3=kritisch
    time_window_start: Optional[str] = None  # "09:00"
    time_window_end: Optional[str] = None  # "17:00"


@dataclass
class GeneratedTour:
    tour_id: str
    customers: List[Customer]
    estimated_duration_minutes: int
    estimated_distance_km: float
    estimated_cost_euro: float
    tour_sequence: int  # 1, 2, 3, 4, 5, 6
    constraints_satisfied: bool
    optimization_notes: str


@dataclass
class MultiTourResult:
    tour_group_name: str  # "W-09:00"
    original_customer_count: int
    valid_customers: List[Customer]
    invalid_customers: List[Tuple[Customer, str]]  # (customer, reason)
    generated_tours: List[GeneratedTour]
    total_estimated_time: int
    total_estimated_cost: float
    optimization_summary: str


class MultiTourGenerator:
    """Generiert multiple optimierte Touren aus großer Kundenliste"""

    def __init__(self, rules: OptimizationRules = None):
        self.rules = rules or default_rules
        self.ai_optimizer = AIOptimizer(use_local=True)
        # Lokale Tour-Zählung - wird bei jedem neuen Import auf 0 zurückgesetzt
        self._global_tour_counter = 0

    def _number_to_letter(self, number: int) -> str:
        """Konvertiert eine Zahl (1-basiert) in einen Großbuchstaben (A, B, C...)."""
        if not isinstance(number, int) or number < 1:
            return str(number) # Fallback für ungültige Eingabe
        # ASCII-Wert von 'A' ist 65
        return chr(64 + number)

    def _get_next_tour_letter(self) -> str:
        """Gibt den nächsten fortlaufenden Tour-Buchstaben zurück"""
        self._global_tour_counter += 1
        return self._number_to_letter(self._global_tour_counter)

    async def generate_tours_from_customers(
        self, customers: List[Customer], tour_group_name: str
    ) -> MultiTourResult:
        """Hauptfunktion: 40 Kunden → 6 optimierte Touren"""

        # Tour-Zähler für jede neue Tour-Gruppe zurücksetzen
        self._global_tour_counter = 0
        
        print(
            f"🚀 Multi-Tour-Generator für '{tour_group_name}': {len(customers)} Kunden"
        )

        # 1. Geografische Validierung
        valid_customers, invalid_customers = await self._validate_customers(customers)
        print(
            f"✅ {len(valid_customers)} gültige Kunden, ❌ {len(invalid_customers)} ungültige"
        )

        if len(valid_customers) < 2:
            return MultiTourResult(
                tour_group_name=tour_group_name,
                original_customer_count=len(customers),
                valid_customers=valid_customers,
                invalid_customers=invalid_customers,
                generated_tours=[],
                total_estimated_time=0,
                total_estimated_cost=0.0,
                optimization_summary="Zu wenige gültige Kunden für Tour-Generierung",
            )

        # 2. Optimale Anzahl Touren berechnen
        optimal_tour_count = self._calculate_optimal_tour_count(valid_customers)
        print(f"📊 Optimale Tour-Anzahl: {optimal_tour_count}")

        # 3. KI-basierte geografische Clustering für alle W-Touren
        customer_groups = await self._ai_cluster_customers_into_tours(
            valid_customers, optimal_tour_count, tour_group_name
        )

        # 4. Jede Gruppe zu optimierter Tour verarbeiten mit KI
        generated_tours = []
        if not customer_groups:
            print("⚠️ Keine Kundengruppen zur Generierung vorhanden.")
        else:
            for idx, group in enumerate(customer_groups, 1):
                # KI-Optimierung für alle Touren
                tour = await self._optimize_customer_group_with_ai(group, tour_group_name, idx)
                print(
                    f"✅ Tour {idx}/{optimal_tour_count} (KI-optimiert): {len(group)} Kunden, {tour.estimated_duration_minutes}min"
                )
                generated_tours.append(tour)

        # 5. Gesamtstatistiken berechnen
        total_time = sum(tour.estimated_duration_minutes for tour in generated_tours)
        total_cost = sum(tour.estimated_cost_euro for tour in generated_tours)

        summary = self._create_optimization_summary(
            generated_tours, valid_customers, invalid_customers
        )

        return MultiTourResult(
            tour_group_name=tour_group_name,
            original_customer_count=len(customers),
            valid_customers=valid_customers,
            invalid_customers=invalid_customers,
            generated_tours=generated_tours,
            total_estimated_time=total_time,
            total_estimated_cost=total_cost,
            optimization_summary=summary,
        )

    async def _validate_customers(
        self, customers: List[Customer]
    ) -> Tuple[List[Customer], List[Tuple[Customer, str]]]:
        """Prüft alle Kunden auf geografische Gültigkeit"""

        valid = []
        invalid = []

        for customer in customers:
            if customer.lat is None or customer.lon is None:
                invalid.append((customer, "Keine Koordinaten verfügbar"))
                continue

            result, error = geo_validator.validate_coordinates(
                customer.lat, customer.lon, customer.address
            )

            if result == ValidationResult.VALID:
                valid.append(customer)
            else:
                reason = error.message if error else "Unbekannter Validierungsfehler"
                invalid.append((customer, reason))

        return valid, invalid

    def _calculate_optimal_tour_count(self, customers: List[Customer]) -> int:
        """Berechnet optimale Anzahl Touren basierend auf Constraints"""

        customer_count = len(customers)
        max_per_tour = self.rules.max_stops_per_tour

        # Mindestanzahl Touren basierend auf Stopp-Limit
        min_tours = math.ceil(customer_count / max_per_tour)

        # Optimaler Bereich: 6-8 Kunden pro Tour für beste Effizienz
        optimal_per_tour = 7
        optimal_tours = math.ceil(customer_count / optimal_per_tour)

        # Wähle das Maximum für Sicherheit
        return max(min_tours, optimal_tours)

    async def _ai_cluster_customers_into_tours(
        self, customers: List[Customer], tour_count: int, tour_group_name: str
    ) -> List[List[Customer]]:
        """KI-basierte geografische Clustering für optimale Tourenaufteilung"""

        if tour_count == 1:
            return [customers]

        print(f"🤖 KI-Clustering für {len(customers)} Kunden in {tour_count} Touren...")

        try:
            # Konvertiere Kunden zu Stops für KI
            stops = []
            for customer in customers:
                stops.append(Stop(
                    id=str(customer.id),
                    name=customer.name,
                    address=customer.address,
                    lat=customer.lat,
                    lon=customer.lon,
                    sequence=0  # Wird von KI neu bestimmt
                ))

            # KI-basierte Clustering
            clustering_result = await self.ai_optimizer.cluster_stops_into_tours(stops, self.rules)
            
            if not clustering_result or 'tours' not in clustering_result:
                print("⚠️ KI-Clustering fehlgeschlagen, verwende Fallback")
                return self._fallback_clustering(customers, tour_count)

            # Konvertiere KI-Ergebnis zurück zu Kundengruppen
            customer_groups = []
            for tour_data in clustering_result['tours']:
                tour_customers = []
                for customer_id in tour_data.get('customer_ids', []):
                    customer = next((c for c in customers if str(c.id) == str(customer_id)), None)
                    if customer:
                        tour_customers.append(customer)
                
                if tour_customers:
                    customer_groups.append(tour_customers)

            print(f"✅ KI-Clustering erfolgreich: {len(customer_groups)} Touren erstellt")
            return customer_groups

        except Exception as e:
            print(f"❌ KI-Clustering Fehler: {e}, verwende Fallback")
            return self._fallback_clustering(customers, tour_count)

    def _fallback_clustering(self, customers: List[Customer], tour_count: int) -> List[List[Customer]]:
        """Fallback-Clustering wenn KI fehlschlägt"""
        print("🔄 Verwende Fallback-Clustering...")
        
        if tour_count == 1:
            return [customers]

        # Einfache geografische Clustering-Strategie
        depot_lat, depot_lon = self.rules.depot_lat, self.rules.depot_lon

        # Berechne Distanz zu FAMO für jeden Kunden
        customers_with_distance = []
        for customer in customers:
            distance = self._calculate_distance(
                customer.lat, customer.lon, depot_lat, depot_lon
            )
            customers_with_distance.append((customer, distance))

        # Sortiere: Priorität zuerst, dann Distanz
        customers_with_distance.sort(key=lambda x: (x[0].priority, x[1]), reverse=True)

        # Verteile gleichmäßig auf Touren
        groups = [[] for _ in range(tour_count)]
        for idx, (customer, _) in enumerate(customers_with_distance):
            group_idx = idx % tour_count
            groups[group_idx].append(customer)

        # Entferne leere Gruppen
        return [group for group in groups if group]

    async def _optimize_customer_group_with_ai(
        self, customers: List[Customer], base_name: str, sequence: int
    ) -> GeneratedTour:
        """Optimiert eine Kundengruppe zu einer Tour mit KI"""

        # Erstelle den Tour-ID basierend auf dem neuen Schema mit globaler Zählung
        tour_letter = self._get_next_tour_letter()
        tour_id = f"{base_name} - {tour_letter}-Tour"

        # Konvertiere zu Stop-Objekten für AI-Optimizer
        stops = []
        for idx, customer in enumerate(customers):
            stops.append(
                Stop(
                    id=str(customer.id),
                    name=customer.name,
                    address=customer.address,
                    lat=customer.lat,
                    lon=customer.lon,
                    sequence=idx + 1,
                )
            )

        try:
            print(f"🤖 KI-Optimierung für Tour {tour_letter}: {len(customers)} Kunden")
            
            # KI-Optimierung für diese Gruppe
            result = await self.ai_optimizer.optimize_route(
                stops, self.rules.depot_lat, self.rules.depot_lon, self.rules
            )

            # Zeit-Constraints prüfen
            driving_time = result.estimated_time_minutes or 0
            service_time = len(customers) * self.rules.service_time_per_customer_minutes
            return_time = self.rules.return_trip_buffer_minutes
            total_time = driving_time + service_time + return_time

            constraints_satisfied = total_time <= (
                self.rules.max_driving_time_to_last_customer
                + self.rules.return_trip_buffer_minutes
            )

            # Kosten schätzen
            distance = result.total_distance_km or self._estimate_distance(customers)
            fuel_cost = (
                (distance / 100)
                * self.rules.fuel_consumption_per_100km
                * self.rules.fuel_price_per_liter
            )
            time_cost = (total_time / 60) * self.rules.driver_cost_per_hour
            vehicle_cost = distance * self.rules.vehicle_depreciation_per_km
            total_cost = fuel_cost + time_cost + vehicle_cost

            optimization_notes = result.reasoning or "KI-Optimierung angewendet"
            
            print(f"✅ KI-Optimierung erfolgreich: {total_time}min, {distance:.1f}km, {total_cost:.2f}€")

        except Exception as e:
            print(f"❌ KI-Optimierung Fehler: {e}, verwende Fallback")
            # Fallback bei KI-Fehlern
            total_time = self._estimate_time_simple(customers)
            distance = self._estimate_distance(customers)
            total_cost = self._estimate_cost_simple(distance, total_time)
            constraints_satisfied = True  # Konservative Annahme
            optimization_notes = f"Fallback-Optimierung verwendet (KI-Fehler: {str(e)})"

        return GeneratedTour(
            tour_id=tour_id,
            customers=customers,
            estimated_duration_minutes=total_time,
            estimated_distance_km=distance,
            estimated_cost_euro=total_cost,
            tour_sequence=sequence,
            constraints_satisfied=constraints_satisfied,
            optimization_notes=optimization_notes,
        )

    def _calculate_distance(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """Luftlinie-Distanz in km"""
        import math

        R = 6371  # Erdradius
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(
            math.radians(lat1)
        ) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) * math.sin(dlon / 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def _estimate_distance(self, customers: List[Customer]) -> float:
        """Schätzt Gesamtdistanz einer Tour"""
        if not customers:
            return 0.0

        total_distance = 0.0
        depot_lat, depot_lon = self.rules.depot_lat, self.rules.depot_lon

        # FAMO → erster Kunde
        if customers:
            total_distance += self._calculate_distance(
                depot_lat, depot_lon, customers[0].lat, customers[0].lon
            )

        # Kunde zu Kunde
        for i in range(len(customers) - 1):
            total_distance += self._calculate_distance(
                customers[i].lat,
                customers[i].lon,
                customers[i + 1].lat,
                customers[i + 1].lon,
            )

        # Letzter Kunde → FAMO
        if customers:
            total_distance += self._calculate_distance(
                customers[-1].lat, customers[-1].lon, depot_lat, depot_lon
            )

        # Korrekturfaktor für Straßen
        return total_distance * 1.3

    def _estimate_time_simple(self, customers: List[Customer]) -> int:
        """Einfache Zeitschätzung"""
        distance = self._estimate_distance(customers)
        driving_time = (distance / 30) * 60  # 30 km/h Durchschnitt in Minuten
        service_time = len(customers) * self.rules.service_time_per_customer_minutes
        return int(driving_time + service_time + self.rules.return_trip_buffer_minutes)

    def _estimate_cost_simple(self, distance: float, time_minutes: int) -> float:
        """Einfache Kostenschätzung"""
        fuel = (
            (distance / 100)
            * self.rules.fuel_consumption_per_100km
            * self.rules.fuel_price_per_liter
        )
        driver = (time_minutes / 60) * self.rules.driver_cost_per_hour
        vehicle = distance * self.rules.vehicle_depreciation_per_km
        return fuel + driver + vehicle

    def _create_optimization_summary(
        self,
        tours: List[GeneratedTour],
        valid: List[Customer],
        invalid: List[Tuple[Customer, str]],
    ) -> str:
        """Erstellt Zusammenfassung der Multi-Tour-Optimierung"""

        total_customers = len(valid)
        tour_count = len(tours)
        avg_customers_per_tour = total_customers / tour_count if tour_count > 0 else 0

        constraints_ok = sum(1 for tour in tours if tour.constraints_satisfied)

        summary = f"""MULTI-TOUR OPTIMIERUNG ABGESCHLOSSEN:

📊 STATISTIKEN:
- Ursprünglich: {len(valid) + len(invalid)} Kunden
- Gültig: {len(valid)} Kunden  
- Ungültig: {len(invalid)} Kunden (außerhalb Geschäftsgebiet)
- Generierte Touren: {tour_count}
- Ø Kunden pro Tour: {avg_customers_per_tour:.1f}

✅ CONSTRAINTS:
- Touren unter Zeitlimit: {constraints_ok}/{tour_count}
- Max. Zeit pro Tour: {self.rules.max_driving_time_to_last_customer + self.rules.return_trip_buffer_minutes} Minuten
- Verweilzeit berücksichtigt: {self.rules.service_time_per_customer_minutes} min/Kunde

💰 GESCHÄTZTE KOSTEN:
- Gesamtkosten: {sum(tour.estimated_cost_euro for tour in tours):.2f} €
- Ø pro Tour: {sum(tour.estimated_cost_euro for tour in tours) / len(tours) if tours else 0:.2f} €
"""

        if invalid:
            summary += "\n⚠️ PROBLEMATISCHE ADRESSEN:\n"
            for customer, reason in invalid[:5]:  # Nur erste 5
                summary += f"- {customer.name}: {reason}\n"
            if len(invalid) > 5:
                summary += f"... und {len(invalid) - 5} weitere\n"

        return summary


# Test-Funktion
async def test_multi_tour_generator():
    """Test der Multi-Tour-Generierung"""

    # Test-Kunden aus verschiedenen Regionen
    test_customers = [
        Customer(
            1,
            "Kunde Leipzig",
            "Augustusplatz 10, 04109 Leipzig",
            51.3397,
            12.3731,
            priority=2,
        ),
        Customer(2, "Kunde Dresden", "Hauptstraße 1, 01067 Dresden", 51.0504, 13.7373),
        Customer(
            3, "Kunde Potsdam", "Brandenburger Str. 5, 14467 Potsdam", 52.3906, 13.0645
        ),
        Customer(
            4, "Kunde Magdeburg", "Breiter Weg 10, 39104 Magdeburg", 52.1205, 11.6276
        ),
        Customer(5, "Kunde Erfurt", "Anger 1, 99084 Erfurt", 50.9848, 11.0299),
        Customer(
            6, "Kunde München", "Marienplatz 1, 80331 München", 48.1371, 11.5754
        ),  # Ungültig!
        Customer(7, "Kunde Chemnitz", "Markt 1, 09111 Chemnitz", 50.8322, 12.9252),
        Customer(
            8, "Kunde Hamburg", "Rathausmarkt 1, 20095 Hamburg", 53.5511, 9.9937
        ),  # Ungültig!
    ]

    generator = MultiTourGenerator()
    result = await generator.generate_tours_from_customers(
        test_customers, "W-09:00-Test"
    )

    print("🎯 MULTI-TOUR TEST-ERGEBNIS:")
    print(f"📋 {result.optimization_summary}")

    for tour in result.generated_tours:
        print(f"\n🚛 {tour.tour_id}:")
        print(f"   Kunden: {len(tour.customers)}")
        print(f"   Zeit: {tour.estimated_duration_minutes} min")
        print(f"   Distanz: {tour.estimated_distance_km:.1f} km")
        print(f"   Kosten: {tour.estimated_cost_euro:.2f} €")
        print(f"   Constraints OK: {'✅' if tour.constraints_satisfied else '❌'}")


if __name__ == "__main__":
    asyncio.run(test_multi_tour_generator())
