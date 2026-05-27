"""SQLite storage for runs, lifts, and injury notes."""
import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager

DB_PATH = os.environ.get("DB_PATH", "tracker.db")


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strava_id INTEGER UNIQUE,
                date TEXT NOT NULL,
                name TEXT,
                distance_km REAL,
                moving_time_s INTEGER,
                pace_s_per_km REAL,
                avg_hr REAL,
                max_hr REAL,
                elevation_m REAL,
                source TEXT DEFAULT 'strava'
            );

            CREATE TABLE IF NOT EXISTS lifts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                split TEXT,
                exercise TEXT NOT NULL,
                weight_kg REAL,
                reps INTEGER,
                sets INTEGER
            );

            CREATE TABLE IF NOT EXISTS injuries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                area TEXT NOT NULL,
                severity INTEGER,
                note TEXT
            );

            CREATE TABLE IF NOT EXISTS tokens (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                access_token TEXT,
                refresh_token TEXT,
                expires_at INTEGER
            );
            """
        )


def save_run(run: dict):
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO runs (strava_id, date, name, distance_km, moving_time_s,
                              pace_s_per_km, avg_hr, max_hr, elevation_m, source)
            VALUES (:strava_id, :date, :name, :distance_km, :moving_time_s,
                    :pace_s_per_km, :avg_hr, :max_hr, :elevation_m, :source)
            ON CONFLICT(strava_id) DO UPDATE SET
                distance_km=excluded.distance_km,
                pace_s_per_km=excluded.pace_s_per_km,
                avg_hr=excluded.avg_hr
            """,
            run,
        )


def get_runs(limit: int = 100):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM runs ORDER BY date DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def add_lift(lift: dict):
    with get_db() as conn:
        cur = conn.execute(
            """INSERT INTO lifts (date, split, exercise, weight_kg, reps, sets)
               VALUES (:date, :split, :exercise, :weight_kg, :reps, :sets)""",
            lift,
        )
        return cur.lastrowid


def get_lifts(limit: int = 100):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM lifts ORDER BY date DESC, id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def add_injury(injury: dict):
    with get_db() as conn:
        cur = conn.execute(
            """INSERT INTO injuries (date, area, severity, note)
               VALUES (:date, :area, :severity, :note)""",
            injury,
        )
        return cur.lastrowid


def get_injuries(limit: int = 50):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM injuries ORDER BY date DESC, id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def save_tokens(access_token: str, refresh_token: str, expires_at: int):
    with get_db() as conn:
        conn.execute(
            """INSERT INTO tokens (id, access_token, refresh_token, expires_at)
               VALUES (1, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
                 access_token=excluded.access_token,
                 refresh_token=excluded.refresh_token,
                 expires_at=excluded.expires_at""",
            (access_token, refresh_token, expires_at),
        )


def get_tokens():
    with get_db() as conn:
        row = conn.execute("SELECT * FROM tokens WHERE id = 1").fetchone()
        return dict(row) if row else None
