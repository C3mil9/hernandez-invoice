"""Create and open the local SQLite database.

All amounts are stored as integer cents. Quantities use thousandths and tax
rates use hundredths of a percent, which keeps money calculations predictable.
"""
from contextlib import contextmanager
from pathlib import Path
import os
import sqlite3

PROJECT_DIRECTORY = Path(__file__).resolve().parent.parent
DEFAULT_DATABASE = PROJECT_DIRECTORY / "data" / "hernandez_invoice.sqlite3"


def database_path():
    return Path(os.environ.get("INVOICE_DB_PATH", str(DEFAULT_DATABASE))).expanduser()


@contextmanager
def connect():
    """Open a short-lived transaction; commit on success and roll back on error."""
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database():
    with connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            store TEXT NOT NULL DEFAULT '',
            email TEXT NOT NULL DEFAULT '',
            phone TEXT NOT NULL DEFAULT '',
            address TEXT NOT NULL DEFAULT '',
            notes TEXT NOT NULL DEFAULT '',
            archived INTEGER NOT NULL DEFAULT 0 CHECK (archived IN (0, 1)),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            sku TEXT NOT NULL DEFAULT '',
            price_cents INTEGER NOT NULL CHECK (price_cents >= 0),
            description TEXT NOT NULL DEFAULT '',
            archived INTEGER NOT NULL DEFAULT 0 CHECK (archived IN (0, 1)),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS business_settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            business_name TEXT NOT NULL DEFAULT '',
            email TEXT NOT NULL DEFAULT '',
            phone TEXT NOT NULL DEFAULT '',
            address TEXT NOT NULL DEFAULT '',
            invoice_message TEXT NOT NULL DEFAULT '',
            default_tax_basis_points INTEGER NOT NULL DEFAULT 0
        );
        INSERT OR IGNORE INTO business_settings (id) VALUES (1);
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_date TEXT NOT NULL,
            due_date TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL CHECK (status IN ('Unpaid', 'Paid', 'Void')),
            customer_id INTEGER NOT NULL REFERENCES customers(id),
            customer_name TEXT NOT NULL,
            customer_store TEXT NOT NULL DEFAULT '',
            customer_email TEXT NOT NULL DEFAULT '',
            customer_phone TEXT NOT NULL DEFAULT '',
            customer_address TEXT NOT NULL DEFAULT '',
            business_name TEXT NOT NULL DEFAULT '',
            business_email TEXT NOT NULL DEFAULT '',
            business_phone TEXT NOT NULL DEFAULT '',
            business_address TEXT NOT NULL DEFAULT '',
            invoice_message TEXT NOT NULL DEFAULT '',
            subtotal_cents INTEGER NOT NULL,
            tax_basis_points INTEGER NOT NULL,
            tax_cents INTEGER NOT NULL,
            shipping_cents INTEGER NOT NULL,
            total_cents INTEGER NOT NULL,
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS invoice_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
            product_id INTEGER REFERENCES products(id),
            name TEXT NOT NULL,
            sku TEXT NOT NULL DEFAULT '',
            quantity_milli INTEGER NOT NULL,
            unit_price_cents INTEGER NOT NULL,
            line_total_cents INTEGER NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_invoices_date ON invoices(invoice_date);
        CREATE INDEX IF NOT EXISTS idx_invoice_items_invoice ON invoice_items(invoice_id);
        """)
