import mediapipe as mp
import cv2
import numpy as np
from typing import Optional
from config import (MIN_DETECTION_CONFIDENCE, MIN_TRACKING_CONFIDENCE,
                    MODEL_COMPLEXITY, PROCESS_WIDTH, PROCESS_HEIGHT)

_DrawingSpec = mp.solutions.drawing_utils.DrawingSpec
_EMA_ALPHA   = 0.6   # mevcut frame ağırlığı; 0.4 = önceki frame ağırlığı


class _Landmark:
    """EMA sonrası koordinatları tutan hafif sarmalayıcı."""
    __slots__ = ("x", "y", "z", "visibility")

    def __init__(self, x, y, z, visibility):
        self.x, self.y, self.z, self.visibility = x, y, z, visibility


class PoseDetector:
    def __init__(self, **kwargs):
        self._mp_pose   = mp.solutions.pose
        self._mp_draw   = mp.solutions.drawing_utils
        self._mp_styles = mp.solutions.drawing_styles
        seg = kwargs.pop("enable_segmentation", False)
        complexity = kwargs.pop("model_complexity", MODEL_COMPLEXITY)
        self.pose = self._mp_pose.Pose(
            min_detection_confidence=MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=MIN_TRACKING_CONFIDENCE,
            model_complexity=complexity,
            smooth_landmarks=True,
            enable_segmentation=seg,
            smooth_segmentation=seg,
        )
        # Her frame'de yeniden oluşturmak yerine bir kez cache'le
        self._default_style = self._mp_styles.get_default_pose_landmarks_style()
        self._conn_spec     = _DrawingSpec(color=(200, 200, 200), thickness=2)

        # EMA state: shape (33, 4) → [x, y, z, visibility]
        self._ema: Optional[np.ndarray] = None
        self._last_results_id: Optional[int] = None  # aynı frame'i iki kez EMA'lamamak için

    def process(self, frame):
        small = cv2.resize(frame, (PROCESS_WIDTH, PROCESS_HEIGHT))
        rgb   = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        results = self.pose.process(rgb)
        rgb.flags.writeable = True
        return results

    def _apply_ema(self, results):
        """EMA uygulayıp düzeltilmiş _Landmark listesi döner."""
        if not results or not results.pose_landmarks:
            self._ema = None
            self._last_results_id = None
            return None

        # PoseWorker aynı results nesnesini birden fazla frame'e verebilir.
        # id kontrolüyle aynı nesneye EMA'yı tekrar uygulamamak gerekir.
        rid = id(results)
        if rid == self._last_results_id and self._ema is not None:
            return [_Landmark(*row) for row in self._ema]

        self._last_results_id = rid
        raw = results.pose_landmarks.landmark
        cur = np.array([[lm.x, lm.y, lm.z, lm.visibility] for lm in raw],
                       dtype=np.float32)

        if self._ema is None:
            self._ema = cur
        else:
            # yeni = 0.6 * şuanki + 0.4 * önceki
            self._ema = _EMA_ALPHA * cur + (1.0 - _EMA_ALPHA) * self._ema

        return [_Landmark(*row) for row in self._ema]

    def draw_skeleton(self, frame, results, landmark_colors=None):
        if not results.pose_landmarks:
            return frame

        if landmark_colors:
            style = dict(self._default_style)
            for idx, color in landmark_colors.items():
                style[idx] = _DrawingSpec(color=color, thickness=4, circle_radius=6)
            self._mp_draw.draw_landmarks(
                frame,
                results.pose_landmarks,
                self._mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=style,
                connection_drawing_spec=self._conn_spec,
            )
        else:
            self._mp_draw.draw_landmarks(
                frame,
                results.pose_landmarks,
                self._mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=self._default_style,
            )
        return frame

    def get_landmarks(self, results):
        """EMA uygulanmış landmark listesi döner. draw_skeleton raw results kullanır."""
        return self._apply_ema(results)

    def get_segmentation_mask(self, results, target_W, target_H):
        """Segmentasyon maskesini hedef çözünürlüğe yeniden ölçekleyerek döner (float32 0-1)."""
        if results is None or results.segmentation_mask is None:
            return None
        return cv2.resize(results.segmentation_mask, (target_W, target_H))

    def close(self):
        self.pose.close()
