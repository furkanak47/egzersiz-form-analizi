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

# Ayakta on kameradan analiz: kablo gogus press / smith machine
# NOT: yatik barbell bench press bu kamera kurulumu ile analiz edilemez.
#
# Hareket esikleri (ampirik tahmin — egitim verisiyle kalibre edilmeli)
# inverted=False: kollar bukulu (kucuk aci) = UP, kollar uzatilmis (buyuk aci) = DOWN
FULL_PUSH    = 150.0  # kollar uzatilmis (DOWN fazi)
FULL_BOTTOM  =  80.0  # dirsek bukulu, gogus hizasinda (UP fazi)
MIN_EXTEND   = 155.0  # tam uzatma uyari esigi
MAX_FLARE    =  75.0  # dirsek yana acilma esigi


class BenchPress(BaseExercise):
    """Gogus Press — on kamera, ayakta (kablo / smith machine)."""

    CAL_PEAK_ATTR = "FULL_PUSH"
    CAL_REST_ATTR = "FULL_BOTTOM"
    CAL_WARN_PEAK = "MIN_EXTEND"
    CAL_WARN_REST = None
    CAL_INVERTED  = True

    def __init__(self):
        super().__init__("Gogus Press")

    def analyze(self, landmarks, w, h):
        errors, warnings = [], []
        angles  = {}
        lc      = {}
        act     = {}
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
            lc[el] = WHITE

            if in_motion:
                # Tam uzatma kontrolu
                if elbow > 120 and elbow < MIN_EXTEND:
                    warnings.append(f"{lbl} kol tam uzatilmiyor ({elbow:.0f})")
                    lc[el] = YELLOW
                elif elbow >= MIN_EXTEND:
                    lc[el] = GREEN

                # Dirsek yana acilmasi
                flare = calculate_angle(p_hi, p_sh, p_el)
                angles[f"{lbl} flare"] = round(flare, 1)
                if flare > MAX_FLARE + 15:
                    errors.append(f"{lbl} dirsek cok disari — ice al")
                    lc[el] = RED
                elif flare > MAX_FLARE:
                    warnings.append(f"{lbl} dirsek hafif genis")

        # inverted=False: kollar bukulu = UP (kucuk aci), uzatilmis = DOWN (buyuk aci)
        if act:
            self._update_phase_bilateral(act, FULL_BOTTOM, FULL_PUSH)

        primary = sum(act.values()) / len(act) if act else None

        return FormResult(
            is_correct=len(errors) == 0,
            errors=errors, warnings=warnings,
            phase=self.phase, rep_count=self.rep_count,
            angles=angles, landmark_colors=lc,
            primary_angle=round(primary, 1) if primary else None,
            primary_range=(40, 180),
        )
