-- Database Initialization for Kedai Ayam Merdeka Chatbot

CREATE DATABASE IF NOT EXISTS kedai_ayam_merdeka;
USE kedai_ayam_merdeka;

-- Table Structure for 'menu'
CREATE TABLE IF NOT EXISTS menu (
    id_menu INT AUTO_INCREMENT PRIMARY KEY,
    nama_menu VARCHAR(100) NOT NULL,
    harga DECIMAL(10,2) NOT NULL,
    kategori VARCHAR(50),
    ketersediaan BOOLEAN DEFAULT TRUE
);

-- Table Structure for 'pelanggan'
CREATE TABLE IF NOT EXISTS pelanggan (
    id_pelanggan VARCHAR(20) PRIMARY KEY, -- Will hold WhatsApp Phone Number or Telegram Chat ID
    nama VARCHAR(100),
    riwayat_pesanan TEXT
);

-- Table Structure for 'inventori'
CREATE TABLE IF NOT EXISTS inventori (
    id_item INT AUTO_INCREMENT PRIMARY KEY,
    nama_item VARCHAR(100) NOT NULL,
    stok INT DEFAULT 0,
    satuan VARCHAR(20)
);

-- Table Structure for 'pesanan'
CREATE TABLE IF NOT EXISTS pesanan (
    id_pesanan INT AUTO_INCREMENT PRIMARY KEY,
    id_pelanggan VARCHAR(20),
    detail_pesanan TEXT,
    total_harga DECIMAL(10,2),
    status ENUM('dipesan', 'diproses', 'selesai', 'batal') DEFAULT 'dipesan',
    waktu_pesan DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_pelanggan) REFERENCES pelanggan(id_pelanggan)
);

-- Dump Data for 'menu'
INSERT INTO menu (nama_menu, harga, kategori, ketersediaan) VALUES 
('Ayam Geprek', 15000, 'Ayam', 1),
('Ayam Bakar', 18000, 'Ayam', 1),
('Ayam Goreng', 15000, 'Ayam', 1),
('Nasi', 5000, 'Lauk', 1),
('Es Teh Manis', 5000, 'Minuman', 1),
('Es Jeruk', 6000, 'Minuman', 1),
('Es Campur', 12000, 'Minuman', 1),
('Es Teler', 10000, 'Minuman', 1),
('Tahu Crispy', 3000, 'Lauk', 1),
('Tempe Crispy', 3000, 'Lauk', 1);

-- Dump Data for 'inventori' (Optional Initial Data)
INSERT INTO inventori (nama_item, stok, satuan) VALUES 
('Ayam Mentah', 50, 'kg'),
('Beras', 100, 'kg'),
('Cabai', 10, 'kg');
