import os
import sys
import re
import json
import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog, QMessageBox, QCheckBox, QGroupBox,
    QDialog, QFormLayout, QDialogButtonBox, QAbstractItemView, QMenu,
    QStatusBar, QFrame, QTabWidget, QComboBox
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QColor, QBrush, QIcon, QKeySequence, QShortcut

from enc_core import ENCManager, InventoryManager, ENCDatabase, get_db_path, extract_cell_codes
from pdf_generator import generate_basket_pdf, generate_inventory_pdf

SETTINGS_FILE = "app_settings.json"

def load_settings() -> dict:
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_settings(settings: dict):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
    except Exception:
        pass

STYLE_SHEET = """
QMainWindow {
    background-color: #111827;
    color: #f3f4f6;
    font-family: "Segoe UI", Arial, sans-serif;
}
QWidget {
    background-color: #111827;
    color: #f3f4f6;
    font-size: 13px;
}
QTabWidget::pane {
    border: 1px solid #1f2937;
    background-color: #111827;
    border-radius: 6px;
    top: -1px;
}
QTabBar::tab {
    background-color: #1f2937;
    color: #9ca3af;
    padding: 10px 22px;
    margin-right: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: 600;
    font-size: 13px;
}
QTabBar::tab:selected {
    background-color: #2563eb;
    color: #ffffff;
}
QTabBar::tab:hover:!selected {
    background-color: #374151;
    color: #e5e7eb;
}
QGroupBox {
    border: 1px solid #374151;
    border-radius: 6px;
    margin-top: 8px;
    font-weight: bold;
    padding-top: 12px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
    color: #38bdf8;
}
QPushButton {
    background-color: #2563eb;
    color: #ffffff;
    border: none;
    border-radius: 5px;
    padding: 6px 12px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #1d4ed8;
}
QPushButton:pressed {
    background-color: #1e40af;
}
QPushButton:disabled {
    background-color: #374151;
    color: #6b7280;
}
QPushButton#btn_paste {
    background-color: #0284c7;
    font-size: 13px;
    padding: 7px 15px;
}
QPushButton#btn_paste:hover {
    background-color: #0369a1;
}
QPushButton#btn_import_file {
    background-color: #0891b2;
    font-size: 13px;
    padding: 7px 14px;
}
QPushButton#btn_import_file:hover {
    background-color: #0e7490;
}
QPushButton#btn_extractor {
    background-color: #7c3aed;
    font-size: 13px;
    padding: 7px 14px;
}
QPushButton#btn_extractor:hover {
    background-color: #6d28d9;
}
QPushButton#btn_copy_cells {
    background-color: #0d9488;
}
QPushButton#btn_copy_cells:hover {
    background-color: #0f766e;
}
QPushButton#btn_dedup {
    background-color: #ea580c;
}
QPushButton#btn_dedup:hover {
    background-color: #c2410c;
}
QPushButton#btn_delete {
    background-color: #dc2626;
}
QPushButton#btn_delete:hover {
    background-color: #b91c1c;
}
QPushButton#btn_export {
    background-color: #059669;
}
QPushButton#btn_export:hover {
    background-color: #047857;
}
QPushButton#btn_export_pdf {
    background-color: #b91c1c;
    color: #ffffff;
    font-weight: bold;
}
QPushButton#btn_export_pdf:hover {
    background-color: #991b1b;
}
QPushButton#btn_secondary {
    background-color: #374151;
}
QPushButton#btn_secondary:hover {
    background-color: #4b5563;
}
QPushButton#btn_renew_crit {
    background-color: #ea580c;
}
QPushButton#btn_renew_crit:hover {
    background-color: #c2410c;
}
QPushButton#btn_renew_act {
    background-color: #2563eb;
}
QPushButton#btn_renew_act:hover {
    background-color: #1d4ed8;
}
QPushButton#btn_renew_all {
    background-color: #7c3aed;
}
QPushButton#btn_renew_all:hover {
    background-color: #6d28d9;
}
QPushButton#btn_chip {
    background-color: #1f2937;
    color: #e5e7eb;
    border: 1px solid #374151;
    border-radius: 4px;
    padding: 3px 8px;
    font-size: 11px;
    font-weight: 500;
}
QPushButton#btn_chip:hover {
    background-color: #374151;
    border-color: #38bdf8;
    color: #38bdf8;
}
QLineEdit, QTextEdit, QComboBox {
    background-color: #030712;
    border: 1px solid #374151;
    border-radius: 5px;
    padding: 5px 8px;
    color: #f9fafb;
    selection-background-color: #2563eb;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border: 1px solid #38bdf8;
}
QTableWidget {
    background-color: #030712;
    alternate-background-color: #0f172a;
    border: 1px solid #1f2937;
    border-radius: 6px;
    gridline-color: #1e293b;
    selection-background-color: #1d4ed8;
    selection-color: #ffffff;
}
QHeaderView::section {
    background-color: #1e293b;
    color: #94a3b8;
    padding: 6px;
    font-weight: bold;
    border: 1px solid #2d3748;
}
QTableCornerButton::section {
    background-color: #1e293b;
    border: 1px solid #2d3748;
}
QCheckBox {
    spacing: 6px;
    font-weight: 500;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid #475569;
    background-color: #030712;
}
QCheckBox::indicator:checked {
    background-color: #2563eb;
    border: 1px solid #38bdf8;
}
QStatusBar {
    background-color: #030712;
    border-top: 1px solid #1f2937;
    color: #9ca3af;
}
QMenu {
    background-color: #1f2937;
    border: 1px solid #374151;
    padding: 5px;
}
QMenu::item {
    padding: 6px 25px;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: #2563eb;
}
"""

