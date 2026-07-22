"""V5 Future Return Backfiller — 回填 3d/7d/14d 回報率

Reads V5 CSV files, fetches historical prices from Binance API,
and fills in future_3d_return, future_7d_return, future_14d_return.
Runs daily via crontab.
Zero third-party dependencies (stdlib only).
"""

import csv
import os
import time
import urllib.request
import urllib.error
import json
from datetime import datetime, timedelta

API_BASE = "https://fapi.binance.com"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")


def http_get(url):
    """GET request with retry (stdlib only)."""
    headers = {"User-Agent": "Mozilla/5.0"}
    req = urllib.request.Request(url, headers=headers)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode())
        except (urllib.error.URLError, Exception) as e:
            if attempt == 2:
                print(f"Error: {url} — {e}")
                return None
            time.sleep(1)
    return None


def get_historical_price(symbol, target_timestamp_ms):
    """Fetch price at a specific historical minute."""
    url = f"{API_BASE}/fapi/v1/klines?symbol={symbol}&interval=1m&startTime={target_timestamp_ms}&limit=1"
    klines = http_get(url)
    if klines and len(klines) > 0:
        return float(klines[0][1])  # Open price
    return None


def get_csv_header():
    """Match the exact V5 CSV header from data_loader.py."""
    from data_loader import get_csv_header as v5_header
    return v5_header()


def update_file(filepath):
    """Read CSV, backfill future returns, write back."""
    print(f"Processing: {filepath}")
    header = get_csv_header()
    col_idx = {col: i for i, col in enumerate(header)}

    rows = []
    try:
        with open(filepath, "r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            file_header = next(reader)
            if len(file_header) != len(header):
                print(f"  Header mismatch — expected {len(header)}, got {len(file_header)}. Skipping.")
                return 0
            for row in reader:
                rows.append(row)
    except Exception as e:
        print(f"  Read error: {e}")
        return 0

    now = datetime.now()
    updated = 0

    for row in rows:
        scan_time_str = row[col_idx["scan_time"]]
        try:
            scan_time = datetime.strptime(scan_time_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue

        symbol = row[col_idx["symbol"]]
        current_price = float(row[col_idx["price"]])

        periods = [
            (3, "future_3d_return"),
            (7, "future_7d_return"),
            (14, "future_14d_return"),
        ]

        for days, col_name in periods:
            idx = col_idx[col_name]
            if row[idx] != "":
                continue  # Already filled

            target_time = scan_time + timedelta(days=days)
            if now < target_time:
                continue  # Not yet due

            target_ts_ms = int(target_time.timestamp() * 1000)
            print(f"  Fetching {symbol} +{days}d price...", flush=True)
            time.sleep(0.1)

            future_price = get_historical_price(symbol, target_ts_ms)
            if future_price is not None:
                return_pct = ((future_price - current_price) / current_price) * 100
                row[idx] = f"{return_pct:.2f}%"
            else:
                row[idx] = "N/A"
            updated += 1

    if updated > 0:
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)
        print(f"  Updated {updated} fields.")
    else:
        print(f"  Nothing to update.")

    return updated


def main():
    if not os.path.exists(DATA_DIR):
        print(f"Data directory not found: {DATA_DIR}")
        return

    files = sorted([
        os.path.join(DATA_DIR, f)
        for f in os.listdir(DATA_DIR)
        if f.startswith("signals_") and f.endswith(".csv")
    ])

    if not files:
        print("No signals_*.csv files found.")
        return

    total = 0
    for filepath in files:
        total += update_file(filepath)

    print(f"\nDone. Total updates: {total}")


if __name__ == "__main__":
    main()
