"""CSV read/write, V4 migration, and data loading utilities."""

import csv
import os
from datetime import datetime


def get_csv_header():
    """Return the V5 CSV column header."""
    return [
        "scan_id", "scan_time", "signal_timestamp", "signal_version", "scan_rank",
        "is_top10", "is_top20", "symbol", "price", "funding_rate", "funding_bucket",
        "oi_value", "oi_change_short", "oi_change_mid", "oi_breakout_strength",
        "oi_expansion", "taker_buy_ratio", "volume_ratio", "volume_bucket",
        "dist_ma25", "dist_ma99", "dist_support_low", "dist_high",
        "struct_5", "struct_10", "struct_20", "structure_score",
        "score_oi_breakout", "score_oi_expansion", "score_oi_mid_change", "score_taker",
        "is_overextended", "base_score", "bonus_score", "penalty_score", "penalty_detail",
        "final_score", "market_regime",
        "btc_dist_ma99", "eth_dist_ma99",
        "entry_type", "interest_zone_low", "interest_zone_high", "entry_distance_pct",
        "future_3d_return", "future_7d_return", "future_14d_return",
    ]


def _row_from_dict(d, rank):
    """Convert an indicator dict to a CSV row list."""
    h = get_csv_header()
    row = [""] * len(h)
    mapping = {
        "scan_id": "", "scan_time": "", "signal_timestamp": d.get("signal_timestamp", ""),
        "signal_version": d.get("signal_version", "V5-BETA-1"), "scan_rank": rank,
        "is_top10": str(d.get("is_top10", False)), "is_top20": str(d.get("is_top20", False)),
        "symbol": d["symbol"], "price": d["price"],
        "funding_rate": d["funding_rate"], "funding_bucket": d["funding_bucket"],
        "oi_value": d["oi_value"], "oi_change_short": d["oi_change_short"],
        "oi_change_mid": d["oi_change_mid"], "oi_breakout_strength": d["oi_breakout_strength"],
        "oi_expansion": d["oi_expansion"], "taker_buy_ratio": d["taker_buy_ratio"],
        "volume_ratio": d["volume_ratio"], "volume_bucket": d["volume_bucket"],
        "dist_ma25": d["dist_ma25"], "dist_ma99": d["dist_ma99"],
        "dist_support_low": d["dist_support_low"], "dist_high": d["dist_high"],
        "struct_5": d["struct_5"], "struct_10": d["struct_10"], "struct_20": d["struct_20"],
        "structure_score": d["structure_score"],
        "score_oi_breakout": d["score_oi_breakout"], "score_oi_expansion": d["score_oi_expansion"],
        "score_oi_mid_change": d["score_oi_mid_change"], "score_taker": d["score_taker"],
        "is_overextended": str(d.get("is_overextended", False)),
        "base_score": d.get("base_score", ""), "bonus_score": d.get("bonus_score", ""),
        "penalty_score": d.get("penalty_score", ""), "penalty_detail": d.get("penalty_detail", ""),
        "final_score": d.get("final_score", ""),
        "market_regime": d["market_regime"],
        "btc_dist_ma99": d.get("btc_dist_ma99", ""), "eth_dist_ma99": d.get("eth_dist_ma99", ""),
        "entry_type": d.get("entry_type", ""), "interest_zone_low": d.get("interest_zone_low", ""),
        "interest_zone_high": d.get("interest_zone_high", ""),
        "entry_distance_pct": d.get("entry_distance_pct", ""),
        "future_3d_return": "", "future_7d_return": "", "future_14d_return": "",
    }
    for i, col in enumerate(h):
        row[i] = mapping.get(col, "")
    return row


def save_to_csv(data_list, scan_time, scan_id, base_dir):
    """Save scan results to monthly CSV with atomic write."""
    header = get_csv_header()
    dt = datetime.strptime(scan_time, "%Y-%m-%d %H:%M:%S")
    month_str = dt.strftime("%Y_%m")

    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    filepath = os.path.join(data_dir, f"signals_{month_str}.csv")
    temp_filepath = os.path.join(data_dir, f"signals_{month_str}.tmp")

    existing_rows = []
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", newline="", encoding="utf-8") as rf:
                reader = csv.reader(rf)
                file_header = next(reader)
                if len(file_header) == len(header):
                    existing_rows = list(reader)
        except Exception:
            pass

    for rank, d in enumerate(data_list, 1):
        row = _row_from_dict(d, rank)
        row[0] = scan_id  # scan_id
        row[1] = scan_time  # scan_time
        existing_rows.append(row)

    try:
        with open(temp_filepath, "w", newline="", encoding="utf-8") as wf:
            writer = csv.writer(wf)
            writer.writerow(header)
            writer.writerows(existing_rows)
            wf.flush()
            os.fsync(wf.fileno())
        os.replace(temp_filepath, filepath)
    except Exception:
        if os.path.exists(temp_filepath):
            try:
                os.remove(temp_filepath)
            except OSError:
                pass
        raise


def load_all_csvs(data_dir):
    """Load all signals_*.csv files from a directory. Returns list of dicts."""
    if not os.path.exists(data_dir):
        return []

    all_rows = []

    csv_files = sorted([
        f for f in os.listdir(data_dir)
        if f.startswith("signals_") and f.endswith(".csv")
    ])

    for filename in csv_files:
        filepath = os.path.join(data_dir, filename)
        try:
            with open(filepath, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    all_rows.append(row)
        except Exception:
            continue

    return all_rows
