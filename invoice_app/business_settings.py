"""Business information printed on newly created invoices."""
from .database import connect
from .validation import text, tax_rate, decimal_string


def get_settings():
    with connect() as db:
        settings = dict(db.execute("SELECT * FROM business_settings WHERE id=1").fetchone())
    settings['default_tax_rate'] = decimal_string(settings['default_tax_basis_points'], 2)
    return settings


def save_settings(data):
    values = [text(data.get('business_name'), 'Business name', max_length=200),
              text(data.get('email'), 'Email', max_length=200),
              text(data.get('phone'), 'Phone', max_length=200),
              text(data.get('address'), 'Address', max_length=2000),
              text(data.get('invoice_message'), 'Invoice message', max_length=2000),
              tax_rate(data.get('default_tax_rate', '0'))]
    with connect() as db:
        db.execute("UPDATE business_settings SET business_name=?, email=?, phone=?, address=?, invoice_message=?, default_tax_basis_points=? WHERE id=1", values)
