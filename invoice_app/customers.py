"""Client records. Removing a client archives it to protect invoice history."""
from .database import connect
from .validation import InputError, text

FIELDS = ("name", "store", "email", "phone", "address", "notes")


def list_customers():
    with connect() as db:
        return [dict(row) for row in db.execute("SELECT * FROM customers ORDER BY archived, name COLLATE NOCASE, id")]


def save_customer(data, customer_id=None):
    values = [text(data.get(field), field.replace('_', ' ').title(), field == 'name', 2000 if field in ('address', 'notes') else 200) for field in FIELDS]
    with connect() as db:
        if customer_id is None:
            cursor = db.execute("INSERT INTO customers (name, store, email, phone, address, notes) VALUES (?, ?, ?, ?, ?, ?)", values)
            return cursor.lastrowid
        cursor = db.execute("UPDATE customers SET name=?, store=?, email=?, phone=?, address=?, notes=? WHERE id=?", values + [customer_id])
        if not cursor.rowcount:
            raise InputError("Client not found.")
        return customer_id


def set_archived(customer_id, archived):
    with connect() as db:
        cursor = db.execute("UPDATE customers SET archived=? WHERE id=?", (int(archived), customer_id))
        if not cursor.rowcount:
            raise InputError("Client not found.")
