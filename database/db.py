"""
Database Connection Manager and Helper for n8n Workflow Intelligence & Ranking System.
Supports SQLite with WAL mode and foreign key integrity, designed for PostgreSQL compatibility.
"""

import os
import sqlite3
import logging
from pathlib import Path
from typing import Generator, Any, Dict, List, Optional
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = os.getenv("DATABASE_PATH", "data/n8n_workflows.db")


def get_db_path() -> str:
    path = os.getenv("DATABASE_PATH", DEFAULT_DB_PATH)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    return path


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    target_path = db_path or get_db_path()
    conn = sqlite3.connect(target_path, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    return conn


@contextmanager
def get_db(db_path: Optional[str] = None) -> Generator[sqlite3.Connection, None, None]:
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database transaction rolled back due to error: {e}")
        raise
    finally:
        conn.close()


def run_migrations(conn: sqlite3.Connection) -> None:
    """Ensure all required columns exist in tables, adding missing columns dynamically."""
    cursor = conn.cursor()
    
    # Check workflows columns
    cursor.execute("PRAGMA table_info(workflows)")
    workflow_columns = {row["name"] for row in cursor.fetchall()}
    
    new_workflow_columns = {
        "problem_it_solves": "TEXT",
        "daily_life_practicality_score": "REAL NOT NULL DEFAULT 0.0",
        "daily_life_practicality_label": "TEXT",
        "daily_life_practicality_reason": "TEXT",
        "daily_life_use_frequency": "TEXT",
    }
    
    for col_name, col_type in new_workflow_columns.items():
        if col_name not in workflow_columns and len(workflow_columns) > 0:
            logger.info(f"Running migration: ALTER TABLE workflows ADD COLUMN {col_name} {col_type}")
            try:
                cursor.execute(f"ALTER TABLE workflows ADD COLUMN {col_name} {col_type}")
            except Exception as e:
                logger.warning(f"Migration add column {col_name} warning: {e}")


def init_db(db_path: Optional[str] = None, schema_path: Optional[str] = None) -> None:
    """Initialize database schema from schema.sql and apply migrations."""
    target_db = db_path or get_db_path()
    if schema_path is None:
        base_dir = Path(__file__).parent
        schema_path = str(base_dir / "schema.sql")

    logger.info(f"Initializing database at {target_db} with schema from {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    with get_db(target_db) as conn:
        conn.executescript(schema_sql)
        run_migrations(conn)
    logger.info("Database schema initialized successfully.")


def execute_query(query: str, params: tuple = (), db_path: Optional[str] = None) -> int:
    with get_db(db_path) as conn:
        cursor = conn.execute(query, params)
        return cursor.rowcount


def fetch_one(query: str, params: tuple = (), db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    with get_db(db_path) as conn:
        cursor = conn.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None


def fetch_all(query: str, params: tuple = (), db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    with get_db(db_path) as conn:
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
