"""Export chat_logs dari Railway langsung ke CSV tanpa input manual."""
import mysql.connector
import csv, os

conn = mysql.connector.connect(
    host='turntable.proxy.rlwy.net',
    user='root',
    password='TAKbTTsWlfbWUcJlwqjsakiOAGHcKkWe',
    database='railway',
    port=39744
)
cur = conn.cursor(dictionary=True)
cur.execute("""
    SELECT id_log, pesan_masuk, intent_terdeteksi AS predicted, confidence_score, waktu_interaksi
    FROM chat_logs
    ORDER BY waktu_interaksi DESC
    LIMIT 1000
""")
rows = cur.fetchall()
conn.close()

out = 'chat_logs_export.csv'
with open(out, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['id_log','pesan_masuk','predicted','actual','confidence_score','waktu_interaksi'])
    writer.writeheader()
    for r in rows:
        writer.writerow({
            'id_log': r['id_log'],
            'pesan_masuk': r['pesan_masuk'],
            'predicted': r['predicted'],
            'actual': '',
            'confidence_score': r['confidence_score'],
            'waktu_interaksi': r['waktu_interaksi'],
        })

print(f'[OK] Diekspor {len(rows)} baris ke: {os.path.abspath(out)}')
