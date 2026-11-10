"""Check safe startup, database selection, and shutdown of the local app."""
import errno
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from http.client import HTTPConnection
from urllib.error import URLError
from urllib.request import urlopen
from unittest import mock

from invoice_app.database import initialize_database
from invoice_app.local_web_server import run_server
import start_hernandez_invoice


class AppLauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_database = os.environ.get('INVOICE_DB_PATH')
        self.database = Path(self.temp.name) / 'usb data' / 'hernandez_invoice.sqlite3'
        os.environ['INVOICE_DB_PATH'] = str(self.database)
        initialize_database()
        self.server = run_server(0)
        self.port = self.server.server_port
        self.thread = threading.Thread(target=self.server.serve_forever,
                                       kwargs={'poll_interval': 0.05}, daemon=True)
        self.thread.start()

    def tearDown(self):
        if self.thread.is_alive():
            self.server.shutdown()
            self.thread.join(5)
        self.server.server_close()
        if self.old_database is None:
            os.environ.pop('INVOICE_DB_PATH', None)
        else:
            os.environ['INVOICE_DB_PATH'] = self.old_database
        self.temp.cleanup()

    def request(self, method, path, body=None, headers=None):
        connection = HTTPConnection('127.0.0.1', self.port, timeout=5)
        try:
            connection.request(method, path, body=body, headers=headers or {})
            response = connection.getresponse()
            return response.status, response.read()
        finally:
            connection.close()

    def test_health_identifies_the_database_in_use(self):
        status, body = self.request('GET', '/api/health')
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body), {'app': 'Hernandez Invoice',
                                            'database_path': str(self.database.resolve())})
        self.assertEqual(start_hernandez_invoice.running_app_for_port(self.port),
                         os.path.normcase(str(self.database.resolve())))

    def test_opening_same_copy_twice_reopens_the_browser(self):
        busy = OSError(errno.EADDRINUSE, 'address already in use')
        with mock.patch.dict(os.environ, {'HERNANDEZ_INVOICE_PORT': str(self.port),
                                         'HERNANDEZ_NO_BROWSER': '0'}), \
             mock.patch.object(start_hernandez_invoice, 'run_server', side_effect=busy), \
             mock.patch.object(start_hernandez_invoice.webbrowser, 'open', return_value=True) as browser:
            self.assertEqual(start_hernandez_invoice.main(), 0)
        browser.assert_called_once_with(f'http://127.0.0.1:{self.port}/')

    def test_different_database_is_not_opened_or_created(self):
        busy = OSError(errno.EADDRINUSE, 'address already in use')
        other = Path(self.temp.name) / 'other-copy' / 'different.sqlite3'
        with mock.patch.dict(os.environ, {'HERNANDEZ_INVOICE_PORT': str(self.port),
                                         'HERNANDEZ_NO_BROWSER': '0'}), \
             mock.patch.object(start_hernandez_invoice, 'run_server', side_effect=busy), \
             mock.patch.object(start_hernandez_invoice, 'database_path', return_value=other), \
             mock.patch.object(start_hernandez_invoice, 'show_startup_error') as alert, \
             mock.patch.object(start_hernandez_invoice.webbrowser, 'open') as browser:
            self.assertEqual(start_hernandez_invoice.main(graphical=True), 1)
        alert.assert_called_once()
        self.assertIn('different data', alert.call_args.args[0])
        browser.assert_not_called()
        self.assertFalse(other.exists())

    def test_shutdown_rejects_foreign_origins_and_non_json_requests(self):
        status, _ = self.request('POST', '/api/shutdown', '{}',
                                 {'Origin': 'https://example.com', 'Content-Type': 'application/json'})
        self.assertEqual(status, 403)
        status, _ = self.request('POST', '/api/shutdown', '', {'Content-Type': 'text/plain'})
        self.assertEqual(status, 400)
        self.assertTrue(self.thread.is_alive())

    def test_closing_waits_for_an_in_progress_request(self):
        started = threading.Event()
        release = threading.Event()
        completed = threading.Event()
        request_thread = None
        closer = None

        def slow_customers():
            started.set()
            release.wait(5)
            return []

        try:
            with mock.patch('invoice_app.local_web_server.customers.list_customers', side_effect=slow_customers):
                request_thread = threading.Thread(target=lambda: self.request('GET', '/api/customers'), daemon=True)
                request_thread.start()
                self.assertTrue(started.wait(2))
                status, body = self.request('POST', '/api/shutdown', '{}', {'Content-Type': 'application/json'})
                self.assertEqual((status, json.loads(body)), (200, {'ok': True}))
                self.thread.join(2)
                self.assertFalse(self.thread.is_alive())
                closer = threading.Thread(target=lambda: (self.server.server_close(), completed.set()), daemon=True)
                closer.start()
                self.assertFalse(completed.wait(0.1), 'Closing should wait for the active request')
                release.set()
                self.assertTrue(completed.wait(2))
        finally:
            release.set()
            if request_thread:
                request_thread.join(2)
            if closer:
                closer.join(2)


