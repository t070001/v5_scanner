import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from indicators import (
    calculate_ma,
    get_market_structure,
    categorize_funding,
    categorize_volume,
    categorize_structure_score,
    calculate_oi_breakout,
    calculate_oi_expansion,
    calculate_oi_mid_change,
    calculate_overextended,
)


class TestCalculateMA:
    def test_returns_none_when_insufficient_data(self):
        assert calculate_ma([1, 2], 10) is None

    def test_returns_correct_average(self):
        prices = [10.0, 20.0, 30.0, 40.0, 50.0]
        assert calculate_ma(prices, 5) == 30.0

    def test_uses_only_last_n_values(self):
        prices = [100.0, 1.0, 2.0, 3.0, 4.0]
        assert calculate_ma(prices, 3) == 3.0


class TestGetMarketStructure:
    def test_bullish(self):
        # Second half higher highs and higher lows
        highs = [10, 11, 12, 13, 14, 15, 16, 17]
        lows = [5, 6, 7, 8, 9, 10, 11, 12]
        assert get_market_structure(highs, lows, 8) == "Bullish"

    def test_bearish(self):
        # Second half lower highs and lower lows
        highs = [20, 19, 18, 17, 16, 15, 14, 13]
        lows = [15, 14, 13, 12, 11, 10, 9, 8]
        assert get_market_structure(highs, lows, 8) == "Bearish"

    def test_neutral(self):
        # Mixed signals: higher highs but lower lows
        highs = [10, 12, 11, 13, 12, 14, 13, 15]
        lows = [5, 7, 6, 4, 5, 3, 4, 2]
        assert get_market_structure(highs, lows, 8) == "Neutral"

    def test_returns_neutral_when_insufficient_data(self):
        assert get_market_structure([1, 2], [1, 2], 10) == "Neutral"


class TestCategorizeFunding:
    def test_negative(self):
        assert categorize_funding(-0.001) == "NEGATIVE"

    def test_neutral(self):
        assert categorize_funding(0.0003) == "NEUTRAL"

    def test_positive(self):
        assert categorize_funding(0.001) == "POSITIVE"

    def test_boundary_zero(self):
        assert categorize_funding(0.0) == "NEUTRAL"

    def test_boundary_positive_threshold(self):
        assert categorize_funding(0.0005) == "NEUTRAL"
        assert categorize_funding(0.0006) == "POSITIVE"


class TestCategorizeVolume:
    def test_low(self):
        assert categorize_volume(0.5) == "LOW"

    def test_normal(self):
        assert categorize_volume(1.0) == "NORMAL"

    def test_high(self):
        assert categorize_volume(1.5) == "HIGH"

    def test_extreme(self):
        assert categorize_volume(2.5) == "EXTREME"


class TestCategorizeStructureScore:
    def test_low(self):
        assert categorize_structure_score(20.0) == (0, 25)

    def test_mid_low(self):
        assert categorize_structure_score(40.0) == (25, 50)

    def test_mid_high(self):
        assert categorize_structure_score(60.0) == (50, 75)

    def test_high(self):
        assert categorize_structure_score(90.0) == (75, 100)


class TestOIMetrics:
    def test_oi_breakout_full_score(self):
        oi_values = [100.0] * 21 + [150.0]  # 50% breakout -> capped at 1.0
        assert calculate_oi_breakout(oi_values) == 1.0

    def test_oi_breakout_partial_score(self):
        oi_values = [100.0] * 21 + [115.0]  # 15% breakout
        result = calculate_oi_breakout(oi_values)
        assert 0.0 < result < 1.0

    def test_oi_breakout_zero_when_no_breakout(self):
        oi_values = [100.0] * 21 + [95.0]
        assert calculate_oi_breakout(oi_values) == 0.0

    def test_oi_expansion(self):
        oi_values = [100.0] * 10 + [100.0] * 10 + [150.0]  # 50% expansion
        result = calculate_oi_expansion(oi_values)
        assert result == 1.0

    def test_oi_mid_change(self):
        oi_values = [100.0] * 13 + [150.0]  # 50% change
        result = calculate_oi_mid_change(oi_values)
        assert result == 1.0


class TestOverextended:
    def test_not_overextended(self):
        assert calculate_overextended(
            dist_ma25=3.0, dist_support_low=10.0, dist_high=2.0, thresholds={
                "overextended_ma25": 30.0,
                "overextended_support": 40.0,
                "overextended_high": 10.0,
            }
        ) is False

    def test_overextended_by_ma25(self):
        assert calculate_overextended(
            dist_ma25=35.0, dist_support_low=10.0, dist_high=2.0, thresholds={
                "overextended_ma25": 30.0,
                "overextended_support": 40.0,
                "overextended_high": 10.0,
            }
        ) is True

    def test_overextended_by_support(self):
        assert calculate_overextended(
            dist_ma25=5.0, dist_support_low=45.0, dist_high=2.0, thresholds={
                "overextended_ma25": 30.0,
                "overextended_support": 40.0,
                "overextended_high": 10.0,
            }
        ) is True

    def test_overextended_by_high(self):
        assert calculate_overextended(
            dist_ma25=5.0, dist_support_low=10.0, dist_high=12.0, thresholds={
                "overextended_ma25": 30.0,
                "overextended_support": 40.0,
                "overextended_high": 10.0,
            }
        ) is True
