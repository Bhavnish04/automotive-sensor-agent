import sqlite3
import os
from typing import Optional
DB_PATH = os.environ.get("DB_PATH", "data/obd.db")

def get_connection()-> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok= True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory =sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db() -> None:
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS vehicles (
                vehicle_id    TEXT PRIMARY KEY,
                make          TEXT NOT NULL,
                model         TEXT NOT NULL,
                year          INTEGER,
                fuel_type     TEXT,
                transmission  TEXT
            );
            CREATE TABLE IF NOT EXISTS drivers (
                driver_id          TEXT PRIMARY KEY,
                vehicle_id         TEXT NOT NULL REFERENCES vehicles(vehicle_id),
                total_sessions     INTEGER DEFAULT 0,
                total_distance_km  REAL
            );

            CREATE TABLE IF NOT EXISTS sessions (
                session_id              TEXT PRIMARY KEY,
                driver_id               TEXT NOT NULL REFERENCES drivers(driver_id),
                vehicle_id              TEXT NOT NULL REFERENCES vehicles(vehicle_id),
                date                    TEXT,
                avg_rpm                 REAL,
                max_rpm                 REAL,
                avg_speed               REAL,
                max_speed               REAL,
                avg_engine_load         REAL,
                max_coolant_temp        REAL,
                avg_throttle            REAL,
                max_steering_angle      REAL,
                avg_fuel_level          REAL,
                avg_battery_voltage     REAL,
                aggressive_event_count  INTEGER DEFAULT 0,
                total_events            INTEGER DEFAULT 0,
                driving_label           TEXT
            );

            CREATE TABLE IF NOT EXISTS events (
                event_id          TEXT PRIMARY KEY,
                session_id        TEXT NOT NULL REFERENCES sessions(session_id),
                driver_id         TEXT NOT NULL REFERENCES drivers(driver_id),
                rpm               REAL,
                speed             REAL,
                engine_load       REAL,
                coolant_temp      REAL,
                throttle_position REAL,
                steering_angle    REAL,
                label             TEXT,
                timestamp         INTEGER
            );
        """)
        
        
        
if __name__ == "__main__":
    init_db()
    print("✅ Database initialised successfully")
    
    
    
    
def seed_db() -> None:
    """Read sessions_clean.csv and populate the database."""
    import pandas as pd

    # Check if already seeded
    with get_connection() as conn:
        if conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] > 0:
            print("Database already seeded, skipping.")
            return

    df = pd.read_csv("data/sessions_clean.csv")

    # Vehicle data
    vehicles = [
        ("VH001", "Volkswagen", "Jetta",  2015, "Gasoline", "Automatic"),
        ("VH002", "Seat",       "Leon",   2015, "Gasoline", "Automatic"),
        ("VH003", "Nissan",     "Sentra", 2015, "Gasoline", "Automatic"),
    ]

    drivers = [
        ("D001", "VH001", "Driver 1"),
        ("D002", "VH002", "Driver 2"),
        ("D003", "VH003", "Driver 3"),
    ]

    vehicle_map = {1: "VH001", 2: "VH002", 3: "VH003"}
    driver_map  = {1: "D001",  2: "D002",  3: "D003"}

    with get_connection() as conn:
        # Insert vehicles
        conn.executemany(
            "INSERT INTO vehicles VALUES (?,?,?,?,?,?)",
            vehicles
        )

        # Insert drivers
        conn.executemany(
            "INSERT INTO drivers (driver_id, vehicle_id, total_sessions) VALUES (?,?,?)",
            [(d[0], d[1], 0) for d in drivers]
        )

        # Insert sessions
        for _, row in df.iterrows():
            unique_session_id = f"{row['session_id']}_D{int(row['driver_id'])}"
            conn.execute("""
                INSERT INTO sessions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                unique_session_id,
                driver_map[int(row['driver_id'])],
                vehicle_map[int(row['driver_id'])],
                None,
                round(row['avg_rpm'], 2),
                round(row['max_rpm'], 2),
                round(row['avg_speed'], 2),
                round(row['max_speed'], 2),
                round(row['avg_engine_load'], 2),
                round(row['max_coolant_temp'], 2),
                round(row['avg_throttle'], 2),
                round(row['max_steering_angle'], 2),
                round(row['avg_fuel_level'], 2),
                round(row['avg_battery_voltage'], 2),
                int(row['aggressive_event_count']),
                int(row['total_events']),
                row['driving_label'],
            ))

    print("✅ Database seeded successfully")
    
if __name__ == "__main__":
    init_db()
    seed_db()
    print("✅ Database initialised and seeded successfully")
    
    
def get_all_drivers() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT d.driver_id, d.vehicle_id, v.make, v.model, v.year,
                   COUNT(s.session_id) as total_sessions
            FROM drivers d
            JOIN vehicles v ON d.vehicle_id = v.vehicle_id
            JOIN sessions s ON d.driver_id = s.driver_id
            GROUP BY d.driver_id
        """).fetchall()
        return [dict(row) for row in rows]
    
def get_sessions_by_driver(driver_id: str) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM sessions
            WHERE driver_id = ?
            ORDER BY max_rpm DESC
        """, (driver_id,)).fetchall()
        return [dict(row) for row in rows]
    
def get_most_aggressive_driver() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT d.driver_id, v.make, v.model,
                   COUNT(s.session_id) as total_sessions,
                   SUM(s.aggressive_event_count) as total_aggressive_events,
                   ROUND(AVG(s.avg_rpm), 2) as overall_avg_rpm,
                   ROUND(AVG(s.max_speed), 2) as overall_max_speed
            FROM sessions s
            JOIN drivers d ON s.driver_id = d.driver_id
            JOIN vehicles v ON d.vehicle_id = v.vehicle_id
            GROUP BY d.driver_id
            ORDER BY total_aggressive_events DESC
        """).fetchall()
        return [dict(row) for row in rows]
    
def get_sessions_by_label(label: str) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT s.*, v.make, v.model
            FROM sessions s
            JOIN vehicles v ON s.vehicle_id = v.vehicle_id
            WHERE s.driving_label = ?
            ORDER BY s.avg_rpm DESC
        """, (label,)).fetchall()
        return [dict(row) for row in rows]


def compare_drivers() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT 
                d.driver_id,
                v.make,
                v.model,
                ROUND(AVG(s.avg_rpm), 2) as avg_rpm,
                ROUND(AVG(s.max_speed), 2) as avg_max_speed,
                ROUND(AVG(s.avg_throttle), 2) as avg_throttle,
                ROUND(AVG(s.max_steering_angle), 2) as avg_steering,
                SUM(s.aggressive_event_count) as total_aggressive_events
            FROM sessions s
            JOIN drivers d ON s.driver_id = d.driver_id
            JOIN vehicles v ON d.vehicle_id = v.vehicle_id
            GROUP BY d.driver_id
            ORDER BY avg_rpm DESC
        """).fetchall()
        return [dict(row) for row in rows]