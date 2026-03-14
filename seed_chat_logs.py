"""
Seed ulang chat_logs Railway dengan pesan campuran Bahasa Indonesia + Luwu/Palopo.
Partikel lokal: ji, mi, ko, pi, mo, to, pole, elo/melo, engka, iyye, aga, de, pura
"""
import mysql.connector
from datetime import datetime, timedelta
import random

conn = mysql.connector.connect(
    host='turntable.proxy.rlwy.net',
    user='root',
    password='TAKbTTsWlfbWUcJlwqjsakiOAGHcKkWe',
    database='railway',
    port=39744
)
cur = conn.cursor()

# Hapus dummy lama
cur.execute("DELETE FROM chat_logs WHERE id_pelanggan IN ('user_001','user_002','user_003','user_004','user_005')")
conn.commit()
print("[OK] Data dummy lama dihapus")

# Pastikan pelanggan dummy ada
pelanggan_dummy = [
    ('user_001', 'Budi'),
    ('user_002', 'Sari'),
    ('user_003', 'Andi'),
    ('user_004', 'Dewi'),
    ('user_005', 'Reza'),
]
for pid, nama in pelanggan_dummy:
    cur.execute("""
        INSERT INTO pelanggan (id_pelanggan, nama) VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE nama = %s
    """, (pid, nama, nama))
conn.commit()

