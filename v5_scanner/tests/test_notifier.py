import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from notifier import format_signal, format_message

SAMPLE_SIGNAL = {
    "symbol": "ETHUSDT",
    "price": 3450.20,
    "funding_rate": 0.0012,
    "funding_bucket": "POSITIVE",
    "oi_breakout_strength": 0.82,
    "oi_expansion": 1.45,
    "volume_ratio": 1.8,
    "dist_ma25": 2.5,
    "entry_type": "MA25_NEAR",
    "entry_distance_pct": 5.2,
    "base_score": 65.0,
    "bonus_score": 18,
    "penalty_score": -4.5,
    "penalty_detail": "\U0001f43b 熊市突破: +10\n\U0001f4c9 空頭擁擠: +8",
    "bonus_detail": "\U0001f4b0 費率正: -8",
    "final_score": 78.5,
}


class TestFormatSignal:
    def test_contains_symbol_and_rank(self):
        result = format_signal(1, SAMPLE_SIGNAL)
        assert "#1" in result
        assert "ETHUSDT" in result

    def test_contains_scores(self):
        result = format_signal(1, SAMPLE_SIGNAL)
        assert "78.5" in result
        assert "65.0" in result

    def test_contains_price(self):
        result = format_signal(1, SAMPLE_SIGNAL)
        assert "3450.2" in result

    def test_contains_penalty_detail(self):
        result = format_signal(1, SAMPLE_SIGNAL)
        assert "熊市突破" in result

    def test_rank_10_uses_correct_emoji(self):
        result = format_signal(10, SAMPLE_SIGNAL)
        assert "#10" in result


class TestFormatMessage:
    def test_contains_header(self):
        result = format_message([SAMPLE_SIGNAL], "2026-07-22 15:00:00", "BEAR", -0.032, -0.018)
        assert "V5-BETA-1" in result
        assert "2026-07-22 15:00:00" in result

    def test_contains_market_regime(self):
        result = format_message([SAMPLE_SIGNAL], "2026-07-22 15:00:00", "BEAR", -0.032, -0.018)
        assert "BEAR" in result

    def test_contains_separator(self):
        result = format_message([SAMPLE_SIGNAL], "2026-07-22 15:00:00", "MIXED", 0.0, 0.0)
        assert "━━━━" in result
