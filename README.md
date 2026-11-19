# ENC Cell Manager Pro & Permit Expiry Monitor
*ADMIRALTY Digital Catalogue Edition for Nautical Officers & ECDIS Navigators*

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/GUI-PyQt6-green.svg)](https://riverbankcomputing.com/software/pyqt/)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6.svg)](https://microsoft.com/windows)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A standalone Windows application for marine navigators, nautical officers, and vessel managers. It streamlines Electronic Navigational Chart (ENC) ordering, eliminates duplicate chart orders, parses ECDIS status reports, manages multi-vessel profiles, preserves cumulative chart history in a local SQLite database, and monitors IHO S-63 permit license expirations with automated remaining-days calculations.

---

## 📸 Overview & Key Capabilities

1. **Multi-Vessel Profiles & Cumulative Database System (SQLite)**:
   - **Isolated Vessel Profiles**: Easily create and switch between vessels (`MV PROSPERA`, `MV OCEAN STAR`, etc.).
   - **Cumulative Permit Retention**: When importing a new `PERMIT.TXT` or `ENC.PMT`, **previous chart records are NEVER wiped**. They are preserved in the vessel's database as `🔴 Expired`, ensuring a full audit trail for Port State Control (PSC) inspections.
   - **Automatic Basket Particulars**: Profile details (`#ShipName`, `#ShipType`, `#ShipEmail`, `#OwnerName`) automatically populate chart order requisitions and PDF headers.

2. **Seamless Input & ECDIS Import**:
   - **One-Click Clipboard Paste (`Ctrl+V`)**: Instantly parse ENC codes from raw text, comma-separated lists, or spreadsheets.
   - **Direct ECDIS Report Import**: Automatically parses ECDIS ENC Update Status Reports (`.eusr.csv`), extracting vessel metadata and chart lists.
   - **Cell Extractor**: Extracts clean comma-separated list of ENC cell codes (`AU130120, AU130150, KR1O0000`) ready for one-click copy to clipboard.

3. **Offline ADMIRALTY Database (35,277 Charts)**:
   - Embedded SQLite database indexed directly from UKHO / SevenCs 7CB catalogues (`AVCS.cat` and `ENC Units.cat`).
   - Automatically populates official chart titles (e.g. `Australia Northern Approaches`) and navigation scales (e.g. `1 : 3500000`) instantly without internet.

4. **Intelligent Deduplication & Smart Selection**:
   - Visual highlighting for duplicate chart orders (`⚠️ DUPLICATE (2x)`).
   - One-click duplicate cleanup button to ensure clean, cost-effective chart orders.
   - Quick selection chips: `All`, `In Permit`, `Active <= 30d`, `Active > 30d`, `Not in Permit (New)`, `Duplicates`.

5. **IHO S-63 Permit Expiry Monitor**:
   - Loads standard `PERMIT.TXT` and `ENC.PMT` permit files.
   - Dynamic real-time calculation of days remaining until expiration.
   - Color-coded status badges:
     - 🔴 **Expired (<= 0 days)**
     - 🟠 **Critical / Expiring (1 - 30 days)**
     - 🟡 **Warning (31 - 60 days)**
     - 🟢 **Active (> 60 days)**

6. **Professional Publication-Quality PDF Reports**:
   - **Official Order Requisition Report**: Complete with IMO carriage verification, vessel particulars, chart count, scale distribution, and navigation officer signature lines.
   - **Permit Compliance Audit Report**: PSC-ready full-color table highlighting active, expiring, and historical expired permits.

7. **Light & Dark Nautical Themes**:
   - Toggle between a midnight nautical dark theme and a crisp daylight office theme.

6. **Official ADMIRALTY Order Export**:
   - Exports exact tab-delimited format required by ADMIRALTY chart distributors:
     ```tsv
     Product Type	Product Number	Product Title	Scale	Status
     ENC Units	AU130120	Australia Northern Approaches	1 : 3500000	
     ENC Units	KR1O0000	Korea Strait	1 : 1500000	
     #ShipName|PROSPERA
     #ShipType|Bulk Carrier
     #ShipEmail|master@prospera.vessel.com
     ...
     ```

---

## 🛠️ Installation & Quick Start

### Option 1: Run Pre-Compiled Windows Executable (No Python Required)
You can directly run `ENC_Manager_Pro.exe` located in the release or `dist/` directory:
- Double-click `ENC_Manager_Pro.exe` to launch immediately.

### Option 2: Run from Source Code
1. **Prerequisites**: Python 3.10+ installed on Windows.
2. **Install Dependencies**:
   ```bash
   pip install PyQt6
   ```
3. **Run Application**:
   ```bash
   python main_gui.py
   ```

---

## 📖 User Guide / Cara Menggunakan

### Workflow 1: Ordering Charts from Route Plan / ECDIS Report
1. On your vessel ECDIS or passage planning software, export the route chart status report (e.g. `2026-09-01 11-57-56.eusr.csv`).
2. Open **ENC Cell Manager Pro** and go to **Tab 1: 📋 Order Basket & Deduplication**.
3. Click **"📂 Import CSV / EUSR / TXT..."** and select your report file.
   - The app automatically sets `#ShipName` from the header.
   - All charts are loaded with official titles and scales.
4. **Filter out charts with plenty of validity**:
   - Click **`Active > 30 Days`** on the *Select Rows* bar.
   - Click **`❌ Delete Selected`**.
   - Now only the charts expiring soon (`<= 30 days`) and new charts (`Not in Permit`) remain in the basket!
5. Click **"🗑️ Remove Duplicates"** if any duplicate entries exist.
6. Click **"💾 Export Basket (.txt)"** to save the final order file and send it to your chart agent.

---

### Workflow 2: Monitoring Permits & 1-Click Renewal
1. Switch to **Tab 2: 📦 Permit Inventory & Expiry Monitor**.
2. Click **"📂 Load Permit File"** and choose `PERMIT.TXT` or `ENC.PMT` (or click **"📁 Browse Permit Folder..."**).
3. The app displays all licensed charts with live expiry countdowns and KPI statistics (Active, Warning, Critical, Expired).
4. To prepare a renewal order for expiring charts:
   - Click **"🟠 Active <= 30 Days (Expiring)"** under *Add to Basket*.
   - The expiring charts are automatically transferred to **Tab 1 (Order Basket)**.
5. Review the basket in Tab 1 and export your renewal order `.txt` file.

---

## 🏗️ Project Architecture

```
enc-manager-app/
├── enc_core.py          # Core logic (Database, Permit Parser, Duplicate Manager)
├── main_gui.py          # PyQt6 Dark Modern User Interface
├── catalog_builder.py   # Catalogue extractor for UKHO 7CB databases
├── enc_database.db      # SQLite database containing 35,277 ADMIRALTY chart cells
├── app_icon.ico         # Application icon
├── README.md            # English Documentation
├── README_ID.md         # Indonesian Documentation
└── .gitignore           # Git ignore rules
```

---

## 📦 Building the Executable with PyInstaller

To rebuild the single-file Windows executable:
```bash
pip install pyinstaller pyqt6
python -m PyInstaller --onefile --noconsole --name "ENC_Manager_Pro" --icon "app_icon.ico" --add-data "enc_database.db;." --add-data "app_icon.ico;." main_gui.py
```
The output file will be generated in `dist/ENC_Manager_Pro.exe`.

---

## 📄 License
This project is open-source and available under the [MIT License](LICENSE).
