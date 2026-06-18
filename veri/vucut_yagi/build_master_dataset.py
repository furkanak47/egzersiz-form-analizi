"""
build_master_dataset.py
Combines all data sources into two output files:
  master_dataset.csv     - records with fat_pct (model training)
  population_norms.csv   - all records (population percentile reference)

Sources:
  NHANES  (BMX + DXX files, XPT format)
  ANSUR II (MALE + FEMALE CSV, measurements in mm)
  Kaggle   (BodyFat - Extended.csv)
  combined_dataset.csv   (pre-processed, already cm/kg)
"""

import pandas as pd
import numpy as np
import pyreadstat
from pathlib import Path

HERE = Path(__file__).parent


# ---------------------------------------------------------------------------
# NHANES helpers
# ---------------------------------------------------------------------------

BMX_FILES = [
    "BMX_D.xpt",
    "BMX_E.xpt",
    "BMX_F.xpt",
    "BMX_G.xpt",
    "BMX_H.xpt",
    "BMX_I.xpt",
    "BMX_J (1).xpt",
    "BMX_L.xpt",
    "P_BMX.xpt",
]

DXX_FILES = [
    "dxx_d.xpt",
    "DXX_G.xpt",
    "DXX_H.xpt",
    "DXX_I.xpt",
    "DXX_J (2).xpt",
]

# Pair each DXX file with one or more BMX files by NHANES cycle
# dxx_d covers cycle D; others are single-cycle
DXX_BMX_PAIRS = [
    ("dxx_d.xpt",      "BMX_D.xpt"),
    ("DXX_G.xpt",      "BMX_G.xpt"),
    ("DXX_H.xpt",      "BMX_H.xpt"),
    ("DXX_I.xpt",      "BMX_I.xpt"),
    ("DXX_J (2).xpt",  "BMX_J (1).xpt"),
]


def _read_xpt(path):
    df, _ = pyreadstat.read_xport(str(path))
    df.columns = df.columns.str.upper()
    return df


def load_all_bmx():
    """Load all BMX files, stack them, keep standard anthropometric columns."""
    parts = []
    for fname in BMX_FILES:
        p = HERE / fname
        if not p.exists():
            print(f"  [SKIP] {fname} not found")
            continue
        df = _read_xpt(p)
        out = pd.DataFrame()
        out["seqn"]       = df["SEQN"]
        out["weight_kg"]  = df["BMXWT"]   if "BMXWT"   in df.columns else np.nan
        out["height_cm"]  = df["BMXHT"]   if "BMXHT"   in df.columns else np.nan
        out["arm_cm"]     = df["BMXARMC"] if "BMXARMC" in df.columns else np.nan
        out["waist_cm"]   = df["BMXWAIST"]if "BMXWAIST"in df.columns else np.nan
        out["hip_cm"]     = df["BMXHIP"]  if "BMXHIP"  in df.columns else np.nan
        out["bmi_raw"]    = df["BMXBMI"]  if "BMXBMI"  in df.columns else np.nan
        out["_file"]      = fname
        parts.append(out)
        print(f"  BMX {fname}: {len(df)} rows, BMXHIP={'BMXHIP' in df.columns}")
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def load_dxx_fat():
    """Load DXX files, return SEQN -> fat_pct mapping (unique per SEQN)."""
    parts = []
    for fname in DXX_FILES:
        p = HERE / fname
        if not p.exists():
            print(f"  [SKIP] {fname} not found")
            continue
        df = _read_xpt(p)
        # Prefer DXDTOPF (total body fat %) directly
        if "DXDTOPF" in df.columns:
            sub = df[["SEQN", "DXDTOPF"]].rename(columns={"DXDTOPF": "fat_pct"})
        elif "DXDTOFAT" in df.columns and "DXDTOTOT" in df.columns:
            # fat_pct = fat_mass / total_mass * 100
            df["fat_pct"] = df["DXDTOFAT"] / df["DXDTOTOT"] * 100
            sub = df[["SEQN", "fat_pct"]]
        else:
            print(f"  [SKIP DXX] {fname}: no usable fat column")
            continue
        # Drop duplicates: dxx_d has multiple rows per SEQN; take first non-null
        sub = sub.dropna(subset=["fat_pct"])
        sub = sub.drop_duplicates(subset="SEQN", keep="first")
        print(f"  DXX {fname}: {len(sub)} unique SEQN with fat_pct")
        parts.append(sub)
    if not parts:
        return pd.DataFrame(columns=["SEQN", "fat_pct"])
    combined = pd.concat(parts, ignore_index=True)
    combined = combined.drop_duplicates(subset="SEQN", keep="first")
    return combined


def load_nhanes():
    """Build NHANES dataframe: BMX + DXX fat_pct merged on SEQN."""
    bmx_all = load_all_bmx()
    if bmx_all.empty:
        return pd.DataFrame()

    dxx_fat = load_dxx_fat()

    # Merge fat_pct onto BMX rows
    if not dxx_fat.empty:
        dxx_fat = dxx_fat.rename(columns={"SEQN": "seqn"})
        bmx_all = bmx_all.merge(dxx_fat, on="seqn", how="left")
    else:
        bmx_all["fat_pct"] = np.nan

    bmx_all["source"] = "nhanes"
    bmx_all = bmx_all.drop(columns=["seqn", "_file", "bmi_raw"], errors="ignore")
    return bmx_all


