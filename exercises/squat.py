import mediapipe as mp
from exercises.base_exercise import BaseExercise, FormResult
from utils.angle_calculator import calculate_angle
from utils.landmark_utils import get_px, visibility
from config import GREEN, RED, YELLOW, WHITE

_lm = mp.solutions.pose.PoseLandmark
L_HI, R_HI = _lm.LEFT_HIP.value,   _lm.RIGHT_HIP.value
L_KN, R_KN = _lm.LEFT_KNEE.value,  _lm.RIGHT_KNEE.value
L_AN, R_AN = _lm.LEFT_ANKLE.value,  _lm.RIGHT_ANKLE.value
L_SH, R_SH = _lm.LEFT_SHOULDER.value, _lm.RIGHT_SHOULDER.value

DEEP_SQUAT  = 95.0
STAND_UP    = 165.0
WARN_DEPTH  = 110.0
WARN_STAND  = 150.0


class Squat(BaseExercise):
    CAL_PEAK_ATTR = "DEEP_SQUAT"
    CAL_REST_ATTR = "STAND_UP"
    CAL_WARN_PEAK = "WARN_DEPTH"
    CAL_WARN_REST = "WARN_STAND"
    CAL_INVERTED  = False

    def __init__(self):
        super().__init__("Squat")

    def analyze(self, landmarks, w, h):
        errors, warnings = [], []
        angles, lc, act = {}, {}, {}
        in_motion = self.phase != "IDLE"

        for side, (hi, kn, an, sh) in [
            ("L", (L_HI, L_KN, L_AN, L_SH)),
            ("R", (R_HI, R_KN, R_AN, R_SH)),
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
            lc[kn] = GREEN if knee_angle <= DEEP_SQUAT else WHITE

            if in_motion:
                if self.phase == "UP" and knee_angle > WARN_DEPTH:
                    warnings.append(f"{lbl} daha derin cin ({knee_angle:.0f})")
                    lc[kn] = YELLOW
                if self.phase == "DOWN" and knee_angle < WARN_STAND:
                    warnings.append(f"{lbl} bacak tam duzelmedi ({knee_angle:.0f})")
                    lc[kn] = YELLOW

        if in_motion:
            tilt = abs(landmarks[L_HI].y - landmarks[R_HI].y)
            if tilt > 0.06:
                errors.append("Kalcalar esit tutulmali")

        if act:
            self._update_phase_bilateral(act, DEEP_SQUAT, STAND_UP)

        primary = sum(act.values()) / len(act) if act else None

        return FormResult(
            is_correct=len(errors) == 0,
            errors=errors, warnings=warnings,
            phase=self.phase, rep_count=self.rep_count,
            angles=angles, landmark_colors=lc,
            primary_angle=round(primary, 1) if primary else None,
            primary_range=(60, 180),
        )
