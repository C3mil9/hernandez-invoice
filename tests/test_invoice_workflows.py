"""Tests for the business rules and local HTTP workflows.

Each test uses a temporary database, so running the suite never modifies the
business database in the data folder.
"""
import csv
import io
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from http.client import HTTPConnection

from invoice_app import business_settings, csv_exports, customers, invoices, products, sales_reports
from invoice_app.database import initialize_database
from invoice_app.local_web_server import run_server
from invoice_app.validation import InputError


class InvoiceWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.previous_database = os.environ.get('INVOICE_DB_PATH')
        os.environ['INVOICE_DB_PATH'] = str(Path(self.temporary_directory.name) / 'test.sqlite3')
        initialize_database()
        self.client_id = customers.save_customer({
            'name': 'María Alvarez', 'store': 'Alvarez Market', 'email': 'maria@example.com',
            'phone': '555-0100', 'address': '123 Main St',
        })
        self.product_id = products.save_product({'name': 'Coffee', 'sku': 'COF-1', 'price': '1.00'})
        business_settings.save_settings({
            'business_name': 'Example Business', 'default_tax_rate': '8.25',
            'invoice_message': 'Thank you!',
        })

    def tearDown(self):
        if self.previous_database is None:
            os.environ.pop('INVOICE_DB_PATH', None)
        else:
            os.environ['INVOICE_DB_PATH'] = self.previous_database
        self.temporary_directory.cleanup()

    def invoice_data(self, **changes):
        data = {
            'customer_id': self.client_id, 'invoice_date': '2026-11-10',
            'due_date': '2026-11-30', 'status': 'Unpaid', 'tax_rate': '8.25',
            'shipping': '2.50', 'notes': 'Handle with care',
            'items': [{'product_id': self.product_id, 'name': 'Coffee', 'sku': 'COF-1',
                       'quantity': '1.005', 'unit_price': '1.00'}],
        }
        data.update(changes)
        return data

    def test_invoice_rounding_and_historical_snapshots(self):
        invoice_id = invoices.save_invoice(self.invoice_data())
        original = invoices.get_invoice(invoice_id)
        # 1.005 × $1 rounds up to $1.01; tax is rounded after the subtotal.
        self.assertEqual((original['subtotal_cents'], original['tax_cents'], original['total_cents']),
                         (101, 8, 359))
        self.assertEqual(original['items'][0]['quantity'], '1.005')

        customers.save_customer({'name': 'Renamed client', 'store': 'New store'}, self.client_id)
        products.save_product({'name': 'Renamed product', 'price': '9.99'}, self.product_id)
        business_settings.save_settings({'business_name': 'Renamed business', 'default_tax_rate': '0'})
        invoices.save_invoice(self.invoice_data(notes='Updated notes'), invoice_id)
        saved = invoices.get_invoice(invoice_id)
        self.assertEqual((saved['customer_name'], saved['customer_store']), ('María Alvarez', 'Alvarez Market'))
        self.assertEqual((saved['business_name'], saved['invoice_message']), ('Example Business', 'Thank you!'))
        self.assertEqual((saved['items'][0]['name'], saved['items'][0]['unit_price_cents']), ('Coffee', 100))
        self.assertEqual(saved['notes'], 'Updated notes')

    def test_archived_records_preserve_history_and_can_be_restored(self):
        invoice_id = invoices.save_invoice(self.invoice_data())
        customers.set_archived(self.client_id, True)
        products.set_archived(self.product_id, True)
        self.assertEqual(invoices.get_invoice(invoice_id)['customer_name'], 'María Alvarez')
        invoices.save_invoice(self.invoice_data(), invoice_id)  # Existing associations remain valid.
        with self.assertRaisesRegex(InputError, 'active client'):
            invoices.save_invoice(self.invoice_data())
        customers.set_archived(self.client_id, False)
        with self.assertRaisesRegex(InputError, 'no longer active'):
            invoices.save_invoice(self.invoice_data())
        products.set_archived(self.product_id, False)
        self.assertGreater(invoices.save_invoice(self.invoice_data()), invoice_id)

    def test_reports_and_exports_include_paid_and_unpaid_but_not_void(self):
        paid_id = invoices.save_invoice(self.invoice_data(status='Paid', invoice_date='2026-01-15', due_date=''))
        unpaid_id = invoices.save_invoice(self.invoice_data())
        void_id = invoices.save_invoice(self.invoice_data(status='Void'))
        invoices.save_invoice(self.invoice_data(invoice_date='2025-11-10', due_date=''))
        report = sales_reports.sales_report(2026, 11)
        self.assertEqual(report['selected_month']['invoice_count'], 1)
        self.assertEqual(report['selected_month']['unpaid_cents'], 359)
        self.assertEqual(report['yearly'], {'invoice_count': 2, 'total_cents': 718,
                                            'paid_cents': 359, 'unpaid_cents': 359})
        sales = list(csv.DictReader(io.StringIO(csv_exports.make_csv('sales', 2026).decode('utf-8-sig'))))
        self.assertEqual([row['Invoice'] for row in sales],
                         [invoices.invoice_number(paid_id), invoices.invoice_number(unpaid_id)])
        self.assertNotIn(invoices.invoice_number(void_id), [row['Invoice'] for row in sales])
        items = list(csv.DictReader(io.StringIO(csv_exports.make_csv('invoice-items', 2026).decode('utf-8-sig'))))
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]['Quantity'], '1.005')
        invoices.set_status(unpaid_id, 'Void')
        self.assertEqual(sales_reports.sales_report(2026, 11)['yearly']['total_cents'], 359)

    def test_csv_protects_formulas_and_preserves_accented_names(self):
        customers.save_customer({'name': '=SUM(A1:A2)', 'store': '+Example'})
        output = csv_exports.make_csv('clients').decode('utf-8-sig')
        rows = list(csv.DictReader(io.StringIO(output)))
        self.assertIn('María Alvarez', [row['Name'] for row in rows])
        dangerous = next(row for row in rows if row['Name'].startswith("'="))
        self.assertEqual(dangerous['Store'], "'+Example")

    def test_invalid_dates_amounts_and_periods_are_rejected(self):
        with self.assertRaisesRegex(InputError, 'Due date'):
            invoices.save_invoice(self.invoice_data(due_date='2026-11-01'))
        with self.assertRaises(InputError):
            invoices.save_invoice(self.invoice_data(shipping='-1'))
        with self.assertRaises(InputError):
            sales_reports.sales_report(2026, 13)
        self.assertEqual(invoices.list_invoices(), [])

    def test_local_http_routes_and_origin_protection(self):
        server = run_server(0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        port = server.server_port

        def request(method, path, payload=None, headers=None):
            connection = HTTPConnection('127.0.0.1', port, timeout=5)
            request_headers = dict(headers or {})
            body = None
            if payload is not None:
                body = json.dumps(payload)
                request_headers['Content-Type'] = 'application/json'
            try:
                connection.request(method, path, body=body, headers=request_headers)
                response = connection.getresponse()
                return response.status, response.getheaders(), response.read()
            finally:
                connection.close()

        try:
            status, _, body = request('POST', '/api/invoices', self.invoice_data())
            self.assertEqual(status, 201)
            invoice_id = json.loads(body)['id']
            status, _, body = request('GET', f'/api/invoices/{invoice_id}')
            self.assertEqual((status, json.loads(body)['total_cents']), (200, 359))
            status, headers, body = request('GET', '/api/exports/sales.csv?year=2026&month=11')
            self.assertEqual(status, 200)
            self.assertIn('text/csv', dict(headers)['Content-Type'])
            self.assertIn(b'INV-000001', body)
            status, _, body = request('GET', '/print?id=1')
            self.assertEqual(status, 200)
            self.assertIn(b'print_invoice.js', body)
            status, _, _ = request('POST', '/api/invoices', self.invoice_data(), {'Origin': 'https://example.com'})
            self.assertEqual(status, 403)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


if __name__ == '__main__':
    unittest.main()
