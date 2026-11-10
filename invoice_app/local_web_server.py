"""Serve the local web interface and a small JSON API using Python's standard library."""
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit
import json
import mimetypes
import re
import threading
import traceback

from . import business_settings, customers, products, invoices, sales_reports, csv_exports
from .database import database_path
from .validation import InputError

WEB_DIRECTORY = Path(__file__).resolve().parent.parent / 'web'
MAX_REQUEST_BYTES = 1_000_000


class LocalRequestHandler(BaseHTTPRequestHandler):
    server_version = 'HernandezInvoice/1.0'

    def _allowed_request(self):
        # Reject unexpected hosts to reduce DNS-rebinding and cross-site attacks.
        try:
            host = urlsplit('http://' + self.headers.get('Host', ''))
            if host.hostname not in ('localhost', '127.0.0.1') or host.port != self.server.server_port:
                return False
            origin = self.headers.get('Origin')
            if origin:
                parsed = urlsplit(origin)
                if parsed.scheme != 'http' or parsed.hostname not in ('localhost', '127.0.0.1') or parsed.port != self.server.server_port:
                    return False
        except ValueError:
            return False
        return True

    def _send(self, status, body, content_type, extra_headers=None):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Content-Security-Policy', "default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        for name, value in (extra_headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, data, status=HTTPStatus.OK):
        self._send(status, json.dumps(data, ensure_ascii=False).encode('utf-8'), 'application/json; charset=utf-8')

    def _read_json(self):
        if self.headers.get_content_type() != 'application/json':
            raise InputError('This request must contain JSON.')
        try:
            size = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            raise InputError('Invalid request length.') from None
        if size <= 0 or size > MAX_REQUEST_BYTES:
            raise InputError('Request is empty or too large.')
        try:
            def reject_constant(_):
                raise ValueError('Invalid number')
            data = json.loads(self.rfile.read(size).decode('utf-8'), parse_constant=reject_constant)
        except (ValueError, UnicodeDecodeError):
            raise InputError('The request could not be read.') from None
        if not isinstance(data, dict):
            raise InputError('The request must be an object.')
        return data

    def _handle(self):
        if not self._allowed_request():
            return self._json({'error': 'This app only accepts requests from its local address.'}, HTTPStatus.FORBIDDEN)
        parsed = urlsplit(self.path)
        path = unquote(parsed.path)
        query = parse_qs(parsed.query)
        method = self.command
        if not path.startswith('/api/'):
            if method != 'GET':
                return self._json({'error': 'Not found.'}, HTTPStatus.NOT_FOUND)
            return self._serve_static(path)
        if method == 'GET' and path == '/api/health':
            # Used by a second launcher to avoid opening a different database.
            return self._json({'app': 'Hernandez Invoice', 'database_path': str(database_path().resolve())})
        if method == 'POST' and path == '/api/shutdown':
            # Requiring JSON also prevents ordinary cross-site form submissions.
            self._read_json()
            self._json({'ok': True})
            # shutdown() must run outside the server's serve_forever thread.
            threading.Thread(target=self.server.shutdown, daemon=True).start()
            return
        if method == 'GET' and path == '/api/customers':
            return self._json(customers.list_customers())
        if method == 'GET' and path == '/api/products':
            return self._json(products.list_products())
        if method == 'GET' and path == '/api/invoices':
            return self._json(invoices.list_invoices())
        if path == '/api/settings':
            if method == 'GET':
                return self._json(business_settings.get_settings())
            if method == 'PUT':
                business_settings.save_settings(self._read_json())
                return self._json({'ok': True})
        if method == 'GET' and path == '/api/reports':
            return self._json(sales_reports.sales_report(query.get('year', [None])[0], query.get('month', [None])[0]))
        export_match = re.fullmatch(r'/api/exports/(clients|products|sales|invoice-items)\.csv', path)
        if method == 'GET' and export_match:
            kind = export_match.group(1)
            body = csv_exports.make_csv(kind, query.get('year', [None])[0], query.get('month', [None])[0])
            return self._send(HTTPStatus.OK, body, 'text/csv; charset=utf-8', {'Content-Disposition': f'attachment; filename="hernandez-{kind}.csv"'})
        for label, service in (('customers', customers), ('products', products), ('invoices', invoices)):
            if path == '/api/' + label and method == 'POST':
                identifier = getattr(service, 'save_' + {'customers': 'customer', 'products': 'product', 'invoices': 'invoice'}[label])(self._read_json())
                return self._json({'id': identifier}, HTTPStatus.CREATED)
            match = re.fullmatch('/api/' + label + r'/(\d+)(?:/(restore|status))?', path)
            if match:
                identifier, action = int(match.group(1)), match.group(2)
                if label == 'invoices' and action is None and method == 'GET':
                    return self._json(invoices.get_invoice(identifier))
                if action is None and method == 'PUT':
                    getattr(service, 'save_' + {'customers': 'customer', 'products': 'product', 'invoices': 'invoice'}[label])(self._read_json(), identifier)
                    return self._json({'ok': True})
                if label in ('customers', 'products') and action is None and method == 'DELETE':
                    service.set_archived(identifier, True)
                    return self._json({'ok': True})
                if label in ('customers', 'products') and action == 'restore' and method == 'POST':
                    service.set_archived(identifier, False)
                    return self._json({'ok': True})
                if label == 'invoices' and action == 'status' and method == 'POST':
                    invoices.set_status(identifier, self._read_json().get('status'))
                    return self._json({'ok': True})
        return self._json({'error': 'Not found.'}, HTTPStatus.NOT_FOUND)

    def _serve_static(self, path):
        if path == '/':
            file_path = WEB_DIRECTORY / 'index.html'
        elif path == '/print':
            file_path = WEB_DIRECTORY / 'print_invoice.html'
        elif path.startswith('/assets/'):
            file_path = (WEB_DIRECTORY / path[len('/assets/'):]).resolve()
            if WEB_DIRECTORY.resolve() not in file_path.parents:
                return self._json({'error': 'Not found.'}, HTTPStatus.NOT_FOUND)
        else:
            return self._json({'error': 'Not found.'}, HTTPStatus.NOT_FOUND)
        if not file_path.is_file():
            return self._json({'error': 'Not found.'}, HTTPStatus.NOT_FOUND)
        mime = mimetypes.guess_type(file_path.name)[0] or 'application/octet-stream'
        self._send(HTTPStatus.OK, file_path.read_bytes(), mime + ('; charset=utf-8' if mime.startswith('text/') or mime in ('application/javascript',) else ''))

    def _run_safely(self):
        try:
            self._handle()
        except InputError as error:
            self._json({'error': str(error)}, HTTPStatus.BAD_REQUEST)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:
            traceback.print_exc()
            self._json({'error': 'Something went wrong. Check the terminal for details.'}, HTTPStatus.INTERNAL_SERVER_ERROR)

    do_GET = _run_safely
    do_POST = _run_safely
    do_PUT = _run_safely
    do_DELETE = _run_safely


class LocalHTTPServer(ThreadingHTTPServer):
    # Finish in-progress requests before the process exits and a USB is ejected.
    daemon_threads = False
    block_on_close = True


def run_server(port=8000):
    return LocalHTTPServer(('127.0.0.1', port), LocalRequestHandler)
