"""Monthly and yearly invoice totals. Void invoices are excluded."""
from datetime import date
from .database import connect
from .validation import InputError


def validate_period(year, month=None):
    try:
        year = int(year)
        month = int(month) if month not in (None, '') else None
    except (TypeError, ValueError):
        raise InputError('Choose a valid year and month.') from None
    if year < 1900 or year > 9999 or (month is not None and not 1 <= month <= 12):
        raise InputError('Choose a valid year and month.')
    return year, month


def sales_report(year=None, month=None):
    today = date.today()
    year, month = validate_period(year if year is not None else today.year, month if month is not None else today.month)
    with connect() as db:
        rows = db.execute('''SELECT CAST(substr(invoice_date, 6, 2) AS INTEGER) AS month,
            COUNT(*) AS invoice_count, SUM(total_cents) AS total_cents,
            SUM(CASE WHEN status='Paid' THEN total_cents ELSE 0 END) AS paid_cents,
            SUM(CASE WHEN status='Unpaid' THEN total_cents ELSE 0 END) AS unpaid_cents
            FROM invoices WHERE substr(invoice_date, 1, 4)=? AND status != 'Void'
            GROUP BY substr(invoice_date, 6, 2)''', (f'{year:04d}',)).fetchall()
        recent = db.execute('''SELECT id, invoice_date, status, customer_name, total_cents
            FROM invoices WHERE substr(invoice_date, 1, 7)=? AND status != 'Void'
            ORDER BY invoice_date DESC, id DESC''', (f'{year:04d}-{month:02d}',)).fetchall()
    by_month = {row['month']: dict(row) for row in rows}
    months = [by_month.get(number, {'month': number, 'invoice_count': 0, 'total_cents': 0, 'paid_cents': 0, 'unpaid_cents': 0}) for number in range(1, 13)]
    yearly = {key: sum(row[key] for row in months) for key in ('invoice_count', 'total_cents', 'paid_cents', 'unpaid_cents')}
    return {'year': year, 'month': month, 'months': months, 'selected_month': months[month - 1], 'yearly': yearly,
            'invoices': [dict(row) for row in recent]}
