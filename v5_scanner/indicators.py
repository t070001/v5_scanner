"""Pure indicator calculations. No API calls, no I/O, no side effects."""


def calculate_ma(prices, period):
    """Simple Moving Average over the last `period` values."""
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period


def get_market_structure(highs, lows, window):
    """
    Determine market structure by comparing first/second half extremes.
    Returns 'Bullish', 'Bearish', or 'Neutral'.
    """
    if len(highs) < window or len(lows) < window:
        return "Neutral"

    half = window // 2
    first_high = max(highs[-window:-half])
    first_low = min(lows[-window:-half])
    second_high = max(highs[-half:])
    second_low = min(lows[-half:])

    if second_high > first_high and second_low > first_low:
        return "Bullish"
    elif second_high < first_high and second_low < first_low:
        return "Bearish"
    return "Neutral"


def categorize_funding(funding_rate, thresholds=None):
    """
    Categorize funding rate into NEGATIVE / NEUTRAL / POSITIVE.
    thresholds dict should have keys:
        'funding_negative' (default 0) - rates below this are NEGATIVE
        'funding_positive' (default 0.0005) - rates above this are POSITIVE
    """
    if thresholds is None:
        thresholds = {"funding_negative": 0, "funding_positive": 0.0005}
    if funding_rate < thresholds.get("funding_negative", 0):
        return "NEGATIVE"
    elif funding_rate > thresholds.get("funding_positive", 0.0005):
        return "POSITIVE"
    return "NEUTRAL"


def categorize_volume(volume_ratio, thresholds=None):
    """
    Categorize volume ratio into LOW / NORMAL / HIGH / EXTREME.
    thresholds dict should have keys:
        'volume_low' (default 0.8) - ratios below this are LOW
        'volume_high' (default 1.2) - ratios at or below this (but above volume_low) are NORMAL;
                                       ratios above this but at or below volume_extreme are HIGH
        'volume_extreme' (default 2.0) - ratios above this are EXTREME
    """
    if thresholds is None:
        thresholds = {"volume_low": 0.8, "volume_high": 1.2, "volume_extreme": 2.0}
    if volume_ratio < thresholds.get("volume_low", 0.8):
        return "LOW"
    elif volume_ratio <= thresholds.get("volume_high", 1.2):
        return "NORMAL"
    elif volume_ratio <= thresholds.get("volume_extreme", 2.0):
        return "HIGH"
    return "EXTREME"


def categorize_structure_score(score):
    """Return (low, high) bucket for structure score."""
    if score < 25:
        return (0, 25)
    elif score < 50:
        return (25, 50)
    elif score < 75:
        return (50, 75)
    return (75, 100)


def calculate_oi_breakout(oi_values):
    """
    OI breakout strength: how much current OI exceeds the max of previous 21 periods.
    30% breakout -> score 1.0 (capped).
    """
    if len(oi_values) < 22:
        return 0.0
    current_oi = oi_values[-1]
    prev_max = max(oi_values[-21:-1])
    if prev_max <= 0:
        return 0.0
    breakout_pct = (current_oi - prev_max) / prev_max
    return max(0.0, min(breakout_pct / 0.30, 1.0))


def calculate_oi_expansion(oi_values):
    """
    OI expansion: ratio of current OI to average of previous 10 periods.
    50% expansion -> score 1.0 (capped).
    """
    if len(oi_values) < 11:
        return 0.0
    current_oi = oi_values[-1]
    prev_avg = sum(oi_values[-11:-1]) / 10
    if prev_avg <= 0:
        return 0.0
    expansion = current_oi / prev_avg
    return max(0.0, min((expansion - 1.0) / 0.50, 1.0))


def calculate_oi_mid_change(oi_values):
    """
    OI mid-term change: percentage change over ~13 periods.
    50% change -> score 1.0 (capped).
    """
    if len(oi_values) < 13:
        return 0.0
    current_oi = oi_values[-1]
    prev_oi = oi_values[-13]
    if prev_oi <= 0:
        return 0.0
    change = (current_oi - prev_oi) / prev_oi
    return max(0.0, min(change / 0.50, 1.0))


def calculate_overextended(dist_ma25, dist_support_low, dist_high, thresholds):
    """
    Check if price is overextended (chasing high).
    Any condition triggers -> True.
    thresholds dict must have keys:
        'overextended_ma25', 'overextended_support', 'overextended_high'
    """
    if dist_ma25 > thresholds.get("overextended_ma25", 30.0):
        return True
    if dist_support_low > thresholds.get("overextended_support", 40.0):
        return True
    if dist_high > thresholds.get("overextended_high", 10.0):
        return True
    return False


# Note: get_market_regime() is intentionally in scanner.py because it requires API calls (indicators are pure).
