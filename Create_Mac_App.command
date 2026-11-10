#!/bin/sh
# One-time setup on a Mac. AppleScript's compiler creates a native app bundle.
PROJECT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd -P)
APP_PATH="$PROJECT_DIR/Hernandez Invoice.app"
if [ -e "$APP_PATH" ]; then
  /usr/bin/osascript -e 'display dialog "Hernandez Invoice.app already exists in this folder. Open it to start the app." with title "Hernandez Invoice" buttons {"OK"} default button "OK"'
  exit 0
fi
if ! /usr/bin/osacompile -o "$APP_PATH" "$PROJECT_DIR/mac_launcher/Launch_Hernandez_Invoice.applescript"; then
  /usr/bin/osascript -e 'display dialog "The app icon could not be created. Check that this folder is writable and try again." with title "Hernandez Invoice" buttons {"OK"} default button "OK" with icon stop'
  exit 1
fi
if ! /bin/cp "$PROJECT_DIR/assets/hernandez_invoice.icns" "$APP_PATH/Contents/Resources/applet.icns"; then
  /usr/bin/osascript -e 'display dialog "The app was created, but its icon could not be copied. You can still open Hernandez Invoice.app." with title "Hernandez Invoice" buttons {"OK"} default button "OK"'
  exit 0
fi
/usr/bin/osascript -e 'display dialog "Hernandez Invoice.app is ready in this folder. Double-click it to open the app. You can make an alias on your desktop." with title "Hernandez Invoice" buttons {"OK"} default button "OK"'
