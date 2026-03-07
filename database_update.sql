-- ============================================
-- 1. ALTER TABLE PESANAN
-- Tambahkan kolom baru (cek manual sebelum eksekusi)
-- ============================================

-- Jalankan ini hanya jika kolom belum ada
ALTER TABLE pesanan 
ADD COLUMN waktu_pengambilan VARCHAR(50) AFTER status,
ADD COLUMN tipe_pengambilan ENUM('immediate', 'specific', 'relative', 'later') DEFAULT 'immediate' AFTER waktu_pengambilan;

-- ============================================
-- 2. CREATE TABEL CHAT_LOGS
-- Untuk menyimpan log interaksi chatbot
-- ============================================

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
);

-- ============================================
-- 3. CREATE TABEL FEEDBACK
-- Untuk menyimpan rating dan saran dari pelanggan
-- ============================================

CREATE TABLE IF NOT EXISTS feedback (
    id_feedback INT AUTO_INCREMENT PRIMARY KEY,
    id_pelanggan VARCHAR(20),
    id_pesanan INT,
    rating INT CHECK (rating BETWEEN 1 AND 5),
    saran TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_pelanggan) REFERENCES pelanggan(id_pelanggan),
    FOREIGN KEY (id_pesanan) REFERENCES pesanan(id_pesanan)
);

-- ============================================
-- 4. CREATE TABEL ADMIN
-- Untuk autentikasi admin panel
-- ============================================

CREATE TABLE IF NOT EXISTS admin (
    id_admin INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nama VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 5. INSERT DEFAULT ADMIN
-- Username: admin | Password: admin123
-- ============================================

INSERT IGNORE INTO admin (username, password_hash, nama) VALUES 
('admin', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', 'Administrator');

-- ============================================
-- SELESAI
-- ============================================
