"""One-time migration: V4 CSV -> V5 format. Run once, then archive."""

import csv
import os
import sys

from data_loader import get_csv_header

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
V4_DATA_DIR = os.path.join(BASE_DIR, "..", "v4_scanner", "data")
V5_DATA_DIR = os.path.join(BASE_DIR, "data")


def migrate_file(v4_path, v5_path):
    """Migrate a single V4 CSV file to V5 format."""
    v5_header = get_csv_header()
    v5_rows = []

    with open(v4_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        v4_fields = reader.fieldnames

        for row in reader:
            v5_row = {col: "" for col in v5_header}

            # Direct copy of matching fields
            for field in v4_fields:
                if field in v5_row:
                    v5_row[field] = row[field]

            # Migrated V4 data: set signal_version to V4-MIGRATED
            v5_row["signal_version"] = "V4-MIGRATED"

            # New V5 fields left empty (no data to compute)
            v5_row["base_score"] = ""
            v5_row["bonus_score"] = ""
            v5_row["penalty_score"] = ""
            v5_row["penalty_detail"] = ""
            v5_row["final_score"] = ""

            v5_rows.append(v5_row)

    os.makedirs(os.path.dirname(v5_path), exist_ok=True)
    with open(v5_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=v5_header)
        writer.writeheader()
        writer.writerows(v5_rows)

    return len(v5_rows)


def main():
    if not os.path.exists(V4_DATA_DIR):
        print(f"V4 data directory not found: {V4_DATA_DIR}")
        print("Please ensure v4_scanner/data/ exists with signals_*.csv files.")
        sys.exit(1)

    csv_files = sorted([
        f for f in os.listdir(V4_DATA_DIR)
        if f.startswith("signals_") and f.endswith(".csv")
    ])

    if not csv_files:
        print("No V4 signals_*.csv files found.")
        sys.exit(0)

    total = 0
    for filename in csv_files:
        v4_path = os.path.join(V4_DATA_DIR, filename)
        v5_path = os.path.join(V5_DATA_DIR, filename)
        count = migrate_file(v4_path, v5_path)
        total += count
        print(f"  Migrated {filename}: {count} rows -> {v5_path}")

    print(f"\nDone! Total: {total} rows migrated to V5 format in {V5_DATA_DIR}")


if __name__ == "__main__":
    main()
