"""
Kişiye özel kalibrasyon sistemi.

Kullanıcı 3 tekrar yapar → sistem min/max açıları kaydeder
→ exercise eşikleri kişiye göre ayarlanır → profil bazlı kaydedilir.
"""

import json
import numpy as np
from pathlib import Path
from typing import Optional, Dict

CAL_DIR    = Path(__file__).parent.parent / "data" / "calibration"
N_CAL_REPS = 3


class CalibrationSession:
    """Tek bir egzersiz için kalibrasyon verisi toplar."""

    def __init__(self):
        self._rep_buf: list = []   # mevcut tekrardaki açı değerleri
        self._reps:    list = []   # tamamlanan tekrarların [(min, max), ...] listesi

    @property
    def n_reps(self) -> int:
        return len(self._reps)

    def add_angle(self, val: float):
        """Her frame'de birincil açıyı ekle (result.primary_angle)."""
        if val is not None and not np.isnan(val):
            self._rep_buf.append(float(val))

    def rep_completed(self):
        """Analyzer yeni tekrar saydığında çağır."""
        if len(self._rep_buf) >= 10:
            self._reps.append((float(min(self._rep_buf)), float(max(self._rep_buf))))
        self._rep_buf.clear()

    def is_ready(self) -> bool:
        return len(self._reps) >= N_CAL_REPS

    def compute(self) -> Optional[Dict[str, float]]:
        """
        Doner: {"angle_min": float, "angle_max": float}
        angle_min = kullanıcının ulaştığı minimum açı (en fazla bükülen/eğilen)
        angle_max = kullanıcının ulaştığı maksimum açı (tam uzatılmış/dik)
        """
        if not self._reps:
            return None
        mins = [r[0] for r in self._reps]
        maxs = [r[1] for r in self._reps]
        return {
            "angle_min": float(np.mean(mins)),
            "angle_max": float(np.mean(maxs)),
        }


def save(profile_name: str, exercise: str, data: Dict[str, float]):
    CAL_DIR.mkdir(parents=True, exist_ok=True)
    path = CAL_DIR / f"{profile_name}_{exercise}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    print(f"Kalibrasyon kaydedildi: {path.name}")


def load(profile_name: str, exercise: str) -> Optional[Dict[str, float]]:
    if not profile_name:
        return None
    path = CAL_DIR / f"{profile_name}_{exercise}.json"
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None
