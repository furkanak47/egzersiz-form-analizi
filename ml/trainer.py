"""
Egzersiz form kalite modeli egitici.

Kullanim:
  python ml/trainer.py --exercise biceps_curl
  python ml/trainer.py --all
"""

import argparse
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import classification_report

from ml.feature_extractor import FEATURE_NAMES, N_FEATURES

DATA_DIR   = Path(__file__).parent.parent / "data" / "form_data"
MODEL_DIR  = Path(__file__).parent / "models"
MIN_SAMPLES_PER_CLASS = 5


def train_exercise(exercise: str, verbose: bool = True) -> bool:
    csv_path = DATA_DIR / f"{exercise}.csv"
    if not csv_path.exists():
        print(f"  [{exercise}] Veri bulunamadi: {csv_path}")
        return False

    df = pd.read_csv(csv_path)
    if 'label' not in df.columns:
        print(f"  [{exercise}] CSV'de 'label' sutunu yok")
        return False

    # Yeterli veri olmayan siniflari kaldir
    counts = df['label'].value_counts()
    valid_labels = counts[counts >= MIN_SAMPLES_PER_CLASS].index
    df = df[df['label'].isin(valid_labels)]
    if df.empty:
        print(f"  [{exercise}] Yeterli veri yok (min {MIN_SAMPLES_PER_CLASS} / sinif)")
        return False

    feature_cols = [c for c in FEATURE_NAMES if c in df.columns]
    X = df[feature_cols].fillna(0).values.astype(np.float32)
    y = df['label'].values

    le = LabelEncoder()
    y_enc = le.fit_transform(y)

    if verbose:
        print(f"\n[{exercise}]")
        print(f"  Veri: {len(X)} ornek, {len(le.classes_)} sinif")
        print(f"  Siniflar: {list(le.classes_)}")

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y_enc, test_size=0.2, random_state=42, stratify=y_enc)

    clf = RandomForestClassifier(
        n_estimators=300,
        max_depth=None,
        class_weight='balanced',
        n_jobs=-1,
        random_state=42,
        min_samples_leaf=3,
    )
    clf.fit(X_tr, y_tr)

    y_pred = clf.predict(X_te)
    acc    = (y_pred == y_te).mean()

    if verbose:
        print(f"  Test dogrulugu: {acc*100:.1f}%")
        print(classification_report(y_te, y_pred,
                                    target_names=le.classes_,
                                    zero_division=0))

    # 5-fold CV (buyuk veri setleri icin)
    if len(X) >= 100:
        cv = cross_val_score(clf, X, y_enc, cv=5, scoring='accuracy', n_jobs=-1)
        if verbose:
            print(f"  5-Fold CV: {cv.mean()*100:.1f}% (+/- {cv.std()*100:.1f}%)")

    MODEL_DIR.mkdir(exist_ok=True)
    model_path = MODEL_DIR / f"{exercise}_form.joblib"
    joblib.dump({"clf": clf, "le": le, "features": feature_cols}, model_path)
    if verbose:
        print(f"  Model kaydedildi: {model_path}")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--exercise", default=None)
    parser.add_argument("--all",      action="store_true")
    parser.add_argument("-q", "--quiet", action="store_true")
    args = parser.parse_args()

    if args.all:
        targets = [p.stem for p in DATA_DIR.glob("*.csv")]
    elif args.exercise:
        targets = [args.exercise]
    else:
        print("--exercise <isim> veya --all kullan")
        targets = []

    ok = 0
    for ex in targets:
        if train_exercise(ex, verbose=not args.quiet):
            ok += 1

    print(f"\n{ok}/{len(targets)} model egitildi.")
