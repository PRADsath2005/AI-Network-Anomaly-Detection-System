"""
database.py
-----------
SQLite integration — initializes the DB, provides insert/fetch helpers.
FIX: All operations wrapped in try-except; connection scoped per call.
"""

import sqlite3
import os
import logging
from datetime import datetime

BASE_DIR = os.path.dirname(__file__)
DB_PATH  = os.path.join(BASE_DIR, "anomaly_detection.db")

logger = logging.getLogger(__name__)


# -------------------------------------------------------------------
# Schema
# -------------------------------------------------------------------
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS detection_logs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp       TEXT    NOT NULL,
    source_ip       TEXT    NOT NULL,
    prediction      TEXT    NOT NULL,
    confidence_score REAL   NOT NULL
);
"""


def _get_connection() -> sqlite3.Connection:
    """Return a new SQLite connection with row factory."""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> bool:
    """Create the detection_logs table if it does not exist."""
    try:
        with _get_connection() as conn:
            conn.execute(CREATE_TABLE_SQL)
            conn.commit()
        logger.info("[DB] Database initialized at %s", DB_PATH)
        return True
    except sqlite3.Error as e:
        logger.error("[DB] init_db error: %s", e)
        return False


# -------------------------------------------------------------------
# Write
# -------------------------------------------------------------------
def insert_log(
    source_ip: str,
    prediction: str,
    confidence_score: float,
    timestamp: str = None,
) -> bool:
    """
    Insert a single detection result into detection_logs.

    Parameters
    ----------
    source_ip        : simulated IP address string
    prediction       : "Normal" or "Attack"
    confidence_score : probability / confidence (0.0 – 1.0)
    timestamp        : ISO-8601 string; defaults to current UTC time
    """
    if timestamp is None:
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with _get_connection() as conn:
            conn.execute(
                """INSERT INTO detection_logs
                   (timestamp, source_ip, prediction, confidence_score)
                   VALUES (?, ?, ?, ?)""",
                (timestamp, source_ip, prediction, round(float(confidence_score), 4)),
            )
            conn.commit()
        return True
    except sqlite3.Error as e:
        logger.error("[DB] insert_log error: %s", e)
        return False


# -------------------------------------------------------------------
# Read
# -------------------------------------------------------------------
def fetch_all_logs() -> list[dict]:
    """Return all rows from detection_logs ordered newest first."""
    try:
        with _get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM detection_logs ORDER BY id DESC"
            ).fetchall()
        return [dict(r) for r in rows]
    except sqlite3.Error as e:
        logger.error("[DB] fetch_all_logs error: %s", e)
        return []


def fetch_recent_logs(n: int = 20) -> list[dict]:
    """Return the most recent N rows."""
    try:
        with _get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM detection_logs ORDER BY id DESC LIMIT ?", (n,)
            ).fetchall()
        return [dict(r) for r in rows]
    except sqlite3.Error as e:
        logger.error("[DB] fetch_recent_logs error: %s", e)
        return []


def fetch_stats() -> dict:
    """Return aggregate statistics: total, attacks, normals."""
    try:
        with _get_connection() as conn:
            total   = conn.execute("SELECT COUNT(*) FROM detection_logs").fetchone()[0]
            attacks = conn.execute(
                "SELECT COUNT(*) FROM detection_logs WHERE prediction='Attack'"
            ).fetchone()[0]
        return {
            "total":   total,
            "attacks": attacks,
            "normals": total - attacks,
            "attack_rate": round(attacks / total * 100, 2) if total > 0 else 0.0,
        }
    except sqlite3.Error as e:
        logger.error("[DB] fetch_stats error: %s", e)
        return {"total": 0, "attacks": 0, "normals": 0, "attack_rate": 0.0}


def clear_logs() -> bool:
    """Delete all rows (for testing / reset)."""
    try:
        with _get_connection() as conn:
            conn.execute("DELETE FROM detection_logs")
            conn.commit()
        return True
    except sqlite3.Error as e:
        logger.error("[DB] clear_logs error: %s", e)
        return False


# -------------------------------------------------------------------
# CLI test
# -------------------------------------------------------------------
if __name__ == "__main__":
    init_db()
    insert_log("192.168.1.1", "Normal", 0.95)
    insert_log("10.0.0.5",    "Attack", 0.88)
    print(fetch_recent_logs(5))
    print(fetch_stats())
