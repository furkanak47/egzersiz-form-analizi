"""
train_comprehensive_model.py
Trains a GradientBoostingRegressor to predict body fat percentage.

Inputs  : master_dataset.csv  (built by build_master_dataset.py)
Outputs : fat_model.joblib     (best model, saved next to this script)

Feature sets compared:
  A  - BMI only
  B  - BMI + age + sex_num
  C  - full set (all available measurements)
"""

import pandas as pd
import numpy as np
import joblib
from pathlib import Path

from sklearn.ensemble import GradientBoostingRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import mean_absolute_error

HERE = Path(__file__).parent

# ---------------------------------------------------------------------------
# Feature definitions
# ---------------------------------------------------------------------------

# All possible feature columns (model handles missing via imputation)
ALL_FEATURES = [
    "height_cm",
    "weight_kg",
    "bmi",
    "age",
    "sex_num",
    "arm_cm",
    "chest_cm",
    "waist_cm",
    "hip_cm",
    "neck_cm",
    "waist_hip_ratio",
    "WHtR",
]

FEATURE_SETS = {
    "A_bmi_only":       ["bmi"],
    "B_bmi_age_sex":    ["bmi", "age", "sex_num"],
    "C_full":           ALL_FEATURES,
}

TARGET = "fat_pct"


# ---------------------------------------------------------------------------
# Data loading and feature engineering
# ---------------------------------------------------------------------------

def load_data():
    p = HERE / "master_dataset.csv"
    if not p.exists():
        raise FileNotFoundError(
            f"master_dataset.csv not found at {p}. "
            "Run build_master_dataset.py first."
        )
    df = pd.read_csv(p, encoding="latin1")
    print(f"Loaded master_dataset.csv: {len(df)} rows, cols={list(df.columns)}")

    # sex -> numeric  (M=1, F=0, unknown=NaN)
    if "sex" in df.columns:
        df["sex_num"] = df["sex"].map({"M": 1, "F": 0}).astype(float)
    else:
        df["sex_num"] = np.nan

    # Derived ratios (recalculate in case not already present)
    if "waist_cm" in df.columns and "hip_cm" in df.columns:
        df["waist_hip_ratio"] = df["waist_cm"] / df["hip_cm"].replace(0, np.nan)
    else:
        df["waist_hip_ratio"] = np.nan

    if "waist_cm" in df.columns and "height_cm" in df.columns:
        df["WHtR"] = df["waist_cm"] / df["height_cm"].replace(0, np.nan)
    else:
        df["WHtR"] = np.nan

    # Ensure all feature columns exist (fill with NaN if absent)
    for col in ALL_FEATURES:
        if col not in df.columns:
            df[col] = np.nan

    df = df.dropna(subset=[TARGET])
    print(f"After dropping missing {TARGET}: {len(df)} rows")
    return df


# ---------------------------------------------------------------------------
# Model pipeline factory
# ---------------------------------------------------------------------------

def make_pipeline():
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler",  StandardScaler()),
        ("gbr",     GradientBoostingRegressor(
            n_estimators=300,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.8,
            random_state=42,
        )),
    ])


# ---------------------------------------------------------------------------
# Evaluation helpers
# ---------------------------------------------------------------------------

def evaluate_feature_set(name, features, X_all, y, X_test, y_test):
    """5-fold CV MAE + test MAE for a given feature subset."""
    # Only keep columns that actually exist in X_all
    feat_avail = [f for f in features if f in X_all.columns]
    X_sub      = X_all[feat_avail]
    X_test_sub = X_test[feat_avail]

    pipe = make_pipeline()
    cv_scores = cross_val_score(
        pipe, X_sub, y,
        cv=5, scoring="neg_mean_absolute_error", n_jobs=-1
    )
    cv_mae = -cv_scores.mean()
    cv_std = cv_scores.std()

    pipe.fit(X_sub, y)
    test_preds = pipe.predict(X_test_sub)
    test_mae   = mean_absolute_error(y_test, test_preds)

    print(f"  {name:<22}  features={len(feat_avail):<3}  "
          f"CV MAE={cv_mae:.2f}+/-{cv_std:.2f}  Test MAE={test_mae:.2f}")
    return pipe, feat_avail, cv_mae, test_mae


# ---------------------------------------------------------------------------
# Sample predictions
# ---------------------------------------------------------------------------

