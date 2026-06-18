from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import time


@dataclass
class FormResult:
    is_correct:      bool
    errors:          List[str]
    warnings:        List[str]
    phase:           str
    rep_count:       int
    angles:          Dict[str, float]
    landmark_colors: Dict[int, tuple]
    primary_angle:   Optional[float] = None   # sol panelde aci barinda gosterilir
    primary_range:   Optional[Tuple] = None   # (lo, hi) bar olcegi icin


class BaseExercise(ABC):
    MIN_REP_INTERVAL = 1.0  # iki rep arasi minimum sure (sn)
    TIME_BASED = False       # True olan egzersizlerde rep_count = saniye (ses calmaz)

    # ── Kalibrasyon eşlemeleri — alt sınıflar override eder ─────────────────
    CAL_PRIMARY   = None   # takip edilecek açı anahtarı ("l_elbow" vb.)
    CAL_PEAK_ATTR = None   # zirve pozisyon attr adı (ör. "FULL_CURL")
    CAL_REST_ATTR = None   # dinlenme pozisyon attr adı (ör. "FULL_EXTEND")
    CAL_WARN_PEAK = None   # zirve uyarı eşiği attr adı (None = yok)
    CAL_WARN_REST = None   # dinlenme uyarı eşiği attr adı (None = yok)
    CAL_INVERTED  = False  # True ise zirve = büyük açı (shoulder press, triceps vb.)

    def __init__(self, name: str):
        self.name      = name
        self.rep_count = 0
        self.phase     = "IDLE"   # IDLE → DOWN → UP → DOWN → ...
        self._last_rep = 0.0

    @abstractmethod
    def analyze(self, landmarks, w: int, h: int) -> FormResult:
        pass

    # ── Tek-taraf faz guncelleme ─────────────────────────────────────────────

    def _update_phase(self, angle: float, up_thresh: float, down_thresh: float,
                      inverted: bool = False) -> str:
        """
        inverted=False  UP = kucuk aci  (biceps curl, fly)
        inverted=True   UP = buyuk aci  (shoulder press, lateral raise, triceps)
        IDLE, DOWN ile esde tutulur — ilk harekette hemen faz degisir.
        """
        eff = "DOWN" if self.phase == "IDLE" else self.phase
        if not inverted:
            if angle <= up_thresh:
                if eff == "DOWN":
                    self._try_rep()
                self.phase = "UP"
            elif angle >= down_thresh:
                self.phase = "DOWN"
        else:
            if angle >= up_thresh:
                if eff == "DOWN":
                    self._try_rep()
                self.phase = "UP"
            elif angle <= down_thresh:
                self.phase = "DOWN"
        return self.phase

    # ── Cift-taraf (bilateral) faz guncelleme ────────────────────────────────

    def _update_phase_bilateral(self, angles: dict, up_thresh: float, down_thresh: float,
                                inverted: bool = False) -> str:
        """
        Her iki taraf da esigi gecmeden faz degismez.
        inverted=False  max(angles) <= up_thresh → UP   |  min(angles) >= down_thresh → DOWN
        inverted=True   min(angles) >= up_thresh → UP   |  max(angles) <= down_thresh → DOWN
        """
        if not angles:
            return self.phase
        vals = list(angles.values())
        eff  = "DOWN" if self.phase == "IDLE" else self.phase

        if not inverted:
            if max(vals) <= up_thresh:       # en az kivrilmis kol bile esigi gecmeli
                if eff == "DOWN":
                    self._try_rep()
                self.phase = "UP"
            elif min(vals) >= down_thresh:   # en az uzatilmis kol bile esigi gecmeli
                self.phase = "DOWN"
        else:
            if min(vals) >= up_thresh:       # en az yukselenmis / uzatilmis kol bile esigi gecmeli
                if eff == "DOWN":
                    self._try_rep()
                self.phase = "UP"
            elif max(vals) <= down_thresh:   # en cok yukselenmis kol bile duse inmeli
                self.phase = "DOWN"

        return self.phase

    def _try_rep(self):
        now = time.perf_counter()
        if now - self._last_rep >= self.MIN_REP_INTERVAL:
            self.rep_count += 1
            self._last_rep = now

    def apply_calibration(self, cal_data: dict) -> bool:
        """
        cal_data: {"angle_min": float, "angle_max": float}
        Exercise sabitlerini kişisel ölçümlere göre instance düzeyinde günceller.
        Doner True başarılı, False tanımlı kalibrasyon yok.
        """
        if not cal_data or not self.CAL_PEAK_ATTR or not self.CAL_REST_ATTR:
            return False

        if self.CAL_INVERTED:
            peak = cal_data["angle_max"]
            rest = cal_data["angle_min"]
        else:
            peak = cal_data["angle_min"]
            rest = cal_data["angle_max"]

        setattr(self, self.CAL_PEAK_ATTR, float(peak))
        setattr(self, self.CAL_REST_ATTR, float(rest))

        range_  = abs(rest - peak)
        margin  = max(range_ * 0.15, 5.0)  # en az 5 derece

        if self.CAL_WARN_PEAK:
            w = peak + margin if not self.CAL_INVERTED else peak - margin
            setattr(self, self.CAL_WARN_PEAK, float(w))

        if self.CAL_WARN_REST:
            w = rest - margin if not self.CAL_INVERTED else rest + margin
            setattr(self, self.CAL_WARN_REST, float(w))

        return True

    def reset(self):
        self.rep_count = 0
        self.phase     = "IDLE"
        self._last_rep = 0.0
