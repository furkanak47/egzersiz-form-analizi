"""
Gida veritabani — USDA food_db.csv uzerinde arama.
453K gida, 100g basina kcal/protein/carb/fat/fiber.
"""

import pandas as pd
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / 'veri' / 'beslenme' / 'food_db.csv'

# Oncelikli data type'lar aramada once gelir
_PRIORITY = {'turkish_food': 0,
             'sr_legacy_food': 1, 'foundation_food': 2,
             'survey_fndds_food': 3, 'branded_food': 4}

_df: pd.DataFrame | None = None


def load():
    """food_db.csv'yi bellegee yukle. Bir kez cagrilmasi yeterli."""
    global _df
    if _df is not None:
        return
    if not DB_PATH.exists():
        print("UYARI: food_db.csv bulunamadi — beslenmedata/build_food_db.py calistirin")
        _df = pd.DataFrame(columns=['fdc_id','name','category','data_type',
                                    'kcal','protein_g','carb_g','fat_g','fiber_g'])
        return

    print("Gida veritabani yukleniyor (453K gida)...")
    _df = pd.read_csv(DB_PATH, dtype={
        'fdc_id': 'int32',
        'kcal':       'float32',
        'protein_g':  'float32',
        'carb_g':     'float32',
        'fat_g':      'float32',
        'fiber_g':    'float32',
    })
    _df['_prio'] = _df['data_type'].map(_PRIORITY).fillna(3).astype('int8')
    print("  %d gida yuklendi" % len(_df))


def search(query: str, limit: int = 20) -> list[dict]:
    """
    Gida adi icinde arama yapar.
    Dondurur: [{'fdc_id', 'name', 'category', 'kcal', 'protein_g', 'carb_g', 'fat_g', 'fiber_g'}, ...]
    Her deger 100g basina.
    """
    if _df is None or _df.empty:
        return []

    q = query.strip().lower()
    if not q:
        return []

    # Tum kelimelerin isimde gecmesini ara (AND mantigi)
    words = q.split()
    mask = pd.Series([True] * len(_df), index=_df.index)
    for w in words:
        mask &= _df['name'].str.lower().str.contains(w, na=False, regex=False)

    hits = _df[mask].sort_values('_prio')
    results = []
    for _, row in hits.head(limit).iterrows():
        results.append({
            'fdc_id':    int(row['fdc_id']),
            'name':      str(row['name']),
            'category':  str(row['category']),
            'kcal':      float(row['kcal']),
            'protein_g': float(row['protein_g']),
            'carb_g':    float(row['carb_g']),
            'fat_g':     float(row['fat_g']),
            'fiber_g':   float(row['fiber_g']),
        })
    return results


def get_by_id(fdc_id: int) -> dict | None:
    """fdc_id ile tek gida dondurur."""
    if _df is None:
        return None
    row = _df[_df['fdc_id'] == fdc_id]
    if row.empty:
        return None
    r = row.iloc[0]
    return {
        'fdc_id':    int(r['fdc_id']),
        'name':      str(r['name']),
        'category':  str(r['category']),
        'kcal':      float(r['kcal']),
        'protein_g': float(r['protein_g']),
        'carb_g':    float(r['carb_g']),
        'fat_g':     float(r['fat_g']),
        'fiber_g':   float(r['fiber_g']),
    }


def nutrients_for_grams(food: dict, grams: float) -> dict:
    """100g baz degerlerini verilen gram miktarina gore olcekler."""
    import math
    def _safe(v):
        x = v or 0.0
        return 0.0 if math.isnan(x) else x

    ratio = grams / 100.0
    return {
        'kcal':      round(_safe(food['kcal'])      * ratio, 1),
        'protein_g': round(_safe(food['protein_g']) * ratio, 1),
        'carb_g':    round(_safe(food['carb_g'])    * ratio, 1),
        'fat_g':     round(_safe(food['fat_g'])     * ratio, 1),
        'fiber_g':   round(_safe(food.get('fiber_g', 0)) * ratio, 1),
    }
