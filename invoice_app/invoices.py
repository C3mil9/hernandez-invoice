"""Create, edit and list invoices while preserving historical snapshots."""
from .database import connect
from .validation import InputError, date_string, decimal_string, money, positive_id, quantity, tax_rate, text

STATUSES = ('Unpaid', 'Paid', 'Void')


def invoice_number(invoice_id):
    return f"INV-{invoice_id:06d}"


def _prepare_items(raw_items):
    if not isinstance(raw_items, list) or not raw_items or len(raw_items) > 100:
        raise InputError('Add between 1 and 100 invoice items.')
    items = []
    for raw in raw_items:
        if not isinstance(raw, dict):
            raise InputError('Each invoice item must be valid.')
        product_id = raw.get('product_id')
        if product_id not in (None, ''):
            product_id = positive_id(product_id, 'product')
        else:
            product_id = None  # Custom invoice items need no catalog record.
        qty = quantity(raw.get('quantity'))
        price = money(raw.get('unit_price'), 'Unit price')
        # Round each line to the nearest cent, half up.
        line_total = (qty * price + 500) // 1000
        items.append({'product_id': product_id,
                      'name': text(raw.get('name'), 'Item name', True, 200),
                      'sku': text(raw.get('sku'), 'SKU', max_length=100),
                      'quantity_milli': qty, 'unit_price_cents': price,
                      'line_total_cents': line_total})
    return items


def save_invoice(data, invoice_id=None):
    customer_id = positive_id(data.get('customer_id'), 'client')
    invoice_date = date_string(data.get('invoice_date'), 'Invoice date')
    due_date = date_string(data.get('due_date'), 'Due date', required=False)
    if due_date and due_date < invoice_date:
        raise InputError('Due date cannot be before the invoice date.')
    status = data.get('status', 'Unpaid')
    if status not in STATUSES:
        raise InputError('Select a valid invoice status.')
    notes = text(data.get('notes'), 'Notes', max_length=2000)
    items = _prepare_items(data.get('items'))
    tax_basis_points = tax_rate(data.get('tax_rate', '0'))
    shipping = money(data.get('shipping', '0'), 'Shipping')
    subtotal = sum(item['line_total_cents'] for item in items)
    # Keep totals within JavaScript's exact integer range and SQLite's limits.
    if subtotal > 1_000_000_000_000:
        raise InputError('The invoice subtotal is too large.')
    tax = (subtotal * tax_basis_points + 5000) // 10000
    total = subtotal + tax + shipping

    with connect() as db:
        old = db.execute('SELECT * FROM invoices WHERE id=?', (invoice_id,)).fetchone() if invoice_id else None
        if invoice_id and old is None:
            raise InputError('Invoice not found.')
        customer = db.execute('SELECT * FROM customers WHERE id=?', (customer_id,)).fetchone()
        if customer is None or (customer['archived'] and (old is None or old['customer_id'] != customer_id)):
            raise InputError('Select an active client.')
        previous_products = set()
        if old:
            previous_products = {row['product_id'] for row in db.execute('SELECT product_id FROM invoice_items WHERE invoice_id=?', (invoice_id,))}
        for item in items:
            if item['product_id'] is not None:
                product = db.execute('SELECT archived FROM products WHERE id=?', (item['product_id'],)).fetchone()
                if product is None or (product['archived'] and item['product_id'] not in previous_products):
                    raise InputError('One of the selected products is no longer active.')

        # Keep the old snapshot on edits unless the user switches the client.
        if old and old['customer_id'] == customer_id:
            customer_snapshot = [old['customer_name'], old['customer_store'], old['customer_email'], old['customer_phone'], old['customer_address']]
        else:
            customer_snapshot = [customer['name'], customer['store'], customer['email'], customer['phone'], customer['address']]
        if old:
            business_snapshot = [old['business_name'], old['business_email'], old['business_phone'], old['business_address'], old['invoice_message']]
        else:
            business = db.execute('SELECT * FROM business_settings WHERE id=1').fetchone()
            business_snapshot = [business['business_name'], business['email'], business['phone'], business['address'], business['invoice_message']]
        values = [invoice_date, due_date, status, customer_id] + customer_snapshot + business_snapshot + [subtotal, tax_basis_points, tax, shipping, total, notes]
        columns = ('invoice_date', 'due_date', 'status', 'customer_id', 'customer_name', 'customer_store',
                   'customer_email', 'customer_phone', 'customer_address', 'business_name', 'business_email',
                   'business_phone', 'business_address', 'invoice_message', 'subtotal_cents', 'tax_basis_points',
                   'tax_cents', 'shipping_cents', 'total_cents', 'notes')
        if old:
            db.execute('UPDATE invoices SET ' + ', '.join(column + '=?' for column in columns) + ', updated_at=CURRENT_TIMESTAMP WHERE id=?', values + [invoice_id])
            db.execute('DELETE FROM invoice_items WHERE invoice_id=?', (invoice_id,))
        else:
            cursor = db.execute('INSERT INTO invoices (' + ', '.join(columns) + ') VALUES (' + ', '.join('?' for _ in columns) + ')', values)
            invoice_id = cursor.lastrowid
        for item in items:
            db.execute('INSERT INTO invoice_items (invoice_id, product_id, name, sku, quantity_milli, unit_price_cents, line_total_cents) VALUES (?, ?, ?, ?, ?, ?, ?)',
                       (invoice_id, item['product_id'], item['name'], item['sku'], item['quantity_milli'], item['unit_price_cents'], item['line_total_cents']))
    return invoice_id


def set_status(invoice_id, status):
    if status not in STATUSES:
        raise InputError('Select a valid invoice status.')
    with connect() as db:
        cursor = db.execute('UPDATE invoices SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?', (status, invoice_id))
        if not cursor.rowcount:
            raise InputError('Invoice not found.')


def list_invoices():
    with connect() as db:
        rows = [dict(row) for row in db.execute('SELECT id, invoice_date, due_date, status, customer_name, customer_store, total_cents FROM invoices ORDER BY invoice_date DESC, id DESC')]
    for row in rows:
        row['invoice_number'] = invoice_number(row['id'])
    return rows


def get_invoice(invoice_id):
    with connect() as db:
        row = db.execute('SELECT * FROM invoices WHERE id=?', (invoice_id,)).fetchone()
        if row is None:
            raise InputError('Invoice not found.')
        result = dict(row)
        result['items'] = [dict(item) for item in db.execute('SELECT * FROM invoice_items WHERE invoice_id=? ORDER BY id', (invoice_id,))]
    result['invoice_number'] = invoice_number(result['id'])
    result['tax_rate'] = decimal_string(result['tax_basis_points'], 2)
    result['shipping'] = decimal_string(result['shipping_cents'], 2)
    for item in result['items']:
        item['quantity'] = decimal_string(item['quantity_milli'], 3).rstrip('0').rstrip('.')
        item['unit_price'] = decimal_string(item['unit_price_cents'], 2)
    return result
