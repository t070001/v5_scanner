# V5 Capital Flow Scanner

A **zero-dependency** Binance USDT-margined futures scanner that identifies capital flow breakouts using Open Interest (OI), Taker Buy/Sell Ratio, Volume, and Market Structure analysis.

Built on **22,000+ historical signals** from V4, V5 introduces a **Penalty Score System** — no hard filters, every signal is retained and scored.

## Features

- **OI Breakout Detection** — Spots abnormal Open Interest spikes
- **Taker Flow Analysis** — Measures aggressive buy/sell pressure
- **Volume Surge Detection** — Identifies high-relative-volume activity
- **Market Structure** — Multi-timeframe structure (5/10/20 periods)
- **Penalty Score System** — Context-aware ranking (funding, overextension, market regime)
- **Telegram Alerts** — Top 10 signals pushed to your phone (Chinese)
- **Zero Dependencies** — Pure Python stdlib, no pip install needed

## Quick Start

```bash
# Clone
git clone https://github.com/t070001/v5_scanner.git
cd v5_scanner/v5_scanner

# Setup Telegram (optional — skip for dry-run)
cp .env.example .env
# Edit .env with your bot token and chat ID

# Run once (test)
python3 scanner.py --dry-run

# Run with Telegram
python3 scanner.py
```

## Crontab (every 3 hours)

```cron
0 */3 * * * cd ~/v5_scanner/v5_scanner && /usr/bin/python3 scanner.py 2>> logs/cron_error.log
```

## Telegram Format

```
📊 資金流掃描 V5-BETA-1
時間: 2026-07-22 15:00
大盤: 🐻 BEAR (BTC -3.2% / ETH -1.8%)

━━━━━━━━━━━━━━━━━━
🥇 #1 ETHUSDT | 3,450.20
   綜合分: 78.5 | 基礎: 65.0 | 獎勵: +18 | 懲罰: -4.5
   📌 Penalty:
      🐂 牛市: -10
      💰 費率正: -8
   ✅ Bonus:
      🐻 熊市突破: +10
   OI 突破: 0.82 | 擴張: 1.45x | 費率: 0.0012%
   距推薦區: 5.2% | 類型: MA25_NEAR
```

## Scoring System

```
Final Score = Base Score + Bonus - Penalty
```

**Base Score** (same as V4):
- OI Breakout (40%) — Current OI vs 21-period max
- OI Expansion (25%) — Current OI vs 10-period avg
- OI Mid Change (20%) — OI change over ~13 periods
- Taker Ratio (15%) — Aggressive buy/sell balance

**Bonus/Penalty** (configurable in `weights.json`):
| Condition | Effect |
|-----------|--------|
| BEAR Market | +10 bonus |
| Negative Funding | +8 bonus (short squeeze potential) |
| BULL Market | -10 penalty |
| Positive Funding | -8 penalty (long crowded) |
| Overextended | -12 penalty (chasing price) |
| Low Volume | -4 penalty |

## File Structure

```
v5_scanner/
├── scanner.py        # Main orchestrator
├── indicators.py     # Pure indicator calculations
├── scoring.py        # Penalty + ranking score system
├── data_loader.py    # CSV persistence
├── notifier.py       # Telegram notifications (Chinese)
├── updater.py        # Future return backfiller (run daily)
├── migrate_v4.py     # One-time V4→V5 data migration
├── weights.json      # Configurable weights & thresholds
├── data/             # Monthly CSV database (auto-created)
├── logs/             # Daily log files (auto-created)
└── .env.example      # Telegram config template

analysis_tools/       # Local analysis (separate venv)
├── cross_analyzer.py       # Single + dual dimension analysis
├── optimize_weights.py     # Grid search weight optimization
├── feature_importance.py   # Random Forest + XGBoost
└── requirements.txt        # scikit-learn, xgboost, pandas
```

## License

MIT
