#!/bin/sh
# Finder has a short PATH; look in common Python.org and Homebrew locations.
SCRIPT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd -P)
PROJECT_DIR=$(dirname "$SCRIPT_DIR")
if [ ! -f "$PROJECT_DIR/open_hernandez_invoice.pyw" ]; then
  /usr/bin/osascript -e 'display dialog "Keep the app inside the Hernandez Invoice folder. Make an alias to place on the desktop." with title "Hernandez Invoice" buttons {"OK"} default button "OK" with icon stop'
  exit 1
fi
for PYTHON in /Library/Frameworks/Python.framework/Versions/Current/bin/python3 /opt/homebrew/bin/python3 /usr/local/bin/python3 /usr/bin/python3; do
  if [ -x "$PYTHON" ] && "$PYTHON" -c 'import sys, sqlite3; assert sys.version_info >= (3, 9)' >/dev/null 2>&1; then
    exec "$PYTHON" "$PROJECT_DIR/open_hernandez_invoice.pyw"
  fi
done
/usr/bin/osascript -e 'display dialog "Install Python 3.9 or newer with SQLite support, then open Hernandez Invoice again." with title "Hernandez Invoice" buttons {"OK"} default button "OK" with icon stop'
exit 1