# Format: (pesan_masuk, intent_predicted, confidence, balasan, state_before, state_after)
# Campuran Indonesia + Luwu/Palopo — beberapa sengaja ambigu → predicted bisa salah
SAMPLES = [
    # -------- SALAM (20) --------
    ("halo", "salam", 0.95, "Halo! Selamat datang di Kedai Ayam Merdeka!", "idle", "idle"),
    ("hai", "salam", 0.93, "Hai kak! Ada yang bisa dibantu?", "idle", "idle"),
    ("pole-pole kak", "salam", 0.72, "Halo kak! Silakan, ada yang bisa dibantu?", "idle", "idle"),      # pole = datang
    ("elo kak, ada ji?", "salam", 0.68, "Ada kak! Mau pesan apa?", "idle", "idle"),                     # elo = hei
    ("iyye assalamualaikum", "salam", 0.85, "Waalaikumsalam kak!", "idle", "idle"),
    ("halo kak, engka ji disini?", "salam", 0.70, "Ada kak! Siap melayani.", "idle", "idle"),            # engka = ada
    ("selamat pagi kak", "salam", 0.90, "Selamat pagi! Mau pesan apa?", "idle", "idle"),
    ("malam kak", "salam", 0.80, "Selamat malam kak!", "idle", "idle"),
    ("hei bot ada ko?", "salam", 0.75, "Ada kak! Mau pesan apa?", "idle", "idle"),                      # ko = kamu
    ("hello kak", "salam", 0.88, "Halo kak! Selamat datang!", "idle", "idle"),
    ("siang kak", "salam", 0.78, "Selamat siang kak!", "idle", "idle"),
    ("selamat sore", "salam", 0.87, "Selamat sore kak!", "idle", "idle"),
    ("permisi kak", "salam", 0.73, "Halo kak! Kami siap membantu.", "idle", "idle"),
    ("hai kak engka ki?", "salam", 0.65, "Ada kak! Silakan.", "idle", "idle"),                          # engka ki = ada kamu
    ("numpang tanya kak", "salam", 0.60, "Silakan kak, ada yang bisa dibantu?", "idle", "idle"),
    ("adekko kak!", "unknown", 0.45, "Maaf kak, bisa diulang?", "idle", "idle"),                        # FN: harusnya salam
    ("assalamualaikum kak", "salam", 0.89, "Waalaikumsalam kak!", "idle", "idle"),
    ("hay kak!", "salam", 0.82, "Halo kak!", "idle", "idle"),
    ("selamat datang", "salam", 0.77, "Halo! Selamat datang juga kak.", "idle", "idle"),
    ("apa khabar kak", "unknown", 0.50, "Maaf kak, saya hanya bisa bantu pesan makanan.", "idle", "idle"), # FN salam

    # -------- PESAN MENU (25) --------
    ("melo pesan ayam geprek kak", "pesan_menu", 0.91, "Mau berapa porsi?", "idle", "asking_quantity"),     # melo = mau
    ("mau ji pesan 2 ayam bakar", "pesan_menu", 0.93, "2 ayam bakar ya!", "idle", "asking_sambal"),
    ("order ayam goreng 1 porsi kak", "pesan_menu", 0.90, "Siap! 1 ayam goreng.", "idle", "asking_sambal"),
    ("beli ji ayam geprek kak", "pesan_menu", 0.87, "Mau berapa porsi?", "idle", "asking_quantity"),
    ("pesan ji ayam bakar sama nasi", "pesan_menu", 0.89, "Oke catat ya!", "idle", "asking_sambal"),
    ("melo ji ayam goreng 3 kak", "pesan_menu", 0.85, "3 ayam goreng ya!", "idle", "asking_sambal"),
    ("kasih mi ayam crispy 2", "pesan_menu", 0.83, "Baik 2 ayam crispy!", "idle", "asking_sambal"),
    ("ayam geprek 1 sambal ijo pale", "pesan_menu", 0.88, "Siap! Sambal ijo ya.", "idle", "asking_time"),  # pale = saja
    ("mau ji order kak", "pesan_menu", 0.70, "Mau pesan menu apa kak?", "idle", "asking_menu"),
    ("pesan es teh manis kak", "pesan_menu", 0.86, "Es teh manis ya! Mau berapa?", "idle", "asking_quantity"),
    ("2 nasi sama es jeruk pale", "pesan_menu", 0.84, "2 nasi + es jeruk, oke!", "idle", "asking_time"),
    ("order mi ayam geprek pole tanpa sambal", "pesan_menu", 0.87, "Tanpa sambal ya kak!", "idle", "asking_time"),
    ("melo beli ayam apa ji ada?", "salam", 0.65, "Halo kak! Mau pesan apa?", "idle", "idle"),              # FP: harusnya cek_ketersediaan
    ("tiga ji ayam bakar kak", "pesan_menu", 0.85, "3 ayam bakar ya kak!", "idle", "asking_sambal"),
    ("pesan tempe crispy 2 kak", "pesan_menu", 0.82, "2 tempe crispy ya!", "idle", "asking_time"),
    ("1 ayam goreng 1 nasi pale kak", "pesan_menu", 0.88, "1 ayam goreng + 1 nasi, siap!", "idle", "asking_sambal"),
    ("melo makang ayam geprek", "pesan_menu", 0.84, "Mau berapa porsi kak?", "idle", "asking_quantity"),    # makang = makan (Luwu)
    ("order 2 es campur kak", "pesan_menu", 0.83, "2 es campur ya!", "idle", "asking_time"),
    ("beli es teler 1 pale", "pesan_menu", 0.81, "1 es teler kak!", "idle", "asking_time"),
    ("tambah ji 1 nasi lagi kak", "pesan_menu", 0.80, "Oke! Ditambah 1 nasi.", "idle", "asking_time"),
    ("minta ayam geprek 2 sambal bawang pale", "pesan_menu", 0.90, "Siap! Sambal bawang ya.", "idle", "asking_time"),
    ("pesan ji tahu crispy kak", "pesan_menu", 0.83, "Tahu crispy, mau berapa?", "idle", "asking_quantity"),
    ("1 ayam bakar pale kak", "pesan_menu", 0.87, "1 ayam bakar, siap!", "idle", "asking_sambal"),
    ("melo mapperi makang kak", "unknown", 0.55, "Maaf kak, mau pesan apa?", "idle", "idle"),               # FN: mapperi = pesan (Bugis)
    ("2 ayam geprek 1 nasi pale", "pesan_menu", 0.92, "2 ayam geprek + 1 nasi, oke!", "idle", "asking_sambal"),

    # -------- CEK STATUS (10) --------
    ("cek ji pesanan ku kak", "cek_status", 0.88, "Oke, saya cek ya!", "idle", "idle"),
    ("pura ji di proses pesanan ku?", "cek_status", 0.85, "Sedang diproses kak!", "idle", "idle"),          # pura = sudah
    ("makanan ku pura selesai mi?", "cek_status", 0.83, "Sebentar lagi kak!", "idle", "idle"),
    ("pesanan ku mana ji kak?", "cek_status", 0.80, "Masih diproses kak.", "idle", "idle"),
    ("udah selesai mi kak?", "cek_status", 0.82, "Sedang diproses kak!", "idle", "idle"),
    ("cek status pale kak", "cek_status", 0.86, "Oke dicek ya!", "idle", "idle"),
    ("de pura ji kak pesanan ku?", "cek_status", 0.78, "Masih diproses kak.", "idle", "idle"),              # de = belum/tidak
    ("kapan mi selesai kak?", "cek_status", 0.76, "Sebentar lagi kak!", "idle", "idle"),
    ("lama pi kak", "cek_status", 0.62, "Mohon ditunggu ya kak!", "idle", "idle"),
    ("pesanan ku aga nomornya?", "cek_status", 0.72, "Dicek ya kak!", "idle", "idle"),                      # aga = apa

    # -------- TERIMA KASIH (8) --------
    ("makasih ji kak", "terima_kasih", 0.93, "Sama-sama kak!", "idle", "idle"),
    ("terima kasih kak", "terima_kasih", 0.97, "Sama-sama!", "idle", "idle"),
    ("thanks kak", "terima_kasih", 0.90, "You're welcome kak!", "idle", "idle"),
    ("makasih banyak kak", "terima_kasih", 0.91, "Sama-sama kak!", "idle", "idle"),
    ("sip makasih kak", "terima_kasih", 0.88, "Sama-sama! Selamat menikmati!", "idle", "idle"),
    ("oke tengkyu kak", "terima_kasih", 0.85, "Terima kasih kak!", "idle", "idle"),
    ("iyye makasih pole kak", "terima_kasih", 0.87, "Sama-sama kak!", "idle", "idle"),
    ("siap kak makasih ji", "terima_kasih", 0.86, "Sama-sama!", "idle", "idle"),

    # -------- INFO PEMBAYARAN (8) --------
    ("bayar pakai apa ji kak?", "info_pembayaran", 0.89, "Bisa transfer atau e-wallet kak.", "idle", "idle"),
    ("cara bayar gimana kak?", "info_pembayaran", 0.87, "Transfer BCA/BRI/GoPay/OVO.", "idle", "idle"),
    ("bisa bayar di tempat ki kak?", "info_pembayaran", 0.84, "Bisa bayar saat ambil kak!", "idle", "idle"),
    ("engka ji gopay?", "info_pembayaran", 0.82, "Ada kak, bisa GoPay!", "idle", "idle"),
    ("terima ji transfer kak?", "info_pembayaran", 0.85, "Iya, bisa transfer kak.", "idle", "idle"),
    ("pembayaran apa ji ada kak?", "info_pembayaran", 0.88, "Transfer bank/e-wallet kak.", "idle", "idle"),
    ("ovo bisa ji kak?", "info_pembayaran", 0.83, "Bisa OVO kak!", "idle", "idle"),
    ("cod bisa kak?", "info_pembayaran", 0.80, "Bayar di tempat pengambilan ya kak.", "idle", "idle"),

    # -------- INFO JAM & LOKASI (6) --------
    ("jam berapa ji buka kak?", "info_jam", 0.87, "Buka 09.00 - 21.00 kak.", "idle", "idle"),
    ("tutup jam berapa kak?", "info_jam", 0.85, "Tutup jam 21.00 kak.", "idle", "idle"),
    ("alamat ji kak dimana?", "lokasi", 0.86, "Jl. Merdeka No.1 kak.", "idle", "idle"),
    ("lokasi ko kak?", "lokasi", 0.83, "Jl. Merdeka No.1, bisa lihat di Maps.", "idle", "idle"),
    ("masih buka mi kak?", "info_jam", 0.80, "Masih buka sampai jam 21.00!", "idle", "idle"),
    ("ditempat aga kak?", "lokasi", 0.75, "Di Jl. Merdeka No.1 kak.", "idle", "idle"),

    # -------- BATALKAN / UBAH (5) --------
    ("batal ji pesanan ku kak", "batalkan_pesanan", 0.87, "Oke, dibatalkan ya kak.", "idle", "idle"),
    ("de jadi mi kak, cancel pale", "batalkan_pesanan", 0.84, "Baik, pesanan dibatalkan.", "idle", "idle"),
    ("ganti ji pesanan ku kak", "ubah_pesanan", 0.81, "Mau diganti jadi apa kak?", "idle", "modifying"),
    ("edit pale pesanan ku kak", "ubah_pesanan", 0.79, "Silakan, diganti jadi apa?", "idle", "modifying"),
    ("de jadi kak pesan mi", "batalkan_pesanan", 0.76, "Baik, pesanan dibatalkan ya kak.", "idle", "idle"),

    # -------- UNKNOWN / AMBIGU (8) --------
    ("aga ko kak?", "unknown", 0.40, "Maaf kak, bisa diulang?", "idle", "idle"),                            # aga ko = kamu siapa
    ("engka pallawa?", "unknown", 0.35, "Maaf kak, kurang mengerti.", "idle", "idle"),
    ("cuaca sore ini kak?", "unknown", 0.28, "Maaf, saya hanya bisa bantu pesan makanan.", "idle", "idle"),
    ("harga minyak goreng kak?", "unknown", 0.22, "Maaf kak, itu di luar menu kami.", "idle", "idle"),
    ("mammak de engka?", "unknown", 0.48, "Maaf kak, bisa diulang ya?", "idle", "idle"),
    ("boleh minta nomormu kak?", "unknown", 0.33, "Maaf kak, saya hanya bisa bantu pesan.", "idle", "idle"),
    ("rekomen aga mi kak?", "rekomendasi_menu", 0.70, "Kami rekomendasikan Ayam Geprek kak!", "idle", "idle"), # aga = apa
    ("menu aga ji ada kak?", "rekomendasi_menu", 0.68, "Ada geprek, bakar, goreng, dll kak!", "idle", "idle"),
]

insert_q = """
    INSERT INTO chat_logs 
    (id_pelanggan, nama_pelanggan, pesan_masuk, intent_terdeteksi, confidence_score,
     entities_extracted, pesan_keluar, state_sebelumnya, state_setelahnya, waktu_interaksi)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

pelanggan_ids = [p[0] for p in pelanggan_dummy]
base_time = datetime(2026, 3, 9, 8, 0, 0)
sukses = 0

for i, (pesan, intent, conf, balasan, sb, sa) in enumerate(SAMPLES):
    pid  = random.choice(pelanggan_ids)
    nama = next(n for p, n in pelanggan_dummy if p == pid)
    waktu = base_time + timedelta(minutes=i * 9 + random.randint(0, 4))
    try:
        cur.execute(insert_q, (pid, nama, pesan, intent, conf, '{}', balasan, sb, sa, waktu))
        sukses += 1
    except Exception as e:
        print(f"[SKIP] {pesan}: {e}")

conn.commit()
cur.close()
conn.close()
print(f"[OK] Berhasil insert {sukses}/{len(SAMPLES)} baris")
print("[INFO] Jalankan: python export_railway.py")
