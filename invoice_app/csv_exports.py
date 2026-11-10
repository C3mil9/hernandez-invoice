"""Download UTF-8 CSV files that Excel can open, including formula protection."""
import csv
import io
from .database import connect
from .sales_reports import validate_period
from .validation import InputError, decimal_string
from .invoices import invoice_number


def safe_text(value):
    value = str(value or '')
    # Spreadsheet apps can execute text that starts with these characters.
    if value.lstrip(' \t\r\n').startswith(('=', '+', '-', '@')):
        return "'" + value
    return value


def make_csv(kind, year=None, month=None):
    output = io.StringIO(newline='')
    writer = csv.writer(output)
    with connect() as db:
        if kind == 'clients':
            writer.writerow(['Name', 'Store', 'Email', 'Phone', 'Address', 'Notes', 'Archived'])
            for row in db.execute('SELECT * FROM customers ORDER BY name COLLATE NOCASE'):
                writer.writerow([safe_text(row[key]) for key in ('name', 'store', 'email', 'phone', 'address', 'notes')] + ['Yes' if row['archived'] else 'No'])
        elif kind == 'products':
            writer.writerow(['Product', 'SKU', 'Price', 'Description', 'Archived'])
            for row in db.execute('SELECT * FROM products ORDER BY name COLLATE NOCASE'):
                writer.writerow([safe_text(row['name']), safe_text(row['sku']), decimal_string(row['price_cents'], 2), safe_text(row['description']), 'Yes' if row['archived'] else 'No'])
        elif kind in ('sales', 'invoice-items'):
            year, month = validate_period(year, month)
            period = f'{year:04d}' + (f'-{month:02d}' if month is not None else '')
            if kind == 'sales':
                writer.writerow(['Invoice', 'Invoice date', 'Due date', 'Client', 'Store', 'Status', 'Subtotal', 'Tax', 'Shipping', 'Total'])
                rows = db.execute("SELECT * FROM invoices WHERE substr(invoice_date, 1, ?) = ? AND status != 'Void' ORDER BY invoice_date, id", (len(period), period))
                for row in rows:
                    writer.writerow([invoice_number(row['id']), row['invoice_date'], row['due_date'], safe_text(row['customer_name']), safe_text(row['customer_store']), row['status']] +
                                    [decimal_string(row[k], 2) for k in ('subtotal_cents', 'tax_cents', 'shipping_cents', 'total_cents')])
            else:
                writer.writerow(['Invoice', 'Invoice date', 'Client', 'Status', 'Item', 'SKU', 'Quantity', 'Unit price', 'Line total'])
                rows = db.execute("SELECT i.id AS invoice_id, i.invoice_date, i.customer_name, i.status, x.* FROM invoice_items x JOIN invoices i ON i.id=x.invoice_id WHERE substr(i.invoice_date, 1, ?) = ? AND i.status != 'Void' ORDER BY i.invoice_date, i.id, x.id", (len(period), period))
                for row in rows:
                    writer.writerow([invoice_number(row['invoice_id']), row['invoice_date'], safe_text(row['customer_name']), row['status'], safe_text(row['name']), safe_text(row['sku']), decimal_string(row['quantity_milli'], 3), decimal_string(row['unit_price_cents'], 2), decimal_string(row['line_total_cents'], 2)])
        else:
            raise InputError('Export not found.')
    # A UTF-8 BOM helps Excel recognize accented characters correctly.
    return ('\ufeff' + output.getvalue()).encode('utf-8')
