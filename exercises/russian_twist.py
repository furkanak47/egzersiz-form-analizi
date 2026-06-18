import mediapipe as mp
from exercises.base_exercise import BaseExercise, FormResult
from utils.angle_calculator import calculate_angle
from utils.landmark_utils import get_px, visibility
from config import GREEN, RED, YELLOW, WHITE

_lm = mp.solutions.pose.PoseLandmark
L_SH, R_SH = _lm.LEFT_SHOULDER.value,  _lm.RIGHT_SHOULDER.value
L_HI, R_HI = _lm.LEFT_HIP.value,       _lm.RIGHT_HIP.value
L_WR, R_WR = _lm.LEFT_WRIST.value,     _lm.RIGHT_WRIST.value

TWIST_THRESH = 0.08   # omuz x ekseni asimetrisi esigi (normalize)
LEAN_THRESH  = 100.0  # govde aci esigi


class RussianTwist(BaseExercise):
    def __init__(self):
        super().__init__("Russian Twist")
        self._last_side    = None   # son algilanan taraf
        self._switch_count = 0      # kac taraf degisimi oldu (2 = 1 tam rep)

    def reset(self):
        super().reset()
        self._last_side    = None
        self._switch_count = 0

    def analyze(self, landmarks, w, h):
        errors, warnings = [], []
        angles, lc = {}, {}
        in_motion = self.phase != "IDLE"

        l_sh_vis = visibility(landmarks, L_SH)
        r_sh_vis = visibility(landmarks, R_SH)
        l_hi_vis = visibility(landmarks, L_HI)

        if min(l_sh_vis, r_sh_vis) < 0.5:
            return FormResult(
                is_correct=True, errors=[], warnings=[],
                phase=self.phase, rep_count=self.rep_count,
                angles={}, landmark_colors={},
            )

        # Omuz x asimetrisi = donme miktari
        sh_diff = landmarks[L_SH].x - landmarks[R_SH].x
        angles["Donus"] = round(abs(sh_diff) * 100, 1)

        # Sol ve sag donusu ayir
        if sh_diff > TWIST_THRESH:
            side = "L"
        elif sh_diff < -TWIST_THRESH:
            side = "R"
        else:
            side = None

        if side and side != self._last_side:
            if self._last_side is not None:
                self._switch_count += 1
                if self._switch_count >= 2:   # iki taraf gecisi = 1 tam rep
                    self._try_rep()
                    self._switch_count = 0
            self._last_side = side
            self.phase = "L" if side == "L" else "R"
        elif not side:
            self.phase = "CENTER"

        # Govde acisi kontrolu
        if l_hi_vis > 0.5:
            p_sh = get_px(landmarks, L_SH, w, h)
            p_hi = get_px(landmarks, L_HI, w, h)
            ref  = [p_hi[0], p_hi[1] + 100]
            lean = calculate_angle(p_sh, p_hi, ref)
            angles["Govde"] = round(lean, 1)
            if lean < LEAN_THRESH:
                warnings.append("Govde cok dik — hafif geriye yaslan")

        lc[L_SH] = GREEN if self.phase == "L" else WHITE
        lc[R_SH] = GREEN if self.phase == "R" else WHITE

        return FormResult(
            is_correct=len(errors) == 0,
            errors=errors, warnings=warnings,
            phase=self.phase, rep_count=self.rep_count,
            angles=angles, landmark_colors=lc,
        )
