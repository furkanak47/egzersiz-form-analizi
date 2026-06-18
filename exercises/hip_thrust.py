import mediapipe as mp
from exercises.base_exercise import BaseExercise, FormResult
from utils.angle_calculator import calculate_angle
from utils.landmark_utils import get_px, visibility
from config import GREEN, RED, YELLOW, WHITE

_lm = mp.solutions.pose.PoseLandmark
L_SH, R_SH = _lm.LEFT_SHOULDER.value,  _lm.RIGHT_SHOULDER.value
L_HI, R_HI = _lm.LEFT_HIP.value,       _lm.RIGHT_HIP.value
L_KN, R_KN = _lm.LEFT_KNEE.value,      _lm.RIGHT_KNEE.value

UP_ANGLE   = 165.0   # kalca yukarda (omuz-kalca-diz duz)
DOWN_ANGLE = 100.0   # kalca asagida
WARN_UP    = 155.0
WARN_DOWN  = 115.0


class HipThrust(BaseExercise):
    CAL_PEAK_ATTR = "UP_ANGLE"
    CAL_REST_ATTR = "DOWN_ANGLE"
    CAL_WARN_PEAK = "WARN_UP"
    CAL_WARN_REST = "WARN_DOWN"
    CAL_INVERTED  = True

    def __init__(self):
        super().__init__("Hip Thrust")

    def analyze(self, landmarks, w, h):
        errors, warnings = [], []
        angles, lc, act = {}, {}, {}
        in_motion = self.phase != "IDLE"

        for side, (sh, hi, kn) in [
            ("L", (L_SH, L_HI, L_KN)),
            ("R", (R_SH, R_HI, R_KN)),
        ]:
            if min(visibility(landmarks, sh),
                   visibility(landmarks, hi),
                   visibility(landmarks, kn)) < 0.5:
                continue

            p_sh = get_px(landmarks, sh, w, h)
            p_hi = get_px(landmarks, hi, w, h)
            p_kn = get_px(landmarks, kn, w, h)
            lbl  = "Sol" if side == "L" else "Sag"

            hip_angle = calculate_angle(p_sh, p_hi, p_kn)
            act[side] = hip_angle
            angles[f"{lbl} kalca"] = round(hip_angle, 1)
            lc[hi] = GREEN if hip_angle >= UP_ANGLE else WHITE

            if in_motion:
                if self.phase == "UP" and hip_angle < WARN_UP:
                    warnings.append(f"{lbl} kalcayi daha yukari kaldir")
                    lc[hi] = YELLOW
                if self.phase == "DOWN" and hip_angle > WARN_DOWN:
                    warnings.append(f"{lbl} kalcayi daha asagi indir")
                    lc[hi] = YELLOW

        if in_motion:
            tilt = abs(landmarks[L_HI].y - landmarks[R_HI].y)
            if tilt > 0.06:
                errors.append("Kalcalar esit tutulmali")

        if act:
            # Hip thrust: UP = buyuk aci, inverted=True
            self._update_phase_bilateral(act, UP_ANGLE, DOWN_ANGLE, inverted=True)

        primary = sum(act.values()) / len(act) if act else None

        return FormResult(
            is_correct=len(errors) == 0,
            errors=errors, warnings=warnings,
            phase=self.phase, rep_count=self.rep_count,
            angles=angles, landmark_colors=lc,
            primary_angle=round(primary, 1) if primary else None,
            primary_range=(80, 200),
        )
