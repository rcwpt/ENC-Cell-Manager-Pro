import os
import sys
import re
import csv
import sqlite3
import datetime
from typing import List, Dict, Tuple, Optional

def get_db_path() -> str:
    if hasattr(sys, '_MEIPASS'):
        bundle_db = os.path.join(sys._MEIPASS, 'enc_database.db')
        if os.path.exists(bundle_db):
            return bundle_db
    
    exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    local_db = os.path.join(exe_dir, 'enc_database.db')
    if os.path.exists(local_db):
        return local_db
        
    cur_dir_db = os.path.join(os.getcwd(), 'enc_database.db')
    if os.path.exists(cur_dir_db):
        return cur_dir_db
        
    return local_db

def extract_cell_codes(text: str, unique_only: bool = True, sort_alphabetical: bool = True) -> List[str]:
    if not text:
        return []
    
    lines = text.strip().splitlines()
    collected = []
    try:
        reader = csv.reader(lines)
        header_found = False
        name_idx = -1
        for row in reader:
            if not row:
                continue
            row_lower = [c.strip().lower() for c in row]
            if not header_found:
                candidates = ['name', 'cell', 'cell id', 'cellid', 'chart', 'product number']
                for cand in candidates:
                    if cand in row_lower:
                        header_found = True
                        name_idx = row_lower.index(cand)
                        break
                continue
            if header_found and name_idx >= 0 and len(row) > name_idx:
                val = row[name_idx].strip().upper()
                if len(val) == 8 and val.isalnum():
                    collected.append(val)
    except Exception:
        pass

    if not collected:
        found = re.findall(r'\b[A-Za-z0-9]{8}\b', text)
        if not found:
            tokens = re.split(r'[,;\s\r\n\t]+', text)
            found = [t.strip().upper() for t in tokens if len(t.strip()) == 8 and t.strip().isalnum()]
        collected = [c.upper() for c in found]

    if unique_only:
        seen = set()
        deduped = []
        for c in collected:
            if c not in seen:
                seen.add(c)
                deduped.append(c)
        collected = deduped

    if sort_alphabetical:
        collected.sort()

    return collected

class ENCDatabase:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or get_db_path()
        self._conn = None
        if os.path.exists(self.db_path):
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row

    def lookup(self, cell_id: str) -> Dict[str, str]:
        cell_id = cell_id.strip().upper()
        if not self._conn:
            return {"cell_id": cell_id, "title": f"ENC Cell {cell_id}", "scale": "1 : 180000", "usage": "Unknown"}
        
        cur = self._conn.cursor()
        cur.execute("SELECT cell_id, title, scale, usage FROM enc_catalogue WHERE cell_id = ?", (cell_id,))
        row = cur.fetchone()
        if row:
            return dict(row)
        return {"cell_id": cell_id, "title": f"ENC Cell {cell_id}", "scale": "1 : 180000", "usage": "Standard"}

    def lookup_batch(self, cell_ids: List[str]) -> Dict[str, Dict[str, str]]:
        if not cell_ids:
            return {}
        norm_ids = [c.strip().upper() for c in cell_ids]
        res = {}
        if not self._conn:
            for cid in norm_ids:
                res[cid] = {"cell_id": cid, "title": f"ENC Cell {cid}", "scale": "1 : 180000", "usage": "Standard"}
            return res

        cur = self._conn.cursor()
        for i in range(0, len(norm_ids), 500):
            chunk = norm_ids[i:i+500]
            placeholders = ",".join(["?"] * len(chunk))
            cur.execute(f"SELECT cell_id, title, scale, usage FROM enc_catalogue WHERE cell_id IN ({placeholders})", chunk)
            for row in cur.fetchall():
                res[row["cell_id"]] = dict(row)
                
        for cid in norm_ids:
            if cid not in res:
                res[cid] = {"cell_id": cid, "title": f"ENC Cell {cid}", "scale": "1 : 180000", "usage": "Custom"}
        return res

class PermitItem:
    def __init__(self, cell_id: str, expiry_date: datetime.date, today: Optional[datetime.date] = None, title: str = "", scale: str = ""):
        self.cell_id = cell_id.strip().upper()
        self.expiry_date = expiry_date
        self.expiry_str = expiry_date.strftime("%Y-%m-%d")
        
        ref_today = today or datetime.date.today()
        self.days_left = (expiry_date - ref_today).days
        self.title = title
        self.scale = scale
        
        # 0 = Expired, 1 = Critical (<=30), 2 = Warning (31-60), 3 = Active (>60)
        if self.days_left < 0:
            self.status_level = 0
            self.status_label = f"🔴 Expired ({abs(self.days_left)}d ago)"
        elif self.days_left == 0:
            self.status_level = 0
            self.status_label = "🔴 Expires Today"
        elif self.days_left <= 30:
            self.status_level = 1
            self.status_label = f"🟠 {self.days_left}d left (Critical)"
        elif self.days_left <= 60:
            self.status_level = 2
            self.status_label = f"🟡 {self.days_left}d left (Warning)"
        else:
            self.status_level = 3
            self.status_label = f"🟢 {self.days_left}d left (Active)"

