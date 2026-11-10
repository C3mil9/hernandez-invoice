"""Show a helpful startup message when the app is launched without a terminal."""
import subprocess
import sys


def show_startup_error(message):
    """Use built-in operating-system dialogs; fall back to the terminal."""
    try:
        if sys.platform == 'win32':
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, message, 'Hernandez Invoice', 0x10)
            return
        if sys.platform == 'darwin':
            script = ('on run argv\n'
                      'display dialog (item 1 of argv) with title "Hernandez Invoice" '
                      'buttons {"OK"} default button "OK" with icon stop\n'
                      'end run')
            subprocess.run(['/usr/bin/osascript', '-e', script, message], check=True)
            return
    except (OSError, subprocess.SubprocessError):
        pass
    print(message, file=sys.stderr)
