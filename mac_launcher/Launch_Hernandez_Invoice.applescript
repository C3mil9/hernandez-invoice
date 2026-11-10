-- Compiled into a real Mac application by Create_Mac_App.command.
-- Keep the generated app inside the project folder and move an alias if desired.
on run
    try
        set appPath to POSIX path of (path to me)
        set projectDir to do shell script "/usr/bin/dirname " & quoted form of appPath
        set launcherPath to projectDir & "/mac_launcher/open_hernandez_invoice_mac.sh"
        do shell script "/bin/test -f " & quoted form of launcherPath
        -- Redirect all streams so AppleScript can exit while Python runs.
        do shell script "/bin/sh " & quoted form of launcherPath & " >/dev/null 2>&1 &"
    on error errorMessage
        display dialog "Keep the app inside the Hernandez Invoice folder. Make an alias to place on the desktop." with title "Hernandez Invoice" buttons {"OK"} default button "OK" with icon stop
    end try
end run
