"""Product catalog. Existing invoices retain their original product prices."""
from .database import connect
from .validation import InputError, text, money, decimal_string


def list_products():
    with connect() as db:
        products = [dict(row) for row in db.execute("SELECT * FROM products ORDER BY archived, name COLLATE NOCASE, id")]
    for product in products:
        product['price'] = decimal_string(product['price_cents'], 2)
    return products


def save_product(data, product_id=None):
    values = [text(data.get('name'), 'Product name', True, 200),
              text(data.get('sku'), 'SKU', max_length=100),
              money(data.get('price'), 'Price'),
              text(data.get('description'), 'Description', max_length=2000)]
    with connect() as db:
        if product_id is None:
            cursor = db.execute("INSERT INTO products (name, sku, price_cents, description) VALUES (?, ?, ?, ?)", values)
            return cursor.lastrowid
        cursor = db.execute("UPDATE products SET name=?, sku=?, price_cents=?, description=? WHERE id=?", values + [product_id])
        if not cursor.rowcount:
            raise InputError("Product not found.")
        return product_id


def set_archived(product_id, archived):
    with connect() as db:
        cursor = db.execute("UPDATE products SET archived=? WHERE id=?", (int(archived), product_id))
        if not cursor.rowcount:
            raise InputError("Product not found.")