def sample_predictions(pipe, features):
    """Print predicted fat % for typical BMI/sex combinations."""
    # Build synthetic rows; imputer will fill missing columns
    scenarios = [
        {"bmi": 20, "sex_num": 1, "label": "BMI=20 Male"},
        {"bmi": 20, "sex_num": 0, "label": "BMI=20 Female"},
        {"bmi": 25, "sex_num": 1, "label": "BMI=25 Male"},
        {"bmi": 25, "sex_num": 0, "label": "BMI=25 Female"},
        {"bmi": 30, "sex_num": 1, "label": "BMI=30 Male"},
        {"bmi": 30, "sex_num": 0, "label": "BMI=30 Female"},
        {"bmi": 35, "sex_num": 1, "label": "BMI=35 Male"},
        {"bmi": 35, "sex_num": 0, "label": "BMI=35 Female"},
    ]
    print("\nSample predictions (full model, other features imputed to median):")
    print(f"  {'Scenario':<20}  Predicted fat %")
    print("  " + "-" * 38)
    for s in scenarios:
        row = {f: np.nan for f in features}
        row["bmi"]     = s["bmi"]
        row["sex_num"] = s["sex_num"]
        # Rough height/weight consistent with the BMI for realism
        row["height_cm"] = 170.0
        row["weight_kg"] = s["bmi"] * (1.70 ** 2)
        df_row = pd.DataFrame([row])[features]
        pred = pipe.predict(df_row)[0]
        print(f"  {s['label']:<20}  {pred:.1f}%")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("Training comprehensive body fat model")
    print("=" * 60)

    df = load_data()

    X_all = df[ALL_FEATURES].copy()
    y     = df[TARGET].values

    X_train, X_test, y_train, y_test = train_test_split(
        X_all, y, test_size=0.15, random_state=42
    )
    print(f"Train: {len(X_train)}  Test: {len(X_test)}")

    # ---- Compare feature sets -------------------------------------------
    print("\nFeature set comparison (5-fold CV):")
    results = {}
    for set_name, feature_list in FEATURE_SETS.items():
        pipe, feat_used, cv_mae, test_mae = evaluate_feature_set(
            set_name, feature_list, X_train, y_train, X_test, y_test
        )
        results[set_name] = {
            "pipe":      pipe,
            "features":  feat_used,
            "cv_mae":    cv_mae,
            "test_mae":  test_mae,
        }

    # ---- Pick best model (lowest test MAE) --------------------------------
    best_name = min(results, key=lambda k: results[k]["test_mae"])
    best      = results[best_name]
    print(f"\nBest feature set: {best_name}  (Test MAE={best['test_mae']:.2f}%)")

    # Refit best pipeline on full training data
    best_pipe     = make_pipeline()
    best_features = best["features"]
    best_pipe.fit(X_train[best_features], y_train)
    final_test_preds = best_pipe.predict(X_test[best_features])
    final_test_mae   = mean_absolute_error(y_test, final_test_preds)
    print(f"Final model Test MAE: {final_test_mae:.2f}%")

    # ---- Feature importances (from GBR inside pipeline) -------------------
    gbr_model = best_pipe.named_steps["gbr"]
    importances = gbr_model.feature_importances_
    feat_imp = sorted(zip(best_features, importances),
                      key=lambda x: x[1], reverse=True)
    print("\nFeature importances (best model):")
    for feat, imp in feat_imp:
        bar = "#" * int(imp * 50)
        print(f"  {feat:<20}  {imp:.4f}  {bar}")

    # ---- Save model -------------------------------------------------------
    model_path = HERE / "fat_model.joblib"
    joblib.dump({
        "pipeline": best_pipe,
        "features": best_features,
        "test_mae": final_test_mae,
        "feature_set": best_name,
    }, model_path)
    print(f"\nModel saved to: {model_path}")

    # ---- Sample predictions -----------------------------------------------
    sample_predictions(best_pipe, best_features)

    # ---- Final summary -----------------------------------------------------
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    print(f"Training samples     : {len(X_train)}")
    print(f"Test samples         : {len(X_test)}")
    print(f"Best feature set     : {best_name}")
    print(f"Features used        : {len(best_features)}")
    print(f"Test MAE             : {final_test_mae:.2f}%")
    print(f"Model file           : {model_path}")

    print("\nAll feature set results:")
    for name, res in results.items():
        print(f"  {name:<22}  CV MAE={res['cv_mae']:.2f}  Test MAE={res['test_mae']:.2f}")

    print("\nDone.")


if __name__ == "__main__":
    main()
