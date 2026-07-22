"""Feature Importance via Random Forest and XGBoost.

Trains RF and XGBoost models on historical signal data to determine which
features are most predictive of future_7d_return. Outputs a ranked table
in both Markdown and CSV format.

Usage:
    cd analysis_tools && venv\\Scripts\\activate && python feature_importance.py
"""

import csv
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
V5_DATA_DIR = os.path.join(BASE_DIR, "..", "v5_scanner", "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "..", "v5_scanner", "analysis")

# Import header from data_loader (used for validation if needed)
sys.path.insert(0, os.path.join(BASE_DIR, "..", "v5_scanner"))
from data_loader import get_csv_header

TARGET = "future_7d_return"

NUMERICAL_FEATURES = [
    "score_oi_breakout", "score_oi_expansion", "score_oi_mid_change", "score_taker",
    "oi_value", "oi_change_short", "oi_change_mid", "oi_breakout_strength", "oi_expansion",
    "taker_buy_ratio", "volume_ratio", "dist_ma25", "dist_ma99",
    "dist_support_low", "dist_high", "structure_score",
    "btc_dist_ma99", "eth_dist_ma99",
]

CATEGORICAL_FEATURES = {
    "funding_bucket": {"NEGATIVE": -1, "NEUTRAL": 0, "POSITIVE": 1},
    "volume_bucket": {"LOW": 0, "NORMAL": 1, "HIGH": 2, "EXTREME": 3},
    "market_regime": {"BEAR": -1, "MIXED": 0, "BULL": 1},
    "is_overextended": {"False": 0, "True": 1},
}

HEADER = get_csv_header()


def load_data():
    """Load all signals_*.csv files from the V5 data directory.

    Uses csv.DictReader without explicit fieldnames so the header row
    is automatically skipped and used as dictionary keys.
    """
    rows = []
    if not os.path.exists(V5_DATA_DIR):
        return rows
    for filename in sorted(os.listdir(V5_DATA_DIR)):
        if not (filename.startswith("signals_") and filename.endswith(".csv")):
            continue
        filepath = os.path.join(V5_DATA_DIR, filename)
        try:
            with open(filepath, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    rows.append(row)
        except Exception:
            continue
    return rows


def prepare_features(rows):
    """Convert CSV rows to feature matrix X and target vector y."""
    X, y = [], []

    for row in rows:
        target_val = row.get(TARGET, "")
        if not target_val or target_val.strip() == "" or target_val == "N/A":
            continue
        try:
            target = float(target_val.replace("%", "").strip())
        except ValueError:
            continue

        features = []
        valid = True

        for feat in NUMERICAL_FEATURES:
            val = row.get(feat, "")
            if not val or val.strip() == "":
                valid = False
                break
            try:
                features.append(float(val))
            except ValueError:
                valid = False
                break

        if not valid:
            continue

        for feat_name, mapping in CATEGORICAL_FEATURES.items():
            val = row.get(feat_name, "NEUTRAL")
            features.append(mapping.get(val, 0))

        X.append(features)
        y.append(target)

    return X, y


def main():
    try:
        import numpy as np
        from sklearn.ensemble import RandomForestRegressor
        import xgboost as xgb
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Please activate the analysis_tools venv first:")
        print("  Windows: analysis_tools\\venv\\Scripts\\activate.bat")
        print("  Linux:   source analysis_tools/venv/bin/activate")
        sys.exit(1)

    rows = load_data()
    if not rows:
        print("No data found. Run migrate_v4.py first.")
        sys.exit(1)

    print(f"Loaded {len(rows):,} signals. Preparing features...")
    X, y = prepare_features(rows)
    if len(X) < 100:
        print(f"Only {len(X)} valid samples. Need at least 100 for reliable results.")
        sys.exit(1)

    X_arr = np.array(X)
    y_arr = np.array(y)
    feature_names = NUMERICAL_FEATURES + list(CATEGORICAL_FEATURES.keys())

    print(f"Features: {len(feature_names)} | Samples: {len(X_arr)}")

    # Random Forest
    print("\nTraining Random Forest...")
    rf = RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42, n_jobs=-1)
    rf.fit(X_arr, y_arr)
    rf_importance = rf.feature_importances_

    # XGBoost
    print("Training XGBoost...")
    xgb_model = xgb.XGBRegressor(
        n_estimators=200, max_depth=6, learning_rate=0.1,
        random_state=42, n_jobs=-1, verbosity=0,
    )
    xgb_model.fit(X_arr, y_arr)
    xgb_importance = xgb_model.feature_importances_

    # Average importance
    avg_importance = (rf_importance + xgb_importance) / 2

    # Sort by average importance (descending)
    ranked = sorted(
        zip(feature_names, rf_importance, xgb_importance, avg_importance),
        key=lambda x: x[3],
        reverse=True,
    )

    # --- Output Markdown ---
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    md_path = os.path.join(OUTPUT_DIR, "feature_importance.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Feature Importance Report\n\n")
        f.write(f"Generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write(f"Target: `{TARGET}` | Samples: {len(X_arr):,} | Features: {len(feature_names)}\n\n")
        f.write("## Rankings\n\n")
        f.write("| Rank | Feature | RF Importance | XGBoost Importance | Average |\n")
        f.write("|------|---------|---------------|-------------------|---------|\n")
        for rank, (name, rf_imp, xgb_imp, avg_imp) in enumerate(ranked, 1):
            f.write(f"| {rank} | {name} | {rf_imp:.4f} | {xgb_imp:.4f} | {avg_imp:.4f} |\n")
        f.write("\n## Interpretation\n\n")
        f.write("- **RF Importance**: How much the Random Forest uses this feature for splits\n")
        f.write("- **XGBoost Importance**: How much XGBoost uses this feature for gain\n")
        f.write("- **Average**: Combined ranking across both models\n")

    print(f"\nFeature importance report: {md_path}")

    # --- Output CSV ---
    csv_path = os.path.join(OUTPUT_DIR, "feature_importance.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["rank", "feature", "rf_importance", "xgb_importance", "avg_importance"])
        for rank, (name, rf_imp, xgb_imp, avg_imp) in enumerate(ranked, 1):
            writer.writerow([rank, name, f"{rf_imp:.4f}", f"{xgb_imp:.4f}", f"{avg_imp:.4f}"])

    print(f"CSV data: {csv_path}")
    print("\nFeature importance analysis complete!")


if __name__ == "__main__":
    main()
