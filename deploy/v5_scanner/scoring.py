"""Penalty + Ranking Score System. Reads weights from weights.json."""

import json


def load_weights(weights_path):
    """Load weights from JSON file."""
    with open(weights_path, "r", encoding="utf-8") as f:
        return json.load(f)


def calculate_base_score(indicators, weights):
    """
    Base score: weighted sum of OI breakout, expansion, mid change, taker.
    Each factor is 0.0-1.0, multiplied by weight percentage, scaled to 0-100.
    """
    bw = weights.get("base_weights", {})
    score = (
        indicators.get("score_oi_breakout", 0.0) * bw.get("oi_breakout", 0.0)
        + indicators.get("score_oi_expansion", 0.0) * bw.get("oi_expansion", 0.0)
        + indicators.get("score_oi_mid_change", 0.0) * bw.get("oi_mid_change", 0.0)
        + indicators.get("score_taker", 0.0) * bw.get("taker", 0.0)
    )
    return round(score * 100, 2)


def calculate_bonus(indicators, weights):
    """Calculate bonus score. Returns (total_bonus, list_of_detail_strings)."""
    bonus = weights["bonus"]
    total = 0
    details = []

    regime = indicators.get("market_regime", "MIXED")
    if regime == "BEAR":
        total += bonus["bear_market"]
        details.append(f"\U0001f43b 熊市突破: +{bonus['bear_market']}")

    funding_bucket = indicators.get("funding_bucket", "NEUTRAL")
    if funding_bucket == "NEGATIVE":
        total += bonus["negative_funding"]
        details.append(f"\U0001f4c9 空頭擁擠: +{bonus['negative_funding']}")

    struct = indicators.get("structure_score", 50.0)
    thresholds = weights.get("thresholds", {})
    if struct < thresholds.get("structure_low", 33):
        total += bonus["low_structure"]
        details.append(f"\U0001f4ca 低結構突破: +{bonus['low_structure']}")

    vol = indicators.get("volume_ratio", 1.0)
    if vol > thresholds.get("volume_extreme", 2.0):
        total += bonus["extreme_volume"]
        details.append(f"\U0001f525 極端放量: +{bonus['extreme_volume']}")

    return total, details


def calculate_penalty_score(indicators, weights):
    """Calculate penalty score (negative). Returns (total_penalty, list_of_detail_strings)."""
    penalty = weights["penalty"]
    total = 0
    details = []

    regime = indicators.get("market_regime", "MIXED")
    if regime == "BULL":
        total += penalty["bull_market"]
        details.append(f"\U0001f402 牛市: {penalty['bull_market']}")

    funding_bucket = indicators.get("funding_bucket", "NEUTRAL")
    if funding_bucket == "POSITIVE":
        total += penalty["positive_funding"]
        details.append(f"\U0001f4b0 費率正: {penalty['positive_funding']}")

    if indicators.get("is_overextended", False):
        total += penalty["overextended"]
        details.append(f"⚠️ 過度延伸: {penalty['overextended']}")

    struct = indicators.get("structure_score", 50.0)
    thresholds = weights.get("thresholds", {})
    if struct > thresholds.get("structure_high", 83):
        total += penalty["high_structure"]
        details.append(f"\U0001f4ca 高結構: {penalty['high_structure']}")

    vol = indicators.get("volume_ratio", 1.0)
    if vol < thresholds.get("volume_low", 0.8):
        total += penalty["low_volume"]
        details.append(f"\U0001f4c9 縮量: {penalty['low_volume']}")

    return total, details


def calculate_final_score(base, bonus, penalty):
    """Final Score = Base + Bonus + Penalty (penalty is already negative)."""
    return round(base + bonus + penalty, 2)
