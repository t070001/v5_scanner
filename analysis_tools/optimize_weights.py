"""Offline weight optimization via grid search on historical data."""

import csv
import json
import os
import sys
from datetime import datetime
from itertools import product

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
V5_DATA_DIR = os.path.join(BASE_DIR, "..", "v5_scanner", "data")
WEIGHTS_DIR = os.path.join(BASE_DIR, "..", "v5_scanner")
OUTPUT_DIR = os.path.join(BASE_DIR, "..", "v5_scanner", "analysis")

CURRENT_WEIGHTS_PATH = os.path.join(WEIGHTS_DIR, "weights.json")

# Import header from data_loader
sys.path.insert(0, os.path.join(BASE_DIR, "..", "v5_scanner"))
from data_loader import get_csv_header


def parse_pct(val):
    """Parse a percentage string like '12.34%' or 'N/A' to float."""
    if not val or val.strip() == "" or val == "N/A":
        return None
    try:
        return float(val.replace("%", "").strip())
    except ValueError:
        return None


def parse_float(val):
    """Parse a numeric string to float, returning None on failure."""
    if not val or val.strip() == "":
        return None
    try:
        return float(val)
    except ValueError:
        return None


def load_current_weights():
    """Load the current weights.json from v5_scanner."""
    with open(CURRENT_WEIGHTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_signal_data():
    """Load all signals_*.csv rows as dicts."""
    header = get_csv_header()

    rows = []
    if not os.path.exists(V5_DATA_DIR):
        return rows

    for filename in sorted(os.listdir(V5_DATA_DIR)):
        if not (filename.startswith("signals_") and filename.endswith(".csv")):
            continue
        filepath = os.path.join(V5_DATA_DIR, filename)
        try:
            with open(filepath, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f, fieldnames=header)
                for row in reader:
                    rows.append(row)
        except Exception:
            continue
    return rows


def simulate_scores(rows, weights):
    """Compute final_score for each row using given weights."""
    bw = weights["base_weights"]
    bonus = weights["bonus"]
    penalty = weights["penalty"]
    thr = weights["thresholds"]

    scored = []
    for row in rows:
        ob = parse_float(row.get("score_oi_breakout")) or 0
        oe = parse_float(row.get("score_oi_expansion")) or 0
        om = parse_float(row.get("score_oi_mid_change")) or 0
        tk = parse_float(row.get("score_taker")) or 0
        base = (ob * bw["oi_breakout"] + oe * bw["oi_expansion"] +
                om * bw["oi_mid_change"] + tk * bw["taker"]) * 100

        b = 0
        regime = row.get("market_regime", "MIXED")
        if regime == "BEAR":
            b += bonus["bear_market"]
        fb = row.get("funding_bucket", "NEUTRAL")
        if fb == "NEGATIVE":
            b += bonus["negative_funding"]
        ss = parse_float(row.get("structure_score")) or 50
        if ss < thr.get("structure_low", 33):
            b += bonus["low_structure"]
        vr = parse_float(row.get("volume_ratio")) or 1.0
        if vr > thr.get("volume_extreme", 2.0):
            b += bonus["extreme_volume"]

        p = 0
        if regime == "BULL":
            p += penalty["bull_market"]
        if fb == "POSITIVE":
            p += penalty["positive_funding"]
        if row.get("is_overextended") == "True":
            p += penalty["overextended"]
        if ss > thr.get("structure_high", 83):
            p += penalty["high_structure"]
        if vr < thr.get("volume_low", 0.8):
            p += penalty["low_volume"]

        final = round(base + b + p, 2)
        r7d = parse_pct(row.get("future_7d_return"))
        scored.append({"final_score": final, "return_7d": r7d})

    return scored


def evaluate_scored(scored):
    """Evaluate how well scores predict returns. Higher avg return in top quartile = better."""
    valid = [s for s in scored if s["return_7d"] is not None]
    if len(valid) < 100:
        return -999
    valid.sort(key=lambda x: x["final_score"], reverse=True)
    top_quarter = valid[: len(valid) // 4]
    return sum(s["return_7d"] for s in top_quarter) / len(top_quarter)


def grid_search(rows):
    """Search for optimal penalty weights via grid search."""
    current = load_current_weights()
    best_score = -999
    best_weights = current

    # Search ranges around current values
    penalty_ranges = {
        "bull_market": range(-15, -5, 1),
        "positive_funding": range(-12, -4, 1),
        "overextended": range(-18, -8, 1),
        "high_structure": range(-10, -2, 1),
        "low_volume": range(-8, -1, 1),
    }

    total = 1
    for r in penalty_ranges.values():
        total *= len(list(r))
    print(f"Running grid search over {total:,} combinations...")

    for bm, pf, oe, hs, lv in product(
        penalty_ranges["bull_market"],
        penalty_ranges["positive_funding"],
        penalty_ranges["overextended"],
        penalty_ranges["high_structure"],
        penalty_ranges["low_volume"],
    ):
        trial = json.loads(json.dumps(current))
        trial["penalty"]["bull_market"] = bm
        trial["penalty"]["positive_funding"] = pf
        trial["penalty"]["overextended"] = oe
        trial["penalty"]["high_structure"] = hs
        trial["penalty"]["low_volume"] = lv

        scored = simulate_scores(rows, trial)
        score = evaluate_scored(scored)

        if score > best_score:
            best_score = score
            best_weights = trial

    return best_weights, best_score, current


def main():
    rows = load_signal_data()
    if not rows:
        print("No data found. Run migrate_v4.py first.")
        sys.exit(1)

    print(f"Loaded {len(rows):,} signals for weight optimization.")

    best_weights, best_score, current = grid_search(rows)

    # Compare current vs optimized
    current_scored = simulate_scores(rows, current)
    current_eval = evaluate_scored(current_scored)
    best_scored = simulate_scores(rows, best_weights)
    best_eval = evaluate_scored(best_scored)

    # Output optimized weights
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    opt_path = os.path.join(OUTPUT_DIR, "weights_optimized.json")
    with open(opt_path, "w", encoding="utf-8") as f:
        best_weights["meta"]["generated_by"] = "optimize_weights.py"
        best_weights["meta"]["generated_at"] = datetime.now().strftime("%Y-%m-%d")
        json.dump(best_weights, f, indent=2, ensure_ascii=False)

    # Output analysis markdown
    md_path = os.path.join(OUTPUT_DIR, "weight_analysis.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Weight Optimization Report\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write("## Evaluation Metric\n")
        f.write("Top quartile average 7d return (higher = better ranking)\n\n")
        f.write("## Results\n\n")
        f.write("| Metric | Current | Optimized |\n")
        f.write("|--------|---------|----------|\n")
        f.write(f"| Top Q 7d Avg Return | {current_eval:.2f}% | {best_eval:.2f}% |\n\n")
        f.write("## Penalty Weights Comparison\n\n")
        f.write("| Penalty | Current | Optimized |\n")
        f.write("|---------|---------|----------|\n")
        for key in ["bull_market", "positive_funding", "overextended", "high_structure", "low_volume"]:
            c = current["penalty"][key]
            o = best_weights["penalty"][key]
            f.write(f"| {key} | {c} | {o} |\n")
        f.write("\n## Instructions\n\n")
        f.write("1. Review the comparison above\n")
        f.write("2. If optimized looks better, copy:\n")
        f.write(f"   ```bash\n   cp {opt_path} {CURRENT_WEIGHTS_PATH}\n   ```\n")
        f.write("3. Run `python v5_scanner/scanner.py --dry-run` to verify\n")

    print(f"\nOptimized weights: {opt_path}")
    print(f"Analysis report: {md_path}")
    print(f"\nCurrent eval: {current_eval:.2f}% | Optimized eval: {best_eval:.2f}%")


if __name__ == "__main__":
    main()
