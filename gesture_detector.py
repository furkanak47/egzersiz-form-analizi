"""
El jesti ile egzersiz secimi (AI auto-detection yedegi).

Basparmak HARIC 4 parmak sayilir.
Parmak sayisini 1.5 saniye sabit tutunca egzersiz secilir.

  0 (yumruk)  → Squat
  1 parmak    → Biceps Curl
  2 parmak    → Push-up
  3 parmak    → Shoulder Press
  4 parmak    → Bench Press
"""

import time
import cv2
import mediapipe as mp
from typing import Optional

# İşaret, orta, yüzük, serçe — başparmak yok
_TIPS = [8,  12, 16, 20]
_PIPS = [6,  10, 14, 18]

GESTURE_EXERCISE_MAP = {
    0: "squat",
    1: "biceps_curl",
    2: "push_up",
    3: "shoulder_press",
    4: "bench_press",
}

GESTURE_LABELS = {
    0: "yumruk (0)   Squat",
    1: "1 parmak     Biceps Curl",
    2: "2 parmak     Push-up",
    3: "3 parmak     Shoulder Press",
    4: "4 parmak     Bench Press",
}

HOLD_SECONDS = 1.5


class GestureDetector:
    def __init__(self):
        self._hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            model_complexity=0,
            min_detection_confidence=0.75,
            min_tracking_confidence=0.6,
        )
        self._last_count: Optional[int] = None
        self._hold_start: Optional[float] = None
        self.current_count: Optional[int] = None
        self.hold_progress: float = 0.0

    def _count_fingers(self, lm_list) -> int:
        """Başparmak hariç kaç parmak açık? (0-4)"""
        count = 0
        for tip, pip in zip(_TIPS, _PIPS):
            # Parmak ucu PIP ekleminin üstündeyse (y küçük = yukarı) açık sayılır
            if lm_list[tip].y < lm_list[pip].y:
                count += 1
        return count

    def update(self, frame_bgr: "np.ndarray", now: float):
        """
        Her frame çağrılır.
        Döner: confirmed_exercise (str) veya None
        """
        # Küçük frame'de işle
        small = cv2.resize(frame_bgr, (320, 240))
        rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        res = self._hands.process(rgb)
        rgb.flags.writeable = True

        if res.multi_hand_landmarks:
            lm = res.multi_hand_landmarks[0].landmark
            count = self._count_fingers(lm)
        else:
            count = None

        self.current_count = count

        # Hold mantığı
        confirmed = None
        if count is not None and count == self._last_count:
            if self._hold_start is None:
                self._hold_start = now
            elapsed = now - self._hold_start
            self.hold_progress = min(1.0, elapsed / HOLD_SECONDS)
            if elapsed >= HOLD_SECONDS:
                confirmed = GESTURE_EXERCISE_MAP.get(count)
                self._hold_start = None   # sonraki onay için sıfırla
                self.hold_progress = 0.0
        else:
            self._last_count = count
            self._hold_start = None
            self.hold_progress = 0.0

        return confirmed

    def close(self):
        self._hands.close()
