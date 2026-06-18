import mediapipe as mp
from exercises.base_exercise import BaseExercise, FormResult
from utils.angle_calculator import calculate_angle
from utils.landmark_utils import get_px, visibility
from config import GREEN, RED, YELLOW, WHITE

_lm = mp.solutions.pose.PoseLandmark
L_SH, R_SH = _lm.LEFT_SHOULDER.value,  _lm.RIGHT_SHOULDER.value
L_EL, R_EL = _lm.LEFT_ELBOW.value,     _lm.RIGHT_ELBOW.value
L_WR, R_WR = _lm.LEFT_WRIST.value,     _lm.RIGHT_WRIST.value

# Hareket esikleri (ampirik tahmin — egitim verisiyle kalibre edilmeli)
# inverted=True: UP = buyuk aci (uzatilmis), DOWN = kucuk aci (bukulu)
FULL_EXTEND  = 155.0   # tam uzatilmis (UP fazi — pik kasılma)
FULL_BENT    = 60.0    # tam bukulu (DOWN fazi — baslangic pozisyonu)
WARN_EXTEND  = 145.0   # UP fazinda bu acinin alti = yetersiz uzatma
MAX_FLARE    = 0.15    # dirsek yana acilma esigi (normalize)


class Triceps(BaseExercise):
    """Triceps overhead extension — kollar basta, dirsek yukari-asagi."""

    CAL_PEAK_ATTR = "FULL_EXTEND"
    CAL_REST_ATTR = "FULL_BENT"
    CAL_WARN_PEAK = "WARN_EXTEND"
    CAL_WARN_REST = None
    CAL_INVERTED  = True

    def __init__(self):
        super().__init__("Triceps Extension")

    def analyze(self, landmarks, w, h):
        errors, warnings = [], []
        angles = {}
        lc     = {}
        act    = {}
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
            lc[el] = GREEN if elbow >= FULL_EXTEND else WHITE

            if in_motion:
                # Kol tam uzatilmiyor (UP fazinda)
                if self.phase == "UP" and elbow < WARN_EXTEND:
                    errors.append(f"{lbl} kolu tam uzat ({elbow:.0f}<{WARN_EXTEND:.0f})")
                    lc[el] = RED

                # Dirsek yana aciliyor
                flare = abs(landmarks[el].x - landmarks[sh].x)
                if flare > MAX_FLARE + 0.05:
                    errors.append(f"{lbl} dirsek yana aciliyor — basta tut")
                    lc[el] = RED
                elif flare > MAX_FLARE:
                    warnings.append(f"{lbl} dirsek hafif aciliyor")

        # inverted=True: arm extended (buyuk aci) = UP, arm bent (kucuk aci) = DOWN
        if act:
            self._update_phase_bilateral(act, FULL_EXTEND, FULL_BENT, inverted=True)

        primary = sum(act.values()) / len(act) if act else None

        return FormResult(
            is_correct=len(errors) == 0,
            errors=errors, warnings=warnings,
            phase=self.phase, rep_count=self.rep_count,
            angles=angles, landmark_colors=lc,
            primary_angle=round(primary, 1) if primary else None,
            primary_range=(0, 180),
        )
