"""Telegram notification with Chinese formatting."""

import json
import urllib.request
import urllib.error

RANK_EMOJIS = {1: "🥇", 2: "🥈", 3: "🥉"}

REGIME_EMOJI = {"BULL": "🐂", "BEAR": "🐻", "MIXED": "🔄"}


def format_signal(idx, signal):
    """Format a single signal for Telegram."""
    emoji = RANK_EMOJIS.get(idx, f"#{idx}")
    header = f"{emoji} #{idx} {signal['symbol']} | {signal['price']}"

    scores = (
        f"   綜合分: {signal['final_score']} | "
        f"基礎: {signal['base_score']} | "
        f"獎勵: +{signal['bonus_score']} | "
        f"懲罰: {signal['penalty_score']}"
    )

    parts = [header, scores]

    penalty_detail = signal.get("penalty_detail", "")
    if penalty_detail:
        parts.append(f"   📌 Penalty:\n{penalty_detail}")

    bonus_detail = signal.get("bonus_detail", "")
    if bonus_detail:
        parts.append(f"   ✅ Bonus:\n{bonus_detail}")

    indicators_line = (
        f"   OI 突破: {signal['oi_breakout_strength']} | "
        f"擴張: {signal['oi_expansion']}x | "
        f"費率: {signal['funding_rate']:.4f}%"
    )
    parts.append(indicators_line)

    entry_line = f"   距推薦區: {signal.get('entry_distance_pct', 'N/A')}% | 類型: {signal.get('entry_type', 'N/A')}"
    parts.append(entry_line)

    return "\n".join(parts)


def format_message(top_10, scan_time, market_regime, btc_dist, eth_dist):
    """Format full Telegram message with Top 10 signals."""
    regime_emoji = REGIME_EMOJI.get(market_regime, "🔄")
    btc_pct = f"{btc_dist * 100:.1f}%" if btc_dist is not None else "N/A"
    eth_pct = f"{eth_dist * 100:.1f}%" if eth_dist is not None else "N/A"

    header = (
        f"📊 資金流掃描 V5-BETA-1\n"
        f"時間: {scan_time}\n"
        f"大盤: {regime_emoji} {market_regime} (BTC {btc_pct} / ETH {eth_pct})"
    )

    signal_blocks = []
    for idx, signal in enumerate(top_10, 1):
        block = format_signal(idx, signal)
        signal_blocks.append("━━━━━━━━━━━━━━━━━━\n" + block)

    return header + "\n\n" + "\n\n".join(signal_blocks)


def send_telegram(text, token, chat_id):
    """Send message to Telegram. Returns True on success."""
    if not token or not chat_id:
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status == 200
    except Exception:
        return False
