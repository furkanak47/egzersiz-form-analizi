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
# inverted=True: UP = buyuk aci (kol yukaridayken), DOWN = kucuk aci (kol yandayken)
FULL_UP      = 75.0    # kol yukarda (UP fazi — pik kasılma)
FULL_DOWN    = 25.0    # kol yanda (DOWN fazi — baslangic)
MAX_ELEV     = 112.0   # maksimum kabul edilebilir yukselme acisi
MIN_ELEV_TOP = 65.0    # UP fazinda minimum hedef aci
MAX_BEND     = 65.0    # dirsek maksimum bukukluk
MAX_TILT     = 0.03    # omuz silkme esigi
MIN_BODY     = 166.0   # govde diklik esigi


class LateralRaise(BaseExercise):
    CAL_PEAK_ATTR = "FULL_UP"
    CAL_REST_ATTR = "FULL_DOWN"
    CAL_WARN_PEAK = "MIN_ELEV_TOP"
    CAL_WARN_REST = None
    CAL_INVERTED  = True

    def __init__(self):
        super().__init__("Lateral Raise")

    def analyze(self, landmarks, w, h):
        errors, warnings = [], []
        angles = {}
        lc     = {}
        act    = {}
        in_motion = self.phase != "IDLE"

        for side, (hi_idx, sh, el, wr) in [
            ("L", (L_HI, L_SH, L_EL, L_WR)),
            ("R", (R_HI, R_SH, R_EL, R_WR)),
        ]:
            if min(visibility(landmarks, sh),
                   visibility(landmarks, el),
                   visibility(landmarks, wr)) < 0.5:
                continue

            p_hi = get_px(landmarks, hi_idx, w, h)
            p_sh = get_px(landmarks, sh,     w, h)
            p_el = get_px(landmarks, el,     w, h)
            p_wr = get_px(landmarks, wr,     w, h)
            lbl  = "Sol" if side == "L" else "Sag"

            elev = calculate_angle(p_hi, p_sh, p_wr)
            bend = 180 - calculate_angle(p_sh, p_el, p_wr)
            act[side] = elev
            angles[f"{lbl} kol acisi"] = round(elev, 1)
            lc[sh] = WHITE

            # Form kontrolu sadece kol harekete basladiginda
            in_raise = elev > FULL_DOWN
            if in_motion and in_raise:
                if elev > MAX_ELEV:
                    errors.append(f"{lbl} kol cok yukarda ({elev:.0f}>{MAX_ELEV:.0f})")
                    lc[sh] = RED
                elif elev < MIN_ELEV_TOP and self.phase == "UP":
                    warnings.append(f"{lbl} kol daha fazla kalksin ({elev:.0f})")
                    lc[sh] = YELLOW
                else:
                    lc[sh] = GREEN

                if bend > MAX_BEND:
                    warnings.append(f"{lbl} dirsek cok bukuk ({bend:.0f})")

        if in_motion:
            tilt = abs(landmarks[L_SH].y - landmarks[R_SH].y)
            if tilt > MAX_TILT + 0.02:
                warnings.append("Omuz kaldirilmamali")

            if visibility(landmarks, L_SH) > 0.5 and visibility(landmarks, L_HI) > 0.5:
                p_sh = get_px(landmarks, L_SH, w, h)
                p_hi = get_px(landmarks, L_HI, w, h)
                body = calculate_angle(p_sh, p_hi, [p_hi[0], p_hi[1] + 100])
                angles["Govde"] = round(body, 1)
                if body < MIN_BODY - 6:
                    errors.append("Govdeyi dik tut")
                elif body < MIN_BODY:
                    warnings.append("Hafif egiliyor")

        # inverted=True: kol yukarda (buyuk aci) = UP, kol yanda (kucuk aci) = DOWN
        if act:
            self._update_phase_bilateral(act, FULL_UP, FULL_DOWN, inverted=True)

        primary = sum(act.values()) / len(act) if act else None

        return FormResult(
            is_correct=len(errors) == 0,
            errors=errors, warnings=warnings,
            phase=self.phase, rep_count=self.rep_count,
            angles=angles, landmark_colors=lc,
            primary_angle=round(primary, 1) if primary else None,
            primary_range=(0, 130),
        )
