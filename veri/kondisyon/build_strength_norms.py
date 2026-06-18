"""
OpenPowerlifting verisinden guc persentil tablosu olusturur.
Cikti: strength_norms.csv  (sex, bw_bin, lift, p10..p90, count)

Duzeltmeler:
- Squat/bench/deadlift: kendi event'lerini yapan sporculardan
- Dots: sadece SBD (tam gucalkis) sporcularindan, bw_bin='all' (zaten normalize)
"""

import pandas as pd
import numpy as np
from pathlib import Path

HERE = Path(__file__).parent

# Ham veriyi bul
csv_file = None
root = HERE.parent
for folder in root.iterdir():
    if not folder.is_dir():
        continue
    for f in folder.iterdir():
        if f.suffix == '.csv' and 'openpowerlifting' in f.name:
            csv_file = f
            break
    if csv_file is None:
        for sub in folder.iterdir():
            if sub.is_dir():
                for f in sub.iterdir():
                    if f.suffix == '.csv' and 'openpowerlifting' in f.name:
                        csv_file = f
                        break
    if csv_file:
        break

if csv_file is None:
    raise FileNotFoundError("openpowerlifting CSV bulunamadi -- klasoru kontrol et")

print("Kaynak: %s" % csv_file.name)

COLS = ['Sex', 'Equipment', 'BodyweightKg', 'Event',
        'Best3SquatKg', 'Best3BenchKg', 'Best3DeadliftKg',
        'TotalKg', 'Dots', 'Tested']

print("Veri okunuyor (767MB, ~30sn)...")
df = pd.read_csv(csv_file, usecols=COLS, low_memory=False)
print("Toplam kayit: %s" % f"{len(df):,}")

# Temel filtreler
df = df[df['Tested'] == 'Yes']
df = df[df['Sex'].isin(['M', 'F'])]
df = df[df['BodyweightKg'].between(40, 200)]
df = df[df['Equipment'] == 'Raw']
print("Filtre sonrasi: %s" % f"{len(df):,}")

# Vucut agirligini grupla
BW_BINS   = list(range(40, 161, 5)) + [200]
BW_LABELS = ["%s-%s" % (BW_BINS[i], BW_BINS[i+1]) for i in range(len(BW_BINS)-1)]
df['bw_bin'] = pd.cut(df['BodyweightKg'], bins=BW_BINS, labels=BW_LABELS, right=False)

# Her lift hangi event'lerden alinacak
LIFT_EVENTS = {
    'squat':    ['SBD', 'SD', 'SB', 'S'],
    'bench':    ['SBD', 'BD', 'SB', 'B'],
    'deadlift': ['SBD', 'BD', 'SD', 'D'],
    'total':    ['SBD'],
}
LIFT_COLS = {
    'squat':    'Best3SquatKg',
    'bench':    'Best3BenchKg',
    'deadlift': 'Best3DeadliftKg',
    'total':    'TotalKg',
}

PERCENTILES = [10, 25, 50, 75, 90]
rows = []

for sex in ['M', 'F']:
    sub = df[df['Sex'] == sex]

    # Bireysel kaldirish + total (vucut agirligina gore gruplu)
    for lift_name, col in LIFT_COLS.items():
        valid_events = LIFT_EVENTS[lift_name]
        lift_sub = sub[sub['Event'].isin(valid_events)]
        valid = lift_sub[lift_sub[col] > 0][['bw_bin', col]].dropna()
        grouped = valid.groupby('bw_bin', observed=True)[col]
        for bw_bin, group in grouped:
            if len(group) < 20:
                continue
            row = {'sex': sex, 'bw_bin': str(bw_bin), 'lift': lift_name, 'count': len(group)}
            for p in PERCENTILES:
                row['p%d' % p] = round(float(np.percentile(group, p)), 1)
            rows.append(row)

    # Dots: SADECE SBD, vucut agirligina bakilmadan (zaten normalize)
    sbd_sub = sub[(sub['Event'] == 'SBD') & (sub['Dots'] > 0)]['Dots'].dropna()
    if len(sbd_sub) >= 20:
        row = {'sex': sex, 'bw_bin': 'all', 'lift': 'dots', 'count': len(sbd_sub)}
        for p in PERCENTILES:
            row['p%d' % p] = round(float(np.percentile(sbd_sub, p)), 1)
        rows.append(row)
        print("  %s Dots (SBD only): %s sporcu, p50=%.1f" % (
            sex, f"{len(sbd_sub):,}", float(np.percentile(sbd_sub, 50))))

norms = pd.DataFrame(rows)
out_path = HERE / 'strength_norms.csv'
norms.to_csv(out_path, index=False)
print("\nKaydedildi: %s" % out_path)
print("Toplam satir: %d" % len(norms))

print("\nOrnek (erkek bench, 80-85kg grubu):")
sample = norms[(norms['sex']=='M') & (norms['bw_bin']=='80-85') & (norms['lift']=='bench')]
if not sample.empty:
    print(sample.to_string(index=False))

print("\nOrnek (erkek dots, tum agirliklar):")
sample = norms[(norms['sex']=='M') & (norms['bw_bin']=='all') & (norms['lift']=='dots')]
if not sample.empty:
    print(sample.to_string(index=False))