class InventoryManager:
    def __init__(self, db: Optional[ENCDatabase] = None):
        self.db = db or ENCDatabase()
        self.items: List[PermitItem] = []
        self.permit_date: str = ""
        self.file_path: str = ""
        self.permit_dict: Dict[str, PermitItem] = {}

    def load_permit_file(self, file_path: str, today: Optional[datetime.date] = None) -> int:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Permit file not found: {file_path}")
        
        self.file_path = file_path
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        return self.load_permit_text(content, today)

    def load_permit_text(self, text: str, today: Optional[datetime.date] = None) -> int:
        ref_today = today or datetime.date.today()
        lines = text.strip().splitlines()
        
        raw_entries = []
        permit_date_str = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith(":DATE"):
                parts = line.split()
                if len(parts) >= 2:
                    permit_date_str = " ".join(parts[1:])
                continue
            if line.startswith(":"):
                continue
                
            # Line format: 8-char cell ID + 8-char date (YYYYMMDD)
            if len(line) >= 16:
                cell_id = line[:8].upper()
                date_str = line[8:16]
                if cell_id.isalnum() and date_str.isdigit() and len(date_str) == 8:
                    try:
                        exp_d = datetime.datetime.strptime(date_str, "%Y%m%d").date()
                        raw_entries.append((cell_id, exp_d))
                    except Exception:
                        pass

        if not raw_entries:
            return 0

        cell_ids = [c for c, d in raw_entries]
        meta = self.db.lookup_batch(cell_ids)
        
        self.items.clear()
        self.permit_dict.clear()
        self.permit_date = permit_date_str
        
        for cid, exp_d in raw_entries:
            m = meta.get(cid, {})
            title = m.get("title", f"ENC Cell {cid}")
            scale = m.get("scale", "1 : 180000")
            item = PermitItem(cid, exp_d, ref_today, title, scale)
            self.items.append(item)
            self.permit_dict[cid] = item

        self.items.sort(key=lambda x: (x.days_left, x.cell_id))
        return len(self.items)

    def get_stats(self) -> Dict[str, int]:
        total = len(self.items)
        expired = sum(1 for it in self.items if it.status_level == 0)
        critical = sum(1 for it in self.items if it.status_level == 1)
        warning = sum(1 for it in self.items if it.status_level == 2)
        active = sum(1 for it in self.items if it.status_level == 3)
        return {
            "total": total,
            "expired": expired,
            "critical": critical,
            "warning": warning,
            "active": active
        }

    def get_cells_in_inventory(self) -> List[str]:
        return [it.cell_id for it in self.items]

    def get_cells_active_less_than(self, days: int = 30) -> List[str]:
        return [it.cell_id for it in self.items if it.days_left <= days]

    def get_cells_active_more_than(self, days: int = 30) -> List[str]:
        return [it.cell_id for it in self.items if it.days_left > days]

    def get_expiring_cells(self, max_days: int = 30) -> List[str]:
        return self.get_cells_active_less_than(max_days)

    def export_csv(self) -> str:
        rows = ["Cell ID,Product Title,Scale,Expiry Date,Days Left,Status"]
        for it in self.items:
            clean_title = it.title.replace('"', '""')
            rows.append(f'"{it.cell_id}","{clean_title}","{it.scale}","{it.expiry_str}",{it.days_left},"{it.status_label}"')
        return "\n".join(rows) + "\n"

class CellItem:
    def __init__(self, product_type: str, product_number: str, product_title: str, scale: str, status: str = ""):
        self.product_type = product_type or "ENC Units"
        self.product_number = product_number.strip().upper()
        self.product_title = product_title.strip()
        self.scale = scale.strip()
        self.status = status.strip()
        self.is_duplicate = False
        self.duplicate_count = 1
        self.inventory_info = ""
        self.in_inventory = False
        self.days_left = None

    def to_row_tuple(self) -> Tuple[str, str, str, str, str]:
        return (self.product_type, self.product_number, self.product_title, self.scale, self.status)

