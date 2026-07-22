"""Cross Analysis: single + dual dimension win rate analysis."""

import csv
import os
import sys
from collections import defaultdict
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
V5_DATA_DIR = os.path.join(BASE_DIR, "..", "v5_scanner", "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "..", "v5_scanner", "analysis")

# Import header from data_loader
sys.path.insert(0, os.path.join(BASE_DIR, "..", "v5_scanner"))
from data_loader import get_csv_header

MIN_SAMPLES = 30


def parse_pct(val):
    if not val or val.strip() == "" or val == "N/A":
        return None
    try:
        return float(val.replace("%", "").strip())
    except ValueError:
        return None


def parse_float(val):
    if not val or val.strip() == "":
        return None
    try:
        return float(val)
    except ValueError:
        return None


def bucket_dist(val):
    if val is None:
        return "N/A"
    if val < -10:
        return "<-10%"
    elif val < -5:
        return "-10%~-5%"
    elif val < 0:
        return "-5%~0%"
    elif val < 5:
        return "0%~5%"
    elif val < 10:
        return "5%~10%"
    return ">10%"


def bucket_entry_dist(val):
    if val is None:
        return "N/A"
    if val < 5:
        return "<5%"
    elif val < 10:
        return "5%~10%"
    elif val < 20:
        return "10%~20%"
    return "20%+"


def bucket_structure(val):
    if val is None:
        return "N/A"
    if val < 25:
        return "0-25"
    elif val < 50:
        return "25-50"
    elif val < 75:
        return "50-75"
    return "75-100"


# Dimension definitions: (column_name, bucket_function)
SINGLE_DIMENSIONS = [
    ("funding_bucket", lambda r: r.get("funding_bucket", "N/A")),
    ("volume_bucket", lambda r: r.get("volume_bucket", "N/A")),
    ("structure_bucket", lambda r: bucket_structure(parse_float(r.get("structure_score")))),
    ("is_overextended", lambda r: r.get("is_overextended", "N/A")),
    ("is_top10", lambda r: r.get("is_top10", "N/A")),
    ("is_top20", lambda r: r.get("is_top20", "N/A")),
    ("market_regime", lambda r: r.get("market_regime", "N/A")),
    ("btc_dist_ma99_bucket", lambda r: bucket_dist(parse_float(r.get("btc_dist_ma99")))),
    ("entry_distance_bucket", lambda r: bucket_entry_dist(parse_float(r.get("entry_distance_pct")))),
]

# Cross dimension definitions: ((name_a, func_a), (name_b, func_b))
CROSS_DIMENSIONS = [
    ("funding_bucket", "market_regime"),
    ("funding_bucket", "structure_bucket"),
    ("funding_bucket", "volume_bucket"),
    ("market_regime", "structure_bucket"),
    ("market_regime", "volume_bucket"),
    ("volume_bucket", "structure_bucket"),
    ("is_top20", "market_regime"),
    ("entry_distance_bucket", "market_regime"),
]


def compute_stats(returns):
    valid = [r for r in returns if r is not None]
    if not valid:
        return {"count": 0, "win_rate": None, "avg": None, "median": None}
    count = len(valid)
    wins = sum(1 for r in valid if r > 0)
    avg = sum(valid) / count
    sorted_r = sorted(valid)
    mid = count // 2
    median = (sorted_r[mid - 1] + sorted_r[mid]) / 2 if count % 2 == 0 else sorted_r[mid]
    return {"count": count, "win_rate": wins / count, "avg": avg, "median": median}


def load_csv_data():
    """Load all CSV data from v5_scanner/data/."""
    if not os.path.exists(V5_DATA_DIR):
        print(f"Data directory not found: {V5_DATA_DIR}")
        sys.exit(1)

    header = get_csv_header()

    rows = []
    csv_files = sorted([
        f for f in os.listdir(V5_DATA_DIR)
        if f.startswith("signals_") and f.endswith(".csv")
    ])

    for filename in csv_files:
        filepath = os.path.join(V5_DATA_DIR, filename)
        try:
            with open(filepath, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    rows.append(row)
        except Exception:
            continue

    return rows


def run_single_analysis(rows):
    """Run single dimension analysis."""
    results = []
    for dim_name, bucket_func in SINGLE_DIMENSIONS:
        groups = defaultdict(lambda: {"3d": [], "7d": [], "14d": []})
        for row in rows:
            key = bucket_func(row)
            groups[key]["3d"].append(parse_pct(row.get("future_3d_return")))
            groups[key]["7d"].append(parse_pct(row.get("future_7d_return")))
            groups[key]["14d"].append(parse_pct(row.get("future_14d_return")))

        for group_key in sorted(groups.keys()):
            stats_3d = compute_stats(groups[group_key]["3d"])
            stats_7d = compute_stats(groups[group_key]["7d"])
            stats_14d = compute_stats(groups[group_key]["14d"])
            results.append({
                "dimension_a": dim_name,
                "dimension_b": "",
                "group_a": group_key,
                "group_b": "",
                "count": stats_3d["count"],
                "win_rate_3d": stats_3d["win_rate"],
                "avg_3d": stats_3d["avg"],
                "median_3d": stats_3d["median"],
                "win_rate_7d": stats_7d["win_rate"],
                "avg_7d": stats_7d["avg"],
                "median_7d": stats_7d["median"],
                "win_rate_14d": stats_14d["win_rate"],
                "avg_14d": stats_14d["avg"],
                "median_14d": stats_14d["median"],
            })

    return results


def run_cross_analysis(rows, dim_a_name, dim_b_name):
    """Run dual dimension cross analysis."""
    # Find bucket functions by name
    all_dims = {name: func for name, func in SINGLE_DIMENSIONS}
    func_a = all_dims.get(dim_a_name)
    func_b = all_dims.get(dim_b_name)
    if not func_a or not func_b:
        return []

    groups = defaultdict(lambda: {"3d": [], "7d": [], "14d": []})
    for row in rows:
        key_a = func_a(row)
        key_b = func_b(row)
        key = (key_a, key_b)
        groups[key]["3d"].append(parse_pct(row.get("future_3d_return")))
        groups[key]["7d"].append(parse_pct(row.get("future_7d_return")))
        groups[key]["14d"].append(parse_pct(row.get("future_14d_return")))

    results = []
    for (group_a, group_b) in sorted(groups.keys()):
        stats_3d = compute_stats(groups[(group_a, group_b)]["3d"])
        stats_7d = compute_stats(groups[(group_a, group_b)]["7d"])
        stats_14d = compute_stats(groups[(group_a, group_b)]["14d"])
        results.append({
            "dimension_a": dim_a_name,
            "dimension_b": dim_b_name,
            "group_a": group_a,
            "group_b": group_b,
            "count": stats_3d["count"],
            "win_rate_3d": stats_3d["win_rate"],
            "avg_3d": stats_3d["avg"],
            "median_3d": stats_3d["median"],
            "win_rate_7d": stats_7d["win_rate"],
            "avg_7d": stats_7d["avg"],
            "median_7d": stats_7d["median"],
            "win_rate_14d": stats_14d["win_rate"],
            "avg_14d": stats_14d["avg"],
            "median_14d": stats_14d["median"],
        })

    return results


def format_markdown(single_results, cross_results, total_signals):
    """Format results as Markdown report."""
    lines = [
        f"# Cross Analysis Report",
        f"",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Total Signals: {total_signals:,}",
        f"",
        f"---",
        f"",
        f"## Single Dimension Analysis",
        f"",
    ]

    # Group single results by dimension
    current_dim = ""
    for r in single_results:
        if r["dimension_a"] != current_dim:
            current_dim = r["dimension_a"]
            lines.append(f"### {current_dim}")
            lines.append(f"| Group | Samples | 3d Win% | 3d Avg | 3d Median | 7d Win% | 7d Avg | 14d Win% | 14d Avg |")
            lines.append(f"|-------|---------|---------|--------|-----------|---------|--------|----------|---------|")

        count = r["count"]
        label = f" [樣本不足]" if count < MIN_SAMPLES else ""
        wr3 = f"{r['win_rate_3d']*100:.1f}%" if r["win_rate_3d"] is not None else "N/A"
        a3 = f"{r['avg_3d']:.2f}%" if r["avg_3d"] is not None else "N/A"
        m3 = f"{r['median_3d']:.2f}%" if r["median_3d"] is not None else "N/A"
        wr7 = f"{r['win_rate_7d']*100:.1f}%" if r["win_rate_7d"] is not None else "N/A"
        a7 = f"{r['avg_7d']:.2f}%" if r["avg_7d"] is not None else "N/A"
        wr14 = f"{r['win_rate_14d']*100:.1f}%" if r["win_rate_14d"] is not None else "N/A"
        a14 = f"{r['avg_14d']:.2f}%" if r["avg_14d"] is not None else "N/A"
        lines.append(f"| {r['group_a']}{label} | {count:,} | {wr3} | {a3} | {m3} | {wr7} | {a7} | {wr14} | {a14} |")

    lines.extend(["", "---", "", "## Cross Dimension Analysis", ""])

    # Group cross results by dimension pair
    current_pair = ""
    for r in cross_results:
        pair = (r["dimension_a"], r["dimension_b"])
        if pair != current_pair:
            current_pair = pair
            lines.append(f"### {r['dimension_a']} × {r['dimension_b']}")
            lines.append(f"| {r['dimension_a']} | {r['dimension_b']} | Samples | 3d Win% | 3d Avg | 7d Win% | 7d Avg | 14d Win% | 14d Avg |")
            lines.append(f"|------|------|---------|---------|--------|---------|--------|----------|---------|")

        count = r["count"]
        label = f" [樣本不足]" if count < MIN_SAMPLES else ""
        wr3 = f"{r['win_rate_3d']*100:.1f}%" if r["win_rate_3d"] is not None else "N/A"
        a3 = f"{r['avg_3d']:.2f}%" if r["avg_3d"] is not None else "N/A"
        wr7 = f"{r['win_rate_7d']*100:.1f}%" if r["win_rate_7d"] is not None else "N/A"
        a7 = f"{r['avg_7d']:.2f}%" if r["avg_7d"] is not None else "N/A"
        wr14 = f"{r['win_rate_14d']*100:.1f}%" if r["win_rate_14d"] is not None else "N/A"
        a14 = f"{r['avg_14d']:.2f}%" if r["avg_14d"] is not None else "N/A"
        lines.append(f"| {r['group_a']} | {r['group_b']}{label} | {count:,} | {wr3} | {a3} | {wr7} | {a7} | {wr14} | {a14} |")

    return "\n".join(lines)


def main():
    rows = load_csv_data()
    if not rows:
        print("No data found. Run migrate_v4.py first.")
        sys.exit(1)

    print(f"Loaded {len(rows):,} signals. Running analysis...")

    single_results = run_single_analysis(rows)
    cross_results = []
    for dim_a, dim_b in CROSS_DIMENSIONS:
        cross_results.extend(run_cross_analysis(rows, dim_a, dim_b))

    # Write Markdown
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    md_path = os.path.join(OUTPUT_DIR, "cross_analysis.md")
    md_content = format_markdown(single_results, cross_results, len(rows))
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"Markdown report: {md_path}")

    # Write CSV
    csv_path = os.path.join(OUTPUT_DIR, "cross_analysis.csv")
    csv_fields = [
        "dimension_a", "dimension_b", "group_a", "group_b", "count",
        "win_rate_3d", "avg_3d", "median_3d",
        "win_rate_7d", "avg_7d", "median_7d",
        "win_rate_14d", "avg_14d", "median_14d",
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=csv_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(single_results)
        writer.writerows(cross_results)
    print(f"CSV data: {csv_path}")

    print("Cross analysis complete!")


if __name__ == "__main__":
    main()
