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

# Hareket esikleri (ampirik tahmin — egitim verisiyle kalibre edilmeli)
# inverted=True: UP = buyuk aci (press tamamlandi), DOWN = kucuk aci (baslangic)
FULL_PRESS   = 160.0   # kollar tam uzatilmis (UP fazi)
FULL_BOTTOM  = 100.0   # dirsek bukulu, baslangic (DOWN fazi)
WARN_PRESS   = 145.0   # tam uzatilmamanin uyari esigi
MIN_BODY     = 159.0   # govde diklik esigi
MAX_TILT     = 0.05    # omuz esitlik esigi


class ShoulderPress(BaseExercise):
    CAL_PEAK_ATTR = "FULL_PRESS"
    CAL_REST_ATTR = "FULL_BOTTOM"
    CAL_WARN_PEAK = "WARN_PRESS"
    CAL_WARN_REST = None
    CAL_INVERTED  = True

    def __init__(self):
        super().__init__("Shoulder Press")

    def analyze(self, landmarks, w, h):
        errors, warnings = [], []
        angles = {}
        lc     = {}
        act    = {}
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
            lbl  = "Sol" if side == "L" else "Sag"

            elbow = calculate_angle(p_sh, p_el, p_wr)
            act[side] = elbow
            angles[f"{lbl} dirsek"] = round(elbow, 1)
            lc[el] = WHITE

            if in_motion:
                # Bilek omuzun ustundeyken tam uzatilmali
                wrist_up = landmarks[wr].y < landmarks[sh].y
                if wrist_up and elbow < WARN_PRESS:
                    errors.append(f"{lbl} kolu tam uzat ({elbow:.0f}<{WARN_PRESS:.0f})")
                    lc[el] = RED
                elif elbow >= FULL_PRESS:
                    lc[el] = GREEN

        if in_motion:
            tilt = abs(landmarks[L_SH].y - landmarks[R_SH].y)
            if tilt > MAX_TILT + 0.03:
                warnings.append("Omuzlar esit kalsin")

            if visibility(landmarks, L_SH) > 0.5 and visibility(landmarks, L_HI) > 0.5:
                p_sh = get_px(landmarks, L_SH, w, h)
                p_hi = get_px(landmarks, L_HI, w, h)
                body = calculate_angle(p_sh, p_hi, [p_hi[0], p_hi[1] + 100])
                angles["Govde"] = round(body, 1)
                if body < MIN_BODY - 8:
                    errors.append("Arkaya yaslanma")
                elif body < MIN_BODY:
                    warnings.append("Hafif yaslaniyorsun")

        # inverted=True: press tamamlanmis (buyuk aci) = UP, baslangic (kucuk aci) = DOWN
        if act:
            self._update_phase_bilateral(act, FULL_PRESS, FULL_BOTTOM, inverted=True)

        primary = sum(act.values()) / len(act) if act else None

        return FormResult(
            is_correct=len(errors) == 0,
            errors=errors, warnings=warnings,
            phase=self.phase, rep_count=self.rep_count,
            angles=angles, landmark_colors=lc,
            primary_angle=round(primary, 1) if primary else None,
            primary_range=(60, 180),
        )
