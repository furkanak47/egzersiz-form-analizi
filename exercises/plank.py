import mediapipe as mp
import time
from exercises.base_exercise import BaseExercise, FormResult
from utils.angle_calculator import calculate_angle
from utils.landmark_utils import get_px, visibility
from config import GREEN, RED, YELLOW, WHITE

_lm = mp.solutions.pose.PoseLandmark
L_SH, R_SH = _lm.LEFT_SHOULDER.value,  _lm.RIGHT_SHOULDER.value
L_HI, R_HI = _lm.LEFT_HIP.value,       _lm.RIGHT_HIP.value
L_AN, R_AN = _lm.LEFT_ANKLE.value,      _lm.RIGHT_ANKLE.value
L_KN, R_KN = _lm.LEFT_KNEE.value,      _lm.RIGHT_KNEE.value

BODY_MIN = 160.0   # govde duzluk esigi (omuz-kalca-ayak bileği)
BODY_MAX = 195.0


class Plank(BaseExercise):
    TIME_BASED = True   # rep_count = tutma suresi (saniye)

    def __init__(self):
        super().__init__("Plank")
        self._hold_start  = 0.0
        self._holding     = False
        self._hold_seconds = 0

    def analyze(self, landmarks, w, h):
        errors, warnings = [], []
        angles, lc = {}, {}

        body_ok = False
        for side, (sh, hi, an) in [
            ("L", (L_SH, L_HI, L_AN)),
            ("R", (R_SH, R_HI, R_AN)),
        ]:
            if min(visibility(landmarks, sh),
                   visibility(landmarks, hi),
                   visibility(landmarks, an)) < 0.5:
                continue

            p_sh = get_px(landmarks, sh, w, h)
            p_hi = get_px(landmarks, hi, w, h)
            p_an = get_px(landmarks, an, w, h)
            lbl  = "Sol" if side == "L" else "Sag"

            body = calculate_angle(p_sh, p_hi, p_an)
            angles[f"{lbl} govde"] = round(body, 1)

            if body < BODY_MIN:
                errors.append(f"{lbl} kalca cok asagi")
                lc[hi] = RED
            elif body > BODY_MAX:
                errors.append(f"{lbl} kalca cok yukarda")
                lc[hi] = RED
            else:
                lc[hi] = GREEN
                body_ok = True

        # Plank'te rep sayisi yok — tutma suresi sayilir
        now = time.perf_counter()
        if body_ok and not errors:
            if not self._holding:
                self._hold_start = now
                self._holding    = True
            self._hold_seconds = int(now - self._hold_start)
            self.phase = "HOLD"
        else:
            self._holding      = False
            self._hold_seconds = 0
            self.phase = "IDLE"

        self.rep_count = self._hold_seconds  # rep yerine saniye goster

        primary = list(angles.values())[0] if angles else None

        return FormResult(
            is_correct=len(errors) == 0,
            errors=errors, warnings=warnings,
            phase=self.phase, rep_count=self.rep_count,
            angles=angles, landmark_colors=lc,
            primary_angle=round(primary, 1) if primary else None,
            primary_range=(140, 210),
        )
