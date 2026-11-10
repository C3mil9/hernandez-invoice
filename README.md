# Hernandez Invoice

A local invoice and sales tracking app for a small business. It uses **Python, SQLite, HTML, CSS, and JavaScript**. It runs on your own computer and opens in your web browser. There are no subscriptions, accounts, or extra Python packages to install.

## What the app can do

- Add, edit, search, archive, restore, and export clients. Store a name, company/store, email, phone, address, and notes.
- Add, edit, search, archive, restore, and export products, SKUs, descriptions, and prices.
- Create and edit numbered invoices with saved products or custom items, quantities, adjustable prices, tax, shipping, notes, invoice date, and due date.
- Mark an invoice paid, unpaid, or void; view and print it or save it as a PDF through your browser's print menu.
- See monthly and yearly sales reports. Export a month's sales, a year's sales, or a year's individual invoice items as CSV files that open in Excel.
- Keep customer, product, and business details on each invoice as they were when it was saved. Changing a catalog price or business information won't rewrite old invoices.
- Store all data locally in a SQLite database.

> This version is a single-computer app. It does not have account login, cloud sync, inventory quantity tracking, partial payments, refunds, or automatic tax calculations by location.

## First-time setup

1. Install **Python 3.9 or newer** on each computer if needed. Download it from [python.org](https://www.python.org/downloads/). On Windows, make Python available on your PATH.
2. Extract the ZIP and keep the complete `hernandez-invoice` folder together, either on the computer or on a writable USB drive.
3. If you already have clients or invoices, follow **Moving data from an older copy** below before using the new copy.
4. Follow the one-time setup for your computer below. After setup, open Hernandez Invoice using its icon. The app opens in the default browser.
5. When finished, save your work and select **Close app** at the top of the page. Close the browser tab. If you used a USB drive, safely eject it before unplugging it.

Closing only the browser tab leaves the app running in the background. Open the icon again to return to it, then use **Close app**.

### Windows

1. Inside the project folder, double-click `Create_Desktop_Shortcut_Windows.bat` once. A setup window creates a **Hernandez Invoice** shortcut on the desktop.
2. Double-click that desktop icon whenever you want to use the app. VS Code and a terminal are not needed for day-to-day use.
3. Keep the folder where it was when you made the shortcut. If it moves, or a USB drive gets a different drive letter, run the shortcut setup again. Set up a shortcut separately on each Windows computer.

For development, you can also double-click `Start_Hernandez_Invoice_Windows.bat` or run:

```powershell
py -3 start_hernandez_invoice.py
```

### Mac

1. In the project folder, double-click `Create_Mac_App.command` once. It creates **Hernandez Invoice.app** in that folder using the Mac's built-in script compiler.
2. Double-click **Hernandez Invoice.app** to open the app. For a desktop icon, right-click the app, choose **Make Alias**, and drag the alias to the desktop. Leave the actual app in the project folder, beside its code and data.
3. If you use a USB drive, keep it plugged in while using the app and make an alias on each Mac as needed.

The launcher is an unsigned personal-use script. macOS may show a security warning when opening it. Inspect the files and only open software you trust. See [Apple's guidance](https://support.apple.com/en-us/102445).

### Linux or development on macOS

Open a terminal in the extracted `hernandez-invoice` folder and run:

```bash
python3 start_hernandez_invoice.py
```

The browser is only the app's interface; an internet connection is not required after Python is installed. The server listens on your computer's loopback address only. The app has no password or separate user accounts, so anyone using your computer or local user account may be able to access the running app and database.

### Moving data from an older copy

1. Close the old app and make a backup copy of its `data/hernandez_invoice.sqlite3` file in a safe location.
2. Extract the new ZIP to a separate folder. Before opening the new app, copy the old database file into the new folder's `data` folder.
3. Start the new copy and confirm that your clients, products, and invoices appear. Keep the backup until you have verified them.

Copying a database replaces the destination database; it does not merge two sets of records. Use one copy of the app at a time. A new ZIP never contains your previously saved business data.

## Getting started in the app

1. Open **Business settings** and enter your business name, contact information, and any message for invoices. You can also set a default tax percentage. Settings are copied to new invoices; earlier invoices keep their original details.
2. Open **Clients** and add a client. A client name is required.
3. Open **Products** and add your frequently sold products and prices. You can also type custom items directly on an invoice.
4. Select **New invoice**. Choose a client, add items, edit quantities and prices, and enter any tax, shipping, due date, or notes. Save the invoice.
5. On the **Invoices** page, select **View / print** and use the print button. Your browser can print to paper or save as PDF. Use the invoice actions to edit it or change its status.
6. Open **Sales reports** and choose a year and month. Use the export buttons to download CSV files. Excel can open these files directly.

Use **Archive** to take a client or product out of the active lists. To bring one back, check **Show archived** and select **Restore**. Past invoices retain the information they were issued with. Changing an invoice's client will use the new client's current details.

### How sales totals work

Reports group invoices by **invoice date**. Sales include both paid and unpaid invoices, including their item subtotal, tax, and shipping. Void invoices are excluded. Paid and unpaid totals are based on the status you select; there is no partial-payment ledger. The total is invoiced sales, not profit or cash received. Tax is calculated on item subtotal before shipping. Each line and tax amount is rounded to the nearest cent, with half cents rounded up.

The sales export uses the same paid/unpaid and void rules as the report. The item export contains one row per line item. CSVs use UTF-8 so accented names open correctly in modern Excel. Formula-like text is prefixed with an apostrophe for spreadsheet safety.

## Your data and backups

The database is created automatically at:

```text
data/hernandez_invoice.sqlite3
```

**Back it up regularly:** save your work and select **Close app**, then copy `data/hernandez_invoice.sqlite3` to a safe location such as a backup drive. If you started the app in a terminal, Ctrl+C also stops it. To restore, close the app and replace the database file with your backup before starting it again. Keep backup copies private because they contain client and sales details.

Keep the extracted folder in a location you can write to. If you move the app folder, move the `data` folder with it. Downloading a fresh copy of the ZIP will not include your existing database.

If the project folder is on a USB drive, its database is stored on that drive. Use it on one computer at a time; do not unplug the drive while the app is open. Both computers need Python installed. The app does not synchronize separate database copies.

If you upload the code to GitHub, `.gitignore` excludes database files and Python cache files. Double-check that you have not manually added a database, exported CSV, backup, or other private information before committing.

## Where to make changes

```text
hernandez-invoice/
├── start_hernandez_invoice.py        # Start the server and open the browser
├── open_hernandez_invoice.pyw        # Windowless launcher for desktop icons
├── Create_Desktop_Shortcut_Windows.bat
├── Create_Mac_App.command            # Create the Mac app icon once
├── mac_launcher/                     # Source for the Mac launcher
├── assets/                           # Windows and Mac app icons
├── invoice_app/
│   ├── database.py                   # SQLite tables and database connections
│   ├── validation.py                 # Shared input and decimal validation
│   ├── customers.py                  # Client database operations
│   ├── products.py                   # Product database operations
│   ├── invoices.py                   # Invoice rules, amounts, and snapshots
│   ├── sales_reports.py              # Monthly and yearly report calculations
│   ├── csv_exports.py                # Excel-friendly CSV exports
│   ├── business_settings.py          # Business details and default tax
│   ├── launch_messages.py            # Startup messages for desktop launchers
│   └── local_web_server.py           # Local HTTP routes and static files
├── web/
│   ├── index.html                    # App layout and navigation
│   ├── print_invoice.html            # Printable invoice page
│   ├── css/application.css           # App design and responsive layout
│   ├── css/print_invoice.css         # Printable invoice design
│   └── js/                           # One readable file per screen or feature
├── tests/                            # Application behavior tests
└── data/                             # Your private local SQLite database
```

The code uses integer cents and avoids floating-point math for invoice calculations. Quantities are stored in thousandths. New changes that alter the database structure will need a migration for existing databases.

### Interface design notes

The interface keeps sales totals prominent, groups related invoice fields, and places search and actions near each table. The layout adapts to smaller screens, supports keyboard focus, and explains what to do when a search has no results. These design references can help when improving it later:

- [Carbon Design System: dashboards](https://www.carbondesignsystem.com/building-blocks/data-visualization/dashboards)
- [Carbon Design System: data tables](https://www.carbondesignsystem.com/building-blocks/core/components/data-table/guidelines)
- [Carbon Design System: forms](https://www.carbondesignsystem.com/building-blocks/core/patterns/forms)

## Tests

From the project folder, run:

```bash
python3 -m unittest discover -s tests -v
```

On Windows, you can use `py -3` in place of `python3`. The tests use temporary databases and do not touch your business data.

## Troubleshooting

- **Python isn't found:** Install Python and reopen your terminal. On Windows, try `py -3 --version`; on macOS/Linux, try `python3 --version`.
- **The browser doesn't open:** Go to http://127.0.0.1:8000 while the terminal says the app is running.
- **Another copy has different data:** Select **Close app** in the first copy before opening the second one. This prevents accidentally displaying the wrong database.
- **A desktop shortcut no longer opens the project:** Recreate it after moving the folder or changing USB drive letters. On a Mac, keep the original `.app` in the project folder and move an alias instead.
- **Port 8000 is already in use:** Stop the other program, or set `HERNANDEZ_INVOICE_PORT` to another port before starting. For example, on macOS/Linux: `HERNANDEZ_INVOICE_PORT=8001 python3 start_hernandez_invoice.py`. On Windows PowerShell: `$env:HERNANDEZ_INVOICE_PORT="8001"; py -3 start_hernandez_invoice.py`. Open the address printed in the terminal.
- **The app cannot save:** Confirm the extracted folder and its `data` folder are writable. If using a new folder or computer, restore your existing database from a backup.