# ---------------------------------------------------------------------------
# ANSUR II
# ---------------------------------------------------------------------------

def load_ansur():
    parts = []
    for fname, sex_val in [("ANSUR_II_MALE.csv", "M"), ("ANSUR_II_FEMALE.csv", "F")]:
        p = HERE / fname
        if not p.exists():
            print(f"  [SKIP] {fname} not found")
            continue
        df = pd.read_csv(p, encoding="latin1")
        r = pd.DataFrame()
        r["weight_kg"]   = df["weight_kg"]
        r["height_cm"]   = df["stature_m"] * 100
        r["sex"]         = sex_val
        # Circumferences in mm -> cm (divide by 10)
        r["chest_cm"]    = df["chestcircumference"]      / 10
        r["waist_cm"]    = df["waistcircumference"]      / 10
        r["hip_cm"]      = df["buttockcircumference"]    / 10
        r["arm_cm"]      = df["bicepscircumferenceflexed"] / 10
        r["shoulder_cm"] = df["shouldercircumference"]   / 10
        r["neck_cm"]     = df["neckcircumference"]       / 10
        r["fat_pct"]     = np.nan
        r["source"]      = "ansur2"
        parts.append(r)
        print(f"  ANSUR {fname}: {len(df)} rows")
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


# ---------------------------------------------------------------------------
# Kaggle Body Fat
# ---------------------------------------------------------------------------

def load_kaggle():
    p = HERE / "BodyFat - Extended.csv"
    if not p.exists():
        print(f"  [SKIP] BodyFat - Extended.csv not found")
        return pd.DataFrame()
    df = pd.read_csv(p, encoding="latin1")
    r = pd.DataFrame()
    r["fat_pct"]   = df["BodyFat"]
    r["age"]       = df["Age"] if "Age" in df.columns else np.nan
    r["sex"]       = df["Sex"].str.strip().str.upper() if "Sex" in df.columns else "M"
    # The Extended CSV already has Weight in kg and Height in meters
    # (not lbs/inches as original Kaggle dataset)
    r["weight_kg"] = df["Weight"]             # already kg
    r["height_cm"] = df["Height"] * 100.0     # meters -> cm
    r["neck_cm"]   = df["Neck"]   if "Neck"    in df.columns else np.nan
    r["chest_cm"]  = df["Chest"]  if "Chest"   in df.columns else np.nan
    r["waist_cm"]  = df["Abdomen"]if "Abdomen" in df.columns else np.nan
    r["hip_cm"]    = df["Hip"]    if "Hip"     in df.columns else np.nan
    r["arm_cm"]    = df["Biceps"] if "Biceps"  in df.columns else np.nan
    r["source"]    = "kaggle"
    print(f"  Kaggle: {len(df)} rows")
    return r


# ---------------------------------------------------------------------------
# Combined dataset (pre-processed)
# ---------------------------------------------------------------------------

def load_combined():
    p = HERE / "combined_dataset.csv"
    if not p.exists():
        print(f"  [SKIP] combined_dataset.csv not found")
        return pd.DataFrame()
    df = pd.read_csv(p, encoding="latin1")
    print(f"  combined_dataset.csv: {len(df)} rows, cols={list(df.columns)}")
    # Rename to standard names if needed
    rename_map = {}
    for old, new in [("fat_pct","fat_pct"),("sex","sex"),("age","age"),
                     ("weight_kg","weight_kg"),("height_cm","height_cm"),
                     ("neck_cm","neck_cm"),("waist_cm","waist_cm"),
                     ("hip_cm","hip_cm"),("source","source")]:
        if old in df.columns and old != new:
            rename_map[old] = new
    if rename_map:
        df = df.rename(columns=rename_map)
    if "source" not in df.columns:
        df["source"] = "combined"
    return df


# ---------------------------------------------------------------------------
# Cleaning
# ---------------------------------------------------------------------------

