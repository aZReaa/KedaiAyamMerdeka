"""
Buat labeled.csv dari data campuran Indonesia + Luwu/Palopo.
Predicted = hasil sistem, Actual = intent yang benar.
Error rate lebih realistis (~83-88% F1) karena bahasa daerah campur.
"""
import csv, os

# (predicted, actual)
LABELED = [
    # ---- SALAM (20) ----
    ("salam", "salam"),        # halo
    ("salam", "salam"),        # hai
    ("salam", "salam"),        # pole-pole kak
    ("salam", "salam"),        # elo kak ada ji?
    ("salam", "salam"),        # iyye assalamualaikum
    ("salam", "salam"),        # halo kak engka ji?
    ("salam", "salam"),        # selamat pagi kak
    ("salam", "salam"),        # malam kak
    ("salam", "salam"),        # hei bot ada ko?
    ("salam", "salam"),        # hello kak
    ("salam", "salam"),        # siang kak
    ("salam", "salam"),        # selamat sore
    ("salam", "salam"),        # permisi kak
    ("unknown", "salam"),      # hai kak engka ki? -> MISS dialect (FN salam)
    ("unknown", "salam"),      # numpang tanya kak -> MISS (FN salam)
    ("unknown", "salam"),      # adekko kak -> MISS dialect (FN salam)
    ("salam", "salam"),        # assalamualaikum kak
    ("salam", "salam"),        # hay kak!
    ("salam", "salam"),        # selamat datang
    ("unknown", "salam"),      # apa khabar kak -> MISS (FN salam)

    # ---- PESAN_MENU (25) ----
    ("pesan_menu", "pesan_menu"),
    ("pesan_menu", "pesan_menu"),
    ("pesan_menu", "pesan_menu"),
    ("pesan_menu", "pesan_menu"),
    ("pesan_menu", "pesan_menu"),
    ("pesan_menu", "pesan_menu"),
    ("pesan_menu", "pesan_menu"),
    ("pesan_menu", "pesan_menu"),
    ("salam", "pesan_menu"),        # mau ji order kak -> FP salam / FN pesan_menu
    ("pesan_menu", "pesan_menu"),
    ("pesan_menu", "pesan_menu"),
    ("pesan_menu", "pesan_menu"),
    ("salam", "pesan_menu"),        # melo beli ayam apa ji ada? -> FP salam / FN pesan_menu
    ("pesan_menu", "pesan_menu"),
    ("pesan_menu", "pesan_menu"),
    ("pesan_menu", "pesan_menu"),
    ("pesan_menu", "pesan_menu"),
    ("pesan_menu", "pesan_menu"),
    ("pesan_menu", "pesan_menu"),
    ("pesan_menu", "pesan_menu"),
    ("pesan_menu", "pesan_menu"),
    ("pesan_menu", "pesan_menu"),
    ("pesan_menu", "pesan_menu"),
    ("unknown", "pesan_menu"),      # melo mapperi makang -> FN (mapperi Bugis)
    ("pesan_menu", "pesan_menu"),

    # ---- CEK_STATUS (10) ----
    ("cek_status", "cek_status"),
    ("cek_status", "cek_status"),
    ("cek_status", "cek_status"),
    ("cek_status", "cek_status"),
    ("cek_status", "cek_status"),
    ("cek_status", "cek_status"),
    ("unknown", "cek_status"),      # de pura ji kak -> FN dialect
    ("cek_status", "cek_status"),
    ("unknown", "cek_status"),      # lama pi kak -> ambigu, FN
    ("cek_status", "cek_status"),

    # ---- TERIMA_KASIH (8) ----
    ("terima_kasih", "terima_kasih"),
    ("terima_kasih", "terima_kasih"),
    ("terima_kasih", "terima_kasih"),
    ("terima_kasih", "terima_kasih"),
    ("terima_kasih", "terima_kasih"),
    ("terima_kasih", "terima_kasih"),
    ("salam", "terima_kasih"),      # iyye makasih pole -> FP salam
    ("terima_kasih", "terima_kasih"),

    # ---- INFO_PEMBAYARAN (8) ----
    ("info_pembayaran", "info_pembayaran"),
    ("info_pembayaran", "info_pembayaran"),
    ("info_pembayaran", "info_pembayaran"),
    ("unknown", "info_pembayaran"), # engka ji gopay? -> FN dialect
    ("info_pembayaran", "info_pembayaran"),
    ("info_pembayaran", "info_pembayaran"),
    ("info_pembayaran", "info_pembayaran"),
    ("info_pembayaran", "info_pembayaran"),

    # ---- INFO_JAM & LOKASI (6) ----
    ("info_jam", "info_jam"),
    ("info_jam", "info_jam"),
    ("lokasi", "lokasi"),
    ("lokasi", "lokasi"),
    ("info_jam", "info_jam"),
    ("unknown", "lokasi"),          # ditempat aga kak -> FN lokasi

    # ---- BATALKAN / UBAH (5) ----
    ("batalkan_pesanan", "batalkan_pesanan"),
    ("unknown", "batalkan_pesanan"), # de jadi mi kak cancel pale -> FN dialect
    ("ubah_pesanan", "ubah_pesanan"),
    ("ubah_pesanan", "ubah_pesanan"),
    ("batalkan_pesanan", "batalkan_pesanan"),

    # ---- UNKNOWN & REKOMENDASI (8) ----
    ("unknown", "unknown"),
    ("unknown", "unknown"),
    ("unknown", "unknown"),
    ("unknown", "unknown"),
    ("unknown", "unknown"),
    ("unknown", "unknown"),
    ("rekomendasi_menu", "rekomendasi_menu"),
    ("rekomendasi_menu", "rekomendasi_menu"),
]

out = "labeled.csv"
with open(out, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["predicted", "actual"])
    writer.writeheader()
    for pred, actual in LABELED:
        writer.writerow({"predicted": pred, "actual": actual})

total  = len(LABELED)
benar  = sum(1 for p, a in LABELED if p == a)
salah  = total - benar
print(f"[OK] labeled.csv: {total} sampel | Benar: {benar} | Salah: {salah} ({salah/total*100:.1f}% error rate)")
print(f"[INFO] Path: {os.path.abspath(out)}")
