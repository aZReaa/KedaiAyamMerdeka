"""
Fix: Hapus foreign key constraint di chat_logs agar log_chat_interaction
tidak pernah gagal akibat constraint violation.
"""
import mysql.connector

conn = mysql.connector.connect(
    host='turntable.proxy.rlwy.net',
    user='root',
    password='TAKbTTsWlfbWUcJlwqjsakiOAGHcKkWe',
    database='railway',
    port=39744
)
cur = conn.cursor()

# 1. Hapus FK constraint
try:
    cur.execute('ALTER TABLE chat_logs DROP FOREIGN KEY chat_logs_ibfk_1')
    conn.commit()
    print('[OK] Foreign key constraint chat_logs_ibfk_1 dihapus')
except Exception as e:
    print(f'[INFO] {e}')

# 2. Pastikan tidak ada constraint tersisa
cur.execute("""
    SELECT CONSTRAINT_NAME 
    FROM information_schema.KEY_COLUMN_USAGE
    WHERE TABLE_SCHEMA = 'railway' 
      AND TABLE_NAME = 'chat_logs' 
      AND REFERENCED_TABLE_NAME IS NOT NULL
""")
remaining = cur.fetchall()
if remaining:
    print(f'[WARN] Masih ada constraint: {remaining}')
else:
    print('[OK] Tidak ada FK constraint tersisa di chat_logs')

# 3. Test insert tanpa pelanggan terdaftar
try:
    cur.execute("""
        INSERT INTO chat_logs 
        (id_pelanggan, nama_pelanggan, pesan_masuk, intent_terdeteksi, 
         confidence_score, entities_extracted, pesan_keluar, state_sebelumnya, state_setelahnya)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, ('test_free', 'Test', 'halo', 'salam', 0.95, '{}', 'Halo!', 'idle', 'idle'))
    conn.commit()
    print('[OK] Insert test berhasil - logging sekarang akan bekerja')
    
    # Hapus data test
    cur.execute("DELETE FROM chat_logs WHERE id_pelanggan = 'test_free'")
    conn.commit()
    print('[OK] Data test dihapus')
except Exception as e:
    print(f'[ERROR] {e}')

cur.close()
conn.close()
print('\nSelesai! Restart app Railway agar perubahan efektif.')
