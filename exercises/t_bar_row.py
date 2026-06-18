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

PULL_ANGLE  = 65.0    # bar cekili (dirsek kivrik)
EXTEND_ANGLE = 155.0  # bar asagida (kol uzatilmis)
WARN_PULL   = 85.0
WARN_EXTEND = 140.0


class TBarRow(BaseExercise):
    CAL_PEAK_ATTR = "PULL_ANGLE"
    CAL_REST_ATTR = "EXTEND_ANGLE"
    CAL_WARN_PEAK = "WARN_PULL"
    CAL_WARN_REST = "WARN_EXTEND"
    CAL_INVERTED  = False

    def __init__(self):
        super().__init__("T-Bar Row")

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
            lc[el] = GREEN if elbow <= PULL_ANGLE else WHITE

            if in_motion:
                if self.phase == "UP" and elbow > WARN_PULL:
                    warnings.append(f"{lbl} daha fazla cek ({elbow:.0f})")
                    lc[el] = YELLOW
                if self.phase == "DOWN" and elbow < WARN_EXTEND:
                    warnings.append(f"{lbl} kolu tam uzat ({elbow:.0f})")
                    lc[el] = YELLOW

            # Egim kontrolu (one egik olmali)
            hip_sh = calculate_angle(p_hi, p_sh, [p_sh[0], p_sh[1] + 100])
            if in_motion and hip_sh > 70:
                warnings.append(f"{lbl} one eg")

        if in_motion:
            tilt = abs(landmarks[L_SH].y - landmarks[R_SH].y)
            if tilt > 0.07:
                errors.append("Omuzlar esit tutulmali")

        if act:
            self._update_phase_bilateral(act, PULL_ANGLE, EXTEND_ANGLE)

        primary = sum(act.values()) / len(act) if act else None

        return FormResult(
            is_correct=len(errors) == 0,
            errors=errors, warnings=warnings,
            phase=self.phase, rep_count=self.rep_count,
            angles=angles, landmark_colors=lc,
            primary_angle=round(primary, 1) if primary else None,
            primary_range=(0, 180),
        )
