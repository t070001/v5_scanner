# V5 Crypto Contract Signal Scanner - Design Document

- **Date:** 2026-07-22
- **Project:** Binance Futures Capital Flow Scanner V5
- **Status:** Approved Design

## Overview

V5 是 V4（Binance Futures Capital Flow Scanner V4-BETA-6）的下一代升級。V4 已累積 22,000+ 筆歷史信號，V5 的目標是建立一套可以持續利用歷史數據自我優化的 Scanner。

**核心理念：** 不讓人決定策略，讓資料決定策略。

**V5 第一原則：**
- 不刪除資料
- 不用 Hard Filter
- 改用 Penalty Score System
- 所有規則必須有統計依據

## V5-BETA-1 Scope

1. **Cross Analysis** — 雙變數交叉分析，輸出 Markdown + CSV
2. **Weight Optimization** — 離線分析歷史數據，輸出最佳權重
3. **Feature Importance** — Random Forest / XGBoost 分析特徵重要性

## Architecture

### Module Structure

```
v5_scanner/
├── scanner.py              # 主流程排程器
├── indicators.py           # 指標計算引擎（OI, Taker, MA, Structure, Volume）
├── scoring.py              # Penalty + Ranking Score 系統
├── data_loader.py          # CSV 讀寫 + V4 Migration
├── notifier.py             # Telegram 推播（中文格式）
├── weights.json            # 權重設定檔
├── .env.example
├── requirements.txt        # 零第三方依賴
├── data/                   # V5 格式 CSV（按月分檔）
├── logs/                   # 每日日誌
└── analysis/               # Cross Analysis 輸出
    ├── cross_analysis.md
    └── cross_analysis.csv

analysis_tools/             # 獨立 venv（安裝 scikit-learn, xgboost, pandas）
├── cross_analyzer.py       # 讀 V4+V5 CSV，跑 cross analysis
├── optimize_weights.py     # 讀 cross analysis 結果，輸出 weights.json
└── feature_importance.py   # RF / XGBoost 特徵重要性分析
```

### Module Responsibilities

#### scanner.py
- 讀取 `.env` 和 `weights.json`
- 調用 indicators.py → scoring.py → data_loader.py → notifier.py
- 支援 `--loop`（循環模式）和 `--dry-run`（測試模式）

#### indicators.py
- 純計算，無副作用
- `get_market_regime()` → 大盤趨勢判定
- `calculate_indicators(symbol, klines, oi_data, taker_data)` → 回傳指標 dict

#### scoring.py
- 讀取 `weights.json` 取得 penalty 權重與閾值
- `calculate_base_score(indicators)` → OI breakout + expansion + mid_change + taker
- `calculate_penalty(indicators, weights)` → 計算所有 penalty
- `calculate_final_score(base, penalties)` → base + bonus - penalty
- 不再 return None — 所有信號都保留，只影響排序

#### data_loader.py
- `save_to_csv(data_list, scan_time, scan_id)` — V5 格式，安全寫入
- `migrate_v4_csv()` — 一次性 V4 → V5 格式遷移
- `load_all_csvs()` — 讀取所有歷史 CSV

#### notifier.py
- 中文 Telegram 推播，Top 10
- 含 penalty score 細節
- 精簡好讀

## Penalty Score System

### Formula

```
Final Score = Base Score + Bonus - Penalty
```

### Base Score（與 V4 相同）

| Factor | Weight |
|--------|--------|
| OI Breakout | 40% |
| OI Expansion | 25% |
| OI Mid Change | 20% |
| Taker Ratio | 15% |

### Bonus

| Condition | Score | Description |
|-----------|-------|-------------|
| BEAR Market | +10 | 弱勢突破更有價值 |
| Negative Funding | +8 | 空頭擁擠 |
| Structure Score < 33 | +6 | 偏空結構突破 |
| Volume > 2.0 (EXTREME) | +4 | 極端放量 |

### Penalty

| Condition | Score | Description |
|-----------|-------|-------------|
| BULL Market | -10 | 強勢假突破 |
| Positive Funding | -8 | 多頭踩踏風險 |
| Overextended | -12 | 追高風險最高 |
| Structure Score > 83 | -6 | 偏多結構 |
| Volume < 0.8 (LOW) | -4 | 縮量不可信 |

### weights.json Structure

```json
{
  "meta": {
    "version": "V5-WEIGHTS-1",
    "generated_by": "optimize_weights.py",
    "generated_at": "2026-07-22"
  },
  "base_weights": {
    "oi_breakout": 0.40,
    "oi_expansion": 0.25,
    "oi_mid_change": 0.20,
    "taker": 0.15
  },
  "bonus": {
    "bear_market": 10,
    "negative_funding": 8,
    "low_structure": 6,
    "extreme_volume": 4
  },
  "penalty": {
    "bull_market": -10,
    "positive_funding": -8,
    "overextended": -12,
    "high_structure": -6,
    "low_volume": -4
  },
  "thresholds": {
    "funding_positive": 0.0005,
    "funding_negative": 0,
    "overextended_ma25": 30.0,
    "overextended_support": 40.0,
    "overextended_high": 10.0,
    "structure_low": 33,
    "structure_high": 83,
    "volume_extreme": 2.0,
    "volume_low": 0.8
  }
}
```

