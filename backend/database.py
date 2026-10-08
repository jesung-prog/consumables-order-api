from pathlib import Path
import sqlite3

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
DB_PATH = DATA_DIR / "inventory.db"

DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_tables() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_code TEXT NOT NULL UNIQUE,
                normalized_name TEXT NOT NULL UNIQUE,
                item_name TEXT NOT NULL,
                unit TEXT,
                unit_price REAL NOT NULL DEFAULT 0,
                initial_stock REAL NOT NULL DEFAULT 0,
                lead_time_days INTEGER NOT NULL DEFAULT 3,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS stock_movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_code TEXT NOT NULL,
                movement_type TEXT NOT NULL CHECK (movement_type IN ('IN', 'OUT')),
                event_date TEXT NOT NULL,
                quantity REAL NOT NULL CHECK (quantity >= 0),
                memo TEXT,
                source_file TEXT,
                import_fingerprint TEXT,
                source_row INTEGER,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (item_code) REFERENCES items(item_code),
                UNIQUE(import_fingerprint, source_row)
            );

            CREATE TABLE IF NOT EXISTS stock_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_code TEXT NOT NULL,
                request_date TEXT NOT NULL,
                requested_qty REAL NOT NULL CHECK (requested_qty >= 0),
                issued_qty REAL NOT NULL DEFAULT 0 CHECK (issued_qty >= 0),
                shortage_qty REAL NOT NULL DEFAULT 0 CHECK (shortage_qty >= 0),
                department TEXT,
                memo TEXT,
                FOREIGN KEY (item_code) REFERENCES items(item_code)
            );

            CREATE TABLE IF NOT EXISTS import_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                import_type TEXT NOT NULL,
                fingerprint TEXT NOT NULL UNIQUE,
                file_name TEXT NOT NULL,
                row_count INTEGER NOT NULL,
                imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
