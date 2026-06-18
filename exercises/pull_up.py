import mediapipe as mp
from exercises.base_exercise import BaseExercise, FormResult
from utils.angle_calculator import calculate_angle
from utils.landmark_utils import get_px, visibility
from config import GREEN, RED, YELLOW, WHITE

_lm = mp.solutions.pose.PoseLandmark
L_SH, R_SH = _lm.LEFT_SHOULDER.value,  _lm.RIGHT_SHOULDER.value
L_EL, R_EL = _lm.LEFT_ELBOW.value,     _lm.RIGHT_ELBOW.value
L_WR, R_WR = _lm.LEFT_WRIST.value,     _lm.RIGHT_WRIST.value

UP_ANGLE   = 70.0    # cene bar ustunde (UP)
DOWN_ANGLE = 155.0   # kollar uzatilmis (DOWN)
WARN_UP    = 90.0
WARN_DOWN  = 140.0


class PullUp(BaseExercise):
    CAL_PEAK_ATTR = "UP_ANGLE"
    CAL_REST_ATTR = "DOWN_ANGLE"
    CAL_WARN_PEAK = "WARN_UP"
    CAL_WARN_REST = "WARN_DOWN"
    CAL_INVERTED  = False

    def __init__(self):
        super().__init__("Pull-up")

    def analyze(self, landmarks, w, h):
        errors, warnings = [], []
        angles, lc, act = {}, {}, {}
        in_motion = self.phase != "IDLE"

        for side, (sh, el, wr) in [
            ("L", (L_SH, L_EL, L_WR)),
            ("R", (R_SH, R_EL, R_WR)),
        ]:
            if min(visibility(landmarks, sh),
                   visibility(landmarks, el),
                   visibility(landmarks, wr)) < 0.5:
                continue

            p_sh = get_px(landmarks, sh, w, h)
            p_el = get_px(landmarks, el, w, h)
            p_wr = get_px(landmarks, wr, w, h)
            lbl  = "Sol" if side == "L" else "Sag"

            elbow = calculate_angle(p_sh, p_el, p_wr)
            act[side] = elbow
            angles[f"{lbl} dirsek"] = round(elbow, 1)
            lc[el] = GREEN if elbow <= UP_ANGLE else WHITE

            if in_motion:
                if self.phase == "UP" and elbow > WARN_UP:
                    warnings.append(f"{lbl} daha fazla cek ({elbow:.0f})")
                    lc[el] = YELLOW
                if self.phase == "DOWN" and elbow < WARN_DOWN:
                    warnings.append(f"{lbl} kolu tam ac ({elbow:.0f})")
                    lc[el] = YELLOW

        if in_motion:
            tilt = abs(landmarks[L_SH].y - landmarks[R_SH].y)
            if tilt > 0.08:
                errors.append("Omuzlar esit tutulmali")

        if act:
            # Pull-up: UP = kucuk aci (cekis), DOWN = buyuk aci (asili)
            self._update_phase_bilateral(act, UP_ANGLE, DOWN_ANGLE)

        primary = sum(act.values()) / len(act) if act else None

        return FormResult(
            is_correct=len(errors) == 0,
            errors=errors, warnings=warnings,
            phase=self.phase, rep_count=self.rep_count,
            angles=angles, landmark_colors=lc,
            primary_angle=round(primary, 1) if primary else None,
            primary_range=(0, 180),
        )
