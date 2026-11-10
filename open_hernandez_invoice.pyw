"""Windowless entry point used by the Windows and Mac launchers."""
import os
import sys

# Python's windowless interpreter on Windows may have no console streams.
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w')

from invoice_app.launch_messages import show_startup_error

try:
    if sys.version_info < (3, 9):
        raise RuntimeError('Python 3.9 or newer is required.')
    from start_hernandez_invoice import main
    sys.exit(main(graphical=True))
except Exception as error:
    show_startup_error(f'Could not open Hernandez Invoice: {error}\n\n'
                       'Check that Python 3.9 or newer is installed.')
    sys.exit(1)
