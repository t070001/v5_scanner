import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scoring import (
    load_weights,
    calculate_base_score,
    calculate_bonus,
    calculate_penalty_score,
    calculate_final_score,
)

WEIGHTS = {
    "base_weights": {
        "oi_breakout": 0.40,
        "oi_expansion": 0.25,
        "oi_mid_change": 0.20,
        "taker": 0.15,
    },
    "bonus": {
        "bear_market": 10,
        "negative_funding": 8,
        "low_structure": 6,
        "extreme_volume": 4,
    },
    "penalty": {
        "bull_market": -10,
        "positive_funding": -8,
        "overextended": -12,
        "high_structure": -6,
        "low_volume": -4,
    },
    "thresholds": {
        "funding_positive": 0.0005,
        "funding_negative": 0,
        "structure_low": 33,
        "structure_high": 83,
        "volume_extreme": 2.0,
        "volume_low": 0.8,
    },
}


class TestLoadWeights:
    def test_loads_json_file(self, tmp_path):
        weights_file = tmp_path / "weights.json"
        weights_file.write_text(json.dumps(WEIGHTS), encoding="utf-8")
        result = load_weights(str(weights_file))
        assert result["base_weights"]["oi_breakout"] == 0.40

    def test_raises_on_missing_file(self):
        import pytest
        with pytest.raises(FileNotFoundError):
            load_weights("/nonexistent/weights.json")


class TestBaseScore:
    def test_perfect_scores(self):
        indicators = {
            "score_oi_breakout": 1.0,
            "score_oi_expansion": 1.0,
            "score_oi_mid_change": 1.0,
            "score_taker": 1.0,
        }
        score = calculate_base_score(indicators, WEIGHTS)
        assert score == 100.0

    def test_zero_scores(self):
        indicators = {
            "score_oi_breakout": 0.0,
            "score_oi_expansion": 0.0,
            "score_oi_mid_change": 0.0,
            "score_taker": 0.0,
        }
        score = calculate_base_score(indicators, WEIGHTS)
        assert score == 0.0

    def test_partial_scores(self):
        indicators = {
            "score_oi_breakout": 0.5,
            "score_oi_expansion": 0.5,
            "score_oi_mid_change": 0.5,
            "score_taker": 0.5,
        }
        score = calculate_base_score(indicators, WEIGHTS)
        assert score == 50.0


class TestBonus:
    def test_all_bonuses_apply(self):
        indicators = {
            "market_regime": "BEAR",
            "funding_bucket": "NEGATIVE",
            "structure_score": 20.0,
            "volume_ratio": 2.5,
        }
        bonus, details = calculate_bonus(indicators, WEIGHTS)
        assert bonus == 28  # 10 + 8 + 6 + 4
        assert len(details) == 4

    def test_no_bonuses(self):
        indicators = {
            "market_regime": "BULL",
            "funding_bucket": "POSITIVE",
            "structure_score": 50.0,
            "volume_ratio": 1.0,
        }
        bonus, details = calculate_bonus(indicators, WEIGHTS)
        assert bonus == 0
        assert len(details) == 0

    def test_only_bear_bonus(self):
        indicators = {
            "market_regime": "BEAR",
            "funding_bucket": "POSITIVE",
            "structure_score": 50.0,
            "volume_ratio": 1.0,
        }
        bonus, details = calculate_bonus(indicators, WEIGHTS)
        assert bonus == 10


class TestPenalty:
    def test_all_penalties_apply(self):
        indicators = {
            "market_regime": "BULL",
            "funding_bucket": "POSITIVE",
            "is_overextended": True,
            "structure_score": 90.0,
            "volume_ratio": 0.5,
        }
        penalty, details = calculate_penalty_score(indicators, WEIGHTS)
        assert penalty == -40  # -10 + -8 + -12 + -6 + -4
        assert len(details) == 5

    def test_no_penalties(self):
        indicators = {
            "market_regime": "BEAR",
            "funding_bucket": "NEGATIVE",
            "is_overextended": False,
            "structure_score": 20.0,
            "volume_ratio": 2.5,
        }
        penalty, details = calculate_penalty_score(indicators, WEIGHTS)
        assert penalty == 0
        assert len(details) == 0

    def test_only_overextended(self):
        indicators = {
            "market_regime": "MIXED",
            "funding_bucket": "NEUTRAL",
            "is_overextended": True,
            "structure_score": 50.0,
            "volume_ratio": 1.0,
        }
        penalty, details = calculate_penalty_score(indicators, WEIGHTS)
        assert penalty == -12


class TestFinalScore:
    def test_calculation(self):
        result = calculate_final_score(base=65.0, bonus=18.0, penalty=-4.5)
        assert result == 78.5

    def test_zero_everything(self):
        result = calculate_final_score(base=0.0, bonus=0.0, penalty=0.0)
        assert result == 0.0

    def test_penalty_exceeds_base(self):
        result = calculate_final_score(base=10.0, bonus=0.0, penalty=-20.0)
        assert result == -10.0