class CellExtractorDialog(QDialog):
    def __init__(self, parent=None, initial_text: str = ""):
        super().__init__(parent)
        self.setWindowTitle("⚡ Quick ENC Cell Extractor & Formatter")
        self.resize(650, 480)
        self.parent_window = parent
        self.extracted_cells = []

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Instructions
        lbl_info = QLabel("Paste any text, email, table, or open a CSV/ECDIS file. It will automatically extract only the 8-character ENC codes formatted with commas:")
        lbl_info.setWordWrap(True)
        lbl_info.setStyleSheet("color: #94a3b8;")
        layout.addWidget(lbl_info)

        # Input Area
        lbl_in = QLabel("Input Text / File Content:")
        lbl_in.setStyleSheet("font-weight: bold; color: #38bdf8;")
        layout.addWidget(lbl_in)

        self.txt_input = QTextEdit()
        self.txt_input.setPlaceholderText("Paste raw text, CSV data, route plan, or chart list here...")
        self.txt_input.textChanged.connect(self.do_extract)
        layout.addWidget(self.txt_input, stretch=1)

        # Input Action Buttons
        in_btn_bar = QHBoxLayout()
        in_btn_bar.setSpacing(8)

        btn_paste_in = QPushButton("📋 Paste from Clipboard")
        btn_paste_in.setObjectName("btn_paste")
        btn_paste_in.clicked.connect(self.action_paste_input)
        in_btn_bar.addWidget(btn_paste_in)

        btn_open_in = QPushButton("📂 Open File (CSV / TXT / EUSR)...")
        btn_open_in.setObjectName("btn_import_file")
        btn_open_in.clicked.connect(self.action_open_file)
        in_btn_bar.addWidget(btn_open_in)

        btn_clear_in = QPushButton("🧹 Clear")
        btn_clear_in.setObjectName("btn_secondary")
        btn_clear_in.clicked.connect(self.txt_input.clear)
        in_btn_bar.addWidget(btn_clear_in)

        in_btn_bar.addStretch()
        layout.addLayout(in_btn_bar)

        # Extracted Output Area
        self.lbl_out_title = QLabel("Extracted ENC Cell Codes (0 cells):")
        self.lbl_out_title.setStyleSheet("font-weight: bold; color: #4ade80;")
        layout.addWidget(self.lbl_out_title)

        self.txt_output = QTextEdit()
        self.txt_output.setReadOnly(True)
        self.txt_output.setFont(QFont("Consolas", 10))
        self.txt_output.setPlaceholderText("Extracted comma-separated cell codes will appear here...")
        layout.addWidget(self.txt_output, stretch=1)

        # Bottom Actions
        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(10)

        self.btn_copy_res = QPushButton("📋 Copy Cell Codes to Clipboard")
        self.btn_copy_res.setObjectName("btn_copy_cells")
        self.btn_copy_res.setStyleSheet("font-size: 13px; font-weight: bold; padding: 8px 18px;")
        self.btn_copy_res.clicked.connect(self.action_copy_result)
        bottom_bar.addWidget(self.btn_copy_res)

        self.btn_add_to_basket = QPushButton("➕ Add Directly to Order Basket")
        self.btn_add_to_basket.setObjectName("btn_renew_all")
        self.btn_add_to_basket.clicked.connect(self.action_add_to_basket)
        bottom_bar.addWidget(self.btn_add_to_basket)

        bottom_bar.addStretch()

        btn_close = QPushButton("Close")
        btn_close.setObjectName("btn_secondary")
        btn_close.clicked.connect(self.accept)
        bottom_bar.addWidget(btn_close)

        layout.addLayout(bottom_bar)

        if initial_text:
            self.txt_input.setPlainText(initial_text)

    def action_paste_input(self):
        text = QApplication.clipboard().text()
        if text:
            self.txt_input.setPlainText(text)

    def action_open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select File to Extract Cells", "",
            "All Supported Files (*.csv *.eusr.csv *.txt *.cwo *.cls);;All Files (*)"
        )
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                self.txt_input.setPlainText(content)
            except Exception as e:
                QMessageBox.critical(self, "Error Opening File", f"Failed to read file: {e}")

    def do_extract(self):
        raw = self.txt_input.toPlainText()
        self.extracted_cells = extract_cell_codes(raw, unique_only=True, sort_alphabetical=True)
        count = len(self.extracted_cells)
        self.lbl_out_title.setText(f"Extracted ENC Cell Codes ({count} unique cells):")
        
        formatted_str = ", ".join(self.extracted_cells)
        self.txt_output.setPlainText(formatted_str)

    def action_copy_result(self):
        text = self.txt_output.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Nothing to Copy", "No ENC cell codes have been extracted yet.")
            return
        QApplication.clipboard().setText(text)
        QMessageBox.information(
            self, "Copied to Clipboard",
            f"Successfully copied {len(self.extracted_cells)} ENC cell codes to clipboard!\n\nFormat:\n{text[:120]}..."
        )

    def action_add_to_basket(self):
        text = self.txt_output.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Nothing to Add", "No ENC cell codes have been extracted yet.")
            return
        if self.parent_window and hasattr(self.parent_window, "manager"):
            count = self.parent_window.manager.add_from_text(text)
            self.parent_window.refresh_basket_table()
            self.parent_window.tabs.setCurrentIndex(0)
            QMessageBox.information(
                self, "Added to Order Basket",
                f"Successfully added {count} charts to Order Basket!"
            )
            self.accept()

