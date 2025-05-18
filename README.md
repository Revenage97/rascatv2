# Dashboard Manajemen Stok

Proyek ini adalah aplikasi web berbasis Django untuk manajemen stok dengan fitur upload/backup file Excel, integrasi webhook Telegram, dan log aktivitas.

## Fitur Utama

- Login dan autentikasi pengguna
- Dashboard untuk melihat dan mengelola stok barang
- Upload file Excel untuk memperbarui data stok
- Backup data stok ke file Excel
- Pengaturan webhook Telegram untuk notifikasi
- Kirim data barang ke Telegram
- Log aktivitas untuk melacak perubahan
- Ubah password admin

## Persyaratan Sistem

- Python 3.8 atau lebih tinggi
- Django 4.2 atau lebih tinggi
- PostgreSQL (untuk produksi) atau SQLite (untuk pengembangan lokal)
- Paket Python lainnya (lihat requirements.txt)

## Instalasi dan Penggunaan

1. Ekstrak file ZIP ke direktori pilihan Anda
2. Buka terminal dan navigasi ke direktori proyek
3. Buat virtual environment (opsional tapi direkomendasikan):
   ```
   python -m venv venv
   source venv/bin/activate  # Untuk Linux/Mac
   venv\Scripts\activate     # Untuk Windows
   ```
4. Install dependensi:
   ```
   pip install -r requirements.txt
   ```
5. Jalankan migrasi database:
   ```
   python manage.py migrate
   ```
6. Buat akun admin default:
   ```
   python manage.py create_admin
   ```
7. Inisialisasi pengaturan webhook:
   ```
   python manage.py init_webhook
   ```
8. (Opsional) Import data sampel:
   ```
   python manage.py import_sample_data
   ```
9. Jalankan server pengembangan:
   ```
   python manage.py runserver
   ```
10. Buka browser dan akses `http://localhost:8000`
11. Login dengan kredensial default:
    - Username: `admin`
    - Password: `rascat`

## Konfigurasi Database PostgreSQL

Untuk menggunakan PostgreSQL, edit file `stock_management/settings.py` dan uncomment bagian konfigurasi PostgreSQL, lalu sesuaikan dengan pengaturan database Anda.

## Struktur Proyek

- `stock_management/` - Konfigurasi utama Django
- `inventory/` - Aplikasi utama untuk manajemen stok
- `templates/` - Template HTML
- `static/` - File statis (CSS, JavaScript)
- `sample_data/` - Data sampel untuk pengujian

## Format File Excel

File Excel yang diupload harus memiliki kolom-kolom berikut:
- Kode
- Nama Barang
- Kategori
- Total Stok
- Harga Jual

Nilai Stok Minimum akan tetap tersimpan jika sebelumnya sudah diisi.

## Webhook Telegram

Untuk menggunakan fitur Telegram, Anda perlu mengatur webhook URL di halaman Pengaturan Webhook. Data akan dikirim dalam format JSON dengan struktur:

```json
{
  "produk": [
    {
      "kode_barang": "0000000000001",
      "nama_barang": "Obat Kutu Detick Kucing Anjing 3ml",
      "kategori": "detick",
      "stok": 45,
      "harga": "Rp 36.900",
      "stok_minimum": 5
    },
    ...
  ]
}
```

## Koneksi ke GitHub dan Render

Proyek ini siap untuk dihubungkan ke GitHub dan di-deploy ke Render secara manual. Pastikan untuk mengatur variabel lingkungan yang sesuai saat melakukan deployment.
