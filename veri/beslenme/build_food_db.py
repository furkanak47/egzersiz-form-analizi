"""
USDA FoodData Central (2.1M gida) -> compact food_db.csv
Cikti: fdc_id, name, category, data_type, kcal, protein_g, carb_g, fat_g, fiber_g
Her deger 100g basina.
"""

import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path(__file__).parent / "FoodData_Central_csv_2026-04-30"
OUT_PATH  = Path(__file__).parent / "food_db.csv"

# Hedef nutrient ID'leri
ENERGY_IDS   = {1008, 2047, 2048}     # kcal (birden fazla hesaplama yontemi)
NUTRIENT_MAP = {
    1003: 'protein_g',
    1005: 'carb_g',
    1004: 'fat_g',
    1079: 'fiber_g',
}
TARGET_IDS = ENERGY_IDS | set(NUTRIENT_MAP.keys())

# ── 1. Gida listesi ──────────────────────────────────────────────────────────
print("Gida listesi okunuyor...")
food = pd.read_csv(
    DATA_DIR / 'food.csv',
    usecols=['fdc_id', 'data_type', 'description', 'food_category_id'],
    dtype={'fdc_id': 'int32'},
)
print("  %s gida" % f"{len(food):,}")

# Genel kategori map
cat = pd.read_csv(DATA_DIR / 'food_category.csv')
cat_map = dict(zip(cat['id'].astype(int), cat['description']))
def _cat(x):
    try:
        return cat_map.get(int(float(x)), '')
    except (ValueError, TypeError):
        return str(x) if pd.notna(x) else ''

food['category'] = food['food_category_id'].map(_cat)

# Branded gidalar icin daha aciklayici kategori
print("  Branded kategori okunuyor...")
branded = pd.read_csv(
    DATA_DIR / 'branded_food.csv',
    usecols=['fdc_id', 'branded_food_category'],
    dtype={'fdc_id': 'int32'},
)
branded_cat = dict(zip(branded['fdc_id'], branded['branded_food_category'].fillna('')))
branded_mask = food['data_type'] == 'branded_food'
food.loc[branded_mask, 'category'] = food.loc[branded_mask, 'fdc_id'].map(
    lambda x: branded_cat.get(x, '')
)
del branded, branded_cat

# ── 2. Besin degerleri — 1.7GB chunk'larla ──────────────────────────────────
print("Besin degerleri isleniyor (1.7GB, yaklasik 2-3 dakika)...")

CHUNK   = 500_000
chunks  = []
total   = 0

reader = pd.read_csv(
    DATA_DIR / 'food_nutrient.csv',
    usecols=['fdc_id', 'nutrient_id', 'amount'],
    dtype={'fdc_id': 'int32', 'nutrient_id': 'int32', 'amount': 'float32'},
    chunksize=CHUNK,
)

for i, chunk in enumerate(reader):
    filtered = chunk[chunk['nutrient_id'].isin(TARGET_IDS)][['fdc_id', 'nutrient_id', 'amount']]
    if len(filtered):
        chunks.append(filtered)
    total += len(chunk)
    if (i + 1) % 20 == 0:
        kept = sum(len(c) for c in chunks)
        print("  %s satir islendi, %s satir tutuldu..." % (
            f"{total:,}", f"{kept:,}"))

print("  Toplam %s satir islendi" % f"{total:,}")

all_nut = pd.concat(chunks, ignore_index=True)
del chunks
print("  %s alakali satir bulundu" % f"{len(all_nut):,}")

# ── 3. Pivot: fdc_id x nutrient_id -> amount ────────────────────────────────
print("Pivot tablosu olusturuluyor...")
pivot = all_nut.pivot_table(
    index='fdc_id',
    columns='nutrient_id',
    values='amount',
    aggfunc='max',    # birden fazla kayit varsa en buyugunu al
)
del all_nut

# Energy: 3 farkli ID'nin max'i
energy_cols = [c for c in pivot.columns if c in ENERGY_IDS]
if energy_cols:
    pivot['kcal'] = pivot[energy_cols].max(axis=1)
else:
    pivot['kcal'] = np.nan

# Diger makrolar
for nid, col in NUTRIENT_MAP.items():
    pivot[col] = pivot[nid] if nid in pivot.columns else np.nan

result_nut = pivot[['kcal', 'protein_g', 'carb_g', 'fat_g', 'fiber_g']].reset_index()
del pivot

# ── 4. Birlestir ─────────────────────────────────────────────────────────────
print("Birlestiriliyor...")
result = food.merge(result_nut, on='fdc_id', how='inner')
del result_nut, food

# ── 5. Filtrele ──────────────────────────────────────────────────────────────
# Kalori zorunlu
result = result[result['kcal'] > 0].copy()

# Branded: protein + carb + fat da olmali (eksik veri cok var)
bm = result['data_type'] == 'branded_food'
complete = (result['protein_g'].notna() &
            result['carb_g'].notna() &
            result['fat_g'].notna())
result = result[~bm | complete].copy()

# Eksikleri 0 yap
for col in ['protein_g', 'carb_g', 'fat_g', 'fiber_g']:
    result[col] = result[col].fillna(0)

# Makul araliklar (100g basina)
result = result[
    (result['kcal']      <= 1000) &   # 100g'da 1000 kcal ust sinir (yagsizlar icin)
    (result['protein_g'] <= 100)  &
    (result['carb_g']    <= 100)  &
    (result['fat_g']     <= 100)
].copy()

# ── 6. Son bicim ─────────────────────────────────────────────────────────────
result = result[['fdc_id', 'description', 'category', 'data_type',
                 'kcal', 'protein_g', 'carb_g', 'fat_g', 'fiber_g']].copy()
result.columns = ['fdc_id', 'name', 'category', 'data_type',
                  'kcal', 'protein_g', 'carb_g', 'fat_g', 'fiber_g']

for col in ['kcal', 'protein_g', 'carb_g', 'fat_g', 'fiber_g']:
    result[col] = result[col].round(1)

# ── 7. Tekilleştir ───────────────────────────────────────────────────────────
# Oncelik sirasi: sr_legacy > foundation > survey_fndds > branded
PRIORITY = {'sr_legacy_food': 0, 'foundation_food': 1,
            'survey_fndds_food': 2, 'branded_food': 3}
result['_prio'] = result['data_type'].map(PRIORITY).fillna(9).astype(int)
result = result.sort_values(['_prio', 'name']).reset_index(drop=True)

# Ayni isimde birden fazla kayit varsa daha kaliteli data_type'i tut
result['_name_lower'] = result['name'].str.lower().str.strip()
result = result.drop_duplicates(subset='_name_lower', keep='first')
result = result.drop(columns=['_prio', '_name_lower'])

# ── 8. Kaydet ────────────────────────────────────────────────────────────────
result.to_csv(OUT_PATH, index=False)

print("\n=== TAMAMLANDI ===")
print("Toplam gida: %s" % f"{len(result):,}")
print()
print("data_type dagilimi:")
print(result['data_type'].value_counts().to_string())
print()
size_mb = OUT_PATH.stat().st_size / 1024 / 1024
print("Dosya boyutu: %.1fMB -> %s" % (size_mb, OUT_PATH.name))
print()
print("Ornek (tavuk gogus):")
sample = result[result['name'].str.lower().str.contains('chicken breast', na=False)].head(3)
print(sample[['name','kcal','protein_g','carb_g','fat_g']].to_string(index=False))
