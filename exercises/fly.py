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
MAX_ELBOW_LOCK = 175.0  # dirsek kilitlenme esigi
MIN_OPEN       = 100.0  # acilik hedef acisi
MIN_BODY       = 165.0  # govde diklik esigi

# inverted=False: acilmis (buyuk aci) = DOWN, kapali (kucuk aci) = UP
FULL_OPEN  = 120.0   # kollar acik (DOWN fazi)
FULL_CLOSE =  50.0   # kollar kapali (UP fazi — pik kasılma)


class Fly(BaseExercise):
    def __init__(self):
        super().__init__("Fly / Pec Fly")

    def analyze(self, landmarks, w, h):
        errors, warnings = [], []
        angles = {}
        lc     = {}
        in_motion = self.phase != "IDLE"

        vis_ok = all(
            visibility(landmarks, idx) > 0.5
            for idx in [L_SH, R_SH, L_WR, R_WR, L_EL, R_EL]
        )
        if not vis_ok:
            return FormResult(False, ["Vucut tam gorunur degil"], [],
                              self.phase, self.rep_count, angles, lc,
                              primary_angle=None, primary_range=(0, 180))

        p_lsh = get_px(landmarks, L_SH, w, h)
        p_rsh = get_px(landmarks, R_SH, w, h)
        p_lel = get_px(landmarks, L_EL, w, h)
        p_rel = get_px(landmarks, R_EL, w, h)
        p_lwr = get_px(landmarks, L_WR, w, h)
        p_rwr = get_px(landmarks, R_WR, w, h)

        mid = [(p_lsh[0] + p_rsh[0]) // 2, (p_lsh[1] + p_rsh[1]) // 2]

        open_angle = calculate_angle(p_lwr, mid, p_rwr)
        l_elbow    = calculate_angle(p_lsh, p_lel, p_lwr)
        r_elbow    = calculate_angle(p_rsh, p_rel, p_rwr)

        angles["Acilma acisi"] = round(open_angle, 1)
        angles["Sol dirsek"]   = round(l_elbow, 1)
        angles["Sag dirsek"]   = round(r_elbow, 1)

        if in_motion:
            if l_elbow > MAX_ELBOW_LOCK:
                errors.append("Sol dirsek kilitlendi — hafif bukuk tut")
                lc[L_EL] = RED
            if r_elbow > MAX_ELBOW_LOCK:
                errors.append("Sag dirsek kilitlendi — hafif bukuk tut")
                lc[R_EL] = RED

            in_open = open_angle > 80
            if in_open and open_angle < MIN_OPEN:
                warnings.append(f"Daha genis ac ({open_angle:.0f}<{MIN_OPEN:.0f})")

            if visibility(landmarks, L_HI) > 0.5:
                p_hi = get_px(landmarks, L_HI, w, h)
                body = calculate_angle(p_lsh, p_hi, [p_hi[0], p_hi[1] + 100])
                angles["Govde"] = round(body, 1)
                if body < MIN_BODY - 6:
                    errors.append("Govdeyi dik tut")

        self._update_phase(open_angle, FULL_CLOSE, FULL_OPEN)

        return FormResult(
            is_correct=len(errors) == 0,
            errors=errors, warnings=warnings,
            phase=self.phase, rep_count=self.rep_count,
            angles=angles, landmark_colors=lc,
            primary_angle=round(open_angle, 1),
            primary_range=(0, 180),
        )
