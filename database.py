import mysql.connector
from mysql.connector import Error
import threading
import re
import hashlib
from config import Config

class Database:
    def __init__(self):
        self._local = threading.local()
        self._schema_checked = False
        self._db_config = {
            'host': Config.DB_HOST,
            'port': Config.DB_PORT,
            'user': Config.DB_USER,
            'password': Config.DB_PASSWORD,
            'database': Config.DB_NAME,
            'use_pure': True
        }
        # Connection is established lazily per thread/request.

    @property
    def connection(self):
        return getattr(self._local, 'connection', None)

    @connection.setter
    def connection(self, value):
        self._local.connection = value
    
    def connect(self):
        existing_connection = self.connection
        if existing_connection is not None:
            try:
                if existing_connection.is_connected():
                    return existing_connection
            except Error:
                pass
            self.close()

        try:
            self.connection = mysql.connector.connect(**self._db_config)
            if self.connection.is_connected():
                self.ensure_payment_schema()
                print("Berhasil terkoneksi ke database MySQL")
            return self.connection
        except Error as e:
            print(f"Error koneksi database: {e}")
            self.connection = None
            return None

    def get_connection(self):
        connection = self.connection
        if connection is None:
            print("Koneksi database terputus. Mencoba menghubungkan ulang...")
            return self.connect()

        try:
            if not connection.is_connected():
                print("Koneksi database terputus. Mencoba menghubungkan ulang...")
                return self.connect()
        except Error:
            print("Status koneksi database gagal diperiksa. Mencoba menghubungkan ulang...")
            return self.connect()

        return connection

    def get_cursor(self, dictionary=False):
        connection = self.get_connection()
        if connection:
            return connection.cursor(dictionary=dictionary, buffered=True)
        else:
            print("Gagal menghubungkan ke database.")
            return None

    def commit(self):
        connection = self.get_connection()
        if not connection:
            return False

        try:
            connection.commit()
            return True
        except Error as e:
            print(f"Error commit database: {e}")
            return False
    
    def create_database_and_tables(self):
        connection = self.get_connection()
        if not connection:
            return

        cursor = connection.cursor()
        
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
                    status ENUM(
                        'menunggu_konfirmasi_admin',
                        'menunggu_pembayaran',
                        'diproses',
                        'selesai',
                        'batal',
                        'ditolak_admin'
                    ) DEFAULT 'menunggu_konfirmasi_admin',
                    payment_status ENUM('pending', 'proof_submitted', 'verified', 'rejected') DEFAULT 'pending',
                    payment_proof_file_id VARCHAR(255),
                    payment_proof_kind VARCHAR(20),
                    payment_note TEXT,
                    payment_submitted_at DATETIME NULL,
                    payment_verified_at DATETIME NULL,
                    waktu_pesan DATETIME DEFAULT CURRENT_TIMESTAMP,
                    waktu_pengambilan VARCHAR(50),
                    tipe_pengambilan ENUM('immediate', 'specific', 'relative', 'later') DEFAULT 'immediate',
                    FOREIGN KEY (id_pelanggan) REFERENCES pelanggan(id_pelanggan)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversation_states (
                    id_pelanggan VARCHAR(20) PRIMARY KEY,
                    state VARCHAR(50) DEFAULT 'idle',
                    data TEXT,
                    cart TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (id_pelanggan) REFERENCES pelanggan(id_pelanggan)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_logs (
                    id_log INT AUTO_INCREMENT PRIMARY KEY,
                    id_pelanggan VARCHAR(20),
                    nama_pelanggan VARCHAR(100),
                    pesan_masuk TEXT,
                    intent_terdeteksi VARCHAR(50),
                    confidence_score DECIMAL(5,4),
                    entities_extracted TEXT,
                    pesan_keluar TEXT,
                    state_sebelumnya VARCHAR(50),
                    state_setelahnya VARCHAR(50),
                    waktu_interaksi DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (id_pelanggan) REFERENCES pelanggan(id_pelanggan),
                    INDEX idx_waktu (waktu_interaksi),
                    INDEX idx_intent (intent_terdeteksi),
                    INDEX idx_pelanggan (id_pelanggan)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id_feedback INT AUTO_INCREMENT PRIMARY KEY,
                    id_pelanggan VARCHAR(20),
                    id_pesanan INT,
                    rating INT CHECK (rating BETWEEN 1 AND 5),
                    saran TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (id_pelanggan) REFERENCES pelanggan(id_pelanggan),
                    FOREIGN KEY (id_pesanan) REFERENCES pesanan(id_pesanan)
                )
            """)
            
            # Tabel admin untuk autentikasi
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admin (
                    id_admin INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    nama VARCHAR(100),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.commit()
            print("Tabel database berhasil dibuat")
            
        except Error as e:
            print(f"Error membuat tabel: {e}")
        finally:
            cursor.close()

    def ensure_payment_schema(self):
        if self._schema_checked:
            return True

        cursor = self.get_cursor()
        if not cursor:
            return False

        try:
            cursor.execute("SHOW TABLES LIKE 'pesanan'")
            if not cursor.fetchone():
                self._schema_checked = True
                return True

            def column_exists(column_name):
                cursor.execute("""
                    SELECT 1
                    FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = %s
                      AND TABLE_NAME = 'pesanan'
                      AND COLUMN_NAME = %s
                    LIMIT 1
                """, (Config.DB_NAME, column_name))
                return cursor.fetchone() is not None

            column_definitions = {
                'payment_status': """
                    ALTER TABLE pesanan
                    ADD COLUMN payment_status
                    ENUM('pending', 'proof_submitted', 'verified', 'rejected')
                    DEFAULT 'pending'
                """,
                'payment_proof_file_id': """
                    ALTER TABLE pesanan
                    ADD COLUMN payment_proof_file_id VARCHAR(255) NULL
                """,
                'payment_proof_kind': """
                    ALTER TABLE pesanan
                    ADD COLUMN payment_proof_kind VARCHAR(20) NULL
                """,
                'payment_note': """
                    ALTER TABLE pesanan
                    ADD COLUMN payment_note TEXT NULL
                """,
                'payment_submitted_at': """
                    ALTER TABLE pesanan
                    ADD COLUMN payment_submitted_at DATETIME NULL
                """,
                'payment_verified_at': """
                    ALTER TABLE pesanan
                    ADD COLUMN payment_verified_at DATETIME NULL
                """
            }

            for column_name, statement in column_definitions.items():
                if not column_exists(column_name):
                    cursor.execute(statement)

            # Broaden the status enum first so legacy values and the new admin-first
            # states can coexist during migration on existing Railway databases.
            cursor.execute("""
                ALTER TABLE pesanan
                MODIFY COLUMN status ENUM(
                    'dipesan',
                    'menunggu_konfirmasi_admin',
                    'menunggu_pembayaran',
                    'diproses',
                    'selesai',
                    'batal',
                    'ditolak_admin'
                ) DEFAULT 'menunggu_konfirmasi_admin'
            """)

            cursor.execute("""
                UPDATE pesanan
                SET payment_status = 'pending'
                WHERE payment_status IS NULL
            """)

            # Migrate legacy statuses after payment columns exist.
            cursor.execute("""
                UPDATE pesanan
                SET status = CASE
                    WHEN COALESCE(payment_status, 'pending') = 'verified' THEN 'diproses'
                    WHEN COALESCE(payment_status, 'pending') IN ('proof_submitted', 'rejected') THEN 'menunggu_pembayaran'
                    ELSE 'menunggu_konfirmasi_admin'
                END
                WHERE status = 'dipesan'
            """)

            cursor.execute("""
                ALTER TABLE pesanan
                MODIFY COLUMN status ENUM(
                    'menunggu_konfirmasi_admin',
                    'menunggu_pembayaran',
                    'diproses',
                    'selesai',
                    'batal',
                    'ditolak_admin'
                ) DEFAULT 'menunggu_konfirmasi_admin'
            """)

            self.commit()
            self._schema_checked = True
            return True
        except Error as e:
            print(f"Error ensure payment schema: {e}")
            return False
        finally:
            cursor.close()

    def insert_menu(self, nama_menu, harga, kategori, ketersediaan=True):
        cursor = self.get_cursor()
        if not cursor: return None
        try:
            query = "INSERT INTO menu (nama_menu, harga, kategori, ketersediaan) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (nama_menu, harga, kategori, ketersediaan))
            self.commit()
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
            cursor.execute("SELECT * FROM menu ORDER BY id_menu ASC")
            results = cursor.fetchall()
            # Convert Decimal to float for JSON serialization
            for row in results:
                if row.get('harga') is not None:
                    row['harga'] = float(row['harga'])
            return results
        except Error as e:
            print(f"Error get menu: {e}")
            return []
        finally:
            cursor.close()

    def get_available_menu(self):
        cursor = self.get_cursor(dictionary=True)
        if not cursor:
            return []
        try:
            cursor.execute("SELECT * FROM menu WHERE ketersediaan = TRUE ORDER BY id_menu ASC")
            results = cursor.fetchall()
            for row in results:
                if row.get('harga') is not None:
                    row['harga'] = float(row['harga'])
            return results
        except Error as e:
            print(f"Error get available menu: {e}")
            return []
        finally:
            cursor.close()
    
    def _normalize_lookup_text(self, text):
        if not text:
            return ""
        normalized = re.sub(r'[^a-z0-9\s]', ' ', str(text).lower())
        return re.sub(r'\s+', ' ', normalized).strip()

    def _score_menu_candidates(self, rows, nama_menu, sambal=None):
        normalized_query = self._normalize_lookup_text(nama_menu)
        normalized_sambal = self._normalize_lookup_text(sambal)

        if not normalized_query and not normalized_sambal:
            return []

        query_tokens = [token for token in normalized_query.split() if token]
        sambal_tokens = [token for token in normalized_sambal.split() if token]
        scored_rows = []

        for row in rows:
            normalized_menu = self._normalize_lookup_text(row.get('nama_menu'))
            if not normalized_menu:
                continue

            menu_tokens = set(normalized_menu.split())
            score = 0

            if normalized_query:
                if normalized_menu == normalized_query:
                    score += 1000
                if normalized_query in normalized_menu:
                    score += 250

                matched_query_tokens = sum(1 for token in query_tokens if token in menu_tokens)
                if matched_query_tokens == 0:
                    continue

                score += matched_query_tokens * 40
                if matched_query_tokens == len(query_tokens):
                    score += 120

            if sambal_tokens:
                matched_sambal_tokens = sum(1 for token in sambal_tokens if token in menu_tokens)
                if matched_sambal_tokens == len(sambal_tokens):
                    score += 400
                elif matched_sambal_tokens > 0:
                    score += matched_sambal_tokens * 50
                else:
                    continue

            candidate_row = dict(row)
            if candidate_row.get('harga') is not None:
                candidate_row['harga'] = float(candidate_row['harga'])

            scored_rows.append({
                'score': score,
                'menu_length': len(normalized_menu),
                'row': candidate_row
            })

        scored_rows.sort(key=lambda item: (item['score'], -item['menu_length']), reverse=True)
        return scored_rows

    def _extract_embedded_sambal_variant(self, text):
        normalized_text = self._normalize_lookup_text(text)
        if not normalized_text:
            return None

        alias_map = {
            'sambal bawang': ['sambal bawang', 'bawang'],
            'sambal ijo': ['sambal ijo', 'sambal hijau', 'ijo', 'hijau'],
            'sambal terasi': ['sambal terasi', 'terasi'],
            'sambal matah': ['sambal matah', 'matah'],
            'sambal merah': ['sambal merah', 'merah'],
            'tanpa sambal': [
                'tanpa sambal',
                'tanpa',
                'tidak pakai sambal',
                'ga pakai sambal',
                'gak pakai sambal',
                'nggak pakai sambal',
                'no sambal'
            ]
        }

        for canonical, aliases in alias_map.items():
            for alias in sorted(aliases, key=len, reverse=True):
                alias_normalized = self._normalize_lookup_text(alias)
                pattern = r'(?<!\w)' + re.escape(alias_normalized).replace(r'\ ', r'\s+') + r'(?!\w)'
                if re.search(pattern, normalized_text):
                    return canonical
        return None

    def _strip_variant_tokens(self, text):
        normalized_text = self._normalize_lookup_text(text)
        if not normalized_text:
            return ""

        sambal_patterns = [
            r'\bsambal\s+bawang\b',
            r'\bsambal\s+ijo\b',
            r'\bsambal\s+hijau\b',
            r'\bsambal\s+merah\b',
            r'\bsambal\s+terasi\b',
            r'\bsambal\s+matah\b',
            r'\btanpa\s+sambal\b',
            r'\bbawang\b',
            r'\bijo\b',
            r'\bhijau\b',
            r'\bmerah\b',
            r'\bterasi\b',
            r'\bmatah\b',
        ]
        stripped = normalized_text
        for pattern in sambal_patterns:
            stripped = re.sub(pattern, ' ', stripped)

        stripped = re.sub(r'\s+', ' ', stripped).strip()
        return stripped

    def resolve_menu_choice(self, nama_menu, sambal=None):
        cursor = self.get_cursor(dictionary=True)
        if not cursor:
            return {'match': None, 'ambiguous': False, 'candidates': []}
        try:
            cursor.execute("SELECT * FROM menu WHERE ketersediaan = TRUE ORDER BY id_menu ASC")
            rows = cursor.fetchall() or []
            scored_rows = self._score_menu_candidates(rows, nama_menu, sambal)

            if not scored_rows:
                return {'match': None, 'ambiguous': False, 'candidates': []}

            normalized_sambal = self._normalize_lookup_text(sambal or self._extract_embedded_sambal_variant(nama_menu))
            normalized_query = self._normalize_lookup_text(nama_menu)
            top_scored = [item['row'] for item in scored_rows if item['score'] == scored_rows[0]['score']]

            if normalized_sambal:
                best_candidates = [scored_rows[0]['row']]
                is_ambiguous = False
            else:
                grouped_candidates = {}
                for candidate in top_scored:
                    base_name = self._strip_variant_tokens(candidate.get('nama_menu'))
                    grouped_candidates.setdefault(base_name, []).append(candidate)

                preferred_group = None
                if normalized_query in grouped_candidates:
                    preferred_group = grouped_candidates[normalized_query]
                else:
                    containing_groups = [
                        candidates
                        for base_name, candidates in grouped_candidates.items()
                        if normalized_query and normalized_query in base_name
                    ]
                    if len(containing_groups) == 1:
                        preferred_group = containing_groups[0]

                if preferred_group is None:
                    shortest_row = min(top_scored, key=lambda row: len(self._normalize_lookup_text(row.get('nama_menu'))))
                    preferred_group = [shortest_row]

                best_candidates = preferred_group[:5]
                is_ambiguous = len(best_candidates) > 1

            return {
                'match': None if is_ambiguous else best_candidates[0],
                'ambiguous': is_ambiguous,
                'candidates': best_candidates[:5] if is_ambiguous else [best_candidates[0]]
            }
        except Error as e:
            print(f"Error resolve menu choice: {e}")
            return {'match': None, 'ambiguous': False, 'candidates': []}
        finally:
            cursor.close()

    def get_menu_by_name(self, nama_menu, sambal=None):
        return self.resolve_menu_choice(nama_menu, sambal).get('match')

    def get_menu_by_id(self, id_menu):
        cursor = self.get_cursor(dictionary=True)
        if not cursor:
            return None
        try:
            cursor.execute("SELECT * FROM menu WHERE id_menu = %s LIMIT 1", (id_menu,))
            row = cursor.fetchone()
            if row and row.get('harga') is not None:
                row['harga'] = float(row['harga'])
            return row
        except Error as e:
            print(f"Error get menu by id: {e}")
            return None
        finally:
            cursor.close()

    def get_menu_debug_snapshot(self):
        cursor = self.get_cursor(dictionary=True)
        if not cursor:
            return {'error': 'Database connection failed'}

        try:
            cursor.execute("""
                SELECT
                    DATABASE() AS active_database,
                    CURRENT_USER() AS active_user,
                    @@hostname AS active_hostname
            """)
            connection_info = cursor.fetchone() or {}

            cursor.execute("""
                SELECT
                    COUNT(*) AS total_menu,
                    MIN(id_menu) AS min_id_menu,
                    MAX(id_menu) AS max_id_menu
                FROM menu
            """)
            summary = cursor.fetchone() or {}

            cursor.execute("""
                SELECT id_menu, nama_menu, harga, kategori, ketersediaan
                FROM menu
                ORDER BY id_menu ASC
                LIMIT 20
            """)
            rows = cursor.fetchall() or []

            for row in rows:
                if row.get('harga') is not None:
                    row['harga'] = float(row['harga'])

            return {
                'connection': connection_info,
                'summary': summary,
                'rows': rows
            }
        except Error as e:
            print(f"Error get menu debug snapshot: {e}")
            return {'error': str(e)}
        finally:
            cursor.close()
    
    def create_pesanan(self, id_pelanggan, detail_pesanan, total_harga, waktu_pengambilan=None, tipe_pengambilan='immediate', status='menunggu_konfirmasi_admin'):
        if not self.ensure_payment_schema():
            print("Payment schema belum siap saat membuat pesanan.")
            return None

        cursor = self.get_cursor()
        if not cursor: return None
        try:
            query = """
                INSERT INTO pesanan (id_pelanggan, detail_pesanan, total_harga, waktu_pengambilan, tipe_pengambilan, status) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            waktu_str = waktu_pengambilan['formatted'] if isinstance(waktu_pengambilan, dict) else waktu_pengambilan
            cursor.execute(query, (id_pelanggan, detail_pesanan, total_harga, waktu_str, tipe_pengambilan, status))
            self.commit()
            return cursor.lastrowid
        except Error as e:
            print(f"Error create pesanan: {e}")
            return None
        finally:
            cursor.close()
    
    def update_status_pesanan(self, id_pesanan, status):
        if not self.ensure_payment_schema():
            print("Payment schema belum siap saat mengubah status pesanan.")
            return False

        cursor = self.get_cursor()
        if not cursor: return False
        try:
            query = "UPDATE pesanan SET status = %s WHERE id_pesanan = %s"
            cursor.execute(query, (status, id_pesanan))
            self.commit()
            return cursor.rowcount > 0
        except Error as e:
            print(f"Error update pesanan: {e}")
            return False
        finally:
            cursor.close()

    def update_payment_status(self, id_pesanan, payment_status, note=None):
        cursor = self.get_cursor()
        if not cursor:
            return False

        try:
            query = """
                UPDATE pesanan
                SET payment_status = %s,
                    payment_note = COALESCE(%s, payment_note),
                    payment_verified_at = CASE WHEN %s = 'verified' THEN NOW() ELSE payment_verified_at END
                WHERE id_pesanan = %s
            """
            cursor.execute(query, (payment_status, note, payment_status, id_pesanan))
            self.commit()
            return True
        except Error as e:
            print(f"Error update payment status: {e}")
            return False
        finally:
            cursor.close()

    def submit_payment_proof(self, id_pesanan, file_id, proof_kind='photo', note=None):
        cursor = self.get_cursor()
        if not cursor:
            return False

        try:
            query = """
                UPDATE pesanan
                SET payment_status = 'proof_submitted',
                    payment_proof_file_id = %s,
                    payment_proof_kind = %s,
                    payment_note = %s,
                    payment_submitted_at = NOW()
                WHERE id_pesanan = %s
            """
            cursor.execute(query, (file_id, proof_kind, note, id_pesanan))
            self.commit()
            return True
        except Error as e:
            print(f"Error submit payment proof: {e}")
            return False
        finally:
            cursor.close()

    def verify_payment_and_process_order(self, id_pesanan):
        cursor = self.get_cursor()
        if not cursor:
            return False

        try:
            query = """
                UPDATE pesanan
                SET payment_status = 'verified',
                    payment_verified_at = NOW(),
                    status = 'diproses'
                WHERE id_pesanan = %s
            """
            cursor.execute(query, (id_pesanan,))
            self.commit()
            return True
        except Error as e:
            print(f"Error verify payment: {e}")
            return False
        finally:
            cursor.close()

    def reject_payment_proof(self, id_pesanan, note=None):
        cursor = self.get_cursor()
        if not cursor:
            return False

        try:
            query = """
                UPDATE pesanan
                SET payment_status = 'rejected',
                    payment_note = %s
                WHERE id_pesanan = %s
            """
            cursor.execute(query, (note, id_pesanan))
            self.commit()
            return True
        except Error as e:
            print(f"Error reject payment: {e}")
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
    
    def get_pesanan_by_id(self, id_pesanan):
        """Get single order by ID"""
        cursor = self.get_cursor(dictionary=True)
        if not cursor: return None
        try:
            query = "SELECT * FROM pesanan WHERE id_pesanan = %s"
            cursor.execute(query, (id_pesanan,))
            return cursor.fetchone()
        except Error as e:
            print(f"Error get pesanan by id: {e}")
            return None
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

    def get_latest_unpaid_order(self, id_pelanggan):
        cursor = self.get_cursor(dictionary=True)
        if not cursor:
            return None
        try:
            query = """
                SELECT *
                FROM pesanan
                WHERE id_pelanggan = %s
                  AND status = 'menunggu_pembayaran'
                  AND payment_status IN ('pending', 'proof_submitted', 'rejected')
                ORDER BY id_pesanan DESC
                LIMIT 1
            """
            cursor.execute(query, (id_pelanggan,))
            return cursor.fetchone()
        except Error as e:
            print(f"Error get latest unpaid order: {e}")
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
            self.commit()
            return True
        except Error as e:
            print(f"Error insert pelanggan: {e}")
            return False
        finally:
            cursor.close()
    
    def get_user_state(self, id_pelanggan):
        try:
            # Pastikan pelanggan ada sebelum membuka cursor lain di koneksi yang sama
            self.insert_or_update_pelanggan(id_pelanggan, "Pelanggan")

            cursor = self.get_cursor(dictionary=True)
            if not cursor: return {'state': 'idle', 'data': {}, 'cart': []}

            query = "SELECT state, data, cart FROM conversation_states WHERE id_pelanggan = %s"
            cursor.execute(query, (id_pelanggan,))
            result = cursor.fetchone()
            
            if result:
                import json
                data = json.loads(result['data']) if result['data'] else {}
                cart = json.loads(result['cart']) if result['cart'] else []
                return {'state': result['state'], 'data': data, 'cart': cart}
            else:
                return {'state': 'idle', 'data': {}, 'cart': []}
        except Error as e:
            print(f"Error get user state: {e}")
            return {'state': 'idle', 'data': {}, 'cart': []}
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()

    def update_user_state(self, id_pelanggan, state, data=None, cart=None):
        try:
            # Pastikan pelanggan ada sebelum operasi state lain
            self.insert_or_update_pelanggan(id_pelanggan, "Pelanggan")
            
            import json
            from decimal import Decimal
            
            class DecimalEncoder(json.JSONEncoder):
                def default(self, obj):
                    if isinstance(obj, Decimal):
                        return float(obj)
                    return super().default(obj)
            
            current = self.get_user_state(id_pelanggan)
            cursor = self.get_cursor()
            if not cursor: return False

            new_data = current['data']
            if data is not None:
                new_data.update(data)
                
            new_cart = cart if cart is not None else current['cart']
            
            query = """
                INSERT INTO conversation_states (id_pelanggan, state, data, cart) 
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE state = %s, data = %s, cart = %s
            """
            
            data_json = json.dumps(new_data, cls=DecimalEncoder)
            cart_json = json.dumps(new_cart, cls=DecimalEncoder)
            
            cursor.execute(query, (
                id_pelanggan, state, data_json, cart_json,
                state, data_json, cart_json
            ))
            self.commit()
            return True
        except Error as e:
            print(f"Error update user state: {e}")
            return False
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()

    def reset_user_state(self, id_pelanggan):
        return self.update_user_state(id_pelanggan, 'idle', {}, [])

    # ==================== CHAT LOGGING & ANALYTICS ====================
    
    def log_chat_interaction(self, id_pelanggan, nama_pelanggan, pesan_masuk, 
                            intent_terdeteksi, confidence_score, entities_extracted,
                            pesan_keluar, state_sebelumnya, state_setelahnya):
        """
        Log setiap interaksi chat untuk evaluasi dan analisis
        """
        cursor = self.get_cursor()
        if not cursor: return False
        try:
            import json
            query = """
                INSERT INTO chat_logs 
                (id_pelanggan, nama_pelanggan, pesan_masuk, intent_terdeteksi, 
                 confidence_score, entities_extracted, pesan_keluar, 
                 state_sebelumnya, state_setelahnya)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            entities_json = json.dumps(entities_extracted) if entities_extracted else '{}'
            cursor.execute(query, (
                id_pelanggan, nama_pelanggan, pesan_masuk, intent_terdeteksi,
                confidence_score, entities_json, pesan_keluar,
                state_sebelumnya, state_setelahnya
            ))
            self.commit()
            return True
        except Error as e:
            print(f"Error logging chat: {e}")
            return False
        finally:
            if cursor: cursor.close()

    def get_chat_analytics(self, start_date=None, end_date=None):
        """
        Get analytics data for evaluation
        Returns: dict dengan metrics untuk evaluasi Bab 4
        """
        cursor = self.get_cursor(dictionary=True)
        if not cursor: return {}
        try:
            # Base query conditions
            date_condition = ""
            params = []
            if start_date and end_date:
                date_condition = "WHERE waktu_interaksi BETWEEN %s AND %s"
                params = [start_date, end_date]

            # Total interactions
            cursor.execute(f"SELECT COUNT(*) as total FROM chat_logs {date_condition}", params)
            total_interactions = cursor.fetchone()['total']

            # Intent distribution
            cursor.execute(f"""
                SELECT intent_terdeteksi, COUNT(*) as count 
                FROM chat_logs 
                {date_condition}
                GROUP BY intent_terdeteksi
                ORDER BY count DESC
            """, params)
            intent_distribution = cursor.fetchall()

            # Average confidence score
            cursor.execute(f"""
                SELECT AVG(confidence_score) as avg_confidence 
                FROM chat_logs 
                {date_condition}
            """, params)
            avg_confidence = cursor.fetchone()['avg_confidence'] or 0

            # Confidence distribution
            cursor.execute(f"""
                SELECT 
                    CASE 
                        WHEN confidence_score >= 0.8 THEN 'High (>=0.8)'
                        WHEN confidence_score >= 0.6 THEN 'Medium (0.6-0.8)'
                        ELSE 'Low (<0.6)'
                    END as confidence_level,
                    COUNT(*) as count
                FROM chat_logs
                {date_condition}
                GROUP BY confidence_level
            """, params)
            confidence_distribution = cursor.fetchall()

            # State transitions
            cursor.execute(f"""
                SELECT state_sebelumnya, state_setelahnya, COUNT(*) as count
                FROM chat_logs
                {date_condition}
                GROUP BY state_sebelumnya, state_setelahnya
                ORDER BY count DESC
                LIMIT 10
            """, params)
            state_transitions = cursor.fetchall()

            return {
                'total_interactions': total_interactions,
                'intent_distribution': intent_distribution,
                'average_confidence': round(float(avg_confidence), 4),
                'confidence_distribution': confidence_distribution,
                'top_state_transitions': state_transitions
            }
        except Error as e:
            print(f"Error getting analytics: {e}")
            return {}
        finally:
            if cursor: cursor.close()

    def get_chat_logs_for_evaluation(self, limit=1000):
        """
        Get raw chat logs for manual evaluation (precision/recall calculation)
        """
        cursor = self.get_cursor(dictionary=True)
        if not cursor: return []
        try:
            query = """
                SELECT * FROM chat_logs 
                ORDER BY waktu_interaksi DESC
                LIMIT %s
            """
            cursor.execute(query, (limit,))
            return cursor.fetchall()
        except Error as e:
            print(f"Error getting chat logs: {e}")
            return []
        finally:
            if cursor: cursor.close()

    def get_intent_confusion_matrix_data(self):
        """
        Get data untuk membuat confusion matrix
        Returns: list of (predicted_intent, actual_intent) - actual perlu diisi manual evaluasi
        """
        cursor = self.get_cursor(dictionary=True)
        if not cursor: return []
        try:
            query = """
                SELECT id_log, pesan_masuk, intent_terdeteksi, confidence_score
                FROM chat_logs
                ORDER BY waktu_interaksi DESC
            """
            cursor.execute(query)
            return cursor.fetchall()
        except Error as e:
            print(f"Error getting confusion matrix data: {e}")
            return []
        finally:
            if cursor: cursor.close()

    # ==================== FEEDBACK SYSTEM ====================
    
    def save_feedback(self, id_pelanggan, id_pesanan, rating, saran=None):
        """
        Simpan feedback rating dari pelanggan (untuk SUS evaluation)
        """
        cursor = self.get_cursor()
        if not cursor: return False
        try:
            query = """
                INSERT INTO feedback (id_pelanggan, id_pesanan, rating, saran)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (id_pelanggan, id_pesanan, rating, saran))
            self.commit()
            return True
        except Error as e:
            print(f"Error saving feedback: {e}")
            return False
        finally:
            if cursor: cursor.close()

    def get_feedback_stats(self):
        """
        Get feedback statistics untuk evaluasi
        """
        cursor = self.get_cursor(dictionary=True)
        if not cursor: return {}
        try:
            cursor.execute("""
                SELECT 
                    AVG(rating) as avg_rating,
                    COUNT(*) as total_feedback,
                    SUM(CASE WHEN rating >= 4 THEN 1 ELSE 0 END) as positive_count,
                    SUM(CASE WHEN rating = 3 THEN 1 ELSE 0 END) as neutral_count,
                    SUM(CASE WHEN rating <= 2 THEN 1 ELSE 0 END) as negative_count
                FROM feedback
            """)
            stats = cursor.fetchone()
            return {
                'average_rating': round(float(stats['avg_rating'] or 0), 2),
                'total_feedback': stats['total_feedback'] or 0,
                'positive': stats['positive_count'] or 0,
                'neutral': stats['neutral_count'] or 0,
                'negative': stats['negative_count'] or 0
            }
        except Error as e:
            print(f"Error getting feedback stats: {e}")
            return {}
        finally:
            if cursor: cursor.close()

    def get_feedback_rating_distribution(self):
        """
        Get distribution of ratings (1-5) untuk analisis detail
        """
        cursor = self.get_cursor(dictionary=True)
        if not cursor: return {}
        try:
            cursor.execute("""
                SELECT rating, COUNT(*) as count
                FROM feedback
                GROUP BY rating
                ORDER BY rating DESC
            """)
            results = cursor.fetchall()
            distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            for row in results:
                if row['rating'] in distribution:
                    distribution[row['rating']] = row['count']
            return distribution
        except Error as e:
            print(f"Error getting rating distribution: {e}")
            return {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        finally:
            if cursor: cursor.close()

    # ==================== ADMIN AUTHENTICATION ====================

    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_default_admin(self):
        """Create default admin if not exists"""
        cursor = self.get_cursor(dictionary=True)
        if not cursor: return False
        try:
            # Check if admin exists
            cursor.execute("SELECT COUNT(*) as count FROM admin")
            result = cursor.fetchone()
            
            if result['count'] == 0:
                # Create default admin with password 'admin123'
                password_hash = self._hash_password('admin123')
                
                cursor.execute("""
                    INSERT INTO admin (username, password_hash, nama) 
                    VALUES (%s, %s, %s)
                """, ('admin', password_hash, 'Administrator'))
                self.commit()
                print("Default admin created: username='admin', password='admin123'")
                return True
            return False
        except Error as e:
            print(f"Error creating default admin: {e}")
            return False
        finally:
            if cursor: cursor.close()
    
    def verify_admin_login(self, username, password):
        """Verify admin credentials"""
        cursor = self.get_cursor(dictionary=True)
        if not cursor: return None
        try:
            password_hash = self._hash_password(password)
            
            cursor.execute("""
                SELECT id_admin, username, nama FROM admin 
                WHERE username = %s AND password_hash = %s
            """, (username, password_hash))
            
            return cursor.fetchone()
        except Error as e:
            print(f"Error verifying admin: {e}")
            return None
        finally:
            if cursor: cursor.close()
    
    def change_admin_password(self, admin_id, new_password):
        """Change admin password"""
        cursor = self.get_cursor()
        if not cursor: return False
        try:
            password_hash = self._hash_password(new_password)
            
            cursor.execute("""
                UPDATE admin SET password_hash = %s WHERE id_admin = %s
            """, (password_hash, admin_id))
            
            self.commit()
            return cursor.rowcount > 0
        except Error as e:
            print(f"Error changing password: {e}")
            return False
        finally:
            if cursor: cursor.close()

    def create_or_update_admin(self, username, password, nama=None):
        """Create new admin or update existing admin credentials by username."""
        cursor = self.get_cursor(dictionary=True)
        if not cursor:
            return {'success': False, 'action': None}
        try:
            self.create_database_and_tables()

            safe_username = (username or '').strip()
            safe_nama = (nama or safe_username or 'Administrator').strip()
            if not safe_username or not password:
                return {'success': False, 'action': None}

            password_hash = self._hash_password(password)

            cursor.execute("""
                SELECT id_admin
                FROM admin
                WHERE username = %s
                LIMIT 1
            """, (safe_username,))
            existing_admin = cursor.fetchone()

            if existing_admin:
                cursor.execute("""
                    UPDATE admin
                    SET password_hash = %s,
                        nama = %s
                    WHERE id_admin = %s
                """, (password_hash, safe_nama, existing_admin['id_admin']))
                action = 'updated'
            else:
                cursor.execute("""
                    INSERT INTO admin (username, password_hash, nama)
                    VALUES (%s, %s, %s)
                """, (safe_username, password_hash, safe_nama))
                action = 'created'

            self.commit()
            return {'success': True, 'action': action}
        except Error as e:
            print(f"Error create or update admin: {e}")
            return {'success': False, 'action': None}
        finally:
            if cursor:
                cursor.close()

    def close(self):
        connection = self.connection
        if not connection:
            return

        try:
            if connection.is_connected():
                connection.close()
        except Error:
            pass
        finally:
            self.connection = None

db = Database()
