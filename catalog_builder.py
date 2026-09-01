import os
import zipfile
import re
import sqlite3
import time

def build_catalogue_db(db_path="enc_database.db", cat_dir=r"C:\Program Files (x86)\ADMIRALTY_Digital_Catalogue\catalogue"):
    t0 = time.time()
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS enc_catalogue")
    cur.execute("""
        CREATE TABLE enc_catalogue (
            cell_id TEXT PRIMARY KEY,
            title TEXT,
            scale TEXT,
            scale_num INTEGER,
            usage TEXT
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_cell ON enc_catalogue(cell_id)")
    
    cells = {}
    
    # 1. Parse AVCS.cat
    avcs_cat = os.path.join(cat_dir, "AVCS.cat")
    if os.path.exists(avcs_cat):
        try:
            with zipfile.ZipFile(avcs_cat) as z:
                pattern = re.compile(rb'([A-Z0-9]{8})(\d{4,8})(.*?)(?=AVCS)', re.DOTALL)
                for name in z.namelist():
                    if name.endswith('.7CB'):
                        data = z.read(name)
                        for m in pattern.finditer(data):
                            cell = m.group(1).decode('latin1', errors='ignore')
                            scale_int = int(m.group(2).decode('latin1', errors='ignore'))
                            scale_str = f"1 : {scale_int}"
                            mid = m.group(3)
                            strings = re.findall(rb'[\x20-\x7e]{3,}', mid)
                            title = strings[0].decode('latin1', errors='ignore').strip() if strings else "Unknown Title"
                            
                            # Determine usage band from 3rd char if standard ENC
                            band = cell[2] if len(cell) >= 3 else ''
                            band_map = {'1': 'Overview', '2': 'General', '3': 'Coastal', '4': 'Approach', '5': 'Harbour', '6': 'Berthing'}
                            usage = band_map.get(band, 'Standard')
                            
                            cells[cell] = (cell, title, scale_str, scale_int, usage)
        except Exception as e:
            print(f"Error parsing AVCS.cat: {e}")
            
    # 2. Parse ENC Units.cat for any additional cells not in AVCS
    enc_cat = os.path.join(cat_dir, "ENC Units.cat")
    if os.path.exists(enc_cat):
        try:
            with zipfile.ZipFile(enc_cat) as z:
                pattern = re.compile(rb'([A-Z0-9]{8})(\d{4,8})(.*?)(?=ENC Units)', re.DOTALL)
                for name in z.namelist():
                    if name.endswith('.7CB'):
                        data = z.read(name)
                        for m in pattern.finditer(data):
                            cell = m.group(1).decode('latin1', errors='ignore')
                            if cell not in cells:
                                scale_int = int(m.group(2).decode('latin1', errors='ignore'))
                                scale_str = f"1 : {scale_int}"
                                mid = m.group(3)
                                strings = re.findall(rb'[\x20-\x7e]{3,}', mid)
                                title = strings[0].decode('latin1', errors='ignore').strip() if strings else "Unknown Title"
                                band = cell[2] if len(cell) >= 3 else ''
                                band_map = {'1': 'Overview', '2': 'General', '3': 'Coastal', '4': 'Approach', '5': 'Harbour', '6': 'Berthing'}
                                usage = band_map.get(band, 'Standard')
                                cells[cell] = (cell, title, scale_str, scale_int, usage)
        except Exception as e:
            print(f"Error parsing ENC Units.cat: {e}")

    # Insert into database
    cur.executemany("INSERT OR REPLACE INTO enc_catalogue VALUES (?, ?, ?, ?, ?)", list(cells.values()))
    conn.commit()
    conn.close()
    
    elapsed = time.time() - t0
    print(f"Successfully built SQLite catalogue: {len(cells)} cells in {elapsed:.2f}s -> {db_path}")

if __name__ == '__main__':
    build_catalogue_db()
