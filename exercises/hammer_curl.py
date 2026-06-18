import mediapipe as mp
from exercises.base_exercise import BaseExercise, FormResult
from utils.angle_calculator import calculate_angle
from utils.landmark_utils import get_px, visibility
from config import GREEN, RED, YELLOW, WHITE

_lm = mp.solutions.pose.PoseLandmark
L_SH, R_SH = _lm.LEFT_SHOULDER.value,  _lm.RIGHT_SHOULDER.value
L_EL, R_EL = _lm.LEFT_ELBOW.value,     _lm.RIGHT_ELBOW.value
L_WR, R_WR = _lm.LEFT_WRIST.value,     _lm.RIGHT_WRIST.value
L_HI, R_HI = _lm.LEFT_HIP.value,       _lm.RIGHT_HIP.value

FULL_CURL   = 55.0
FULL_EXTEND = 150.0
WARN_CURL   = 80.0
WARN_EXTEND = 120.0


class HammerCurl(BaseExercise):
    CAL_PEAK_ATTR = "FULL_CURL"
    CAL_REST_ATTR = "FULL_EXTEND"
    CAL_WARN_PEAK = "WARN_CURL"
    CAL_WARN_REST = "WARN_EXTEND"
    CAL_INVERTED  = False

    def __init__(self):
        super().__init__("Hammer Curl")

    def analyze(self, landmarks, w, h):
        errors, warnings = [], []
        angles, lc, act = {}, {}, {}
        in_motion = self.phase != "IDLE"

        for side, (sh, el, wr, hi) in [
            ("L", (L_SH, L_EL, L_WR, L_HI)),
            ("R", (R_SH, R_EL, R_WR, R_HI)),
        ]:
            if min(visibility(landmarks, sh),
                   visibility(landmarks, el),
                   visibility(landmarks, wr)) < 0.5:
                continue

            p_sh = get_px(landmarks, sh, w, h)
            p_el = get_px(landmarks, el, w, h)
            p_wr = get_px(landmarks, wr, w, h)
            p_hi = get_px(landmarks, hi, w, h)
            lbl  = "Sol" if side == "L" else "Sag"

            elbow = calculate_angle(p_sh, p_el, p_wr)
            act[side] = elbow
            angles[f"{lbl} dirsek"] = round(elbow, 1)
            lc[el] = GREEN if elbow <= FULL_CURL else WHITE

            if in_motion:
                if self.phase == "DOWN" and elbow < WARN_EXTEND:
                    warnings.append(f"{lbl} kolu tam uzat")
                    lc[el] = YELLOW
                elif self.phase == "UP" and elbow > WARN_CURL:
                    warnings.append(f"{lbl} daha fazla kivir")
                    lc[el] = YELLOW

                sh_angle = calculate_angle(p_hi, p_sh, p_el)
                if sh_angle > 35:
                    errors.append(f"{lbl} dirsek one kaciyor")
                    lc[el] = RED

        if act:
            self._update_phase_bilateral(act, FULL_CURL, FULL_EXTEND)

        primary = sum(act.values()) / len(act) if act else None

        return FormResult(
            is_correct=len(errors) == 0,
            errors=errors, warnings=warnings,
            phase=self.phase, rep_count=self.rep_count,
            angles=angles, landmark_colors=lc,
            primary_angle=round(primary, 1) if primary else None,
            primary_range=(0, 180),
        )
