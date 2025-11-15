from __future__ import annotations

import sqlite3
from typing import Iterable

from .config import get_database_path

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

Base = declarative_base()

class Customer(Base):
    __tablename__ = 'customers'
    
    id = Column(Integer, primary_key=True)
    kundennr = Column(String(50), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    street = Column(String(200), nullable=False)
    plz = Column(String(10), nullable=False)
    city = Column(String(100), nullable=False)
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    is_bar_cash = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Tour(Base):
    __tablename__ = 'tours'
    
    id = Column(Integer, primary_key=True)
    tour_name = Column(String(100), nullable=False)  # z.B. "W-09:00 A"
    tour_type = Column(String(20), nullable=False)   # W, PIR, T
    tour_date = Column(Date, nullable=False)         # Datum der Tour
    created_at = Column(DateTime, default=datetime.utcnow)
    total_customers = Column(Integer, default=0)
    total_distance_km = Column(Float, default=0.0)
    total_duration_min = Column(Integer, default=0)
    status = Column(String(20), default='active')    # active, completed, cancelled
    driver_notes = Column(Text, nullable=True)
    
    # Relationships
    stops = relationship("TourStop", back_populates="tour", order_by="TourStop.sequence_order")
    performance = relationship("TourPerformance", back_populates="tour", uselist=False)

class TourStop(Base):
    __tablename__ = 'tour_stops'
    
    id = Column(Integer, primary_key=True)
    tour_id = Column(Integer, ForeignKey('tours.id'), nullable=False)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    sequence_order = Column(Integer, nullable=False)  # 1, 2, 3... für Drag & Drop
    estimated_arrival_time = Column(String(10), nullable=True)  # HH:MM
    estimated_departure_time = Column(String(10), nullable=True)
    actual_arrival_time = Column(String(10), nullable=True)
    actual_departure_time = Column(String(10), nullable=True)
    dwell_time_min = Column(Integer, default=2)
    notes = Column(Text, nullable=True)
    
    # Relationships
    tour = relationship("Tour", back_populates="stops")
    customer = relationship("Customer")

class TourPerformance(Base):
    __tablename__ = 'tour_performance'
    
    id = Column(Integer, primary_key=True)
    tour_id = Column(Integer, ForeignKey('tours.id'), nullable=False)
    planned_distance_km = Column(Float, default=0.0)
    actual_distance_km = Column(Float, default=0.0)
    planned_duration_min = Column(Integer, default=0)
    actual_duration_min = Column(Integer, default=0)
    fuel_consumption_l = Column(Float, nullable=True)
    driver_notes = Column(Text, nullable=True)
    customer_feedback = Column(Text, nullable=True)
    weather_conditions = Column(String(100), nullable=True)
    traffic_conditions = Column(String(100), nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    tour = relationship("Tour", back_populates="performance")

class Geocache(Base):
    __tablename__ = 'geocache'
    
    id = Column(Integer, primary_key=True)
    address = Column(String(500), nullable=False, unique=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    provider = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, default=datetime.utcnow)

class AddressCorrection(Base):
    __tablename__ = 'address_corrections'
    
    id = Column(Integer, primary_key=True)
    original_address = Column(String(500), nullable=False)
    corrected_address = Column(String(500), nullable=False)
    correction_type = Column(String(50), nullable=False)  # street_name, plz, city
    confidence_score = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    used_count = Column(Integer, default=0)

# Tour-Statistik-View für einfache Abfragen
class TourStatistics(Base):
    __tablename__ = 'tour_statistics'
    
    id = Column(Integer, primary_key=True)
    tour_date = Column(Date, nullable=False)
    tour_type = Column(String(20), nullable=False)
    total_tours = Column(Integer, default=0)
    total_customers = Column(Integer, default=0)
    avg_distance_km = Column(Float, default=0.0)
    avg_duration_min = Column(Integer, default=0)
    total_distance_km = Column(Float, default=0.0)
    total_duration_min = Column(Integer, default=0)
    completion_rate = Column(Float, default=0.0)  # Prozent der abgeschlossenen Touren


DDL_STATEMENTS: Iterable[str] = (
    # Kundenstammdaten
    """
    CREATE TABLE IF NOT EXISTS kunden (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        adresse TEXT NOT NULL,
        lat REAL,
        lon REAL,
        created_at TEXT DEFAULT (datetime('now'))
    );
    """,
    # Eindeutigkeit: gleicher Kunde (Name+Adresse) nur einmal
    """
    CREATE UNIQUE INDEX IF NOT EXISTS kunden_unique_name_addr
    ON kunden(name COLLATE NOCASE, adresse COLLATE NOCASE);
    """,
    # Touren pro Tag
    """
    CREATE TABLE IF NOT EXISTS touren (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tour_id TEXT NOT NULL,
        datum TEXT NOT NULL,
        kunden_ids TEXT, -- JSON-Liste von kunden.id
        dauer_min INTEGER,
        distanz_km REAL,
        fahrer TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );
    """,
    # Eindeutigkeit: gleiche Tour-ID am selben Datum nur einmal
    """
    CREATE UNIQUE INDEX IF NOT EXISTS touren_unique_by_date
    ON touren(tour_id, datum);
    """,
    # Fahrerfeedback
    """
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tour_id TEXT NOT NULL,
        datum TEXT NOT NULL,
        kommentar TEXT,
        bewertung INTEGER,
        created_at TEXT DEFAULT (datetime('now'))
    );
    """,
    # Geocoding Cache
    """
    CREATE TABLE IF NOT EXISTS geocache (
        adresse TEXT PRIMARY KEY,
        lat REAL,
        lon REAL,
        provider TEXT,
        updated_at TEXT DEFAULT (datetime('now'))
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS postal_code_cache (
        postal_code TEXT PRIMARY KEY,
        city TEXT NOT NULL,
        updated_at TEXT DEFAULT (datetime('now'))
    );
    """,
)


def init_db() -> None:
    db_path = get_database_path()
    with sqlite3.connect(db_path) as conn:
        for ddl in DDL_STATEMENTS:
            conn.execute(ddl)
        conn.commit()
