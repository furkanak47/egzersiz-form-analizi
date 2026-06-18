"""
Open Food Facts -> Turkiye filtresi.
Kullanim:
    python beslenmedata/build_off_turkey.py --csv yol/en.openfoodfacts.org.products.csv

Cikti: beslenmedata/off_turkey.csv  (food_db.csv ile ayni format)
Ayrica mevcut food_db.csv'ye ekler.

Gereksinimler:
    pip install pandas tqdm
"""

import argparse
import pandas as pd
from pathlib import Path

OUT       = Path(__file__).parent / "off_turkey.csv"
FOOD_DB   = Path(__file__).parent / "food_db.csv"
CHUNK     = 200_000

# OFF sutun adlari (buyuk dosyada tab-separated)
COLS_KEEP = [
    'code', 'product_name', 'countries_tags',
    'categories_tags',
    'energy-kcal_100g', 'proteins_100g',
    'carbohydrates_100g', 'fat_100g', 'fiber_100g',
]

# Turkiye filtreleme etiketleri
TR_TAGS = {'en:turkey', 'tr', 'turkiye', 'turkey'}


def _is_turkey(val: str) -> bool:
    if not isinstance(val, str):
        return False
    parts = {p.strip().lower() for p in val.split(',')}
    return bool(parts & TR_TAGS)


def _clean_name(val) -> str:
    return str(val).strip()[:120] if isinstance(val, str) else ''


def build(csv_path: str):
    path = Path(csv_path)
    if not path.exists():
        print("HATA: Dosya bulunamadi:", csv_path)
        return

    print("Open Food Facts isleniyor:", path)
    print("Boyut: %.1f GB" % (path.stat().st_size / 1e9))

    gz = path.suffix == '.gz'
    if gz:
        print("Gzip formati tespit edildi, sikiştirılmış okuma...")

    all_rows = []
    chunk_no = 0

    for chunk in pd.read_csv(
        path,
        sep='\t',
        compression='gzip' if gz else None,
        usecols=lambda c: c in COLS_KEEP,
        on_bad_lines='skip',
        dtype=str,
        chunksize=CHUNK,
        low_memory=False,
    ):
        chunk_no += 1
        if chunk_no % 5 == 0:
            print("  Chunk %d islendi, su ana kadar %d TR urunu..." % (chunk_no, len(all_rows)))

        # Turkiye filtresi
        if 'countries_tags' in chunk.columns:
            mask = chunk['countries_tags'].apply(_is_turkey)
        else:
            continue

        tr = chunk[mask].copy()
        if tr.empty:
            continue

        # Sayisal sutunlara cevir
        for col in ['energy-kcal_100g', 'proteins_100g',
                    'carbohydrates_100g', 'fat_100g', 'fiber_100g']:
            tr[col] = pd.to_numeric(tr.get(col, 0), errors='coerce')

        # Kalori ve protein zorunlu
        tr = tr.dropna(subset=['energy-kcal_100g', 'proteins_100g'])
        tr = tr[tr['energy-kcal_100g'] > 0]
        tr = tr[tr['energy-kcal_100g'] < 900]  # yag saf degilse

        for _, row in tr.iterrows():
            name = _clean_name(row.get('product_name', ''))
            if not name:
                continue
            all_rows.append({
                'fdc_id':    int(str(row.get('code', 0))[:9] or 0) + 8_000_000,
                'name':      name,
                'category':  'Turkish Branded',
                'data_type': 'off_turkey',
                'kcal':      round(float(row.get('energy-kcal_100g', 0)), 1),
                'protein_g': round(float(row.get('proteins_100g', 0) or 0), 1),
                'carb_g':    round(float(row.get('carbohydrates_100g', 0) or 0), 1),
                'fat_g':     round(float(row.get('fat_100g', 0) or 0), 1),
                'fiber_g':   round(float(row.get('fiber_100g', 0) or 0), 1),
            })

    if not all_rows:
        print("Hic Turkiye urunu bulunamadi. countries_tags sutunu kontrol edin.")
        return

    df = pd.DataFrame(all_rows)
    # Ayni isimli urunleri tekilestir
    df['_lower'] = df['name'].str.lower()
    df = df.drop_duplicates(subset='_lower').drop(columns='_lower')
    df = df.reset_index(drop=True)

    df.to_csv(OUT, index=False)
    print("\nKaydedildi: %s (%d urun)" % (OUT, len(df)))

    # Ana veritabanina ekle
    if FOOD_DB.exists():
        main = pd.read_csv(FOOD_DB)
        # Mevcut off_turkey kayitlarini cikar (tekrar eklememek icin)
        main = main[main['data_type'] != 'off_turkey']
        combined = pd.concat([
            main[main['data_type'] == 'turkish_food'],  # Turk ev yemekleri basta
            df,                                          # sonra markalı Turk
            main[main['data_type'] != 'turkish_food'],  # sonra USDA
        ], ignore_index=True)
        combined.to_csv(FOOD_DB, index=False)
        print("food_db.csv guncellendi: %d toplam urun" % len(combined))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--csv', required=True, help='Open Food Facts CSV dosyasi yolu')
    args = ap.parse_args()
    build(args.csv)
