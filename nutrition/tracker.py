"""
Gunluk besin kaydı — profil bazlı JSON depolama.
nutrition_logs.json: {profile_name: {YYYY-MM-DD: [entry, ...]}}
"""

import json
from datetime import date
from pathlib import Path
from .food_db import nutrients_for_grams

LOG_PATH = Path(__file__).parent.parent / 'kullanici_verisi' / 'nutrition_logs.json'


def _load_raw() -> dict:
    if LOG_PATH.exists():
        try:
            return json.loads(LOG_PATH.read_text(encoding='utf-8'))
        except Exception:
            return {}
    return {}


def _save_raw(data: dict):
    LOG_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def today_str() -> str:
    return date.today().isoformat()


def get_log(profile_name: str, day: str | None = None) -> list[dict]:
    """
    Verilen gun icin yemek listesi dondurur.
    Her entry: {fdc_id, name, grams, kcal, protein_g, carb_g, fat_g, fiber_g}
    """
    if day is None:
        day = today_str()
    raw = _load_raw()
    return raw.get(profile_name, {}).get(day, [])


def add_entry(profile_name: str, food: dict, grams: float, day: str | None = None):
    """
    Yemek kaydı ekler.
    food: food_db.search() veya get_by_id() ciktisi (100g degerleri)
    """
    if day is None:
        day = today_str()
    raw = _load_raw()
    raw.setdefault(profile_name, {}).setdefault(day, [])

    scaled = nutrients_for_grams(food, grams)
    entry = {
        'fdc_id':    food['fdc_id'],
        'name':      food['name'],
        'grams':     round(grams, 0),
        **scaled,
    }
    raw[profile_name][day].append(entry)
    _save_raw(raw)
    return entry


def remove_last(profile_name: str, day: str | None = None) -> dict | None:
    """Son eklenen kaydi siler, silinen entry'i dondurur."""
    if day is None:
        day = today_str()
    raw = _load_raw()
    entries = raw.get(profile_name, {}).get(day, [])
    if not entries:
        return None
    removed = entries.pop()
    _save_raw(raw)
    return removed


def daily_totals(entries: list[dict]) -> dict:
    """Gunluk toplam besin degerlerini hesaplar."""
    import math
    totals = {'kcal': 0.0, 'protein_g': 0.0, 'carb_g': 0.0, 'fat_g': 0.0, 'fiber_g': 0.0}
    for e in entries:
        for k in totals:
            v = e.get(k, 0) or 0
            if not math.isnan(v):
                totals[k] += v
    return {k: round(v, 1) for k, v in totals.items()}


def add_exercise_burn(profile_name: str, exercise_id: str,
                      kcal_burned: float, day: str | None = None):
    """Egzersiz kalori yakimini kaydet (negatif entry olarak)."""
    if day is None:
        day = today_str()
    raw = _load_raw()
    raw.setdefault(profile_name, {}).setdefault(day, [])
    entry = {
        'fdc_id':    -1,
        'name':      'Egzersiz: %s' % exercise_id,
        'grams':     0,
        'kcal':      -abs(kcal_burned),
        'protein_g': 0, 'carb_g': 0, 'fat_g': 0, 'fiber_g': 0,
    }
    raw[profile_name][day].append(entry)
    _save_raw(raw)
    return entry
