"""Download UTF-8 CSV files that Excel can open, including formula protection."""
import csv
import io
from .database import connect
from .sales_reports import validate_period
from .validation import InputError, decimal_string
from .invoices import invoice_number
from .csv_translations import HEADINGS, STATUSES, archived_text


def safe_text(value):
    value = str(value or '')
    # Spreadsheet apps can execute text that starts with these characters.
    if value.lstrip(' \t\r\n').startswith(('=', '+', '-', '@')):
        return "'" + value
    return value


def make_csv(kind, year=None, month=None, language='en'):
    # Preserve the original English export format unless Spanish is selected.
    language = 'es' if language == 'es' else 'en'
    if kind not in HEADINGS[language]:
        raise InputError('Export not found.')
    output = io.StringIO(newline='')
    writer = csv.writer(output)
    writer.writerow(HEADINGS[language][kind])
    with connect() as db:
        if kind == 'clients':
            for row in db.execute('SELECT * FROM customers ORDER BY name COLLATE NOCASE'):
                writer.writerow([safe_text(row[key]) for key in ('name', 'store', 'email', 'phone', 'address', 'notes')] + [archived_text(row['archived'], language)])
        elif kind == 'products':
            for row in db.execute('SELECT * FROM products ORDER BY name COLLATE NOCASE'):
                writer.writerow([safe_text(row['name']), safe_text(row['sku']), decimal_string(row['price_cents'], 2), safe_text(row['description']), archived_text(row['archived'], language)])
        elif kind in ('sales', 'invoice-items'):
            year, month = validate_period(year, month)
            period = f'{year:04d}' + (f'-{month:02d}' if month is not None else '')
            if kind == 'sales':
                rows = db.execute("SELECT * FROM invoices WHERE substr(invoice_date, 1, ?) = ? AND status != 'Void' ORDER BY invoice_date, id", (len(period), period))
                for row in rows:
                    writer.writerow([invoice_number(row['id']), row['invoice_date'], row['due_date'], safe_text(row['customer_name']), safe_text(row['customer_store']), STATUSES[language][row['status']]] +
                                    [decimal_string(row[k], 2) for k in ('subtotal_cents', 'tax_cents', 'shipping_cents', 'total_cents')])
            else:
                rows = db.execute("SELECT i.id AS invoice_id, i.invoice_date, i.customer_name, i.status, x.* FROM invoice_items x JOIN invoices i ON i.id=x.invoice_id WHERE substr(i.invoice_date, 1, ?) = ? AND i.status != 'Void' ORDER BY i.invoice_date, i.id, x.id", (len(period), period))
                for row in rows:
                    writer.writerow([invoice_number(row['invoice_id']), row['invoice_date'], safe_text(row['customer_name']), STATUSES[language][row['status']], safe_text(row['name']), safe_text(row['sku']), decimal_string(row['quantity_milli'], 3), decimal_string(row['unit_price_cents'], 2), decimal_string(row['line_total_cents'], 2)])
    # A UTF-8 BOM helps Excel recognize accented characters correctly.
    return ('\ufeff' + output.getvalue()).encode('utf-8')