class ShipInfoDialog(QDialog):
    def __init__(self, ship_info: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Vessel / Ship Details (#ShipName, etc.)")
        self.setFixedWidth(460)
        self.ship_info = ship_info.copy()
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.inputs = {}
        fields = [
            ("ShipName", "Vessel Name (ShipName):"),
            ("ShipType", "Vessel Type (ShipType):"),
            ("ShipEmail", "Vessel Email (ShipEmail):"),
            ("ShipPhone", "Vessel Phone (ShipPhone):"),
            ("OwnerName", "Owner / Manager (OwnerName):"),
            ("ContactEmail", "Contact Email (ContactEmail):"),
            ("ContactPhone", "Contact Phone (ContactPhone):"),
        ]
        
        for key, label in fields:
            edit = QLineEdit(self.ship_info.get(key, ""))
            self.inputs[key] = edit
            form.addRow(label, edit)
            
        layout.addLayout(form)
        
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def get_data(self):
        for k, edit in self.inputs.items():
            self.ship_info[k] = edit.text().strip()
        return self.ship_info

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ENC Cell Manager Pro & Permit Expiry Monitor - ADMIRALTY Edition")
        self.resize(1260, 780)
        
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.db = ENCDatabase()
        self.inventory = InventoryManager(self.db)
        self.manager = ENCManager(self.db, self.inventory)
        
        self.settings = load_settings()
        self.setStyleSheet(STYLE_SHEET)
        
        self.setup_ui()
        self.setup_shortcuts()
        
        self.auto_load_permit()
        self.refresh_basket_table()

    def auto_load_permit(self):
        permit_path = self.settings.get("last_permit_file", "")
        if not permit_path or not os.path.exists(permit_path):
            default_candidate = r"E:\NSRECDIS\2. PERMIT\wk35 26-8-30\PROSPERA-permits\permits\BACKUP\PERMIT.TXT"
            if os.path.exists(default_candidate):
                permit_path = default_candidate

        if permit_path and os.path.exists(permit_path):
            try:
                self.inventory.load_permit_file(permit_path)
                self.manager.update_duplicates_and_inventory()
                self.update_inventory_ui()
            except Exception as e:
                print(f"Failed to auto-load permit: {e}")

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(6)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # TAB 1: Order Basket
        self.tab_basket = QWidget()
        self.setup_basket_tab()
        self.tabs.addTab(self.tab_basket, "📋 Order Basket & Deduplication")

        # TAB 2: Inventory & Expiry Monitor
        self.tab_inventory = QWidget()
        self.setup_inventory_tab()
        self.tabs.addTab(self.tab_inventory, "📦 Permit Inventory & Expiry Monitor")

        # STATUS BAR
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.lbl_stats = QLabel("Basket: 0 Cells | Unique: 0 | Duplicates: 0")
        self.lbl_stats.setStyleSheet("font-weight: bold; padding: 0 10px;")
        self.status_bar.addWidget(self.lbl_stats)

        self.lbl_db_info = QLabel("ADMIRALTY Database: Ready (35,277 Cells)")
        self.lbl_db_info.setStyleSheet("color: #38bdf8; padding-right: 15px;")
        self.status_bar.addPermanentWidget(self.lbl_db_info)

    def setup_basket_tab(self):
        layout = QVBoxLayout(self.tab_basket)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # TOP BAR 1: Quick Add, Import & Extractor
        top_bar = QHBoxLayout()
        top_bar.setSpacing(8)

        self.btn_paste = QPushButton("📋 Paste from Clipboard")
        self.btn_paste.setObjectName("btn_paste")
        self.btn_paste.setToolTip("Paste ENC codes directly from clipboard (Ctrl+V)")
        self.btn_paste.clicked.connect(self.action_paste_clipboard)
        top_bar.addWidget(self.btn_paste)

        self.btn_import_file = QPushButton("📂 Import CSV / EUSR / TXT...")
        self.btn_import_file.setObjectName("btn_import_file")
        self.btn_import_file.setToolTip("Import cells from CSV (including ECDIS .eusr.csv report) or TXT basket")
        self.btn_import_file.clicked.connect(self.action_import_file)
        top_bar.addWidget(self.btn_import_file)

        self.btn_extractor = QPushButton("⚡ Cell Extractor...")
        self.btn_extractor.setObjectName("btn_extractor")
        self.btn_extractor.setToolTip("Extract clean comma-separated list of ENC cell codes from any text/file")
        self.btn_extractor.clicked.connect(self.action_open_cell_extractor)
        top_bar.addWidget(self.btn_extractor)

        self.input_text = QLineEdit()
        self.input_text.setPlaceholderText("Type/Paste ENC cell codes here (e.g. AU130120, AU130150, KR1O0000)...")
        self.input_text.returnPressed.connect(self.action_add_from_input)
        top_bar.addWidget(self.input_text, stretch=1)

        self.btn_add = QPushButton("➕ Add")
        self.btn_add.clicked.connect(self.action_add_from_input)
        top_bar.addWidget(self.btn_add)

        layout.addLayout(top_bar)

        # TOP BAR 2: ADD FROM INVENTORY SHORTCUTS
        inv_add_bar = QHBoxLayout()
        inv_add_bar.setSpacing(6)
        lbl_inv_add = QLabel("➕ Add from Permit:")
        lbl_inv_add.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 12px;")
        inv_add_bar.addWidget(lbl_inv_add)

        btn_add_all_inv = QPushButton("📦 All in Inventory")
        btn_add_all_inv.setObjectName("btn_chip")
        btn_add_all_inv.setToolTip("Add all charts from loaded permit into basket")
        btn_add_all_inv.clicked.connect(self.action_add_all_from_inventory)
        inv_add_bar.addWidget(btn_add_all_inv)

        btn_add_crit_inv = QPushButton("🟠 Active <= 30 Days (Expiring)")
        btn_add_crit_inv.setObjectName("btn_chip")
        btn_add_crit_inv.setToolTip("Add charts with remaining validity 30 days or less into basket")
        btn_add_crit_inv.clicked.connect(self.action_add_expiring_to_basket)
        inv_add_bar.addWidget(btn_add_crit_inv)

        btn_add_act_inv = QPushButton("🟢 Active > 30 Days")
        btn_add_act_inv.setObjectName("btn_chip")
        btn_add_act_inv.setToolTip("Add charts with remaining validity more than 30 days into basket")
        btn_add_act_inv.clicked.connect(self.action_add_active_more_than_30_to_basket)
        inv_add_bar.addWidget(btn_add_act_inv)

        inv_add_bar.addStretch()
        layout.addLayout(inv_add_bar)

        # ACTION TOOLBAR
        action_bar = QHBoxLayout()
        action_bar.setSpacing(8)

        self.btn_dedup = QPushButton("🗑️ Remove Duplicates")
        self.btn_dedup.setObjectName("btn_dedup")
        self.btn_dedup.clicked.connect(self.action_remove_duplicates)
        action_bar.addWidget(self.btn_dedup)

        self.btn_delete_selected = QPushButton("❌ Delete Selected")
        self.btn_delete_selected.setObjectName("btn_delete")
        self.btn_delete_selected.setToolTip("Delete selected rows (Delete key)")
        self.btn_delete_selected.clicked.connect(self.action_delete_selected)
        action_bar.addWidget(self.btn_delete_selected)

        self.btn_clear = QPushButton("🧹 Clear Basket")
        self.btn_clear.setObjectName("btn_secondary")
        self.btn_clear.clicked.connect(self.action_clear_all)
        action_bar.addWidget(self.btn_clear)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        sep.setStyleSheet("color: #374151;")
        action_bar.addWidget(sep)

        self.btn_copy_cells_only = QPushButton("📋 Copy Cell Codes Only (, )")
        self.btn_copy_cells_only.setObjectName("btn_copy_cells")
        self.btn_copy_cells_only.setToolTip("Copy only the cell codes formatted as 'AU130120, AU130150, ...' to clipboard")
        self.btn_copy_cells_only.clicked.connect(self.action_copy_cell_codes_only)
        action_bar.addWidget(self.btn_copy_cells_only)

        self.btn_export_txt = QPushButton("💾 Export Basket (.txt)")
        self.btn_export_txt.setObjectName("btn_export")
        self.btn_export_txt.setToolTip("Save order in official ADMIRALTY tab-delimited format (Ctrl+S)")
        self.btn_export_txt.clicked.connect(self.action_export_txt)
        action_bar.addWidget(self.btn_export_txt)

        self.btn_export_pdf = QPushButton("📄 Export PDF Report")
        self.btn_export_pdf.setObjectName("btn_export_pdf")
        self.btn_export_pdf.setToolTip("Generate professional, full-color PDF Order Requisition Report")
        self.btn_export_pdf.clicked.connect(self.action_export_basket_pdf)
        action_bar.addWidget(self.btn_export_pdf)

        self.btn_copy_all = QPushButton("📋 Copy Full Basket")
        self.btn_copy_all.setObjectName("btn_secondary")
        self.btn_copy_all.setToolTip("Copy formatted order basket text with titles and scales to clipboard")
        self.btn_copy_all.clicked.connect(self.action_copy_all)
        action_bar.addWidget(self.btn_copy_all)

        action_bar.addStretch()

        self.btn_ship_info = QPushButton("🚢 Vessel Info")
        self.btn_ship_info.setObjectName("btn_secondary")
        self.btn_ship_info.setToolTip("Edit vessel details (#ShipName, #ShipType, etc.)")
        self.btn_ship_info.clicked.connect(self.action_edit_ship_info)
        action_bar.addWidget(self.btn_ship_info)

        layout.addLayout(action_bar)

        # SELECTION & FILTER BAR
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(8)

        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("🔍 Search basket (Cell ID, Title, Scale)...")
        self.filter_input.textChanged.connect(self.refresh_basket_table)
        filter_bar.addWidget(self.filter_input, stretch=1)

        self.combo_basket_filter = QComboBox()
        self.combo_basket_filter.addItems([
            "All Charts",
            "📦 In Inventory (All)",
            "🟠 In Inventory (Active <= 30 Days)",
            "🟢 In Inventory (Active > 30 Days)",
            "🆕 Not in Permit (New Charts)",
            "⚠️ Duplicates Only"
        ])
        self.combo_basket_filter.currentIndexChanged.connect(self.refresh_basket_table)
        filter_bar.addWidget(self.combo_basket_filter)

        layout.addLayout(filter_bar)

        # QUICK ROW SELECTION TOOLBAR FOR BASKET
        select_bar = QHBoxLayout()
        select_bar.setSpacing(6)
        lbl_select = QLabel("Select Rows:")
        lbl_select.setStyleSheet("color: #94a3b8; font-weight: 600; font-size: 12px;")
        select_bar.addWidget(lbl_select)

        btn_sel_all = QPushButton("All")
        btn_sel_all.setObjectName("btn_chip")
        btn_sel_all.clicked.connect(lambda: self.select_basket_rows("all"))
        select_bar.addWidget(btn_sel_all)

        btn_sel_inv = QPushButton("In Inventory (All)")
        btn_sel_inv.setObjectName("btn_chip")
        btn_sel_inv.clicked.connect(lambda: self.select_basket_rows("in_inventory"))
        select_bar.addWidget(btn_sel_inv)

        btn_sel_crit = QPushButton("Active <= 30 Days")
        btn_sel_crit.setObjectName("btn_chip")
        btn_sel_crit.clicked.connect(lambda: self.select_basket_rows("less_30"))
        select_bar.addWidget(btn_sel_crit)

        btn_sel_act = QPushButton("Active > 30 Days")
        btn_sel_act.setObjectName("btn_chip")
        btn_sel_act.clicked.connect(lambda: self.select_basket_rows("more_30"))
        select_bar.addWidget(btn_sel_act)

        btn_sel_new = QPushButton("Not in Permit (New)")
        btn_sel_new.setObjectName("btn_chip")
        btn_sel_new.clicked.connect(lambda: self.select_basket_rows("new"))
        select_bar.addWidget(btn_sel_new)

        btn_sel_dup = QPushButton("Duplicates")
        btn_sel_dup.setObjectName("btn_chip")
        btn_sel_dup.clicked.connect(lambda: self.select_basket_rows("duplicates"))
        select_bar.addWidget(btn_sel_dup)

        btn_sel_none = QPushButton("Clear Selection")
        btn_sel_none.setObjectName("btn_chip")
        btn_sel_none.clicked.connect(lambda: self.table.clearSelection())
        select_bar.addWidget(btn_sel_none)

        select_bar.addStretch()
        layout.addLayout(select_bar)

        # BASKET TABLE
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "#", "Product Type", "Product Number (Cell)", "Product Title", "Scale", "Duplicate Status", "Current Permit Status"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.table)

    def setup_inventory_tab(self):
        layout = QVBoxLayout(self.tab_inventory)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # HEADER & CONTROLS
        header_bar = QHBoxLayout()
        header_bar.setSpacing(8)

        self.btn_load_permit = QPushButton("📂 Load Permit File (PERMIT.TXT / ENC.PMT)")
        self.btn_load_permit.setObjectName("btn_paste")
        self.btn_load_permit.clicked.connect(self.action_load_permit_file)
        header_bar.addWidget(self.btn_load_permit)

        self.btn_load_folder = QPushButton("📁 Browse Permit Folder...")
        self.btn_load_folder.setObjectName("btn_secondary")
        self.btn_load_folder.clicked.connect(self.action_load_permit_folder)
        header_bar.addWidget(self.btn_load_folder)

        self.lbl_permit_path = QLabel("No permit file currently loaded.")
        self.lbl_permit_path.setStyleSheet("color: #94a3b8; font-style: italic;")
        header_bar.addWidget(self.lbl_permit_path, stretch=1)

        layout.addLayout(header_bar)

        # KPI STATISTIC CARDS
        kpi_bar = QHBoxLayout()
        kpi_bar.setSpacing(8)

        self.card_total = QLabel("📦 Total: 0")
        self.card_total.setStyleSheet("background-color: #1e293b; padding: 6px 10px; border-radius: 6px; font-weight: bold; border: 1px solid #334155;")
        kpi_bar.addWidget(self.card_total)

        self.card_active = QLabel("🟢 Active (>60d): 0")
        self.card_active.setStyleSheet("background-color: #064e3b; color: #34d399; padding: 6px 10px; border-radius: 6px; font-weight: bold; border: 1px solid #059669;")
        kpi_bar.addWidget(self.card_active)

        self.card_warning = QLabel("🟡 Warning (31-60d): 0")
        self.card_warning.setStyleSheet("background-color: #713f12; color: #fde047; padding: 6px 10px; border-radius: 6px; font-weight: bold; border: 1px solid #ca8a04;")
        kpi_bar.addWidget(self.card_warning)

        self.card_critical = QLabel("🟠 Critical (1-30d): 0")
        self.card_critical.setStyleSheet("background-color: #7c2d12; color: #fb923c; padding: 6px 10px; border-radius: 6px; font-weight: bold; border: 1px solid #ea580c;")
        kpi_bar.addWidget(self.card_critical)

        self.card_expired = QLabel("🔴 Expired: 0")
        self.card_expired.setStyleSheet("background-color: #450a0a; color: #f87171; padding: 6px 10px; border-radius: 6px; font-weight: bold; border: 1px solid #dc2626;")
        kpi_bar.addWidget(self.card_expired)

        kpi_bar.addStretch()
        layout.addLayout(kpi_bar)

        # ACTION TOOLBAR: ADD TO ORDER BASKET & EXPORTS
        action_bar = QHBoxLayout()
        action_bar.setSpacing(6)

        lbl_transfer = QLabel("➕ Add to Basket:")
        lbl_transfer.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 12px;")
        action_bar.addWidget(lbl_transfer)

        self.btn_renew_crit = QPushButton("🟠 Active <= 30 Days (Expiring)")
        self.btn_renew_crit.setObjectName("btn_renew_crit")
        self.btn_renew_crit.setToolTip("Copy all charts expiring in 30 days or less directly into Order Basket")
        self.btn_renew_crit.clicked.connect(self.action_add_expiring_to_basket)
        action_bar.addWidget(self.btn_renew_crit)

        self.btn_renew_act = QPushButton("🟢 Active > 30 Days")
        self.btn_renew_act.setObjectName("btn_renew_act")
        self.btn_renew_act.setToolTip("Copy charts with more than 30 days remaining into Order Basket")
        self.btn_renew_act.clicked.connect(self.action_add_active_more_than_30_to_basket)
        action_bar.addWidget(self.btn_renew_act)

        self.btn_renew_all = QPushButton("📦 All in Inventory")
        self.btn_renew_all.setObjectName("btn_renew_all")
        self.btn_renew_all.setToolTip("Copy all charts from this permit into Order Basket")
        self.btn_renew_all.clicked.connect(self.action_add_all_from_inventory)
        action_bar.addWidget(self.btn_renew_all)

        self.btn_renew_selected = QPushButton("➕ Add Selected")
        self.btn_renew_selected.setObjectName("btn_secondary")
        self.btn_renew_selected.clicked.connect(self.action_add_selected_to_basket)
        action_bar.addWidget(self.btn_renew_selected)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.VLine)
        sep2.setFrameShadow(QFrame.Shadow.Sunken)
        sep2.setStyleSheet("color: #374151;")
        action_bar.addWidget(sep2)

        self.btn_inv_copy_cells = QPushButton("📋 Copy Cell Codes Only (, )")
        self.btn_inv_copy_cells.setObjectName("btn_copy_cells")
        self.btn_inv_copy_cells.setToolTip("Copy inventory cell codes formatted as 'AU130120, AU130150, ...' to clipboard")
        self.btn_inv_copy_cells.clicked.connect(self.action_copy_inventory_cells_only)
        action_bar.addWidget(self.btn_inv_copy_cells)

        self.btn_export_inv_pdf = QPushButton("📄 Export PDF Report")
        self.btn_export_inv_pdf.setObjectName("btn_export_pdf")
        self.btn_export_inv_pdf.setToolTip("Generate professional, full-color PDF Permit Audit & Expiry Report")
        self.btn_export_inv_pdf.clicked.connect(self.action_export_inventory_pdf)
        action_bar.addWidget(self.btn_export_inv_pdf)

        self.btn_export_inv = QPushButton("💾 Export CSV")
        self.btn_export_inv.setObjectName("btn_export")
        self.btn_export_inv.clicked.connect(self.action_export_inventory)
        action_bar.addWidget(self.btn_export_inv)

        self.btn_copy_inv = QPushButton("📋 Copy Report")
        self.btn_copy_inv.setObjectName("btn_secondary")
        self.btn_copy_inv.clicked.connect(self.action_copy_inventory)
        action_bar.addWidget(self.btn_copy_inv)

        action_bar.addStretch()
        layout.addLayout(action_bar)

        # FILTER & SEARCH BAR
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(8)

        self.inv_filter_input = QLineEdit()
        self.inv_filter_input.setPlaceholderText("🔍 Search inventory (Cell ID, Title, Expiry Date)...")
        self.inv_filter_input.textChanged.connect(self.refresh_inventory_table)
        filter_bar.addWidget(self.inv_filter_input, stretch=1)

        self.combo_status_filter = QComboBox()
        self.combo_status_filter.addItems([
            "All Statuses",
            "🟠 Critical & Expired (<= 30d)",
            "🔴 Expired Only",
            "🟠 Critical Only (1-30d)",
            "🟡 Warning Only (31-60d)",
            "🟢 Active Only (> 60d)"
        ])
        self.combo_status_filter.currentIndexChanged.connect(self.refresh_inventory_table)
        filter_bar.addWidget(self.combo_status_filter)

        layout.addLayout(filter_bar)

        # ROW SELECTION TOOLBAR FOR INVENTORY
        inv_select_bar = QHBoxLayout()
        inv_select_bar.setSpacing(6)
        lbl_inv_sel = QLabel("Select Rows:")
        lbl_inv_sel.setStyleSheet("color: #94a3b8; font-weight: 600; font-size: 12px;")
        inv_select_bar.addWidget(lbl_inv_sel)

        btn_inv_sel_all = QPushButton("All")
        btn_inv_sel_all.setObjectName("btn_chip")
        btn_inv_sel_all.clicked.connect(lambda: self.select_inventory_rows("all"))
        inv_select_bar.addWidget(btn_inv_sel_all)

        btn_inv_sel_crit = QPushButton("Active <= 30 Days")
        btn_inv_sel_crit.setObjectName("btn_chip")
        btn_inv_sel_crit.clicked.connect(lambda: self.select_inventory_rows("less_30"))
        inv_select_bar.addWidget(btn_inv_sel_crit)

        btn_inv_sel_act = QPushButton("Active > 30 Days")
        btn_inv_sel_act.setObjectName("btn_chip")
        btn_inv_sel_act.clicked.connect(lambda: self.select_inventory_rows("more_30"))
        inv_select_bar.addWidget(btn_inv_sel_act)

        btn_inv_sel_exp = QPushButton("Expired (<= 0d)")
        btn_inv_sel_exp.setObjectName("btn_chip")
        btn_inv_sel_exp.clicked.connect(lambda: self.select_inventory_rows("expired"))
        inv_select_bar.addWidget(btn_inv_sel_exp)

        btn_inv_sel_none = QPushButton("Clear Selection")
        btn_inv_sel_none.setObjectName("btn_chip")
        btn_inv_sel_none.clicked.connect(lambda: self.inv_table.clearSelection())
        inv_select_bar.addWidget(btn_inv_sel_none)

        inv_select_bar.addStretch()
        layout.addLayout(inv_select_bar)

        # INVENTORY TABLE
        self.inv_table = QTableWidget()
        self.inv_table.setColumnCount(7)
        self.inv_table.setHorizontalHeaderLabels([
            "#", "Cell ID", "Product Title", "Scale", "Expiry Date", "Days Remaining", "Permit Status"
        ])
        self.inv_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.inv_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.inv_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.inv_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.inv_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.inv_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.inv_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)

        self.inv_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.inv_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.inv_table.setAlternatingRowColors(True)
        self.inv_table.setSortingEnabled(True)
        layout.addWidget(self.inv_table)

    def setup_shortcuts(self):
        shortcut_paste = QShortcut(QKeySequence.StandardKey.Paste, self)
        shortcut_paste.activated.connect(self.action_paste_clipboard)

        shortcut_del = QShortcut(QKeySequence.StandardKey.Delete, self)
        shortcut_del.activated.connect(self.action_delete_selected)

        shortcut_save = QShortcut(QKeySequence.StandardKey.Save, self)
        shortcut_save.activated.connect(self.action_export_txt)

    # ------------------ CELL EXTRACTOR & FORMATTER ACTIONS ------------------
    def action_open_cell_extractor(self):
        dlg = CellExtractorDialog(parent=self)
        dlg.exec()

    def action_copy_cell_codes_only(self):
        if not self.manager.items:
            QMessageBox.warning(self, "Basket Empty", "No charts in the order basket.")
            return

        selected_rows = set(index.row() for index in self.table.selectedIndexes())
        if selected_rows:
            indices = []
            for r in selected_rows:
                idx_item = self.table.item(r, 0)
                if idx_item:
                    orig_idx = idx_item.data(Qt.ItemDataRole.UserRole)
                    if orig_idx is not None:
                        indices.append(orig_idx)
            formatted = self.manager.get_cell_codes_string(unique_only=True, sort_alphabetical=True, selected_indices=indices)
            count = len(indices)
            msg = f"Copied {count} selected ENC cell codes to clipboard!"
        else:
            formatted = self.manager.get_cell_codes_string(unique_only=True, sort_alphabetical=True)
            count = len(set(it.product_number for it in self.manager.items))
            msg = f"Copied all {count} unique ENC cell codes to clipboard!"

        QApplication.clipboard().setText(formatted)
        self.status_bar.showMessage(msg, 4000)
        QMessageBox.information(
            self, "Cell Codes Copied",
            f"{msg}\n\nFormatted text:\n{formatted[:150]}{'...' if len(formatted) > 150 else ''}"
        )

    def action_copy_inventory_cells_only(self):
        if not self.inventory.items:
            QMessageBox.warning(self, "Inventory Empty", "No permit data loaded.")
            return

        selected_rows = set(index.row() for index in self.inv_table.selectedIndexes())
        if selected_rows:
            cells = []
            for r in selected_rows:
                c_item = self.inv_table.item(r, 1)
                if c_item:
                    cells.append(c_item.text().strip().upper())
            cells = sorted(list(set(cells)))
            formatted = ", ".join(cells)
            count = len(cells)
            msg = f"Copied {count} selected inventory cell codes to clipboard!"
        else:
            cells = sorted(list(set(it.cell_id for it in self.inventory.items)))
            formatted = ", ".join(cells)
            count = len(cells)
            msg = f"Copied all {count} inventory cell codes to clipboard!"

        QApplication.clipboard().setText(formatted)
        self.status_bar.showMessage(msg, 4000)
        QMessageBox.information(
            self, "Inventory Cells Copied",
            f"{msg}\n\nFormatted text:\n{formatted[:150]}{'...' if len(formatted) > 150 else ''}"
        )

    # ------------------ PDF EXPORT ACTIONS ------------------
    def action_export_basket_pdf(self):
        if not self.manager.items:
            QMessageBox.warning(self, "Basket Empty", "Order basket is empty. Nothing to export.")
            return

        vessel = self.manager.ship_info.get("ShipName", "Vessel").strip()
        date_tag = datetime.datetime.now().strftime("%Y%m%d")
        default_name = f"enc_order_requisition_{vessel}_{date_tag}.pdf"

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Order Requisition PDF Report", default_name, "PDF Files (*.pdf)"
        )
        if file_path:
            try:
                generate_basket_pdf(self.manager, file_path)
                reply = QMessageBox.information(
                    self, "PDF Report Created",
                    f"Professional Order Requisition PDF Report successfully generated:\n{file_path}\n\nWould you like to open it now?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    os.startfile(file_path)
            except Exception as e:
                QMessageBox.critical(self, "PDF Error", f"Failed to generate PDF: {e}")

    def action_export_inventory_pdf(self):
        if not self.inventory.items:
            QMessageBox.warning(self, "Inventory Empty", "No permit data loaded.")
            return

        vessel = self.manager.ship_info.get("ShipName", "Vessel").strip()
        date_tag = datetime.datetime.now().strftime("%Y%m%d")
        default_name = f"enc_permit_inventory_{vessel}_{date_tag}.pdf"

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Permit Inventory PDF Report", default_name, "PDF Files (*.pdf)"
        )
        if file_path:
            try:
                generate_inventory_pdf(self.inventory, file_path, self.manager.ship_info)
                reply = QMessageBox.information(
                    self, "PDF Report Created",
                    f"Professional Vessel Permit Inventory PDF Report successfully generated:\n{file_path}\n\nWould you like to open it now?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    os.startfile(file_path)
            except Exception as e:
                QMessageBox.critical(self, "PDF Error", f"Failed to generate PDF: {e}")

    # ------------------ SELECTION HELPERS ------------------
    def select_basket_rows(self, criteria: str):
        self.table.clearSelection()
        for r in range(self.table.rowCount()):
            idx_item = self.table.item(r, 0)
            if not idx_item:
                continue
            orig_idx = idx_item.data(Qt.ItemDataRole.UserRole)
            if orig_idx is None or orig_idx >= len(self.manager.items):
                continue
            item = self.manager.items[orig_idx]
            
            match = False
            if criteria == "all":
                match = True
            elif criteria == "in_inventory":
                match = item.in_inventory
            elif criteria == "less_30":
                match = item.in_inventory and item.days_left is not None and item.days_left <= 30
            elif criteria == "more_30":
                match = item.in_inventory and item.days_left is not None and item.days_left > 30
            elif criteria == "new":
                match = not item.in_inventory
            elif criteria == "duplicates":
                match = item.is_duplicate

            if match:
                self.table.selectRow(r)

    def select_inventory_rows(self, criteria: str):
        self.inv_table.clearSelection()
        for r in range(self.inv_table.rowCount()):
            cell_item = self.inv_table.item(r, 1)
            if not cell_item:
                continue
            cid = cell_item.text().strip().upper()
            p_item = self.inventory.permit_dict.get(cid)
            if not p_item:
                continue

            match = False
            if criteria == "all":
                match = True
            elif criteria == "less_30":
                match = (p_item.days_left <= 30)
            elif criteria == "more_30":
                match = (p_item.days_left > 30)
            elif criteria == "expired":
                match = (p_item.days_left <= 0)

            if match:
                self.inv_table.selectRow(r)

    # ------------------ INVENTORY ACTIONS ------------------
    def action_load_permit_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Permit File", "", "Permit Files (*.txt *.pmt);;All Files (*)"
        )
        if file_path:
            self.load_permit_from_path(file_path)

    def action_load_permit_folder(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Permit Folder")
        if dir_path:
            candidates = ["PERMIT.TXT", "ENC.PMT", "permit.txt", "enc.pmt"]
            target = None
            for root, dirs, files in os.walk(dir_path):
                for f in files:
                    if f in candidates:
                        target = os.path.join(root, f)
                        break
                if target:
                    break
            
            if target:
                self.load_permit_from_path(target)
            else:
                QMessageBox.warning(self, "No Permit File Found", f"Could not find PERMIT.TXT or ENC.PMT in:\n{dir_path}")

    def load_permit_from_path(self, file_path: str):
        try:
            count = self.inventory.load_permit_file(file_path)
            self.settings["last_permit_file"] = file_path
            save_settings(self.settings)

            self.manager.update_duplicates_and_inventory()
            self.update_inventory_ui()
            self.refresh_basket_table()
            
            QMessageBox.information(
                self, "Permit Loaded Successfully",
                f"Successfully loaded {count} chart permits from:\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Failed to Load Permit", f"Error occurred: {e}")

    def update_inventory_ui(self):
        stats = self.inventory.get_stats()
        path_name = os.path.basename(self.inventory.file_path) if self.inventory.file_path else "Unknown"
        p_date = f" (Issue Date: {self.inventory.permit_date})" if self.inventory.permit_date else ""
        self.lbl_permit_path.setText(f"File: <b>{path_name}</b>{p_date} - {self.inventory.file_path}")

        self.card_total.setText(f"📦 Total: {stats['total']}")
        self.card_active.setText(f"🟢 Active (>60d): {stats['active']}")
        self.card_warning.setText(f"🟡 Warning (31-60d): {stats['warning']}")
        self.card_critical.setText(f"🟠 Critical (1-30d): {stats['critical']}")
        self.card_expired.setText(f"🔴 Expired: {stats['expired']}")

        self.refresh_inventory_table()

    def refresh_inventory_table(self):
        self.inv_table.setSortingEnabled(False)
        self.inv_table.setRowCount(0)

        filter_text = self.inv_filter_input.text().strip().lower()
        filter_cat = self.combo_status_filter.currentIndex()

        bg_expired = QColor(68, 10, 10)
        bg_critical = QColor(88, 32, 10)
        bg_warning = QColor(70, 50, 10)

        row_counter = 0
        for item in self.inventory.items:
            if filter_cat == 1 and item.days_left > 30:
                continue
            elif filter_cat == 2 and item.status_level != 0:
                continue
            elif filter_cat == 3 and item.status_level != 1:
                continue
            elif filter_cat == 4 and item.status_level != 2:
                continue
            elif filter_cat == 5 and item.status_level != 3:
                continue

            if filter_text:
                if (filter_text not in item.cell_id.lower() and
                    filter_text not in item.title.lower() and
                    filter_text not in item.expiry_str and
                    filter_text not in item.scale.lower()):
                    continue

            self.inv_table.insertRow(row_counter)

            it_idx = QTableWidgetItem()
            it_idx.setData(Qt.ItemDataRole.DisplayRole, row_counter + 1)
            it_idx.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            it_cell = QTableWidgetItem(item.cell_id)
            it_cell.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
            it_cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            it_title = QTableWidgetItem(item.title)

            it_scale = QTableWidgetItem(item.scale)
            it_scale.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            it_exp = QTableWidgetItem(item.expiry_str)
            it_exp.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            it_days = QTableWidgetItem()
            days_display = f"{item.days_left}d" if item.days_left >= 0 else f"{item.days_left}d (ago)"
            it_days.setData(Qt.ItemDataRole.DisplayRole, item.days_left)
            it_days.setText(days_display)
            it_days.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            it_status = QTableWidgetItem(item.status_label)
            it_status.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            it_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            row_items = [it_idx, it_cell, it_title, it_scale, it_exp, it_days, it_status]

            for it in row_items:
                if item.status_level == 0:
                    it.setBackground(QBrush(bg_expired))
                elif item.status_level == 1:
                    it.setBackground(QBrush(bg_critical))
                elif item.status_level == 2:
                    it.setBackground(QBrush(bg_warning))
                self.inv_table.setItem(row_counter, row_items.index(it), it)

            row_counter += 1

        self.inv_table.setSortingEnabled(True)

    def action_add_expiring_to_basket(self):
        expiring = self.inventory.get_cells_active_less_than(30)
        if not expiring:
            QMessageBox.information(self, "No Expiring Charts", "There are no charts expiring in 30 days or less.")
            return

        joined = ", ".join(expiring)
        count = self.manager.add_from_text(joined)
        self.refresh_basket_table()
        self.tabs.setCurrentIndex(0)
        QMessageBox.information(
            self, "Added to Order Basket",
            f"Successfully added {count} charts expiring in <= 30 days into Order Basket!"
        )

    def action_add_active_more_than_30_to_basket(self):
        active_more = self.inventory.get_cells_active_more_than(30)
        if not active_more:
            QMessageBox.information(self, "No Active Charts > 30 Days", "There are no charts in inventory with more than 30 days remaining.")
            return

        joined = ", ".join(active_more)
        count = self.manager.add_from_text(joined)
        self.refresh_basket_table()
        self.tabs.setCurrentIndex(0)
        QMessageBox.information(
            self, "Added to Order Basket",
            f"Successfully added {count} charts active > 30 days into Order Basket!"
        )

    def action_add_all_from_inventory(self):
        all_cells = self.inventory.get_cells_in_inventory()
        if not all_cells:
            QMessageBox.warning(self, "Inventory Empty", "No permit file is currently loaded.")
            return

        joined = ", ".join(all_cells)
        count = self.manager.add_from_text(joined)
        self.refresh_basket_table()
        self.tabs.setCurrentIndex(0)
        QMessageBox.information(
            self, "Added All to Basket",
            f"Successfully added all {count} charts from inventory into Order Basket!"
        )

    def action_add_selected_to_basket(self):
        selected_rows = set(index.row() for index in self.inv_table.selectedIndexes())
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select at least 1 chart in the inventory table first.")
            return

        cells = []
        for r in selected_rows:
            c_item = self.inv_table.item(r, 1)
            if c_item:
                cells.append(c_item.text().strip())

        if cells:
            count = self.manager.add_from_text(", ".join(cells))
            self.refresh_basket_table()
            self.tabs.setCurrentIndex(0)
            QMessageBox.information(self, "Charts Added", f"Successfully added {count} selected charts to Order Basket.")

    def action_export_inventory(self):
        if not self.inventory.items:
            QMessageBox.warning(self, "Empty Inventory", "No permit data loaded.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Inventory Report", "enc_inventory_status.csv", "CSV Files (*.csv);;Text Files (*.txt)"
        )
        if file_path:
            try:
                csv_content = self.inventory.export_csv()
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(csv_content)
                QMessageBox.information(self, "Export Successful", f"Inventory report saved to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to save file: {e}")

    def action_copy_inventory(self):
        if not self.inventory.items:
            QMessageBox.warning(self, "Empty Inventory", "No permit data loaded.")
            return
        csv_content = self.inventory.export_csv()
        QApplication.clipboard().setText(csv_content)
        self.status_bar.showMessage("Inventory report copied to clipboard!", 3500)

    # ------------------ BASKET ACTIONS ------------------
    def action_import_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select CSV / EUSR / TXT File", "",
            "All Supported Files (*.csv *.eusr.csv *.txt *.cwo *.cls);;CSV & EUSR Files (*.csv *.eusr.csv);;Text & Basket Files (*.txt *.cwo);;All Files (*)"
        )
        if file_path:
            try:
                count = self.manager.import_file(file_path)
                self.refresh_basket_table()
                vessel_msg = f"\nVessel Name detected: {self.manager.ship_info['ShipName']}" if self.manager.ship_info.get("ShipName") else ""
                QMessageBox.information(
                    self, "File Imported Successfully",
                    f"Successfully imported {count} charts from:\n{os.path.basename(file_path)}{vessel_msg}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Import Error", f"Failed to read file: {e}")

    def action_paste_clipboard(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if not text:
            QMessageBox.information(self, "Clipboard Empty", "Clipboard is empty.")
            return
        
        count = self.manager.add_from_text(text)
        if count > 0:
            self.refresh_basket_table()
            self.status_bar.showMessage(f"Successfully added {count} cells from clipboard!", 4000)
        else:
            QMessageBox.warning(
                self, "No Valid Cells Found",
                "No valid 8-character ENC cell codes found in clipboard.\nExample formats: AU130120, US4TB1L0, KR1O0000."
            )

    def action_add_from_input(self):
        text = self.input_text.text().strip()
        if not text:
            return
        count = self.manager.add_from_text(text)
        if count > 0:
            self.input_text.clear()
            self.refresh_basket_table()
            self.status_bar.showMessage(f"Successfully added {count} cells!", 3000)
        else:
            QMessageBox.warning(self, "Invalid Cell Format", "Cell codes not recognized. Please provide 8-character codes (e.g. AU130120).")

    def action_remove_duplicates(self):
        dups = self.manager.get_stats()[2]
        if dups == 0:
            QMessageBox.information(self, "No Duplicates", "All charts in the basket are already unique.")
            return
        
        removed = self.manager.remove_duplicates()
        self.refresh_basket_table()
        QMessageBox.information(self, "Duplicates Removed", f"Removed {removed} duplicate rows. All remaining charts are now unique!")

    def action_delete_selected(self):
        selected_rows = sorted(set(index.row() for index in self.table.selectedIndexes()), reverse=True)
        if not selected_rows:
            return
        
        indices_to_remove = []
        for r in selected_rows:
            orig_idx_item = self.table.item(r, 0)
            if orig_idx_item:
                orig_idx = orig_idx_item.data(Qt.ItemDataRole.UserRole)
                if orig_idx is not None:
                    indices_to_remove.append(orig_idx)
                    
        if indices_to_remove:
            self.manager.remove_indices(indices_to_remove)
            self.refresh_basket_table()
            self.status_bar.showMessage(f"Deleted {len(indices_to_remove)} rows.", 3000)

    def action_clear_all(self):
        if not self.manager.items:
            return
        reply = QMessageBox.question(
            self, "Confirm Clear",
            "Are you sure you want to clear all charts from the order basket?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.manager.clear()
            self.refresh_basket_table()

    def action_export_txt(self):
        if not self.manager.items:
            QMessageBox.warning(self, "Empty Basket", "Order basket is empty. Nothing to export.")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Order Basket File", "enc_order_basket.txt", "Text Files (*.txt);;CWO Files (*.cwo);;All Files (*)"
        )
        if file_path:
            try:
                content = self.manager.export_basket_text()
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                QMessageBox.information(self, "Export Successful", f"Order basket saved to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to save file: {e}")

    def action_copy_all(self):
        if not self.manager.items:
            QMessageBox.warning(self, "Empty Basket", "Order basket is empty.")
            return
        content = self.manager.export_basket_text()
        QApplication.clipboard().setText(content)
        self.status_bar.showMessage("Order basket text copied to clipboard!", 3500)

    def action_edit_ship_info(self):
        dlg = ShipInfoDialog(self.manager.ship_info, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.manager.ship_info = dlg.get_data()
            self.status_bar.showMessage("Vessel details updated.", 3000)

    def show_context_menu(self, pos):
        menu = QMenu(self)
        act_del = menu.addAction("❌ Delete Selected Rows")
        act_copy = menu.addAction("📋 Copy Cell Code")
        act_copy_all_codes = menu.addAction("📋 Copy Selected Cells as List (, )")
        act_dedup_this = menu.addAction("🗑️ Remove Duplicates of this Cell")
        
        action = menu.exec(self.table.viewport().mapToGlobal(pos))
        if action == act_del:
            self.action_delete_selected()
        elif action == act_copy:
            selected_items = self.table.selectedItems()
            if selected_items:
                row = self.table.currentRow()
                cell_code = self.table.item(row, 2).text()
                QApplication.clipboard().setText(cell_code)
        elif action == act_copy_all_codes:
            self.action_copy_cell_codes_only()
        elif action == act_dedup_this:
            row = self.table.currentRow()
            if row >= 0:
                cell_code = self.table.item(row, 2).text()
                seen = False
                to_del = []
                for i, item in enumerate(self.manager.items):
                    if item.product_number == cell_code:
                        if not seen:
                            seen = True
                        else:
                            to_del.append(i)
                if to_del:
                    self.manager.remove_indices(to_del)
                    self.refresh_basket_table()
                    self.status_bar.showMessage(f"Removed {len(to_del)} duplicates of {cell_code}.", 3000)

    def refresh_basket_table(self):
        filter_text = self.filter_input.text().strip().lower()
        filter_cat = self.combo_basket_filter.currentIndex()

        total, unique, dups = self.manager.get_stats()
        
        if dups > 0:
            self.btn_dedup.setEnabled(True)
            self.btn_dedup.setText(f"🗑️ Remove Duplicates ({dups})")
            self.btn_dedup.setStyleSheet("background-color: #ea580c; font-weight: bold;")
        else:
            self.btn_dedup.setEnabled(False)
            self.btn_dedup.setText("🗑️ No Duplicates")
            self.btn_dedup.setStyleSheet("background-color: #374151; color: #6b7280;")

        dup_style = "color: #ef4444;" if dups > 0 else "color: #10b981;"
        self.lbl_stats.setText(
            f"Basket: <b style='color:#38bdf8;'>{total}</b> Cells | "
            f"Unique: <b style='color:#a855f7;'>{unique}</b> | "
            f"Duplicates: <b style='{dup_style}'>{dups}</b> | "
            f"Inventory: <b style='color:#34d399;'>{len(self.inventory.items)}</b>"
        )

        self.table.setRowCount(0)
        dup_bg = QColor(68, 20, 20)
        
        row_counter = 0
        for orig_idx, item in enumerate(self.manager.items):
            if filter_cat == 1 and not item.in_inventory:
                continue
            elif filter_cat == 2 and (not item.in_inventory or item.days_left is None or item.days_left > 30):
                continue
            elif filter_cat == 3 and (not item.in_inventory or item.days_left is None or item.days_left <= 30):
                continue
            elif filter_cat == 4 and item.in_inventory:
                continue
            elif filter_cat == 5 and not item.is_duplicate:
                continue
                
            if filter_text:
                if (filter_text not in item.product_number.lower() and
                    filter_text not in item.product_title.lower() and
                    filter_text not in item.scale.lower() and
                    filter_text not in item.inventory_info.lower()):
                    continue

            self.table.insertRow(row_counter)

            it_idx = QTableWidgetItem(str(orig_idx + 1))
            it_idx.setData(Qt.ItemDataRole.UserRole, orig_idx)
            it_idx.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            it_type = QTableWidgetItem(item.product_type)
            it_type.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            it_num = QTableWidgetItem(item.product_number)
            it_num.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
            it_num.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            it_title = QTableWidgetItem(item.product_title)
            
            it_scale = QTableWidgetItem(item.scale)
            it_scale.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            if item.is_duplicate:
                status_str = f"⚠️ DUPLICATE ({item.duplicate_count}x)"
                it_status = QTableWidgetItem(status_str)
                it_status.setForeground(QBrush(QColor("#f87171")))
                it_status.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            else:
                it_status = QTableWidgetItem("✓ Unique")
                it_status.setForeground(QBrush(QColor("#4ade80")))
            it_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            it_inv = QTableWidgetItem(item.inventory_info or "Not in Permit")
            if item.in_inventory:
                if item.days_left is not None and item.days_left <= 30:
                    it_inv.setForeground(QBrush(QColor("#fb923c")))
                else:
                    it_inv.setForeground(QBrush(QColor("#38bdf8")))
            else:
                it_inv.setForeground(QBrush(QColor("#9ca3af")))
            it_inv.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            row_items = [it_idx, it_type, it_num, it_title, it_scale, it_status, it_inv]
            for it in row_items:
                if item.is_duplicate:
                    it.setBackground(QBrush(dup_bg))
                self.table.setItem(row_counter, row_items.index(it), it)

            row_counter += 1

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ENC Cell Manager Pro")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
