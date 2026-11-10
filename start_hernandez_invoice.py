"""Start Hernandez Invoice, or reopen the browser if this copy is running."""
import errno
import json
import os
from pathlib import Path
import sqlite3
import sys
import threading
from urllib.error import URLError
from urllib.request import urlopen
import webbrowser

from invoice_app.database import initialize_database, database_path
from invoice_app.launch_messages import show_startup_error
from invoice_app.local_web_server import run_server


def running_app_for_port(port):
    """Identify the app already listening on a port, if it is ours."""
    try:
        with urlopen(f'http://127.0.0.1:{port}/api/health', timeout=1) as response:
            info = json.loads(response.read(16384).decode('utf-8'))
        if isinstance(info, dict) and info.get('app') == 'Hernandez Invoice':
            path = info.get('database_path')
            if isinstance(path, str) and path:
                return os.path.normcase(str(Path(path).resolve()))
    except (OSError, ValueError, UnicodeError, URLError):
        pass
    return None


def main(graphical=False):
    def report_error(message):
        if graphical:
            show_startup_error(message)
        else:
            print(message, file=sys.stderr)

    try:
        port = int(os.environ.get('HERNANDEZ_INVOICE_PORT', '8000'))
        if not 1 <= port <= 65535:
            raise ValueError
    except ValueError:
        report_error('HERNANDEZ_INVOICE_PORT must be a number from 1 to 65535.')
        return 1
    address = f'http://127.0.0.1:{port}/'

    def open_browser():
        if os.environ.get('HERNANDEZ_NO_BROWSER') == '1':
            return
        try:
            if not webbrowser.open(address):
                report_error(f'Open your browser and go to {address}')
        except Exception:
            report_error(f'Open your browser and go to {address}')

    try:
        # Bind first: another copy may be open with a different database.
        server = run_server(port)
    except OSError as error:
        if error.errno == errno.EADDRINUSE or getattr(error, 'winerror', None) == 10048:
            running_database = running_app_for_port(port)
            this_database = os.path.normcase(str(database_path().resolve()))
            if running_database == this_database:
                open_browser()
                return 0
            if running_database is not None:
                report_error('Another copy of Hernandez Invoice is already open with different data. '
                             'Close it in the app before opening this copy.')
            else:
                report_error(f'Another program is using port {port}. Close it, or ask the person '
                             'who maintains the app to select another port.')
        else:
            report_error(f'Could not start Hernandez Invoice: {error}')
        return 1

    try:
        initialize_database()
    except (OSError, sqlite3.Error) as error:
        server.server_close()
        report_error(f'Could not open the database: {error}\n\n'
                     'Check that the app folder and data folder are writable.')
        return 1

    print(f'Hernandez Invoice is running at {address}', flush=True)
    print(f'Database: {database_path()}', flush=True)
    print('Use Close app in the browser, or press Ctrl+C here, to stop.', flush=True)
    if os.environ.get('HERNANDEZ_NO_BROWSER') != '1':
        threading.Timer(0.2, open_browser).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nClosing Hernandez Invoice.')
    finally:
        # Wait for any active save before the USB drive is removed.
        server.server_close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
