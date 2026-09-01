import os
import sys
import datetime
from typing import Optional, List, Dict
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QTextDocument, QPageLayout, QPageSize
from PyQt6.QtPrintSupport import QPrinter
from PyQt6.QtCore import QMarginsF

def generate_basket_pdf(manager, output_path: str) -> bool:
    doc = QTextDocument()
    
    ship_info = manager.ship_info or {}
    vessel_name = ship_info.get("ShipName") or "PROSPERA"
    vessel_type = ship_info.get("ShipType") or "Commercial Vessel"
    ship_email = ship_info.get("ShipEmail") or "-"
    owner_name = ship_info.get("OwnerName") or "-"
    contact_phone = ship_info.get("ShipPhone") or "-"

    now_str = datetime.datetime.now().strftime("%d-%b-%Y %H:%M UTC")
    date_code = datetime.datetime.now().strftime("%Y%m%d-%H%M")
    report_ref = f"REQ-{date_code}"

    total, unique, dups = manager.get_stats()
    new_charts = sum(1 for it in manager.items if not it.in_inventory)
    renewals = total - new_charts
    expiring_soon = sum(1 for it in manager.items if it.in_inventory and it.days_left is not None and it.days_left <= 30)

    # Build Table Rows
    table_rows_html = []
    for idx, item in enumerate(manager.items, 1):
        if not item.in_inventory:
            status_badge = '<span style="background-color: #dbeafe; color: #1e40af; padding: 2px 6px; border-radius: 3px; font-weight: bold; font-size: 9px;">NEW ORDER</span>'
            order_type = '<span style="color: #2563eb; font-weight: 600;">New License</span>'
        elif item.days_left is not None and item.days_left <= 0:
            status_badge = f'<span style="background-color: #fee2e2; color: #991b1b; padding: 2px 6px; border-radius: 3px; font-weight: bold; font-size: 9px;">EXPIRED ({abs(item.days_left)}d ago)</span>'
            order_type = '<span style="color: #dc2626; font-weight: 600;">Renewal (Expired)</span>'
        elif item.days_left is not None and item.days_left <= 30:
            status_badge = f'<span style="background-color: #ffedd5; color: #9a3412; padding: 2px 6px; border-radius: 3px; font-weight: bold; font-size: 9px;">EXPIRING ({item.days_left}d left)</span>'
            order_type = '<span style="color: #ea580c; font-weight: 600;">Renewal (Critical)</span>'
        else:
            days = item.days_left if item.days_left is not None else ">30"
            status_badge = f'<span style="background-color: #f0fdf4; color: #166534; padding: 2px 6px; border-radius: 3px; font-weight: bold; font-size: 9px;">ACTIVE ({days}d left)</span>'
            order_type = '<span style="color: #16a34a; font-weight: 600;">Renewal (Active)</span>'

        row_bg = "#ffffff" if idx % 2 != 0 else "#f8fafc"
        if item.is_duplicate:
            row_bg = "#fef2f2"
            
        dup_tag = ' <span style="color: #dc2626; font-weight: bold; font-size: 9px;">[DUPLICATE]</span>' if item.is_duplicate else ''

        table_rows_html.append(f"""
        <tr style="background-color: {row_bg};">
            <td style="text-align: center; font-size: 9px; padding: 5px; border-bottom: 1px solid #e2e8f0;">{idx}</td>
            <td style="text-align: center; font-size: 9px; padding: 5px; border-bottom: 1px solid #e2e8f0; color: #64748b;">{item.product_type}</td>
            <td style="text-align: center; font-family: Consolas, monospace; font-weight: bold; font-size: 10px; padding: 5px; border-bottom: 1px solid #e2e8f0; color: #0f172a;">{item.product_number}{dup_tag}</td>
            <td style="font-size: 9.5px; padding: 5px 8px; border-bottom: 1px solid #e2e8f0; color: #1e293b;">{item.product_title}</td>
            <td style="text-align: center; font-size: 9px; padding: 5px; border-bottom: 1px solid #e2e8f0; color: #475569;">{item.scale}</td>
            <td style="text-align: center; padding: 5px; border-bottom: 1px solid #e2e8f0;">{status_badge}</td>
            <td style="text-align: center; font-size: 9px; padding: 5px; border-bottom: 1px solid #e2e8f0;">{order_type}</td>
        </tr>
        """)

    rows_str = "".join(table_rows_html)

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: 'Segoe UI', Arial, Helvetica, sans-serif;
            margin: 0;
            padding: 0;
            color: #0f172a;
        }}
        .header-table {{
            width: 100%;
            border-bottom: 3px solid #0284c7;
            padding-bottom: 10px;
            margin-bottom: 12px;
        }}
        .title {{
            color: #0369a1;
            font-size: 18px;
            font-weight: bold;
            letter-spacing: 0.5px;
            margin: 0;
        }}
        .subtitle {{
            color: #64748b;
            font-size: 10px;
            margin-top: 3px;
        }}
        .meta-card {{
            width: 100%;
            background-color: #f8fafc;
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            padding: 10px;
            margin-bottom: 12px;
        }}
        .meta-item {{
            font-size: 9.5px;
            color: #334155;
            padding: 2px 0;
        }}
        .meta-label {{
            font-weight: bold;
            color: #0f172a;
            width: 110px;
            display: inline-block;
        }}
        .kpi-table {{
            width: 100%;
            margin-bottom: 14px;
        }}
        .kpi-box {{
            background-color: #f1f5f9;
            border: 1px solid #cbd5e1;
            border-radius: 5px;
            padding: 8px;
            text-align: center;
        }}
        .kpi-val {{
            font-size: 16px;
            font-weight: bold;
            color: #0f172a;
        }}
        .kpi-lbl {{
            font-size: 8.5px;
            font-weight: 600;
            color: #64748b;
            text-transform: uppercase;
            margin-top: 2px;
        }}
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 6px;
            margin-bottom: 18px;
        }}
        .data-table th {{
            background-color: #0f172a;
            color: #ffffff;
            font-size: 9px;
            font-weight: bold;
            padding: 7px 5px;
            text-align: center;
            border: 1px solid #1e293b;
        }}
        .sig-table {{
            width: 100%;
            margin-top: 20px;
            border-top: 1px solid #cbd5e1;
            padding-top: 10px;
        }}
        .sig-box {{
            width: 31%;
            border: 1px solid #cbd5e1;
            border-radius: 4px;
            background-color: #f8fafc;
            padding: 8px;
            text-align: center;
        }}
        .sig-line {{
            margin-top: 35px;
            border-top: 1px dashed #94a3b8;
            padding-top: 4px;
            font-size: 9px;
            font-weight: bold;
            color: #334155;
        }}
        .sig-role {{
            font-size: 8px;
            color: #64748b;
        }}
        .footer {{
            margin-top: 12px;
            font-size: 8px;
            color: #94a3b8;
            text-align: center;
            border-top: 1px solid #e2e8f0;
            padding-top: 6px;
        }}
    </style>
    </head>
    <body>
        <!-- HEADER -->
        <table class="header-table">
            <tr>
                <td style="width: 70%;">
                    <div class="title">⚓ ENC CHART ORDER REQUISITION REPORT</div>
                    <div class="subtitle">ADMIRALTY Vector Chart Service (AVCS) Specification & Requisition Document</div>
                </td>
                <td style="width: 30%; text-align: right;">
                    <div style="font-size: 11px; font-weight: bold; color: #0284c7;">Ref: {report_ref}</div>
                    <div style="font-size: 9px; color: #64748b;">Date: {now_str}</div>
                </td>
            </tr>
        </table>

        <!-- VESSEL PARTICULARS & ORDER SUMMARY -->
        <table class="meta-card">
            <tr>
                <td style="width: 50%; vertical-align: top;">
                    <div class="meta-item"><span class="meta-label">Vessel Name:</span> <b>{vessel_name}</b></div>
                    <div class="meta-item"><span class="meta-label">Vessel Type:</span> {vessel_type}</div>
                    <div class="meta-item"><span class="meta-label">Owner / Manager:</span> {owner_name}</div>
                </td>
                <td style="width: 50%; vertical-align: top;">
                    <div class="meta-item"><span class="meta-label">Ship Email:</span> {ship_email}</div>
                    <div class="meta-item"><span class="meta-label">Contact Phone:</span> {contact_phone}</div>
                    <div class="meta-item"><span class="meta-label">Format:</span> Official ADMIRALTY Standard Tab-Delimited</div>
                </td>
            </tr>
        </table>

        <!-- KPI SUMMARY TILES -->
        <table class="kpi-table">
            <tr>
                <td style="width: 20%;">
                    <div class="kpi-box">
                        <div class="kpi-val" style="color: #0284c7;">{total}</div>
                        <div class="kpi-lbl">Total Charts</div>
                    </div>
                </td>
                <td style="width: 20%;">
                    <div class="kpi-box">
                        <div class="kpi-val" style="color: #7c3aed;">{unique}</div>
                        <div class="kpi-lbl">Unique Cells</div>
                    </div>
                </td>
                <td style="width: 20%;">
                    <div class="kpi-box">
                        <div class="kpi-val" style="color: #2563eb;">{new_charts}</div>
                        <div class="kpi-lbl">New Licenses</div>
                    </div>
                </td>
                <td style="width: 20%;">
                    <div class="kpi-box">
                        <div class="kpi-val" style="color: #ea580c;">{expiring_soon}</div>
                        <div class="kpi-lbl">Expiring &le; 30d</div>
                    </div>
                </td>
                <td style="width: 20%;">
                    <div class="kpi-box">
                        <div class="kpi-val" style="color: #10b981;">{renewals}</div>
                        <div class="kpi-lbl">In Permit</div>
                    </div>
                </td>
            </tr>
        </table>

        <!-- CHART TABLE -->
        <table class="data-table">
            <thead>
                <tr>
                    <th style="width: 5%;">#</th>
                    <th style="width: 12%;">Product Type</th>
                    <th style="width: 14%;">Cell ID</th>
                    <th style="width: 35%; text-align: left; padding-left: 8px;">Product Title</th>
                    <th style="width: 12%;">Scale</th>
                    <th style="width: 14%;">Current Permit</th>
                    <th style="width: 16%;">Action Type</th>
                </tr>
            </thead>
            <tbody>
                {rows_str}
            </tbody>
        </table>

        <!-- SIGNATURES -->
        <table class="sig-table">
            <tr>
                <td class="sig-box">
                    <div style="font-size: 9px; font-weight: bold; color: #0f172a;">PREPARED BY</div>
                    <div class="sig-line">Navigation Officer (2nd Officer)</div>
                    <div class="sig-role">Date: ________________________</div>
                </td>
                <td style="width: 3%;"></td>
                <td class="sig-box">
                    <div style="font-size: 9px; font-weight: bold; color: #0f172a;">VERIFIED & APPROVED BY</div>
                    <div class="sig-line">Master / Captain</div>
                    <div class="sig-role">Date: ________________________</div>
                </td>
                <td style="width: 3%;"></td>
                <td class="sig-box">
                    <div style="font-size: 9px; font-weight: bold; color: #0f172a;">CHART DISTRIBUTOR</div>
                    <div class="sig-line">UKHO / ADMIRALTY Chart Agent</div>
                    <div class="sig-role">Received Date: ________________</div>
                </td>
            </tr>
        </table>

        <!-- FOOTER -->
        <div class="footer">
            Generated by <b>ENC Cell Manager Pro</b> &bull; Compliant with IMO SOLAS V/19 & V/27 ECDIS Carriage Requirements &bull; Page 1 of 1
        </div>
    </body>
    </html>
    """
    
    doc.setHtml(html_content)

    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setOutputFileName(output_path)
    
    layout = QPageLayout()
    layout.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    layout.setOrientation(QPageLayout.Orientation.Portrait)
    layout.setMargins(QMarginsF(10, 10, 10, 10))
    printer.setPageLayout(layout)

    doc.print(printer)
    return True


def generate_inventory_pdf(inventory, output_path: str, ship_info: Optional[dict] = None) -> bool:
    doc = QTextDocument()
    
    ship_info = ship_info or {}
    vessel_name = ship_info.get("ShipName") or "PROSPERA"
    vessel_type = ship_info.get("ShipType") or "Commercial Vessel"

    now_str = datetime.datetime.now().strftime("%d-%b-%Y %H:%M UTC")
    date_code = datetime.datetime.now().strftime("%Y%m%d-%H%M")
    report_ref = f"AUDIT-{date_code}"

    stats = inventory.get_stats()
    permit_filename = os.path.basename(inventory.file_path) if inventory.file_path else "PERMIT.TXT"
    permit_date_str = inventory.permit_date or "N/A"

    # Build Table Rows
    table_rows_html = []
    for idx, item in enumerate(inventory.items, 1):
        if item.status_level == 0:
            badge = f'<span style="background-color: #fee2e2; color: #991b1b; padding: 2px 6px; border-radius: 3px; font-weight: bold; font-size: 8.5px;">EXPIRED ({abs(item.days_left)}d ago)</span>'
            row_bg = "#fef2f2"
        elif item.status_level == 1:
            badge = f'<span style="background-color: #ffedd5; color: #9a3412; padding: 2px 6px; border-radius: 3px; font-weight: bold; font-size: 8.5px;">CRITICAL ({item.days_left}d left)</span>'
            row_bg = "#fff7ed"
        elif item.status_level == 2:
            badge = f'<span style="background-color: #fef9c3; color: #854d0e; padding: 2px 6px; border-radius: 3px; font-weight: bold; font-size: 8.5px;">WARNING ({item.days_left}d left)</span>'
            row_bg = "#fefce8"
        else:
            badge = f'<span style="background-color: #f0fdf4; color: #166534; padding: 2px 6px; border-radius: 3px; font-weight: bold; font-size: 8.5px;">ACTIVE ({item.days_left}d left)</span>'
            row_bg = "#ffffff" if idx % 2 != 0 else "#f8fafc"

        days_display = f"{item.days_left} days" if item.days_left >= 0 else f"{abs(item.days_left)} days ago"

        table_rows_html.append(f"""
        <tr style="background-color: {row_bg};">
            <td style="text-align: center; font-size: 8.5px; padding: 4px; border-bottom: 1px solid #e2e8f0;">{idx}</td>
            <td style="text-align: center; font-family: Consolas, monospace; font-weight: bold; font-size: 9.5px; padding: 4px; border-bottom: 1px solid #e2e8f0; color: #0f172a;">{item.cell_id}</td>
            <td style="font-size: 9px; padding: 4px 6px; border-bottom: 1px solid #e2e8f0; color: #1e293b;">{item.title}</td>
            <td style="text-align: center; font-size: 8.5px; padding: 4px; border-bottom: 1px solid #e2e8f0; color: #475569;">{item.scale}</td>
            <td style="text-align: center; font-size: 9px; font-weight: 600; padding: 4px; border-bottom: 1px solid #e2e8f0; color: #0f172a;">{item.expiry_str}</td>
            <td style="text-align: center; font-size: 8.5px; padding: 4px; border-bottom: 1px solid #e2e8f0;">{days_display}</td>
            <td style="text-align: center; padding: 4px; border-bottom: 1px solid #e2e8f0;">{badge}</td>
        </tr>
        """)

    rows_str = "".join(table_rows_html)

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: 'Segoe UI', Arial, Helvetica, sans-serif;
            margin: 0;
            padding: 0;
            color: #0f172a;
        }}
        .header-table {{
            width: 100%;
            border-bottom: 3px solid #0d9488;
            padding-bottom: 10px;
            margin-bottom: 12px;
        }}
        .title {{
            color: #0f766e;
            font-size: 18px;
            font-weight: bold;
            letter-spacing: 0.5px;
            margin: 0;
        }}
        .subtitle {{
            color: #64748b;
            font-size: 10px;
            margin-top: 3px;
        }}
        .meta-card {{
            width: 100%;
            background-color: #f8fafc;
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            padding: 10px;
            margin-bottom: 12px;
        }}
        .meta-item {{
            font-size: 9.5px;
            color: #334155;
            padding: 2px 0;
        }}
        .meta-label {{
            font-weight: bold;
            color: #0f172a;
            width: 120px;
            display: inline-block;
        }}
        .kpi-table {{
            width: 100%;
            margin-bottom: 14px;
        }}
        .kpi-box {{
            border-radius: 5px;
            padding: 8px;
            text-align: center;
        }}
        .kpi-val {{
            font-size: 16px;
            font-weight: bold;
        }}
        .kpi-lbl {{
            font-size: 8px;
            font-weight: bold;
            text-transform: uppercase;
            margin-top: 2px;
        }}
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 6px;
            margin-bottom: 18px;
        }}
        .data-table th {{
            background-color: #0f172a;
            color: #ffffff;
            font-size: 9px;
            font-weight: bold;
            padding: 6px 4px;
            text-align: center;
            border: 1px solid #1e293b;
        }}
        .sig-table {{
            width: 100%;
            margin-top: 20px;
            border-top: 1px solid #cbd5e1;
            padding-top: 10px;
        }}
        .sig-box {{
            width: 48%;
            border: 1px solid #cbd5e1;
            border-radius: 4px;
            background-color: #f8fafc;
            padding: 8px;
            text-align: center;
        }}
        .sig-line {{
            margin-top: 35px;
            border-top: 1px dashed #94a3b8;
            padding-top: 4px;
            font-size: 9px;
            font-weight: bold;
            color: #334155;
        }}
        .footer {{
            margin-top: 12px;
            font-size: 8px;
            color: #94a3b8;
            text-align: center;
            border-top: 1px solid #e2e8f0;
            padding-top: 6px;
        }}
    </style>
    </head>
    <body>
        <!-- HEADER -->
        <table class="header-table">
            <tr>
                <td style="width: 70%;">
                    <div class="title">📋 VESSEL ENC PERMIT INVENTORY & EXPIRY STATUS REPORT</div>
                    <div class="subtitle">Official ECDIS Audit & Port State Control (PSC) Compliance Document</div>
                </td>
                <td style="width: 30%; text-align: right;">
                    <div style="font-size: 11px; font-weight: bold; color: #0f766e;">Ref: {report_ref}</div>
                    <div style="font-size: 9px; color: #64748b;">Audit Date: {now_str}</div>
                </td>
            </tr>
        </table>

        <!-- PERMIT PARTICULARS -->
        <table class="meta-card">
            <tr>
                <td style="width: 50%; vertical-align: top;">
                    <div class="meta-item"><span class="meta-label">Vessel Name:</span> <b>{vessel_name}</b></div>
                    <div class="meta-item"><span class="meta-label">Vessel Type:</span> {vessel_type}</div>
                    <div class="meta-item"><span class="meta-label">Permit Source:</span> <code>{permit_filename}</code></div>
                </td>
                <td style="width: 50%; vertical-align: top;">
                    <div class="meta-item"><span class="meta-label">Permit Issue Date:</span> {permit_date_str}</div>
                    <div class="meta-item"><span class="meta-label">Compliance Status:</span> <b>{stats['expired']} Expired &bull; {stats['critical']} Critical</b></div>
                    <div class="meta-item"><span class="meta-label">Format:</span> IHO S-63 / S-57 Encrypted Permit Structure</div>
                </td>
            </tr>
        </table>

        <!-- KPI SUMMARY TILES -->
        <table class="kpi-table">
            <tr>
                <td style="width: 20%;">
                    <div class="kpi-box" style="background-color: #f1f5f9; border: 1px solid #cbd5e1;">
                        <div class="kpi-val" style="color: #0f172a;">{stats['total']}</div>
                        <div class="kpi-lbl" style="color: #64748b;">Total Permits</div>
                    </div>
                </td>
                <td style="width: 20%;">
                    <div class="kpi-box" style="background-color: #f0fdf4; border: 1px solid #bbf7d0;">
                        <div class="kpi-val" style="color: #166534;">{stats['active']}</div>
                        <div class="kpi-lbl" style="color: #15803d;">Active (&gt;60d)</div>
                    </div>
                </td>
                <td style="width: 20%;">
                    <div class="kpi-box" style="background-color: #fefce8; border: 1px solid #fef08a;">
                        <div class="kpi-val" style="color: #854d0e;">{stats['warning']}</div>
                        <div class="kpi-lbl" style="color: #a16207;">Warning (31-60d)</div>
                    </div>
                </td>
                <td style="width: 20%;">
                    <div class="kpi-box" style="background-color: #fff7ed; border: 1px solid #fed7aa;">
                        <div class="kpi-val" style="color: #9a3412;">{stats['critical']}</div>
                        <div class="kpi-lbl" style="color: #c2410c;">Critical (1-30d)</div>
                    </div>
                </td>
                <td style="width: 20%;">
                    <div class="kpi-box" style="background-color: #fef2f2; border: 1px solid #fecaca;">
                        <div class="kpi-val" style="color: #991b1b;">{stats['expired']}</div>
                        <div class="kpi-lbl" style="color: #b91c1c;">Expired (&le;0d)</div>
                    </div>
                </td>
            </tr>
        </table>

        <!-- INVENTORY TABLE -->
        <table class="data-table">
            <thead>
                <tr>
                    <th style="width: 5%;">#</th>
                    <th style="width: 14%;">Cell ID</th>
                    <th style="width: 38%; text-align: left; padding-left: 6px;">Product Title</th>
                    <th style="width: 12%;">Scale</th>
                    <th style="width: 13%;">Expiry Date</th>
                    <th style="width: 10%;">Remaining</th>
                    <th style="width: 18%;">Status</th>
                </tr>
            </thead>
            <tbody>
                {rows_str}
            </tbody>
        </table>

        <!-- SIGNATURES -->
        <table class="sig-table">
            <tr>
                <td class="sig-box">
                    <div style="font-size: 9px; font-weight: bold; color: #0f172a;">AUDITED BY</div>
                    <div class="sig-line">Navigation Officer (2nd Officer)</div>
                    <div style="font-size: 8px; color: #64748b; margin-top: 2px;">Date: ________________________</div>
                </td>
                <td style="width: 4%;"></td>
                <td class="sig-box">
                    <div style="font-size: 9px; font-weight: bold; color: #0f172a;">VERIFIED BY</div>
                    <div class="sig-line">Master / Captain / PSC Inspector</div>
                    <div style="font-size: 8px; color: #64748b; margin-top: 2px;">Date: ________________________</div>
                </td>
            </tr>
        </table>

        <!-- FOOTER -->
        <div class="footer">
            Generated by <b>ENC Cell Manager Pro</b> &bull; Certified ECDIS Navigation Audit Document &bull; SOLAS Chapter V Regulation 27
        </div>
    </body>
    </html>
    """
    
    doc.setHtml(html_content)

    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setOutputFileName(output_path)
    
    layout = QPageLayout()
    layout.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    layout.setOrientation(QPageLayout.Orientation.Portrait)
    layout.setMargins(QMarginsF(10, 10, 10, 10))
    printer.setPageLayout(layout)

    doc.print(printer)
    return True
