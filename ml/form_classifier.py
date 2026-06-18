"""
Rep-bazli form kalite siniflandirici.

Kullanim (main.py icinde):
    fc = FormClassifier("biceps_curl")
    fc.add_frame(angles_dict)   # her karede cagir
    label, conf = fc.finalize_rep()   # tekrar bitince cagir → ornek: 'asymmetric', 0.87
    fc.reset()
"""

import joblib
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, List, Dict

from ml.feature_extractor import extract_rep_features

MODEL_DIR = Path(__file__).parent / "models"

LABEL_TR = {
    "correct":               "Dogru form",
    "wrong":                 "Yanlis form",
    "insufficient_range":    "Hareket yeterince genis degil",
    "asymmetric":            "Sag-sol asimetri var",
    "too_fast":              "Hareket cok hizli",
    "incomplete_extension":  "Uzanma tam degil",
}


class FormClassifier:
    def __init__(self, exercise: str):
        self.exercise = exercise
        self._frames: List[Dict[str, float]] = []
        self._clf    = None
        self._le     = None
        self._feats  = None
        self._loaded = False
        self._load()

    def _load(self):
        path = MODEL_DIR / f"{self.exercise}_form.joblib"
        if not path.exists():
            return
        try:
            bundle = joblib.load(path)
            self._clf    = bundle["clf"]
            self._le     = bundle["le"]
            self._feats  = bundle.get("features")
            self._loaded = True
        except Exception:
            pass

    @property
    def is_available(self) -> bool:
        return self._loaded

    def add_frame(self, angles: Dict[str, float]):
        """Her frame'de cagir (angles = landmarks_to_angles() sonucu)."""
        self._frames.append(angles)

    def reset(self):
        """Yeni tekrar basinda cagir."""
        self._frames.clear()

    def finalize_rep(self) -> Tuple[Optional[str], float]:
        """
        Tekrar bitince cagir.
        Doner: (label_en, confidence)  veya  (None, 0.0) model yoksa / yetersiz frame
        """
        if not self._loaded or len(self._frames) < 5:
            return None, 0.0

        # Primary anahtarini modelden degil varsayimdan al (l_elbow en yaygin)
        feat = extract_rep_features(self._frames, primary='l_elbow')
        if feat is None:
            return None, 0.0

        if self._feats:
            # egitimde kullanilan sutun siralamasina uyu
            from ml.feature_extractor import FEATURE_NAMES
            idx = [FEATURE_NAMES.index(f) if f in FEATURE_NAMES else 0
                   for f in self._feats]
            feat = feat[idx]

        proba = self._clf.predict_proba(feat.reshape(1, -1))[0]
        top   = int(np.argmax(proba))
        label = self._le.inverse_transform([top])[0]
        conf  = float(proba[top])
        return label, conf

    def label_tr(self, label: Optional[str]) -> str:
        if label is None:
            return ""
        return LABEL_TR.get(label, label)

    def reload(self):
        """Model yeniden egitildikten sonra cagir."""
        self._loaded = False
        self._load()