class LauncherPackageTests(unittest.TestCase):
    def test_mac_and_windows_launcher_files_are_present(self):
        root = Path(__file__).resolve().parent.parent
        self.assertTrue((root / 'Create_Mac_App.command').stat().st_mode & 0o111)
        self.assertTrue((root / 'mac_launcher' / 'open_hernandez_invoice_mac.sh').is_file())
        self.assertTrue((root / 'mac_launcher' / 'Launch_Hernandez_Invoice.applescript').is_file())
        self.assertEqual((root / 'assets' / 'hernandez_invoice.icns').read_bytes()[:4], b'icns')
        self.assertEqual((root / 'assets' / 'hernandez_invoice.ico').read_bytes()[:4], b'\x00\x00\x01\x00')
        self.assertTrue((root / 'Create_Desktop_Shortcut_Windows.bat').is_file())
        self.assertTrue((root / 'open_hernandez_invoice.pyw').is_file())

    def test_windowless_entry_starts_reopens_and_shuts_down(self):
        root = Path(__file__).resolve().parent.parent
        with tempfile.TemporaryDirectory(prefix='invoice launcher ') as directory:
            # Obtain a free local port, then immediately give it to the app.
            import socket
            with socket.socket() as reserved:
                reserved.bind(('127.0.0.1', 0))
                port = reserved.getsockname()[1]
            env = dict(os.environ, INVOICE_DB_PATH=str(Path(directory) / 'data.sqlite3'),
                       HERNANDEZ_INVOICE_PORT=str(port), HERNANDEZ_NO_BROWSER='1')
            command = [sys.executable, str(root / 'open_hernandez_invoice.pyw')]
            first = subprocess.Popen(command, cwd=directory, env=env,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                deadline = time.monotonic() + 5
                while True:
                    try:
                        with urlopen(f'http://127.0.0.1:{port}/api/health', timeout=0.5) as response:
                            self.assertEqual(json.load(response)['app'], 'Hernandez Invoice')
                        break
                    except (OSError, URLError):
                        if time.monotonic() >= deadline:
                            self.fail('Windowless launcher did not start')
                        time.sleep(0.05)
                same = subprocess.run(command, cwd=directory, env=env, capture_output=True, text=True, timeout=5)
                self.assertEqual(same.returncode, 0, same.stderr)
                other = dict(env, INVOICE_DB_PATH=str(Path(directory) / 'different.sqlite3'))
                conflict = subprocess.run(command, cwd=directory, env=other, capture_output=True, text=True, timeout=5)
                self.assertEqual(conflict.returncode, 1)
                self.assertFalse(Path(other['INVOICE_DB_PATH']).exists())
                connection = HTTPConnection('127.0.0.1', port, timeout=5)
                try:
                    connection.request('POST', '/api/shutdown', body='{}', headers={'Content-Type':'application/json'})
                    response = connection.getresponse()
                    self.assertEqual(response.status, 200)
                    response.read()
                finally:
                    connection.close()
                self.assertEqual(first.wait(timeout=5), 0)
            finally:
                if first.poll() is None:
                    first.terminate()
                    first.wait(timeout=5)
                first.communicate()



if __name__ == '__main__':
    unittest.main()
