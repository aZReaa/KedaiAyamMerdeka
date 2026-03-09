"""
=======================================================
  Evaluasi Teknis Chatbot - Kedai Ayam Merdeka
  Metrik: Precision, Recall, F1-Score per Intent
=======================================================

Cara penggunaan:
  1. Jalankan: python evaluasi.py
  2. Script akan membaca chat_logs dari database
  3. Anda akan diminta menandai intent BENAR/SALAH satu per satu
     (atau bisa langsung pakai mode auto jika ada label aktual)

Mode:
  - Mode MANUAL  : Anda menilai setiap prediksi intent secara interaktif
  - Mode CSV     : Simpan hasil ke CSV lalu hitung metrik dari file
"""

import sys
import os
import csv
import json
from collections import defaultdict

# Tambahkan path proyek agar bisa import config & database
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
import mysql.connector
from mysql.connector import Error


# ==================== KONEKSI DATABASE ====================

def get_connection():
    print("\nPilih database:")
    print("  1. Lokal (Laragon) - localhost")
    print("  2. Railway (production)")
    db_pilihan = input("Koneksi [1/2]: ").strip()

    if db_pilihan == '2':
        print("\nMasukkan konfigurasi Railway:")
        host     = input("  Host     : ").strip()
        user     = input("  User     : ").strip()
        password = input("  Password : ").strip()
        database = input("  Database : ").strip()
        port_str = input("  Port [default: 3306]: ").strip()
        port     = int(port_str) if port_str.isdigit() else 3306
    else:
        host     = Config.DB_HOST
        user     = Config.DB_USER
        password = Config.DB_PASSWORD
        database = Config.DB_NAME
        port     = 3306

    try:
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port
        )
        print(f"[OK] Terhubung ke database '{database}' di {host}:{port}")
        return conn
    except Error as e:
        print(f"[ERROR] Gagal koneksi database: {e}")
        sys.exit(1)


