"""
Ilerleme kaydi — profil bazli JSON.
progress_log.json: {
  profile_name: {
    "exercise": [{"date","exercise_id","reps","duration_min"}, ...],
    "body":     [{"date","fat_pct","weight_kg","bmi"}, ...],
    "strength": [{"date","squat","bench","deadlift","dots"}, ...]
  }
}
"""

import json
from datetime import date, timedelta
from pathlib import Path

LOG_PATH = Path(__file__).parent.parent / "kullanici_verisi" / "progress_log.json"


# ── IO ────────────────────────────────────────────────────────────────────────

def _load() -> dict:
    if LOG_PATH.exists():
        try:
            return json.loads(LOG_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save(data: dict):
    LOG_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _today() -> str:
    return date.today().isoformat()


# ── Yazma ────────────────────────────────────────────────────────────────────

def log_exercise(profile_name: str, exercise_id: str, reps: int, duration_min: float = 0.0):
    if reps <= 0:
        return
    data = _load()
    data.setdefault(profile_name, {}).setdefault("exercise", [])
    data[profile_name]["exercise"].append({
        "date":         _today(),
        "exercise_id":  exercise_id,
        "reps":         reps,
        "duration_min": round(duration_min, 1),
    })
    _save(data)


def log_body(profile_name: str, fat_pct: float, weight_kg: float, bmi: float):
    data = _load()
    entries = data.setdefault(profile_name, {}).setdefault("body", [])
    # Ayni gun zaten kayitliysa uzerine yaz (en son olcumu tut)
    today = _today()
    entries = [e for e in entries if e["date"] != today]
    entries.append({
        "date":      today,
        "fat_pct":   round(fat_pct, 2),
        "weight_kg": round(weight_kg, 1),
        "bmi":       round(bmi, 2),
    })
    data[profile_name]["body"] = entries
    _save(data)


def log_strength(profile_name: str, lifts: dict, dots: float = 0.0):
    data = _load()
    entries = data.setdefault(profile_name, {}).setdefault("strength", [])
    today = _today()
    entries = [e for e in entries if e["date"] != today]
    entries.append({
        "date":     today,
        "squat":    round(lifts.get("squat", 0), 1),
        "bench":    round(lifts.get("bench", 0), 1),
        "deadlift": round(lifts.get("deadlift", 0), 1),
        "dots":     round(dots, 1),
    })
    data[profile_name]["strength"] = entries
    _save(data)


# ── Okuma ────────────────────────────────────────────────────────────────────

def _last_n_days(entries: list, days: int) -> list:
    cutoff = (date.today() - timedelta(days=days)).isoformat()
    return sorted([e for e in entries if e["date"] >= cutoff], key=lambda e: e["date"])


def get_exercise_history(profile_name: str, days: int = 30) -> list:
    data = _load()
    return _last_n_days(data.get(profile_name, {}).get("exercise", []), days)


def get_body_history(profile_name: str, days: int = 60) -> list:
    data = _load()
    return _last_n_days(data.get(profile_name, {}).get("body", []), days)


def get_strength_history(profile_name: str, days: int = 90) -> list:
    data = _load()
    return _last_n_days(data.get(profile_name, {}).get("strength", []), days)


def get_summary(profile_name: str) -> dict:
    """Son 7 gun ozeti."""
    ex  = get_exercise_history(profile_name, days=7)
    bod = get_body_history(profile_name, days=60)
    sth = get_strength_history(profile_name, days=90)

    total_reps  = sum(e["reps"] for e in ex)
    sessions    = len(set(e["date"] for e in ex))
    last_fat    = bod[-1]["fat_pct"]   if bod else None
    first_fat   = bod[0]["fat_pct"]    if len(bod) > 1 else None
    last_total  = (sth[-1]["squat"] + sth[-1]["bench"] + sth[-1]["deadlift"]) if sth else None

    return {
        "weekly_reps":    total_reps,
        "weekly_sessions": sessions,
        "last_fat_pct":   last_fat,
        "fat_change":     round(last_fat - first_fat, 2) if (last_fat and first_fat) else None,
        "last_total_kg":  last_total,
        "last_dots":      sth[-1]["dots"] if sth else None,
    }
