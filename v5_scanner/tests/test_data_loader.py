import sys
import os
import csv
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data_loader import save_to_csv, load_all_csvs, get_csv_header


class TestCSVHeader:
    def test_header_has_expected_columns(self):
        header = get_csv_header()
        assert "scan_id" in header
        assert "symbol" in header
        assert "final_score" in header
        assert "base_score" in header
        assert "bonus_score" in header
        assert "penalty_score" in header
        assert "penalty_detail" in header
        assert "future_3d_return" in header
        assert "future_7d_return" in header
        assert "future_14d_return" in header


class TestSaveToCSV:
    def test_creates_new_file(self, tmp_path):
        sample = [{
            "symbol": "BTCUSDT",
            "price": 65000.0,
            "funding_rate": 0.0001,
            "funding_bucket": "NEUTRAL",
            "oi_value": 1000000.0,
            "oi_change_short": 5.0,
            "oi_change_mid": 10.0,
            "oi_breakout_strength": 0.5,
            "oi_expansion": 1.2,
            "taker_buy_ratio": 1.1,
            "volume_ratio": 1.3,
            "volume_bucket": "HIGH",
            "dist_ma25": 2.5,
            "dist_ma99": -1.0,
            "dist_support_low": 8.0,
            "dist_high": 1.5,
            "struct_5": "Bullish",
            "struct_10": "Neutral",
            "struct_20": "Bearish",
            "structure_score": 50.0,
            "score_oi_breakout": 0.5,
            "score_oi_expansion": 0.4,
            "score_oi_mid_change": 0.3,
            "score_taker": 0.6,
            "is_overextended": False,
            "base_score": 45.0,
            "bonus_score": 6,
            "penalty_score": -4,
            "penalty_detail": "🐻 熊市突破: +6",
            "final_score": 47.0,
            "market_regime": "BEAR",
            "signal_version": "V5-BETA-1",
            "signal_timestamp": 1721625600,
            "btc_dist_ma99": -0.03,
            "eth_dist_ma99": -0.02,
            "entry_type": "MA25_NEAR",
            "interest_zone_low": 64500.0,
            "interest_zone_high": 65500.0,
            "entry_distance_pct": 0.5,
        }]
        save_to_csv(sample, "2026-07-22 15:00:00", "20260722_150000", str(tmp_path))
        data_dir = os.path.join(tmp_path, "data")
        csv_files = [f for f in os.listdir(data_dir) if f.endswith(".csv")]
        assert len(csv_files) == 1
        with open(os.path.join(data_dir, csv_files[0]), "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0][header.index("symbol")] == "BTCUSDT"

    def test_appends_to_existing_file(self, tmp_path):
        sample = [{"symbol": "BTCUSDT", "price": 65000.0, "funding_rate": 0.0001,
                    "funding_bucket": "NEUTRAL", "oi_value": 1000000.0, "oi_change_short": 5.0,
                    "oi_change_mid": 10.0, "oi_breakout_strength": 0.5, "oi_expansion": 1.2,
                    "taker_buy_ratio": 1.1, "volume_ratio": 1.3, "volume_bucket": "HIGH",
                    "dist_ma25": 2.5, "dist_ma99": -1.0, "dist_support_low": 8.0,
                    "dist_high": 1.5, "struct_5": "Bullish", "struct_10": "Neutral",
                    "struct_20": "Bearish", "structure_score": 50.0, "score_oi_breakout": 0.5,
                    "score_oi_expansion": 0.4, "score_oi_mid_change": 0.3, "score_taker": 0.6,
                    "is_overextended": False, "base_score": 45.0, "bonus_score": 6,
                    "penalty_score": -4, "penalty_detail": "", "final_score": 47.0,
                    "market_regime": "BEAR", "signal_version": "V5-BETA-1",
                    "signal_timestamp": 1721625600, "btc_dist_ma99": -0.03,
                    "eth_dist_ma99": -0.02, "entry_type": "MA25_NEAR",
                    "interest_zone_low": 64500.0, "interest_zone_high": 65500.0,
                    "entry_distance_pct": 0.5}]
        save_to_csv(sample, "2026-07-22 15:00:00", "20260722_150000", str(tmp_path))
        sample2 = [dict(sample[0], symbol="ETHUSDT")]
        save_to_csv(sample2, "2026-07-22 18:00:00", "20260722_180000", str(tmp_path))
        data_dir = os.path.join(tmp_path, "data")
        csv_files = [f for f in os.listdir(data_dir) if f.endswith(".csv")]
        assert len(csv_files) == 1
        with open(os.path.join(data_dir, csv_files[0]), "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)
            rows = list(reader)
            assert len(rows) == 2


class TestLoadAllCSVs:
    def test_loads_multiple_files(self, tmp_path):
        header = get_csv_header()
        for i, month in enumerate(["2026_06", "2026_07"]):
            filepath = tmp_path / f"signals_{month}.csv"
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(header)
                for j in range(5):
                    row = [""] * len(header)
                    row[header.index("symbol")] = f"COIN{i}{j}USDT"
                    writer.writerow(row)
        rows = load_all_csvs(str(tmp_path))
        assert len(rows) == 10

    def test_returns_empty_on_no_files(self, tmp_path):
        rows = load_all_csvs(str(tmp_path))
        assert rows == []
