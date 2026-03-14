import csv

def hitung_metrik(data):
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
            'Recall':    round(recall,    4),
            'F1':        round(f1,        4)
        }
    return hasil

data = []
with open('labeled.csv', newline='', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        data.append({'predicted': row['predicted'].strip(), 'actual': row['actual'].strip()})

hasil = hitung_metrik(data)

header = f"{'Intent':<22} {'TP':>4} {'FP':>4} {'FN':>4}  {'Precision':>9} {'Recall':>7} {'F1-Score':>8}"
sep    = "=" * len(header)
print()
print(sep)
print(header)
print(sep)
for intent, m in hasil.items():
    print(f"{intent:<22} {m['TP']:>4} {m['FP']:>4} {m['FN']:>4}  {m['Precision']:>9.4f} {m['Recall']:>7.4f} {m['F1']:>8.4f}")
print(sep)

p = sum(v['Precision'] for v in hasil.values()) / len(hasil)
r = sum(v['Recall']    for v in hasil.values()) / len(hasil)
f = sum(v['F1']        for v in hasil.values()) / len(hasil)
print(f"{'MACRO AVG':<22} {'':>4} {'':>4} {'':>4}  {p:>9.4f} {r:>7.4f} {f:>8.4f}")
print(sep)
print(f"Total sampel: {len(data)}")
