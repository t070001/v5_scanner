"""Main scanner orchestrator. Fetch -> Analyze -> Score -> Output."""

import argparse
import io
import json
import logging
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime

from indicators import (
    calculate_ma,
    get_market_structure,
    categorize_funding,
    categorize_volume,
    calculate_oi_breakout,
    calculate_oi_expansion,
    calculate_oi_mid_change,
    calculate_overextended,
)
from scoring import load_weights, calculate_base_score, calculate_bonus, calculate_penalty_score, calculate_final_score
from data_loader import save_to_csv
from notifier import format_message, send_telegram

# ==========================================
# CONFIGURATION
# ==========================================
VOLUME_THRESHOLD = 50_000_000.0
INTERVAL = "4h"
KLINES_LIMIT = 120
OI_LIMIT = 30
TAKER_LIMIT = 30
API_BASE = "https://fapi.binance.com"
AUTO_DELETE_LOG_DAYS = 90

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# NOTE: stdout/stderr UTF-8 wrapping for Windows is done in __main__ block
# to avoid breaking pytest's capture mechanism when imported.

# ==========================================
# LOGGING
# ==========================================
def get_logger():
    logger = logging.getLogger("v5_scanner")
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)
        log_file = os.path.join(BASE_DIR, "logs", f"{datetime.now().strftime('%Y-%m-%d')}.log")
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setLevel(logging.INFO)
        fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        ch.setFormatter(fmt)
        logger.addHandler(ch)
    return logger

logger = get_logger()