class ENCManager:
    def __init__(self, db: Optional[ENCDatabase] = None, inventory: Optional[InventoryManager] = None):
        self.db = db or ENCDatabase()
        self.inventory = inventory or InventoryManager(self.db)
        self.items: List[CellItem] = []
        self.ship_info: Dict[str, str] = {
            "ShipName": "",
            "ShipType": "",
            "ShipEmail": "",
            "ShipPhone": "",
            "OwnerName": "",
            "ContactEmail": "",
            "ContactPhone": ""
        }

    def update_duplicates_and_inventory(self):
        counts = {}
        for item in self.items:
            cid = item.product_number
            counts[cid] = counts.get(cid, 0) + 1
            
        for item in self.items:
            cid = item.product_number
            c = counts[cid]
            item.is_duplicate = (c > 1)
            item.duplicate_count = c
            
            p_item = self.inventory.permit_dict.get(cid)
            if p_item:
                item.in_inventory = True
                item.days_left = p_item.days_left
                item.inventory_info = f"Permit: Exp {p_item.expiry_str} ({p_item.days_left}d left)"
            else:
                item.in_inventory = False
                item.days_left = None
                item.inventory_info = "Not in Permit (New)"

    def add_from_text(self, text: str) -> int:
        if not text:
            return 0

        # Check for Vessel Name in header (e.g. from ECDIS reports)
        m_vessel = re.search(r'Vessel Name:\s*([^,\r\n]+)', text, re.IGNORECASE)
        if m_vessel:
            v_val = m_vessel.group(1).strip()
            if v_val and not self.ship_info.get("ShipName"):
                self.ship_info["ShipName"] = v_val

        lines = text.strip().splitlines()
        is_basket = any(line.startswith("Product Type\t") or line.startswith("ENC Units\t") for line in lines)
        
        added_count = 0
        
        if is_basket:
            for line in lines:
                parts = line.split("\t")
                if len(parts) >= 4 and parts[0] == "ENC Units":
                    ptype = parts[0]
                    pnum = parts[1].strip().upper()
                    ptitle = parts[2].strip()
                    pscale = parts[3].strip()
                    pstat = parts[4].strip() if len(parts) > 4 else ""
                    self.items.append(CellItem(ptype, pnum, ptitle, pscale, pstat))
                    added_count += 1
                elif line.startswith("#"):
                    m = re.match(r"^#([A-Za-z]+)\|(.*)$", line.strip())
                    if m:
                        key, val = m.group(1), m.group(2)
                        if key in self.ship_info:
                            self.ship_info[key] = val
        else:
            found_cells = extract_cell_codes(text, unique_only=False, sort_alphabetical=False)
            if found_cells:
                meta = self.db.lookup_batch(found_cells)
                for cid in found_cells:
                    cid_up = cid.upper()
                    m = meta.get(cid_up, {})
                    title = m.get("title", f"ENC Cell {cid_up}")
                    scale = m.get("scale", "1 : 180000")
                    self.items.append(CellItem("ENC Units", cid_up, title, scale))
                    added_count += 1

        self.update_duplicates_and_inventory()
        return added_count

    def import_file(self, file_path: str) -> int:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        return self.add_from_text(content)

    def remove_duplicates(self) -> int:
        seen = set()
        new_items = []
        removed = 0
        for item in self.items:
            cid = item.product_number
            if cid not in seen:
                seen.add(cid)
                new_items.append(item)
            else:
                removed += 1
        self.items = new_items
        self.update_duplicates_and_inventory()
        return removed

    def remove_indices(self, indices: List[int]):
        for idx in sorted(indices, reverse=True):
            if 0 <= idx < len(self.items):
                del self.items[idx]
        self.update_duplicates_and_inventory()

    def clear(self):
        self.items.clear()

    def export_basket_text(self) -> str:
        out = ["Product Type\tProduct Number\tProduct Title\tScale\tStatus"]
        for item in self.items:
            out.append(f"{item.product_type}\t{item.product_number}\t{item.product_title}\t{item.scale}\t{item.status}")
        
        for k in ["ShipName", "ShipType", "ShipEmail", "ShipPhone", "OwnerName", "ContactEmail", "ContactPhone"]:
            val = self.ship_info.get(k, "")
            out.append(f"#{k}|{val}")
        return "\n".join(out) + "\n"

    def get_cell_codes_string(self, unique_only: bool = True, sort_alphabetical: bool = True, selected_indices: Optional[List[int]] = None) -> str:
        if selected_indices is not None:
            cells = [self.items[i].product_number for i in selected_indices if 0 <= i < len(self.items)]
        else:
            cells = [it.product_number for it in self.items]
            
        if unique_only:
            seen = set()
            deduped = []
            for c in cells:
                if c not in seen:
                    seen.add(c)
                    deduped.append(c)
            cells = deduped
            
        if sort_alphabetical:
            cells.sort()
            
        return ", ".join(cells)

    def get_stats(self) -> Tuple[int, int, int]:
        total = len(self.items)
        unique = len(set(item.product_number for item in self.items))
        dups = total - unique
        return (total, unique, dups)

    def get_breakdown(self) -> Dict[str, int]:
        total = len(self.items)
        unique = len(set(item.product_number for item in self.items))
        dups = total - unique
        in_inv = sum(1 for it in self.items if it.in_inventory)
        crit = sum(1 for it in self.items if it.in_inventory and it.days_left is not None and it.days_left <= 30)
        act = sum(1 for it in self.items if it.in_inventory and it.days_left is not None and it.days_left > 30)
        new_cells = sum(1 for it in self.items if not it.in_inventory)
        return {
            "total": total,
            "unique": unique,
            "dups": dups,
            "in_inventory": in_inv,
            "critical": crit,
            "active": act,
            "new": new_cells
        }
