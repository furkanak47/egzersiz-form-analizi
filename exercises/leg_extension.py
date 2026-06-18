import mediapipe as mp
from exercises.base_exercise import BaseExercise, FormResult
from utils.angle_calculator import calculate_angle
from utils.landmark_utils import get_px, visibility
from config import GREEN, RED, YELLOW, WHITE

_lm = mp.solutions.pose.PoseLandmark
L_HI, R_HI = _lm.LEFT_HIP.value,   _lm.RIGHT_HIP.value
L_KN, R_KN = _lm.LEFT_KNEE.value,  _lm.RIGHT_KNEE.value
L_AN, R_AN = _lm.LEFT_ANKLE.value,  _lm.RIGHT_ANKLE.value

UP_ANGLE   = 165.0   # bacak uzatilmis
DOWN_ANGLE = 85.0    # bacak bukulu
WARN_UP    = 150.0
WARN_DOWN  = 100.0


class LegExtension(BaseExercise):
    CAL_PEAK_ATTR = "UP_ANGLE"
    CAL_REST_ATTR = "DOWN_ANGLE"
    CAL_WARN_PEAK = "WARN_UP"
    CAL_WARN_REST = "WARN_DOWN"
    CAL_INVERTED  = True

    def __init__(self):
        super().__init__("Leg Extension")

    def analyze(self, landmarks, w, h):
        errors, warnings = [], []
        angles, lc, act = {}, {}, {}
        in_motion = self.phase != "IDLE"

        for side, (hi, kn, an) in [
            ("L", (L_HI, L_KN, L_AN)),
            ("R", (R_HI, R_KN, R_AN)),
        ]:
            if min(visibility(landmarks, hi),
                   visibility(landmarks, kn),
                   visibility(landmarks, an)) < 0.5:
                continue

            p_hi = get_px(landmarks, hi, w, h)
            p_kn = get_px(landmarks, kn, w, h)
            p_an = get_px(landmarks, an, w, h)
            lbl  = "Sol" if side == "L" else "Sag"

            knee_angle = calculate_angle(p_hi, p_kn, p_an)
            act[side]  = knee_angle
            angles[f"{lbl} diz"] = round(knee_angle, 1)
            lc[kn] = GREEN if knee_angle >= UP_ANGLE else WHITE

            if in_motion:
                if self.phase == "UP" and knee_angle < WARN_UP:
                    warnings.append(f"{lbl} bacak tam uzatilmadi")
                    lc[kn] = YELLOW
                if self.phase == "DOWN" and knee_angle > WARN_DOWN:
                    warnings.append(f"{lbl} bacak tam bukulmedi")
                    lc[kn] = YELLOW

        if act:
            # Leg extension: UP = buyuk aci, inverted=True
            self._update_phase_bilateral(act, UP_ANGLE, DOWN_ANGLE, inverted=True)

        primary = sum(act.values()) / len(act) if act else None

        return FormResult(
            is_correct=len(errors) == 0,
            errors=errors, warnings=warnings,
            phase=self.phase, rep_count=self.rep_count,
            angles=angles, landmark_colors=lc,
            primary_angle=round(primary, 1) if primary else None,
            primary_range=(60, 180),
        )
