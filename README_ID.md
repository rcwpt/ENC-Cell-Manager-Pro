# Panduan Penggunaan: ENC Cell Manager Pro & Expiry Monitor
*Aplikasi Pengelola Pemesanan Chart ENC & Pemantau Masa Aktif Permit Kapal*

Aplikasi mandiri Windows (.exe) yang dirancang khusus untuk perwira navigasi kapal (*nautical officers*), kapten, dan pengelola armada untuk mempermudah proses pemesanan lisensi Electronic Navigational Chart (ENC), membersihkan duplikat, membaca laporan status rute ECDIS (`.eusr.csv`), serta memantau tanggal kadaluwarsa permit kapal secara otomatis.

---

## 🌟 Fitur Utama

1. **Sistem Profil Kapal & Database Kumulatif (SQLite)**:
   - **Profil Multi-Kapal**: Membuat dan berpindah profil kapal dengan mudah (`MV PROSPERA`, `MV PACIFIC GLORY`, dll.).
   - **Penyimpanan Kumulatif & Riwayat Expiry**: Setiap kali memuat file permit baru (`PERMIT.TXT` / `ENC.PMT`), **data chart lama TIDAK dihapus**, melainkan tetap tersimpan di database lokal (`enc_user_data.db`) dengan status `🔴 Expired`. Sangat aman dan berguna untuk riwayat audit Port State Control (PSC).
   - **Otomasi Data Kapal**: Informasi profil (`#ShipName`, `#ShipType`, `#ShipEmail`, `#OwnerName`, kontak agen) otomatis mengisi header file pesanan dan laporan PDF.
2. **Input Cepat & Fleksibel**:
   - **Paste dari Clipboard (`Ctrl+V`)**: Langsung paste daftar kode cell ENC dari teks, email, atau excel.
   - **Buka File CSV / Status Rute ECDIS (`.eusr.csv`)**: Membaca langsung laporan ECDIS seperti `2026-09-01 11-57-56.eusr.csv`, otomatis mengekstrak nama kapal (`#ShipName`) dan kode chart.
   - **Cell Extractor**: Ekstraksi cell kode bersih berformat koma (`AU130120, AU130150, ...`) yang langsung disalin ke clipboard untuk komunikasi email cepat.
3. **Database Offline 35,277 Chart ADMIRALTY**:
   - Terintegrasi langsung dengan database katalog resmi SevenCs / UKHO ADMIRALTY.
   - Judul resmi perairan dan skala navigasi chart langsung terisi otomatis tanpa perlu koneksi internet.
4. **Pembersihan Duplikat (1-Click Deduplication)**:
   - Baris yang sama diberi tanda visual jelas (`⚠️ DUPLICATE (2x)`).
   - Tombol **"🗑️ Remove Duplicates"** menghapus seluruh entri ganda hanya dengan satu klik.
5. **Pemantau Masa Berlaku Permit (Expiry Monitor)**:
   - Membaca file permit kapal `PERMIT.TXT` maupun `ENC.PMT`.
   - Menghitung sisa hari secara otomatis (*days remaining*).
   - Indikator warna badge:
     - 🔴 **Expired (<= 0 hari)**
     - 🟠 **Kritis / Segera Habis (1 - 30 hari)**
     - 🟡 **Perhatian (31 - 60 hari)**
     - 🟢 **Aktif (> 60 hari)**
6. **Ekspor Laporan PDF Profesional Penuh Warna**:
   - **Order Requisition PDF**: Laporan pemesanan resmi standar IMO SOLAS V/19 & V/27 lengkap dengan distribusi skala chart dan kolom tanda tangan perwira navigasi.
   - **Permit Compliance Audit PDF**: Laporan kepatuhan permit siap audit PSC yang menyorot chart aktif, kritis, dan historis kadaluwarsa.
7. **Mode Tema Gelap & Terang (Dark / Light Theme)**:
   - Tombol toggle instan antara tema Midnight Nautical dan Crisp Daylight.

---

## 📖 Cara Menggunakan Aplikasi (Step-by-Step)

### Skenario 1: Memproses Pesanan Chart dari File Rute ECDIS
1. Ekspor file laporan rute dari ECDIS kapal Anda (misalnya `2026-09-01 11-57-56.eusr.csv`).
2. Buka aplikasi **ENC Cell Manager Pro**, buka **Tab 1: 📋 Order Basket & Deduplication**.
3. Klik tombol **"📂 Import CSV / EUSR / TXT..."** dan pilih file laporan ECDIS tersebut.
   - Nama kapal otomatis terdeteksi (contoh: `PROSPERA`).
   - Seluruh 40 chart terisi otomatis lengkap dengan judul perairan dan skala navigasinya.
4. **Menghapus chart yang masa aktifnya masih panjang (> 30 hari)**:
   - Klik tombol seleksi **`Active > 30 Days`** pada bar *Select Rows*.
   - Klik tombol **`❌ Delete Selected`**.
   - Sekarang keranjang pesanan Anda hanya berisi chart yang **segera habis (<= 30 hari)** dan chart **baru** yang memang perlu dipesan!
5. Klik **"🗑️ Remove Duplicates"** jika ada chart ganda.
6. Klik **"💾 Export Basket (.txt)"** untuk menyimpan file pesanan resmi.

---

### Skenario 2: Memantau Permit Kapal & Perpanjangan Lisensi (Renewal)
1. Buka **Tab 2: 📦 Permit Inventory & Expiry Monitor**.
2. Klik **"📂 Load Permit File"** (atau **"📁 Browse Permit Folder..."**) dan pilih file permit kapal Anda (`PERMIT.TXT` atau `ENC.PMT`).
3. Aplikasi akan menampilkan seluruh chart permit, tanggal kadaluwarsa, dan sisa hari.
4. Untuk memperpanjang chart yang masa berlakunya tinggal 30 hari atau kurang:
   - Klik tombol **`🟠 Active <= 30 Days (Expiring)`** pada bagian *Add to Basket*.
   - Seluruh chart yang kritis langsung disalin ke **Tab 1 (Order Basket)**.
5. Pindah ke Tab 1, periksa daftar chart, lalu klik **"💾 Export Basket (.txt)"**.

---

## 🛠️ Kompilasi Ulang File Executable (.exe)
Jika Anda melakukan perubahan pada kode sumber Python:
```bash
pip install pyqt6 pyinstaller
python -m PyInstaller --onefile --noconsole --name "ENC_Manager_Pro" --icon "app_icon.ico" --add-data "enc_database.db;." --add-data "app_icon.ico;." main_gui.py
```
File `.exe` baru akan berada di folder `dist/ENC_Manager_Pro.exe`.