def get_chat_logs(conn, limit=500):
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id_log, pesan_masuk, intent_terdeteksi, confidence_score
        FROM chat_logs
        WHERE intent_terdeteksi IS NOT NULL
        ORDER BY waktu_interaksi DESC
        LIMIT %s
    """, (limit,))
    rows = cursor.fetchall()
    cursor.close()
    return rows


# ==================== HITUNG METRIK ====================

def hitung_metrik(data):
    """
    data: list of dict {'predicted': str, 'actual': str}
    Return: dict per intent {precision, recall, f1, tp, fp, fn}
    """
    intents = set()
    for d in data:
        intents.add(d['predicted'])
        intents.add(d['actual'])

    hasil = {}
    for intent in sorted(intents):
        tp = sum(1 for d in data if d['predicted'] == intent and d['actual'] == intent)
        fp = sum(1 for d in data if d['predicted'] == intent and d['actual'] != intent)
        fn = sum(1 for d in data if d['predicted'] != intent and d['actual'] == intent)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1        = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        hasil[intent] = {
            'TP': tp, 'FP': fp, 'FN': fn,
            'Precision': round(precision, 4),
            'Recall':    round(recall, 4),
            'F1-Score':  round(f1, 4),
        }
    return hasil


def hitung_macro_avg(hasil):
    if not hasil:
        return {'Precision': 0, 'Recall': 0, 'F1-Score': 0}
    p = sum(v['Precision'] for v in hasil.values()) / len(hasil)
    r = sum(v['Recall']    for v in hasil.values()) / len(hasil)
    f = sum(v['F1-Score']  for v in hasil.values()) / len(hasil)
    return {'Precision': round(p,4), 'Recall': round(r,4), 'F1-Score': round(f,4)}


# ==================== TAMPILAN ====================

def cetak_tabel(hasil):
    header = f"{'Intent':<25} {'TP':>4} {'FP':>4} {'FN':>4}  {'Precision':>10} {'Recall':>8} {'F1-Score':>9}"
    print("\n" + "=" * len(header))
    print(header)
    print("=" * len(header))
    for intent, m in hasil.items():
        print(f"{intent:<25} {m['TP']:>4} {m['FP']:>4} {m['FN']:>4}  "
              f"{m['Precision']:>10.4f} {m['Recall']:>8.4f} {m['F1-Score']:>9.4f}")
    print("=" * len(header))

    macro = hitung_macro_avg(hasil)
    print(f"{'MACRO AVG':<25} {'':>4} {'':>4} {'':>4}  "
          f"{macro['Precision']:>10.4f} {macro['Recall']:>8.4f} {macro['F1-Score']:>9.4f}")
    print("=" * len(header))


def simpan_csv(hasil, path="hasil_evaluasi.csv"):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Intent','TP','FP','FN','Precision','Recall','F1-Score'])
        writer.writeheader()
        for intent, m in hasil.items():
            writer.writerow({'Intent': intent, **m})
        macro = hitung_macro_avg(hasil)
        writer.writerow({'Intent': 'MACRO AVG', 'TP': '', 'FP': '', 'FN': '', **macro})
    print(f"\n[INFO] Hasil disimpan ke: {os.path.abspath(path)}")


# ==================== MODE MANUAL ====================

def mode_manual(logs):
    """
    User menilai setiap prediksi: apakah intent benar atau salah,
    jika salah masukkan intent yang sebenarnya.
    """
    intents_dikenal = sorted(set(r['intent_terdeteksi'] for r in logs))
    print("\nDaftar intent yang dikenal:")
    for i, t in enumerate(intents_dikenal, 1):
        print(f"  {i:>2}. {t}")

    data = []
    total = len(logs)
    print(f"\nTotal sampel: {total} interaksi")
    print("Tekan ENTER = benar | Ketik intent lain = salah | 'q' = selesai\n")

    for idx, row in enumerate(logs, 1):
        predicted = row['intent_terdeteksi']
        conf = float(row['confidence_score'] or 0)
        print(f"[{idx}/{total}] Pesan   : {row['pesan_masuk'][:70]}")
        print(f"         Prediksi: {predicted}  (confidence: {conf:.2f})")
        jawab = input("         Aktual  : ").strip()

        if jawab.lower() == 'q':
            print("[INFO] Evaluasi dihentikan oleh pengguna.")
            break
        elif jawab == '':
            actual = predicted  # benar
        else:
            actual = jawab

        data.append({'predicted': predicted, 'actual': actual})
        print()

    return data


# ==================== MODE DARI CSV ====================

def mode_dari_csv(path):
    """
    Baca file CSV dengan kolom: predicted, actual
    """
    data = []
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({'predicted': row['predicted'].strip(),
                         'actual':    row['actual'].strip()})
    print(f"[INFO] Membaca {len(data)} baris dari {path}")
    return data


# ==================== MAIN ====================

def main():
    print("=" * 55)
    print("   EVALUASI TEKNIS CHATBOT - Kedai Ayam Merdeka")
    print("   Metrik: Precision | Recall | F1-Score")
    print("=" * 55)
    print("\nPilih mode evaluasi:")
    print("  1. Manual  - nilai prediksi intent satu per satu dari DB")
    print("  2. CSV     - hitung dari file CSV (kolom: predicted, actual)")
    print("  3. Export  - ekspor chat_logs ke CSV untuk dilabeli manual")

    pilihan = input("\nPilihan [1/2/3]: ").strip()

    conn = get_connection()

    if pilihan == '1':
        limit = input("Berapa sampel terakhir? [default: 100]: ").strip()
        limit = int(limit) if limit.isdigit() else 100
        logs = get_chat_logs(conn, limit)
        if not logs:
            print("[WARN] Tidak ada data di chat_logs.")
            return
        data = mode_manual(logs)

    elif pilihan == '2':
        path = input("Path file CSV [default: labeled.csv]: ").strip() or "labeled.csv"
        if not os.path.exists(path):
            print(f"[ERROR] File tidak ditemukan: {path}")
            return
        data = mode_dari_csv(path)

    elif pilihan == '3':
        logs = get_chat_logs(conn, 1000)
        out = "chat_logs_export.csv"
        with open(out, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['id_log','pesan_masuk','predicted','actual'])
            writer.writeheader()
            for r in logs:
                writer.writerow({
                    'id_log':      r['id_log'],
                    'pesan_masuk': r['pesan_masuk'],
                    'predicted':   r['intent_terdeteksi'],
                    'actual':      ''  # diisi manual di Excel/spreadsheet
                })
        print(f"\n[INFO] Diekspor {len(logs)} baris ke: {os.path.abspath(out)}")
        print("[INFO] Isi kolom 'actual' secara manual, lalu jalankan Mode 2.")
        return

    else:
        print("[ERROR] Pilihan tidak valid.")
        return

    conn.close()

    if not data:
        print("[WARN] Tidak ada data untuk dihitung.")
        return

    # Hitung & tampilkan
    hasil = hitung_metrik(data)
    cetak_tabel(hasil)

    # Simpan ke CSV?
    simpan = input("\nSimpan hasil ke CSV? [y/N]: ").strip().lower()
    if simpan == 'y':
        out_path = input("Nama file [default: hasil_evaluasi.csv]: ").strip() or "hasil_evaluasi.csv"
        simpan_csv(hasil, out_path)


if __name__ == '__main__':
    main()
