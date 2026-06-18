"""
Uygulama ici form veri etiketleyici.

main.py kullanimi:
    dc = DataCollector("biceps_curl")
    dc.start_rep()
    dc.add_frame(angles_dict)       # her karede
    dc.finish_rep("correct")        # veya "insufficient_range" vb.
    dc.save()                       # oturumu CSV'ye yaz
"""

import csv
import time
from pathlib import Path
from typing import Optional, List, Dict

from ml.feature_extractor import extract_rep_features, FEATURE_NAMES

DATA_DIR = Path(__file__).parent.parent / "data" / "form_data"

VALID_LABELS = [
    "correct",
    "wrong",
    "insufficient_range",
    "asymmetric",
    "too_fast",
    "incomplete_extension",
]

LABEL_KEYS = {
    "c": "correct",
    "1": "correct",
    "w": "wrong",
    "0": "wrong",
    "i": "insufficient_range",
    "2": "insufficient_range",
    "a": "asymmetric",
    "3": "asymmetric",
    "f": "too_fast",
    "4": "too_fast",
    "x": "incomplete_extension",
    "5": "incomplete_extension",
}


class DataCollector:
    def __init__(self, exercise: str, primary: str = "l_elbow"):
        self.exercise = exercise
        self.primary  = primary
        self._frames: List[Dict[str, float]] = []
        self._pending: List[dict] = []   # {features, label} listesi
        self._active  = False
        self._t0      = 0.0

    def start_rep(self):
        self._frames.clear()
        self._active = True
        self._t0     = time.time()

    def add_frame(self, angles: Dict[str, float]):
        if self._active:
            self._frames.append(dict(angles))

    def cancel_rep(self):
        """Yarida kalan/hatalı tekrari iptal et."""
        self._frames.clear()
        self._active = False

    def finish_rep(self, label: str) -> bool:
        """
        Tekrari etiketle ve bekleyen listeye ekle.
        label: VALID_LABELS icerisinden biri veya LABEL_KEYS anahtari.
        Doner True basarili, False yetersiz frame / gecersiz label.
        """
        self._active = False
        if label in LABEL_KEYS:
            label = LABEL_KEYS[label]
        if label not in VALID_LABELS:
            self._frames.clear()
            return False

        feat = extract_rep_features(self._frames, primary=self.primary)
        self._frames.clear()
        if feat is None:
            return False

        row = dict(zip(FEATURE_NAMES, feat.tolist()))
        row["label"] = label
        self._pending.append(row)
        return True

    def pending_count(self) -> int:
        return len(self._pending)

    def save(self) -> int:
        """Bekleyen repları CSV'ye ekler. Doner: kaydedilen satir sayisi."""
        if not self._pending:
            return 0
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        path    = DATA_DIR / f"{self.exercise}.csv"
        is_new  = not path.exists()
        with open(path, "a", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=FEATURE_NAMES + ["label"])
            if is_new:
                writer.writeheader()
            writer.writerows(self._pending)
        n = len(self._pending)
        self._pending.clear()
        return n

    def key_to_label(self, key: str) -> Optional[str]:
        """Klavye tusundan label dondurur, bilinmiyorsa None."""
        return LABEL_KEYS.get(key.lower())

    @staticmethod
    def label_hint() -> str:
        return "Etiket: C=Dogru  I=YetersizAralik  A=Asimetri  F=HizliHareket  X=EksikUzanma"
