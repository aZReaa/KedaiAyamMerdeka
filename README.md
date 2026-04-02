# Chatbot Kedai Ayam Merdeka

Chatbot berbasis WhatsApp untuk sistem pemesanan makanan pada Kedai Ayam Merdeka.

## Fitur MVP

- Pemesanan makanan melalui chat
- Pengecekan ketersediaan menu
- Manajemen pesanan (ubah, batalkan, cek status)
- Informasi promo dan jam operasional
- Admin panel untuk kelola menu dan pesanan

## Tech Stack

- **Python 3.10+**
- **Flask** - Web framework untuk webhook
- **MySQL** - Database
- **spaCy** - NLU (Natural Language Understanding)
- **Telegram Bot API** - Platform chat

## Struktur Project

```
ProjectAkhirMusrafil/
├── app.py                      # Flask main application
├── config.py                   # Konfigurasi
├── database.py                 # Database models dan operasi
├── nlu.py                      # NLU dengan spaCy
├── dialog_manager.py           # Logika percakapan
├── dialog_manager.py           # Logika percakapan
├── requirements.txt            # Dependencies
├── .env.example               # Template environment variables (TELEGRAM_BOT_TOKEN)
├── templates/
│   └── admin.html             # Admin panel
├── static/
│   ├── style.css              # Styles
│   └── app.js                 # JavaScript admin panel
└── nlp_data/
    └── intents.json           # Data training intents
```

## Installation

1. Clone repository:
```bash
git clone <repository-url>
cd ProjectAkhirMusrafil
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Download spaCy model:
```bash
python -m spacy download xx_ent_wiki_sm
```

4. Setup environment:
```bash
cp .env.example .env
```
Edit file `.env` sesuai konfigurasi database Anda.

Untuk mode lokal yang terpisah dari Railway:
```powershell
Copy-Item .env.local.example .env.local
```
Lalu isi `.env.local` dengan database MySQL lokal Anda.

5. Setup MySQL database:
- Buat database `kedai_ayam_merdeka` di MySQL
- Atau gunakan endpoint `/api/init_db` untuk auto-create

## Running

1. Start Flask server:
```bash
python app.py
```

Untuk menjalankan versi lokal yang pasti memakai database lokal:
```powershell
.\run_local.ps1
```

Untuk membuat atau reset akun admin lokal:
```powershell
.\create_admin_local.ps1 -Username admin -Password admin123 -Name "Administrator"
```

2. Buka admin panel di browser:
```
http://localhost:5000/admin
```

3. Initialize database dengan sample data:
- Klik tombol "Initialize Database" di admin panel

## API Endpoints

### Chat
- `POST /chat` - Test chatbot endpoint
- `POST /webhook` - WhatsApp webhook endpoint

### Admin
- `GET /admin` - Admin panel UI
- `GET /api/menu` - Get all menus
- `POST /api/menu` - Create new menu
- `DELETE /api/menu/<id>` - Delete menu
- `GET /api/pesanan?id_pelanggan=<id>` - Get customer orders
- `POST /api/init_db` - Initialize database

## Intent yang Didukung

- `salam` - Sapaan pengguna
- `terima_kasih` - Ucapan terima kasih
- `pesan_menu` - Pemesanan menu
- `cek_ketersediaan` - Cek ketersediaan menu
- `ubah_pesanan` - Ubah pesanan
- `batalkan_pesanan` - Batalkan pesanan
- `cek_status` - Cek status pesanan
- `info_promo` - Informasi promo
- `info_jam` - Informasi jam operasional

## Entity yang Didukung

- `NAMA_MENU` - Nama menu yang dipesan
- `JUMLAH` - Jumlah porsi
- `JENIS_SAMBAL` - Jenis sambal (opsional)

## Database Schema

### Menu
- id_menu (PK)
- nama_menu
- harga
- kategori
- ketersediaan

### Pesanan
- id_pesanan (PK)
- id_pelanggan
- detail_pesanan
- total_harga
- status (dipesan/diproses/selesai/batal)
- waktu_pesan

### Pelanggan
- id_pelanggan (PK/No. WA)
- nama
- riwayat_pesanan

### Inventori
- id_item (PK)
- nama_item
- stok
- satuan

## Telegram Bot Setup
1. Chat dengan @BotFather di Telegram
2. Ketik `/newbot` untuk membuat bot baru
3. Salin **HTTP API Token**
4. Paste token ke `.env` sebagai `TELEGRAM_BOT_TOKEN`
5. Setup Webhook (Jalankan sekali):
   ```bash
   curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=<NGROK_URL>/webhook"
   ```

## License

MIT License
