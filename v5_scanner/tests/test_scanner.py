import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scanner import assemble_indicators, analyze_single


def _kline(open_time=0, open_p=0, high=100, low=50, close=75, vol=1000):
    """Create a 12-element Binance kline (index 7 = quote volume)."""
    return [open_time, open_p, high, low, close, vol, 0, vol, 0, 0, 0, 0]


class TestAssembleIndicators:
    def test_returns_complete_dict(self):
        klines = [_kline() for _ in range(120)]
        klines[-1] = _kline(close=80, high=105, low=48, vol=1200)
        oi_data = [{"sumOpenInterestValue": "5000000"} for _ in range(30)]
        taker_data = [{"buySellRatio": "1.1"} for _ in range(30)]
        funding_rate = 0.0003
        market_regime = "MIXED"
        thresholds = {
            "funding_positive": 0.0005,
            "funding_negative": 0,
            "overextended_ma25": 30.0,
            "overextended_support": 40.0,
            "overextended_high": 10.0,
            "structure_low": 33,
            "structure_high": 83,
            "volume_extreme": 2.0,
            "volume_low": 0.8,
        }

        result = assemble_indicators(
            "BTCUSDT", klines, oi_data, taker_data,
            funding_rate, market_regime, thresholds,
        )

        assert result["symbol"] == "BTCUSDT"
        assert "price" in result
        assert "funding_bucket" in result
        assert "volume_bucket" in result
        assert "score_oi_breakout" in result
        assert "score_oi_expansion" in result
        assert "score_oi_mid_change" in result
        assert "score_taker" in result
        assert "structure_score" in result
        assert "is_overextended" in result


class TestAnalyzeSingle:
    def test_returns_none_on_missing_funding(self):
        result = analyze_single("BTCUSDT", None, None, "MIXED", 0.0, 0.0, 100, {})
        assert result is None

    def test_returns_none_on_insufficient_klines(self):
        result = analyze_single("BTCUSDT", [[0]*6]*5, 0.0001, "MIXED", 0.0, 0.0, 100, {})
        assert result is None