## Cross Analysis Dimensions

### Single Variable

| Dimension | Buckets |
|-----------|---------|
| funding_bucket | NEGATIVE / NEUTRAL / POSITIVE |
| volume_bucket | LOW / NORMAL / HIGH / EXTREME |
| structure_score | 0-25 / 25-50 / 50-75 / 75-100 |
| is_overextended | True / False |
| is_top10 | True / False |
| is_top20 | True / False |
| market_regime | BULL / MIXED / BEAR |
| btc_dist_ma99 | <-10% / -10~-5% / -5~0% / 0~5% / 5~10% / >10% |
| entry_distance_pct | <5% / 5~10% / 10~20% / 20%+ |

### Cross Variable (Dual)

| X | Y | Reason |
|---|----|--------|
| funding_bucket | market_regime | 費率在不同大盤下的影響 |
| funding_bucket | structure_score | 費率 + 結構的組合效果 |
| funding_bucket | volume_bucket | 費率 + 量能的組合 |
| funding_bucket | oi_value | 費率 + OI 大小的組合 |
| market_regime | structure_score | 大盤 + 結構的判斷 |
| market_regime | volume_bucket | 大盤 + 量能的判斷 |
| oi_value | volume_bucket | OI 突破 + 量能共振 |
| volume_bucket | structure_score | 量能 + 結構的組合 |
| is_top20 | market_regime | 頂部標的在不同大盤的效果 |
| entry_distance_pct | market_regime | 距離在不同大盤的敏感度 |

Minimum sample threshold: 30 (below → labeled `[樣本不足]`)

## Weight Optimization Process

1. Read `cross_analysis.csv` + historical CSV
2. Calculate statistical impact of each penalty condition
3. Grid search for optimal weights
4. Output `weights_optimized.json` + `weight_analysis.md`
5. Simulate ranking comparison (new vs old weights)
6. User reviews — manually copy to `weights.json`

## Feature Importance

- **Libraries:** scikit-learn (Random Forest), XGBoost
- **Environment:** Separate `analysis_tools/venv/`
- **Target variable:** `future_7d_return`
- **Features:**
  - Numerical: all score_* and dist_* fields
  - Categorical → numerical: funding_bucket (-1/0/1), volume_bucket (0-3), market_regime (-1/0/1), is_overextended (0/1)
- **Output:** `feature_importance.md` + `feature_importance.csv`

## Telegram Notification Format

```
📊 資金流掃描 V5-BETA-1
時間: 2026-07-22 15:00
大盤: 🐻 BEAR (BTC -3.2% / ETH -1.8%)

━━━━━━━━━━━━━━━━━━
🥇 #1 ETHUSDT | 3,450.20
   綜合分: 78.5 | 基礎: 65.0 | 獎勵: +18 | 懲罰: -4.5
   📌 Penalty:
      🐂 牛市: -10 → 大盤偏多 (已由 BEAR 覆蓋)
      💰 費率正: -8 → 多頭擁擠
   ✅ Bonus:
      🐻 熊市突破: +10
      📉 空頭擁擠: +8
   OI 突破: 0.82 | 擴張: 1.45x | 費率: 0.0012%
   距推薦區: 5.2% | 類型: MA25_NEAR
━━━━━━━━━━━━━━━━━━
```

## V4 Data Migration

- **Script:** `migrate_v4.py` (one-time)
- **Location:** `v5_scanner/migrate_v4.py`
- **Process:** Read `v4_scanner/data/signals_*.csv` → convert fields → write to `v5_scanner/data/signals_*.csv`
- **Key rule:** Original V4 scores preserved, new V5 fields left empty (migration only)

## Analysis Flow (Local Testing)

```
1. python v5_scanner/migrate_v4.py                   # V4 → V5 migration
2. python analysis_tools/cross_analyzer.py            # Cross analysis
3. python analysis_tools/optimize_weights.py          # Weight optimization
4. [User reviews weight_analysis.md → confirms]
5. cp weights_optimized.json v5_scanner/weights.json
6. python analysis_tools/feature_importance.py        # Feature importance
7. python v5_scanner/scanner.py --dry-run             # Test scan
8. [User confirms → deploy to VPS]
```

## VPS Deployment

```
# VPS structure:
~/v5_scanner/
├── scanner.py
├── indicators.py
├── scoring.py
├── data_loader.py
├── notifier.py
├── weights.json
├── .env
├── data/
└── logs/

# Crontab (every 3 hours):
0 */3 * * * cd ~/v5_scanner && python3 scanner.py 2>> logs/cron_error.log
```

## Future Roadmap (Post V5-BETA-1)

| Phase | Feature |
|-------|---------|
| V5.1 | Entry Engine — 進場建議 |
| V5.2 | AI Ranking — ML-based scoring |
| V5.x | More data sources, more exchanges |
