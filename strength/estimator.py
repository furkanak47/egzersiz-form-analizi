"""
Güç persentil hesaplama — OpenPowerlifting 1.3M natural sporcu verisinden.
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple

NORMS_PATH = Path(__file__).parent.parent / "veri" / "kondisyon" / "strength_norms.csv"

BW_BINS   = list(range(40, 161, 5)) + [200]
BW_LABELS = [f"{BW_BINS[i]}-{BW_BINS[i+1]}" for i in range(len(BW_BINS) - 1)]

# Dots katsayilari (ekipmansiz natural sporcu normalizasyonu)
_DOTS_M = [-0.0000010930, 0.0007391293, -0.1918759221, 24.0900756, -307.75076]
_DOTS_F = [ 0.0000010706, -0.0023334613, 0.1918759221, -8.6587937,  50.4858695]


def dots_score(total_kg: float, bw_kg: float, sex: str) -> float:
    """Dots skoru — vücut agirligina gore normalize toplam kuvvet."""
    c = _DOTS_M if sex == "M" else _DOTS_F
    denom = (c[0]*bw_kg**4 + c[1]*bw_kg**3 + c[2]*bw_kg**2 + c[3]*bw_kg + c[4])
    if denom <= 0:
        return 0.0
    return round(500 / denom * total_kg, 1)


def _bw_bin(bw_kg: float) -> str:
    for i in range(len(BW_BINS) - 1):
        if BW_BINS[i] <= bw_kg < BW_BINS[i + 1]:
            return BW_LABELS[i]
    return BW_LABELS[-1]


class StrengthEstimator:
    def __init__(self):
        self._norms: Optional[pd.DataFrame] = None
        self.loaded = False

    def load(self):
        if NORMS_PATH.exists():
            self._norms = pd.read_csv(NORMS_PATH)
            self.loaded = True
        else:
            print(f"Guc normlari bulunamadi: {NORMS_PATH}")

    def percentile(self, value: float, lift: str, bw_kg: float, sex: str) -> Optional[int]:
        """
        Verilen kaldirisi ayni cinsiyet ve vucut agirligi grubundaki
        natural sporcularla karsilastirir. 0-100 persentil dondurur.
        Dots zaten normalize olduğu için bw_bin kullanmaz.
        """
        if not self.loaded or value <= 0:
            return None
        bw = 'all' if lift == 'dots' else _bw_bin(bw_kg)
        row = self._norms[
            (self._norms['sex']  == sex) &
            (self._norms['bw_bin'] == bw) &
            (self._norms['lift'] == lift)
        ]
        if row.empty:
            return None
        r = row.iloc[0]
        pts = [r['p10'], r['p25'], r['p50'], r['p75'], r['p90']]
        pcts = [10, 25, 50, 75, 90]
        if value <= pts[0]:
            return max(1, int(round(value / pts[0] * 10)))
        if value >= pts[-1]:
            return min(99, int(round(90 + (value - pts[-1]) / max(pts[-1] * 0.2, 1) * 9)))
        for i in range(len(pts) - 1):
            if pts[i] <= value < pts[i + 1]:
                frac = (value - pts[i]) / max(pts[i + 1] - pts[i], 0.1)
                return int(round(pcts[i] + frac * (pcts[i + 1] - pcts[i])))
        return 50

    def level(self, pct: int) -> Tuple[str, tuple]:
        """Persentilden seviye etiketi ve rengi dondurur (BGR)."""
        if pct >= 90: return "ELIT",          (0, 215, 255)   # altin
        if pct >= 75: return "ILERI",         (0, 255, 0)     # yesil
        if pct >= 50: return "ORTA-UST",      (255, 255, 0)   # cyan
        if pct >= 25: return "ORTA",          (0, 165, 255)   # turuncu
        return             "BASLANGIC",       (150, 150, 150) # gri

    def analyze(self, lifts: dict, bw_kg: float, sex: str) -> dict:
        """
        lifts: {'squat': kg, 'bench': kg, 'deadlift': kg}  — 0 = yapilmadi
        Dondurur: her lift icin persentil + seviye + dots skoru
        """
        results = {}
        valid = {k: v for k, v in lifts.items() if v > 0}
        for lift, kg in valid.items():
            pct = self.percentile(kg, lift, bw_kg, sex)
            if pct is not None:
                lbl, col = self.level(pct)
                results[lift] = {"kg": kg, "pct": pct, "level": lbl, "color": col}

        # Dots yalnizca 3 kaldirish da girilince hesaplanir
        all_three = all(lifts.get(k, 0) > 0 for k in ('squat', 'bench', 'deadlift'))
        if all_three:
            total = lifts['squat'] + lifts['bench'] + lifts['deadlift']
            d = dots_score(total, bw_kg, sex)
            pct_d = self.percentile(d, "dots", bw_kg, sex)
            if pct_d is not None:
                lbl, col = self.level(pct_d)
                results["dots"] = {"score": d, "pct": pct_d, "level": lbl, "color": col}

        return results
