"""
Profil yonetimi — kullanici olcumlerini JSON dosyasinda saklar.
"""

import json
from pathlib import Path

PROFILE_FILE = Path(__file__).parent / "kullanici_verisi" / "profiles.json"

FIELDS = [
    # (key, label, zorunlu, unit, min, max)
    ("name",        "Profil Adi",         True,  "",    None, None),
    ("height_cm",   "Boy",                True,  "cm",  140,  220),
    ("weight_kg",   "Kilo",               True,  "kg",  30,   200),
    ("age",         "Yas",                True,  "",    15,   80),
    ("sex",         "Cinsiyet (E/K)",      True,  "",    None, None),
    ("activity",    "Aktivite (1-5)",      False, "",    None, None),
    ("waist_cm",    "Bel cevresi",         False, "cm",  45,   165),
    ("hip_cm",      "Kalca cevresi",       False, "cm",  50,   175),
    ("chest_cm",    "Gogus cevresi",       False, "cm",  60,   160),
    ("arm_cm",      "Kol cevresi (bic.)",  False, "cm",  15,   60),
    ("neck_cm",     "Boyun cevresi",       False, "cm",  25,   55),
]

_ACTIVITY_MAP = {
    '1': 'sedentary', '2': 'light', '3': 'moderate', '4': 'active', '5': 'very_active',
}

REQUIRED = [f[0] for f in FIELDS if f[2]]
OPTIONAL = [f[0] for f in FIELDS if not f[2]]


def _default():
    return []


def load_profiles():
    if not PROFILE_FILE.exists():
        return []
    try:
        with open(PROFILE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def save_profiles(profiles):
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(profiles, f, ensure_ascii=False, indent=2)


def add_profile(profile_dict):
    profiles = load_profiles()
    # Ayni isimde varsa uzerine yaz
    name = profile_dict.get("name", "").strip()
    profiles = [p for p in profiles if p.get("name", "") != name]
    profiles.append(profile_dict)
    save_profiles(profiles)


def delete_profile(name):
    profiles = load_profiles()
    profiles = [p for p in profiles if p.get("name", "") != name]
    save_profiles(profiles)


def get_profile(name):
    for p in load_profiles():
        if p.get("name", "") == name:
            return p
    return None


def validate_field(key, value_str):
    """
    Ham string degerini dogrulayip uygun tipe donusturur.
    Doner: (deger, hata_mesaji_veya_None)
    """
    meta = next((f for f in FIELDS if f[0] == key), None)
    if meta is None:
        return None, "Bilinmeyen alan"

    _, label, required, unit, vmin, vmax = meta

    if value_str.strip() == "":
        if required:
            return None, f"{label} zorunlu"
        return None, None  # opsiyonel, bos birakildi

    if key == "sex":
        v = value_str.strip().upper()
        if v in ("E", "M", "ERKEK"):
            return "M", None
        if v in ("K", "F", "KADIN"):
            return "F", None
        return None, "E veya K gir"

    if key == "activity":
        v = value_str.strip()
        if v in _ACTIVITY_MAP:
            return _ACTIVITY_MAP[v], None
        if v.lower() in _ACTIVITY_MAP.values():
            return v.lower(), None
        return None, "1=hareketsiz 2=az 3=orta 4=aktif 5=cok"

    if key == "name":
        return value_str.strip(), None

    try:
        v = float(value_str.replace(",", "."))
    except ValueError:
        return None, f"Sayi olmali"

    if vmin is not None and v < vmin:
        return None, f"Min {vmin}"
    if vmax is not None and v > vmax:
        return None, f"Max {vmax}"

    if key == "age":
        return int(v), None
    return round(v, 1), None
