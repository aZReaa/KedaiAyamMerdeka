import mysql.connector
from mysql.connector import Error
from config import Config

class Database:
    def __init__(self):
        self.connection = None
        # Do not connect automatically on init to prevent Gunicorn worker crash
        # Connection will be established when needed
    
    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=Config.DB_HOST,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME
            )
            if self.connection.is_connected():
                print("Berhasil terkoneksi ke database MySQL")
        except Error as e:
            print(f"Error koneksi database: {e}")
            self.connection = None

    def get_cursor(self, dictionary=False):
        if self.connection is None or not self.connection.is_connected():
            print("Koneksi database terputus. Mencoba menghubungkan ulang...")
            self.connect()
        
        if self.connection and self.connection.is_connected():
            return self.connection.cursor(dictionary=dictionary)
        else:
            print("Gagal menghubungkan ke database.")
            return None
    
    def create_database_and_tables(self):
        cursor = self.connection.cursor()
        
        try:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.DB_NAME}")
            cursor.execute(f"USE {Config.DB_NAME}")
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS menu (
                    id_menu INT AUTO_INCREMENT PRIMARY KEY,
                    nama_menu VARCHAR(100) NOT NULL,
                    harga DECIMAL(10,2) NOT NULL,
                    kategori VARCHAR(50),
                    ketersediaan BOOLEAN DEFAULT TRUE
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pelanggan (
                    id_pelanggan VARCHAR(20) PRIMARY KEY,
                    nama VARCHAR(100),
                    riwayat_pesanan TEXT
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inventori (
                    id_item INT AUTO_INCREMENT PRIMARY KEY,
                    nama_item VARCHAR(100) NOT NULL,
                    stok INT DEFAULT 0,
                    satuan VARCHAR(20)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pesanan (
                    id_pesanan INT AUTO_INCREMENT PRIMARY KEY,
                    id_pelanggan VARCHAR(20),
                    detail_pesanan TEXT,
                    total_harga DECIMAL(10,2),
                    status ENUM('dipesan', 'diproses', 'selesai', 'batal') DEFAULT 'dipesan',
                    waktu_pesan DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (id_pelanggan) REFERENCES pelanggan(id_pelanggan)
                )
            """)
            
            self.connection.commit()
            print("Tabel database berhasil dibuat")
            
        except Error as e:
            print(f"Error membuat tabel: {e}")
        finally:
            cursor.close()
    
    def insert_menu(self, nama_menu, harga, kategori, ketersediaan=True):
        cursor = self.get_cursor()
        if not cursor: return None
        try:
            query = "INSERT INTO menu (nama_menu, harga, kategori, ketersediaan) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (nama_menu, harga, kategori, ketersediaan))
            self.connection.commit()
            return cursor.lastrowid
        except Error as e:
            print(f"Error insert menu: {e}")
            return None
        finally:
            cursor.close()
    
    def get_all_menu(self):
        cursor = self.get_cursor(dictionary=True)
        if not cursor: return []
        try:
            cursor.execute("SELECT * FROM menu WHERE ketersediaan = TRUE")
            return cursor.fetchall()
        except Error as e:
            print(f"Error get menu: {e}")
            return []
        finally:
            cursor.close()
    
    def get_menu_by_name(self, nama_menu):
        cursor = self.get_cursor(dictionary=True)
        if not cursor: return None
        try:
            query = "SELECT * FROM menu WHERE nama_menu LIKE %s AND ketersediaan = TRUE"
            cursor.execute(query, (f"%{nama_menu}%",))
            return cursor.fetchone()
        except Error as e:
            print(f"Error get menu by name: {e}")
            return None
        finally:
            cursor.close()
    
    def create_pesanan(self, id_pelanggan, detail_pesanan, total_harga):
        cursor = self.get_cursor()
        if not cursor: return None
        try:
            query = "INSERT INTO pesanan (id_pelanggan, detail_pesanan, total_harga) VALUES (%s, %s, %s)"
            cursor.execute(query, (id_pelanggan, detail_pesanan, total_harga))
            self.connection.commit()
            return cursor.lastrowid
        except Error as e:
            print(f"Error create pesanan: {e}")
            return None
        finally:
            cursor.close()
    
    def update_status_pesanan(self, id_pesanan, status):
        cursor = self.get_cursor()
        if not cursor: return False
        try:
            query = "UPDATE pesanan SET status = %s WHERE id_pesanan = %s"
            cursor.execute(query, (status, id_pesanan))
            self.connection.commit()
            return True
        except Error as e:
            print(f"Error update pesanan: {e}")
            return False
        finally:
            cursor.close()
    
    def get_pesanan_by_pelanggan(self, id_pelanggan, limit=5):
        cursor = self.get_cursor(dictionary=True)
        if not cursor: return []
        try:
            query = "SELECT * FROM pesanan WHERE id_pelanggan = %s ORDER BY waktu_pesan DESC LIMIT %s"
            cursor.execute(query, (id_pelanggan, limit))
            return cursor.fetchall()
        except Error as e:
            print(f"Error get pesanan: {e}")
            return []
        finally:
            cursor.close()
    
    def get_all_pesanan(self, status_filter=None, limit=100):
        """Get all orders with customer information"""
        cursor = self.get_cursor(dictionary=True)
        if not cursor: return []
        try:
            if status_filter:
                query = """
                    SELECT p.*, pel.nama as nama_pelanggan 
                    FROM pesanan p 
                    LEFT JOIN pelanggan pel ON p.id_pelanggan = pel.id_pelanggan 
                    WHERE p.status = %s 
                    ORDER BY p.waktu_pesan DESC 
                    LIMIT %s
                """
                cursor.execute(query, (status_filter, limit))
            else:
                query = """
                    SELECT p.*, pel.nama as nama_pelanggan 
                    FROM pesanan p 
                    LEFT JOIN pelanggan pel ON p.id_pelanggan = pel.id_pelanggan 
                    ORDER BY p.waktu_pesan DESC 
                    LIMIT %s
                """
                cursor.execute(query, (limit,))
            return cursor.fetchall()
        except Error as e:
            print(f"Error get all pesanan: {e}")
            return []
        finally:
            cursor.close()
    
    def get_all_pelanggan(self):
        """Get all customers"""
        cursor = self.get_cursor(dictionary=True)
        if not cursor: return []
        try:
            cursor.execute("SELECT * FROM pelanggan ORDER BY id_pelanggan")
            return cursor.fetchall()
        except Error as e:
            print(f"Error get all pelanggan: {e}")
            return []
        finally:
            cursor.close()

    
    def get_last_pesanan(self, id_pelanggan):
        cursor = self.get_cursor(dictionary=True)
        if not cursor: return None
        try:
            query = "SELECT * FROM pesanan WHERE id_pesanan = (SELECT MAX(id_pesanan) FROM pesanan WHERE id_pelanggan = %s)"
            cursor.execute(query, (id_pelanggan,))
            return cursor.fetchone()
        except Error as e:
            print(f"Error get last pesanan: {e}")
            return None
        finally:
            cursor.close()
    
    def insert_or_update_pelanggan(self, id_pelanggan, nama):
        cursor = self.get_cursor()
        if not cursor: return False
        try:
            query = """
                INSERT INTO pelanggan (id_pelanggan, nama) 
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE nama = %s
            """
            cursor.execute(query, (id_pelanggan, nama, nama))
            self.connection.commit()
            return True
        except Error as e:
            print(f"Error insert pelanggan: {e}")
            return False
        finally:
            cursor.close()
    
    def close(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()

db = Database()
