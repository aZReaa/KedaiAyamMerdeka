import os
from dotenv import load_dotenv

load_dotenv()

app_env = os.getenv('APP_ENV', '').strip().lower()
if app_env == 'local':
    load_dotenv('.env.local', override=True)

class Config:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    APP_ENV = app_env or 'default'
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    ANALYTICS_ENABLED = os.getenv('ANALYTICS_ENABLED', 'false').strip().lower() == 'true'
    APP_VERSION = (
        os.getenv('RAILWAY_GIT_COMMIT_SHA')
        or os.getenv('RAILWAY_DEPLOYMENT_ID')
        or os.getenv('APP_VERSION')
        or 'dev'
    )
    
    # Database Configuration
    DB_HOST = os.getenv('DB_HOST') or os.getenv('MYSQLHOST') or 'localhost'
    DB_PORT = int(os.getenv('DB_PORT') or os.getenv('MYSQLPORT') or 3306)
    DB_USER = os.getenv('DB_USER') or os.getenv('MYSQLUSER') or 'root'
    DB_PASSWORD = os.getenv('DB_PASSWORD') or os.getenv('MYSQLPASSWORD') or ''
    DB_NAME = os.getenv('DB_NAME') or os.getenv('MYSQLDATABASE') or 'kedai_ayam_merdeka'
    
    # Telegram Configuration
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_API_BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
    TELEGRAM_API_URL = f"{TELEGRAM_API_BASE_URL}/sendMessage"
    TELEGRAM_PHOTO_API_URL = f"{TELEGRAM_API_BASE_URL}/sendPhoto"
    TELEGRAM_SEND_QRIS_ON_PAYMENT = os.getenv('TELEGRAM_SEND_QRIS_ON_PAYMENT', 'true').strip().lower() == 'true'
    TELEGRAM_QRIS_IMAGE_URL = os.getenv('TELEGRAM_QRIS_IMAGE_URL', '').strip()
    TELEGRAM_QRIS_IMAGE_PATH = os.getenv('TELEGRAM_QRIS_IMAGE_PATH', 'static/qris-payment.jpg').strip()
    TELEGRAM_QRIS_CAPTION = os.getenv(
        'TELEGRAM_QRIS_CAPTION',
        'QRIS aktif ada di gambar berikut ya kak. Setelah transfer, kirim bukti bayar di chat ini.'
    ).strip()
    TELEGRAM_SEND_MENU_IMAGE = os.getenv('TELEGRAM_SEND_MENU_IMAGE', 'true').strip().lower() == 'true'
    TELEGRAM_MENU_IMAGE_URL = os.getenv('TELEGRAM_MENU_IMAGE_URL', '').strip()
    TELEGRAM_MENU_IMAGE_PATH = os.getenv('TELEGRAM_MENU_IMAGE_PATH', 'static/menu-catalog.jpg').strip()
    TELEGRAM_MENU_CAPTION = os.getenv(
        'TELEGRAM_MENU_CAPTION',
        'Katalog menu terbaru ada di gambar berikut ya kak.'
    ).strip()
    
    # Jam Operasional
    JAM_BUKA = "10:00"
    JAM_TUTUP = "22:00"
    APP_TIMEZONE = os.getenv('APP_TIMEZONE', 'Asia/Makassar')
    STORE_LOCATION = os.getenv(
        'STORE_LOCATION',
        'BTN Merdeka Blok C.16, Salekoe, Kec. Wara, Kota Palopo'
    )
    STORE_LOCATION_NOTE = os.getenv(
        'STORE_LOCATION_NOTE',
        'Kalau mau diantar, kirim lokasi ta dulu ya kak supaya dicek ongkirnya.'
    )
    PAYMENT_TRANSFER_BANK = os.getenv('PAYMENT_TRANSFER_BANK', 'Bank BTN').strip()
    PAYMENT_TRANSFER_ACCOUNT_NUMBER = os.getenv('PAYMENT_TRANSFER_ACCOUNT_NUMBER', '7401500229979').strip()
    PAYMENT_TRANSFER_ACCOUNT_NAME = os.getenv('PAYMENT_TRANSFER_ACCOUNT_NAME', 'Asri Ashari Syam').strip()
    
    # Pesan Promo
    PROMO_MASAKAN = "Promo: Beli 2 Ayam Geprek Gratis 1 Es Teh Manis!"