def clean(df):
    if df.empty:
        return df
    df = df.copy()

    # Recalculate BMI from measured values
    mask_valid = df["height_cm"].notna() & df["weight_kg"].notna() & (df["height_cm"] > 0)
    df["bmi"] = np.where(
        mask_valid,
        df["weight_kg"] / (df["height_cm"] / 100.0) ** 2,
        np.nan
    )

    # Range filters
    df = df[df["height_cm"].between(140, 220)]
    df = df[df["weight_kg"].between(30, 200)]
    df = df[df["bmi"].between(13, 60)]

    if "waist_cm" in df.columns:
        m = df["waist_cm"].notna()
        df = df[~m | df["waist_cm"].between(45, 165)]
    if "hip_cm" in df.columns:
        m = df["hip_cm"].notna()
        df = df[~m | df["hip_cm"].between(50, 175)]
    if "arm_cm" in df.columns:
        m = df["arm_cm"].notna()
        df = df[~m | df["arm_cm"].between(15, 60)]
    if "fat_pct" in df.columns:
        m = df["fat_pct"].notna()
        df = df[~m | df["fat_pct"].between(2, 65)]
    if "age" in df.columns:
        m = df["age"].notna()
        df = df[~m | df["age"].between(10, 100)]

    # Derived ratios (only where inputs are available)
    if "waist_cm" in df.columns and "hip_cm" in df.columns:
        df["waist_hip_ratio"] = df["waist_cm"] / df["hip_cm"]
    if "waist_cm" in df.columns and "height_cm" in df.columns:
        df["WHtR"] = df["waist_cm"] / df["height_cm"]

    return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("Building master dataset")
    print("=" * 60)

    print("\n--- NHANES ---")
    nhanes = load_nhanes()
    if not nhanes.empty:
        nhanes = clean(nhanes)
        n_fat = nhanes["fat_pct"].notna().sum() if "fat_pct" in nhanes.columns else 0
        print(f"  NHANES after cleaning: {len(nhanes)} rows, fat_pct filled={n_fat}")

    print("\n--- ANSUR II ---")
    ansur = load_ansur()
    if not ansur.empty:
        ansur = clean(ansur)
        print(f"  ANSUR II after cleaning: {len(ansur)} rows")

    print("\n--- Kaggle ---")
    kaggle = load_kaggle()
    if not kaggle.empty:
        kaggle = clean(kaggle)
        n_fat = kaggle["fat_pct"].notna().sum()
        print(f"  Kaggle after cleaning: {len(kaggle)} rows, fat_pct filled={n_fat}")

    print("\n--- Combined dataset ---")
    combined = load_combined()
    if not combined.empty:
        combined = clean(combined)
        n_fat = combined["fat_pct"].notna().sum() if "fat_pct" in combined.columns else 0
        print(f"  Combined after cleaning: {len(combined)} rows, fat_pct filled={n_fat}")

    # ---- master_dataset: only records with fat_pct ----------------------
    print("\n--- Building master_dataset.csv ---")
    fat_parts = []
    for label, df in [("nhanes", nhanes), ("kaggle", kaggle), ("combined", combined)]:
        if df is not None and not df.empty and "fat_pct" in df.columns:
            sub = df[df["fat_pct"].notna()].copy()
            if not sub.empty:
                fat_parts.append(sub)
                print(f"  {label}: {len(sub)} rows with fat_pct")

    if fat_parts:
        master = pd.concat(fat_parts, ignore_index=True)
        master = master.dropna(subset=["fat_pct", "height_cm", "weight_kg"])
    else:
        master = pd.DataFrame()

    master.to_csv(HERE / "master_dataset.csv", index=False)
    print(f"  master_dataset.csv written: {len(master)} rows")

    # ---- population_norms: all records ----------------------------------
    print("\n--- Building population_norms.csv ---")
    all_parts = []
    for label, df in [("nhanes", nhanes), ("ansur", ansur),
                      ("kaggle", kaggle), ("combined", combined)]:
        if df is not None and not df.empty:
            all_parts.append(df)
            print(f"  {label}: {len(df)} rows")

    if all_parts:
        population = pd.concat(all_parts, ignore_index=True)
    else:
        population = pd.DataFrame()

    population.to_csv(HERE / "population_norms.csv", index=False)
    print(f"  population_norms.csv written: {len(population)} rows")

    # ---- Summary statistics ---------------------------------------------
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"master_dataset rows       : {len(master)}")
    print(f"population_norms rows     : {len(population)}")

    if not master.empty:
        print(f"\nSource distribution (master):")
        if "source" in master.columns:
            for src, cnt in master["source"].value_counts().items():
                print(f"  {src}: {cnt}")

        if "fat_pct" in master.columns:
            fp = master["fat_pct"].dropna()
            print(f"\nFat pct stats (master):")
            print(f"  mean={fp.mean():.1f}  std={fp.std():.1f}  "
                  f"min={fp.min():.1f}  max={fp.max():.1f}")

        if "age" in master.columns:
            ag = master["age"].dropna()
            if len(ag) > 0:
                print(f"\nAge distribution (master, n={len(ag)}):")
                print(f"  mean={ag.mean():.1f}  std={ag.std():.1f}  "
                      f"min={ag.min():.0f}  max={ag.max():.0f}")

        if "sex" in master.columns:
            print(f"\nSex distribution (master):")
            for s, cnt in master["sex"].value_counts().items():
                print(f"  {s}: {cnt}")

    print(f"\nColumn fill counts (master):")
    measurement_cols = [
        "weight_kg", "height_cm", "bmi", "arm_cm", "waist_cm",
        "hip_cm", "neck_cm", "chest_cm", "shoulder_cm", "fat_pct", "age", "sex"
    ]
    for col in measurement_cols:
        if col in master.columns:
            n = master[col].notna().sum()
            print(f"  {col:<18}: {n:>6} / {len(master)}")

    if not population.empty:
        print(f"\nSource distribution (population_norms):")
        if "source" in population.columns:
            for src, cnt in population["source"].value_counts().items():
                print(f"  {src}: {cnt}")

    print("\nDone.")


if __name__ == "__main__":
    main()