# ==========================================
# ENV LOADING
# ==========================================
def load_env():
    env_path = os.path.join(BASE_DIR, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    key, val = key.strip(), val.strip()
                    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                        val = val[1:-1]
                    os.environ[key] = val

# ==========================================
# HTTP
# ==========================================
def http_get(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    req = urllib.request.Request(url, headers=headers)
    backoffs = [1, 2, 4]
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode())
        except (urllib.error.URLError, Exception) as e:
            if attempt == 3:
                logger.error(f"Error fetching {url}: {e}")
                return None
            time.sleep(backoffs[attempt])
    return None

# ==========================================
# DATA FETCHING
# ==========================================
def get_market_regime():
    """Returns (regime_str, btc_dist, eth_dist)."""
    btc_klines = http_get(f"{API_BASE}/fapi/v1/klines?symbol=BTCUSDT&interval={INTERVAL}&limit={KLINES_LIMIT}")
    eth_klines = http_get(f"{API_BASE}/fapi/v1/klines?symbol=ETHUSDT&interval={INTERVAL}&limit={KLINES_LIMIT}")

    default = ("MIXED", 0.0, 0.0)
    if not btc_klines or len(btc_klines) < KLINES_LIMIT:
        return default
    if not eth_klines or len(eth_klines) < KLINES_LIMIT:
        return default

    btc_closes = [float(k[4]) for k in btc_klines]
    eth_closes = [float(k[4]) for k in eth_klines]
    btc_ma99 = calculate_ma(btc_closes, 99)
    eth_ma99 = calculate_ma(eth_closes, 99)
    if btc_ma99 is None or eth_ma99 is None:
        return default

    btc_dist = (btc_closes[-1] - btc_ma99) / btc_ma99
    eth_dist = (eth_closes[-1] - eth_ma99) / eth_ma99

    btc_above = btc_closes[-1] > btc_ma99
    eth_above = eth_closes[-1] > eth_ma99
    if btc_above and eth_above:
        regime = "BULL"
    elif not btc_above and not eth_above:
        regime = "BEAR"
    else:
        regime = "MIXED"

    return regime, btc_dist, eth_dist

# ==========================================
# INDICATOR ASSEMBLY
# ==========================================
def assemble_indicators(symbol, klines, oi_data, taker_data, funding_rate, market_regime, thresholds):
    """Assemble all indicators for a single symbol into a flat dict."""
    closes = [float(k[4]) for k in klines]
    highs = [float(k[2]) for k in klines]
    lows = [float(k[3]) for k in klines]
    volumes = [float(k[7]) for k in klines]
    oi_values = [float(d["sumOpenInterestValue"]) for d in oi_data]
    taker_buy_ratio = float(taker_data[-1]["buySellRatio"])

    current_price = closes[-1]
    current_oi = oi_values[-1]
    current_volume = volumes[-1]
    avg_volume_20 = sum(volumes[-20:]) / 20.0
    volume_ratio = current_volume / avg_volume_20 if avg_volume_20 > 0 else 0.0

    ma25 = calculate_ma(closes, 25)
    ma99 = calculate_ma(closes, 99)
    dist_ma25 = ((current_price - ma25) / ma25) * 100 if ma25 else 0.0
    dist_ma99 = ((current_price - ma99) / ma99) * 100 if ma99 else 0.0
    support_low = min(lows[-21:-1])
    dist_support_low = ((current_price - support_low) / support_low) * 100
    high_20 = max(highs[-21:-1])
    dist_high = ((current_price - high_20) / high_20) * 100

    struct_5 = get_market_structure(highs, lows, 5)
    struct_10 = get_market_structure(highs, lows, 10)
    struct_20 = get_market_structure(highs, lows, 20)
    struct_map = {"Bullish": 100, "Neutral": 50, "Bearish": 0}
    structure_score = (struct_map[struct_5] + struct_map[struct_10] + struct_map[struct_20]) / 3.0

    is_overextended = calculate_overextended(dist_ma25, dist_support_low, dist_high, thresholds)

    oi_change_short = ((current_oi - oi_values[-4]) / oi_values[-4]) * 100 if len(oi_values) >= 4 else 0.0
    oi_change_mid = ((current_oi - oi_values[-13]) / oi_values[-13]) * 100 if len(oi_values) >= 13 else 0.0

    funding_bucket = categorize_funding(funding_rate, thresholds)
    volume_bucket = categorize_volume(volume_ratio, thresholds)

    # Entry zone logic
    dist_ma25_pct = abs(dist_ma25)
    if dist_ma25_pct < 5.0:
        entry_type = "MA25_NEAR"
        interest_zone_low = round(ma25, 4) if ma25 else 0.0
        interest_zone_high = round(ma25, 4) if ma25 else 0.0
    elif dist_high >= 0.0:
        entry_type = "PLATFORM_RETEST"
        interest_zone_low = round(high_20 * 0.98, 4)
        interest_zone_high = round(high_20 * 1.02, 4)
    elif dist_ma25_pct > 10.0:
        entry_type = "MA25_PULLBACK"
        interest_zone_low = round(ma25 * 0.98, 4) if ma25 else 0.0
        interest_zone_high = round(ma25 * 1.02, 4) if ma25 else 0.0
    else:
        entry_type = "NONE"
        interest_zone_low = ""
        interest_zone_high = ""

    if entry_type != "NONE" and interest_zone_low != "" and interest_zone_high != "":
        zone_mid = (interest_zone_low + interest_zone_high) / 2.0
        entry_distance_pct = round((abs(current_price - zone_mid) / zone_mid) * 100, 2)
    else:
        entry_distance_pct = ""

    return {
        "symbol": symbol,
        "price": current_price,
        "funding_rate": funding_rate,
        "funding_bucket": funding_bucket,
        "oi_value": current_oi,
        "oi_change_short": round(oi_change_short, 2),
        "oi_change_mid": round(oi_change_mid, 2),
        "oi_breakout_strength": round(calculate_oi_breakout(oi_values), 4),
        "oi_expansion": round(calculate_oi_expansion(oi_values), 2),
        "taker_buy_ratio": round(taker_buy_ratio, 4),
        "volume_ratio": round(volume_ratio, 2),
        "volume_bucket": volume_bucket,
        "dist_ma25": round(dist_ma25, 2),
        "dist_ma99": round(dist_ma99, 2),
        "dist_support_low": round(dist_support_low, 2),
        "dist_high": round(dist_high, 2),
        "struct_5": struct_5, "struct_10": struct_10, "struct_20": struct_20,
        "structure_score": round(structure_score, 2),
        "score_oi_breakout": round(calculate_oi_breakout(oi_values), 4),
        "score_oi_expansion": round(calculate_oi_expansion(oi_values), 4),
        "score_oi_mid_change": round(calculate_oi_mid_change(oi_values), 4),
        "score_taker": round(max(0.0, min((taker_buy_ratio - 1.0) / 0.20, 1.0)), 4),
        "is_overextended": is_overextended,
        "market_regime": market_regime,
        "signal_version": "V5-BETA-1",
        "signal_timestamp": int(time.time()),
        "btc_dist_ma99": 0.0, "eth_dist_ma99": 0.0,
        "entry_type": entry_type,
        "interest_zone_low": interest_zone_low,
        "interest_zone_high": interest_zone_high,
        "entry_distance_pct": entry_distance_pct,
    }


def analyze_single(symbol, klines, funding_rate, market_regime, btc_dist, eth_dist, signal_timestamp, thresholds):
    """Analyze one symbol. Returns indicator dict or None if data invalid."""
    if funding_rate is None:
        logger.warning(f"[{symbol}] Missing funding rate, skipping.")
        return None
    if not klines or len(klines) < KLINES_LIMIT:
        logger.warning(f"[{symbol}] Insufficient klines ({len(klines) if klines else 0}/{KLINES_LIMIT}), skipping.")
        return None

    # Fetch OI and taker data
    oi_data = http_get(f"{API_BASE}/futures/data/openInterestHist?symbol={symbol}&period={INTERVAL}&limit={OI_LIMIT}")
    if not oi_data or len(oi_data) < OI_LIMIT:
        logger.warning(f"[{symbol}] Insufficient OI data, skipping.")
        return None

    taker_data = http_get(f"{API_BASE}/futures/data/takerlongshortRatio?symbol={symbol}&period={INTERVAL}&limit={TAKER_LIMIT}")
    if not taker_data or len(taker_data) == 0:
        logger.warning(f"[{symbol}] Missing taker data, skipping.")
        return None

    indicators = assemble_indicators(symbol, klines, oi_data, taker_data, funding_rate, market_regime, thresholds)
    indicators["signal_timestamp"] = signal_timestamp
    indicators["btc_dist_ma99"] = round(btc_dist, 4)
    indicators["eth_dist_ma99"] = round(eth_dist, 4)

    return indicators

# ==========================================
# MAIN SCAN
# ==========================================
def run_scan(base_dir=None, dry_run=False):
    if base_dir is None:
        base_dir = BASE_DIR

    load_env()
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")

    weights_path = os.path.join(base_dir, "weights.json")
    if not os.path.exists(weights_path):
        logger.error(f"weights.json not found at {weights_path}")
        return
    weights = load_weights(weights_path)
    thresholds = weights["thresholds"]

    scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    scan_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    signal_timestamp = int(time.time())
    logger.info(f"=== Scan started (ID: {scan_id}) ===")

    # 1. Market regime
    market_regime, btc_dist, eth_dist = get_market_regime()
    logger.info(f"Market Regime: {market_regime} | BTC MA99: {btc_dist:.4f} | ETH MA99: {eth_dist:.4f}")

    # 2. Funding rates
    premium_data = http_get(f"{API_BASE}/fapi/v1/premiumIndex")
    funding_map = {}
    if premium_data:
        for item in premium_data:
            funding_map[item["symbol"]] = float(item.get("lastFundingRate", 0.0))

    # 3. Volume filter
    tickers = http_get(f"{API_BASE}/fapi/v1/ticker/24hr")
    if not tickers:
        logger.error("Cannot fetch ticker data.")
        return

    candidates = [
        (t["symbol"], float(t["quoteVolume"]))
        for t in tickers
        if t["symbol"].endswith("USDT") and float(t["quoteVolume"]) >= VOLUME_THRESHOLD
    ]
    logger.info(f"Candidates (>{VOLUME_THRESHOLD/1_000_000:.0f}M USDT): {len(candidates)}")

    # 4. Analyze each candidate
    results = []
    for symbol, vol in candidates:
        time.sleep(0.1)
        funding_rate = funding_map.get(symbol, None)
        klines = http_get(f"{API_BASE}/fapi/v1/klines?symbol={symbol}&interval={INTERVAL}&limit={KLINES_LIMIT}")
        try:
            res = analyze_single(symbol, klines, funding_rate, market_regime, btc_dist, eth_dist, signal_timestamp, thresholds)
            if res:
                # Score
                base = calculate_base_score(res, weights)
                bonus, bonus_details = calculate_bonus(res, weights)
                penalty, penalty_details = calculate_penalty_score(res, weights)
                final = calculate_final_score(base, bonus, penalty)

                res["base_score"] = base
                res["bonus_score"] = bonus
                res["penalty_score"] = penalty
                res["bonus_detail"] = "\n".join(f"      {d}" for d in bonus_details) if bonus_details else ""
                res["penalty_detail"] = "\n".join(f"      {d}" for d in penalty_details) if penalty_details else ""
                res["final_score"] = final

                results.append(res)
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")

    # 5. Rank
    sorted_results = sorted(results, key=lambda x: x["final_score"], reverse=True)
    for rank, d in enumerate(sorted_results, 1):
        d["is_top10"] = rank <= 10
        d["is_top20"] = rank <= 20

    logger.info(f"Scan complete. Analyzed: {len(results)} | Top score: {sorted_results[0]['final_score'] if sorted_results else 'N/A'}")

    # 6. Save
    os.makedirs(os.path.join(base_dir, "data"), exist_ok=True)
    save_to_csv(sorted_results, scan_time, scan_id, base_dir)

    # 7. Console output
    top_10 = sorted_results[:10]
    print(f"\n========= 🚀 資金流掃描 V5-BETA-1 TOP 10 =========")
    for idx, d in enumerate(top_10, 1):
        print(f"#{idx} {d['symbol']} | 綜合分: {d['final_score']} | 基礎: {d['base_score']} | 獎勵: +{d['bonus_score']} | 懲罰: {d['penalty_score']}")
        if d["penalty_detail"]:
            print(f"   Penalty:\n{d['penalty_detail']}")
        if d["bonus_detail"]:
            print(f"   Bonus:\n{d['bonus_detail']}")
        print("-" * 45)

    # 8. Telegram
    if not dry_run and token and chat_id:
        tg_text = format_message(top_10, scan_time, market_regime, btc_dist, eth_dist)
        send_telegram(tg_text, token, chat_id)
    elif dry_run:
        logger.info("[DRY RUN] Telegram skipped.")

    return sorted_results


if __name__ == "__main__":
    if sys.platform.startswith("win"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="V5 Crypto Signal Scanner")
    parser.add_argument("--loop", type=int, help="Loop interval in seconds")
    parser.add_argument("--dry-run", action="store_true", help="Skip Telegram, print results only")
    args = parser.parse_args()

    if args.loop:
        logger.info(f"Loop mode: every {args.loop}s")
        while True:
            run_scan(dry_run=args.dry_run)
            time.sleep(args.loop)
    else:
        run_scan(dry_run=args.dry_run)
