from datetime import datetime, date
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import logging

from ..db.schema import Tour, TourStop, TourPerformance, Customer, TourStatistics
from ..db.dao import get_db_session

logger = logging.getLogger(__name__)

class TourManager:
    """Verwaltet die Erstellung, Speicherung und Abfrage von Touren"""
    
    def __init__(self):
        self.db_session = get_db_session()
    
    def create_tour(self, tour_data: Dict) -> Tour:
        """Erstellt eine neue Tour in der Datenbank"""
        try:
            tour = Tour(
                tour_name=tour_data['tour_name'],
                tour_type=tour_data['tour_type'],
                tour_date=datetime.strptime(tour_data['tour_date'], '%Y-%m-%d').date(),
                total_customers=tour_data['total_customers'],
                total_distance_km=tour_data['total_distance_km'],
                total_duration_min=tour_data['total_duration_min'],
                status='active'
            )
            
            self.db_session.add(tour)
            self.db_session.commit()
            self.db_session.refresh(tour)
            
            logger.info(f"Tour {tour.tour_name} erfolgreich erstellt (ID: {tour.id})")
            return tour
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Fehler beim Erstellen der Tour: {e}")
            raise
    
    def add_tour_stops(self, tour_id: int, stops_data: List[Dict]) -> List[TourStop]:
        """Fügt Stopps zu einer Tour hinzu"""
        try:
            stops = []
            for i, stop_data in enumerate(stops_data):
                stop = TourStop(
                    tour_id=tour_id,
                    customer_id=stop_data['customer_id'],
                    sequence_order=i + 1,
                    estimated_arrival_time=stop_data.get('estimated_arrival_time'),
                    estimated_departure_time=stop_data.get('estimated_departure_time'),
                    dwell_time_min=stop_data.get('dwell_time_min', 2)
                )
                stops.append(stop)
            
            self.db_session.add_all(stops)
            self.db_session.commit()
            
            logger.info(f"{len(stops)} Stopps zu Tour {tour_id} hinzugefügt")
            return stops
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Fehler beim Hinzufügen der Stopps: {e}")
            raise
    
    def update_stop_sequence(self, tour_id: int, new_sequence: List[int]) -> bool:
        """Aktualisiert die Reihenfolge der Stopps (Drag & Drop)"""
        try:
            for new_order, stop_id in enumerate(new_sequence, 1):
                stop = self.db_session.query(TourStop).filter(
                    and_(TourStop.tour_id == tour_id, TourStop.id == stop_id)
                ).first()
                
                if stop:
                    stop.sequence_order = new_order
            
            self.db_session.commit()
            logger.info(f"Reihenfolge der Stopps für Tour {tour_id} aktualisiert")
            return True
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Fehler beim Aktualisieren der Stopp-Reihenfolge: {e}")
            return False
    
    def get_tour_with_stops(self, tour_id: int) -> Optional[Dict]:
        """Holt eine Tour mit allen Stopps und Kundendaten"""
        try:
            tour = self.db_session.query(Tour).filter(Tour.id == tour_id).first()
            if not tour:
                return None
            
            stops = self.db_session.query(TourStop).filter(
                TourStop.tour_id == tour_id
            ).order_by(TourStop.sequence_order).all()
            
            tour_data = {
                'id': tour.id,
                'tour_name': tour.tour_name,
                'tour_type': tour.tour_type,
                'tour_date': tour.tour_date.strftime('%Y-%m-%d'),
                'total_customers': tour.total_customers,
                'total_distance_km': tour.total_distance_km,
                'total_duration_min': tour.total_duration_min,
                'status': tour.status,
                'stops': []
            }
            
            for stop in stops:
                customer = self.db_session.query(Customer).filter(
                    Customer.id == stop.customer_id
                ).first()
                
                if customer:
                    stop_data = {
                        'id': stop.id,
                        'sequence_order': stop.sequence_order,
                        'customer': {
                            'id': customer.id,
                            'kundennr': customer.kundennr,
                            'name': customer.name,
                            'street': customer.street,
                            'plz': customer.plz,
                            'city': customer.city,
                            'lat': customer.lat,
                            'lon': customer.lon,
                            'is_bar_cash': customer.is_bar_cash
                        },
                        'estimated_arrival_time': stop.estimated_arrival_time,
                        'estimated_departure_time': stop.estimated_departure_time,
                        'dwell_time_min': stop.dwell_time_min
                    }
                    tour_data['stops'].append(stop_data)
            
            return tour_data
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Tour {tour_id}: {e}")
            return None
    
    def get_tours_by_date(self, tour_date: str) -> List[Dict]:
        """Holt alle Touren für ein bestimmtes Datum"""
        try:
            date_obj = datetime.strptime(tour_date, '%Y-%m-%d').date()
            tours = self.db_session.query(Tour).filter(Tour.tour_date == date_obj).all()
            
            tour_list = []
            for tour in tours:
                tour_data = {
                    'id': tour.id,
                    'tour_name': tour.tour_name,
                    'tour_type': tour.tour_type,
                    'total_customers': tour.total_customers,
                    'total_distance_km': tour.total_distance_km,
                    'total_duration_min': tour.total_duration_min,
                    'status': tour.status
                }
                tour_list.append(tour_data)
            
            return tour_list
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Touren für {tour_date}: {e}")
            return []
    
    def complete_tour(self, tour_id: int, performance_data: Dict) -> bool:
        """Markiert eine Tour als abgeschlossen und speichert Performance-Daten"""
        try:
            tour = self.db_session.query(Tour).filter(Tour.id == tour_id).first()
            if not tour:
                return False
            
            tour.status = 'completed'
            
            performance = TourPerformance(
                tour_id=tour_id,
                planned_distance_km=tour.total_distance_km,
                actual_distance_km=performance_data.get('actual_distance_km', tour.total_distance_km),
                planned_duration_min=tour.total_duration_min,
                actual_duration_min=performance_data.get('actual_duration_min', tour.total_duration_min),
                fuel_consumption_l=performance_data.get('fuel_consumption_l'),
                driver_notes=performance_data.get('driver_notes'),
                customer_feedback=performance_data.get('customer_feedback'),
                weather_conditions=performance_data.get('weather_conditions'),
                traffic_conditions=performance_data.get('traffic_conditions'),
                completed_at=datetime.utcnow()
            )
            
            self.db_session.add(performance)
            self.db_session.commit()
            
            logger.info(f"Tour {tour_id} als abgeschlossen markiert")
            return True
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Fehler beim Abschließen der Tour {tour_id}: {e}")
            return False
    
    def get_tour_statistics(self, start_date: str, end_date: str, tour_type: Optional[str] = None) -> Dict:
        """Holt Tour-Statistiken für einen Zeitraum"""
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            query = self.db_session.query(Tour).filter(
                and_(Tour.tour_date >= start, Tour.tour_date <= end)
            )
            
            if tour_type:
                query = query.filter(Tour.tour_type == tour_type)
            
            tours = query.all()
            
            if not tours:
                return {
                    'total_tours': 0,
                    'total_customers': 0,
                    'avg_distance_km': 0.0,
                    'avg_duration_min': 0,
                    'total_distance_km': 0.0,
                    'total_duration_min': 0,
                    'completion_rate': 0.0
                }
            
            total_tours = len(tours)
            total_customers = sum(tour.total_customers for tour in tours)
            total_distance = sum(tour.total_distance_km for tour in tours)
            total_duration = sum(tour.total_duration_min for tour in tours)
            completed_tours = len([t for t in tours if t.status == 'completed'])
            
            stats = {
                'total_tours': total_tours,
                'total_customers': total_customers,
                'avg_distance_km': round(total_distance / total_tours, 2),
                'avg_duration_min': round(total_duration / total_tours),
                'total_distance_km': round(total_distance, 2),
                'total_duration_min': total_duration,
                'completion_rate': round((completed_tours / total_tours) * 100, 1)
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Tour-Statistiken: {e}")
            return {}
    
    def __del__(self):
        """Cleanup bei Zerstörung des Objekts"""
        if hasattr(self, 'db_session'):
            self.db_session.close()
