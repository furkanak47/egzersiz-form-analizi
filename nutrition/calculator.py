"""
BMR, TDEE ve makro hedefi hesaplama.
Profil: height_cm, weight_kg, age, sex ('M'/'F')
"""

# Egzersiz MET degerleri (yakiti tahmin icin)
EXERCISE_MET = {
    'biceps_curl':    3.5,
    'triceps':        3.5,
    'shoulder_press': 4.0,
    'lateral_raise':  3.5,
    'fly':            3.5,
    'bench_press':    4.0,
}

GOALS = {
    'maintain':    'Kilonu Koru',
    'bulk':        'Kas Yap',
    'cut':         'Yag Yak',
}


def bmr(weight_kg: float, height_cm: float, age: int, sex: str) -> float:
    """Mifflin-St Jeor BMR (kcal/gun)."""
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    return base + 5 if sex.upper() == 'M' else base - 161


def tdee(bmr_val: float, activity: str = 'moderate') -> float:
    """
    TDEE = BMR x aktivite carpani.
    activity: sedentary | light | moderate | active | very_active
    """
    factors = {
        'sedentary':   1.2,
        'light':       1.375,
        'moderate':    1.55,
        'active':      1.725,
        'very_active': 1.9,
    }
    return round(bmr_val * factors.get(activity, 1.55), 0)


def macro_targets(tdee_val: float, weight_kg: float, goal: str = 'maintain') -> dict:
    """
    Hedefe gore gunluk makro hedefleri (g).
    Dondurur: kcal_target, protein_g, carb_g, fat_g
    """
    if goal == 'bulk':
        kcal = tdee_val + 300
        protein = weight_kg * 2.0
    elif goal == 'cut':
        kcal = max(tdee_val - 400, 1200)
        protein = weight_kg * 2.2
    else:  # maintain
        kcal = tdee_val
        protein = weight_kg * 1.6

    fat     = kcal * 0.25 / 9
    carb    = (kcal - protein * 4 - fat * 9) / 4
    fiber   = max(20, round(kcal / 1000 * 14))   # 14g / 1000 kcal

    return {
        'kcal':      round(kcal),
        'protein_g': round(protein),
        'carb_g':    max(0, round(carb)),
        'fat_g':     round(fat),
        'fiber_g':   fiber,
    }


def exercise_calories(exercise_id: str, weight_kg: float, duration_min: float) -> float:
    """Egzersiz sirasinda yaklasik kalori yakimi (MET x kg x saat)."""
    met = EXERCISE_MET.get(exercise_id, 3.5)
    return round(met * weight_kg * (duration_min / 60), 1)


def profile_targets(profile: dict, goal: str = 'maintain') -> dict:
    """
    Profil dict'inden hedef hesapla.
    Dondurur: bmr, tdee, macro_targets, goal
    """
    w   = float(profile.get('weight_kg', 70))
    h   = float(profile.get('height_cm', 170))
    age = int(profile.get('age', 25))
    sex = str(profile.get('sex', 'M')).upper()
    act = str(profile.get('activity', 'moderate'))

    b = bmr(w, h, age, sex)
    t = tdee(b, act)
    m = macro_targets(t, w, goal)

    return {
        'bmr':    round(b),
        'tdee':   round(t),
        'goal':   goal,
        **m,
    }
