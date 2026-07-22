# 幣安合約資金流掃描器 (v4_scanner) 完整專案交接與架構說明書

本文件專為接手本專案的 **AI Agent** 或開發者編寫。讀取本文件後，您將能全面理解 `v4_scanner` 專案的核心目標、檔案結構、數據庫 Schema、指標計算公式、防護設計以及未來的待辦開發需求。

---

## 📌 1. 專案總覽與核心目標 (Project Overview)

- **專案名稱**：Binance Futures Capital Flow Scanner V4 (v4_scanner)
- **核心目標**：零第三方依賴（僅使用 Python 標準庫），高效率且穩健地掃描幣安 U 本位合約市場，尋找未平倉量（OI）與成交量異常放大、但價格尚未極端暴漲、具備潛在上漲機會的標的。
- **技術棧**：Python 3.8+ (無外部套件需求)，urllib、json、csv、logging、unittest。

---

## 📂 2. 檔案目錄與各模組職責說明 (Directory & File Map)

專案根目錄：`v4_scanner/`

```text
v4_scanner/
├── scanner.py          # [主程式] 核心資料抓取、指標計算、評分排序、CSV寫入與TG推播
├── updater.py          # [回填程式] 每日排程執行，回填 3d/7d/14d 的未來實際價格回報率
├── analyze_signals.py  # [分析程式] 讀取歷史 CSV，進行多維度勝率與績效統計分析
├── test_scanner.py     # [測試腳本] 10 個單元測試案例，驗證核心指標與過濾邏輯
├── requirements.txt    # 專案依賴說明檔 (註明零第三方依賴)
├── .env.example        # Telegram Bot Token 與 Chat ID 環境變數設定範例
├── .gitignore          # 安全防護設定，排除敏感金鑰、日誌與數據庫
├── README.md           # 包含 V4-BETA-6 凍結協議 (Freeze Protocol) 與 VPS 部署教學
├── data/               # [數據庫] 按月分檔儲存的歷史訊號 CSV (signals_YYYY_MM.csv)
├── logs/               # [日誌庫] 按日儲存的運行 Log (YYYY-MM-DD.log)
└── .agents/skills/     # [技能庫] 包含 token_efficiency, crypto_futures_trading, system_architect, v5_alpha_discovery
```

### 各核心 Python 檔案詳細說明：

#### 1. `scanner.py` (主掃描器)
- **`get_market_regime()`**：抓取 BTCUSDT 與 ETHUSDT 的 4H K線，比較當前價格與 MA99，判定大盤趨勢（`BULL` / `BEAR` / `MIXED`），並計算各自的 MA99 偏離度 `btc_dist_ma99` 與 `eth_dist_ma99`。
- **`analyze_symbol(...)`**：對單一交易對進行分析：
  - 抓取 4H K線 (長度 120)、OI 歷史 (長度 30)、Taker Buy/Sell Ratio (長度 30)。
  - **Data Quality 檢查**：若 Funding Rate 缺失、K線/OI 數據不足，或價格/OI/量能比 $\le 0$，則印出警告並返回 `None` 跳過，防範數據污染。
  - **指標計算**：計算 `volume_ratio` (及 `volume_bucket`)、`funding_bucket`、OI 短中期變動、OI 突破強度與擴張比、Taker 比率等。
  - **綜合排序分數 (`ranking_score`)**：依 4 大加權項計算（詳見第 4 節）。
  - **過熱延伸懲罰 (`is_overextended`)**：若價格高於 MA25 超過 30%、高於支撐低點 > 40% 或高於前高 > 10%，標記為 True，並將 `ranking_score` 乘以 `0.7`（扣減 30% 分數）。
  - **Entry Zone 診斷**：計算 `entry_type` (`MA25_NEAR` / `PLATFORM_RETEST` / `MA25_PULLBACK` / `NONE`)、推薦區間 `interest_zone_low/high` 與偏離百分比 `entry_distance_pct`。
- **`save_to_csv(...)`**：
  - 寫入 `data/signals_YYYY_MM.csv`。
  - **安全寫入**：寫入 `.tmp` 暫存檔 $\rightarrow$ `flush()` & `fsync()` $\rightarrow$ `os.replace()` 原子性替換，避免斷電損毀。
  - **舊 CSV 平滑升級**：若讀取到舊版 33 欄位 CSV，會自動對齊補齊為 43 欄位新格式，確保歷史資料庫不丟失。
- **`run_scan()`**：執行 Log 清理 (`rotate_logs`)，篩選交易額 $> 50\text{M USDT}$ 標的，排序後標記 `is_top10` 與 `is_top20`，寫入 CSV，並將 Top 10 印出於控制台及推播至 Telegram。

#### 2. `updater.py` (未來回報回填器)
- 每日定時執行一次，遍歷 `data/signals_*.csv`。
- 尋找 `future_3d_return`, `future_7d_return`, `future_14d_return` 為空的記錄。
- 若距離 `scan_time` 已滿 3/7/14 天，透過幣安 API 抓取當時時間點的 1m K 線價格，計算回報率 `((future_price - current_price) / current_price) * 100` 並回填寫回 CSV。

#### 3. `analyze_signals.py` (統計分析腳本)
- 讀取 `data/` 下的所有 CSV 檔案，依據 10 大維度進行 3D / 7D / 14D 的樣本數、勝率、平均報酬、中位數報酬與最大虧損/收益統計。
- 內建 `parse_pct`、`parse_float`、`get_sort_key`（表格美化自訂排序）與 Windows 主控台 UTF-8 stdout 包裝器。

#### 4. `test_scanner.py` (單元測試)
- 包含 10 個無網路依賴的單元測試，覆蓋 MA 計算、二分法市場結構判定、資金費率與量能分組、結構得分、大盤偏離度計算、Top10/20 布林標記、Entry Zone 診斷與偏離比率邏輯。

---

## 📊 3. 資料庫 Schema (CSV 欄位定義 - 共 43 欄位)

每一次掃描產生的數據會寫入 `data/signals_YYYY_MM.csv`：

| 欄位名稱 | 型態 | 說明 |
| :--- | :--- | :--- |
| `scan_id` | String | 掃描批次號 (格式: `YYYYMMDD_HHMMSS`) |
| `scan_time` | String | 掃描時間 (格式: `YYYY-MM-DD HH:MM:SS`) |
| `signal_timestamp` | Integer | 掃描 Unix 時間戳 (秒) |
| `signal_version` | String | 策略版本標記 (如 `"V4-BETA-6"`) |
| `scan_rank` | Integer | 當次掃描的 `ranking_score` 降序排名 (1, 2, 3...) |
| `is_top10` | Boolean | `scan_rank <= 10` 則為 True |
| `is_top20` | Boolean | `scan_rank <= 20` 則為 True |
| `symbol` | String | 幣安合約交易對名稱 (如 `BTCUSDT`) |
| `price` | Float | 觸發時當前價格 |
| `funding_rate` | Float | 當前資金費率 |
| `funding_bucket` | String | `NEGATIVE` (<0) / `NEUTRAL` (0~0.0005) / `POSITIVE` (>0.0005) |
| `oi_value` | Float | 當前未平倉合約美元價值 (sumOpenInterestValue) |
| `oi_change_short` | Float | 短期 (3 根 4H K線) OI 變動 % |
| `oi_change_mid` | Float | 中期 (12 根 4H K線) OI 變動 % |
| `oi_breakout_strength` | Float | 相較於前 20 根 K線 OI 最大值的突破強度比率 |
| `oi_expansion` | Float | 相較於前 10 根 K線 OI 平均值的擴張比率 |
| `taker_buy_ratio` | Float | 主動買賣比 (buySellRatio) |
| `volume_ratio` | Float | 當前成交量相對過去 20 根 K線均值的比率 |
| `volume_bucket` | String | `LOW` (<0.8) / `NORMAL` (0.8~1.2) / `HIGH` (1.2~2.0) / `EXTREME` (>2.0) |
| `dist_ma25` | Float | 價格偏離 4H MA25 百分比 |
| `dist_ma99` | Float | 價格偏離 4H MA99 百分比 |
| `dist_support_low` | Float | 價格高於過去 20 根 K線最低點的百分比 |
| `dist_high` | Float | 價格相對過去 20 根 K線最高點的百分比 |
| `struct_5` / `10` / `20` | String | 5/10/20 週期二分法結構 (`Bullish` / `Neutral` / `Bearish`) |
| `structure_score` | Float | 市場結構平均得分 (0.0 到 100.0) |
| `score_oi_breakout` | Float | OI 突破標準化得分 (30% 突破得滿分 1.0) |
| `score_oi_expansion` | Float | OI 擴張標準化得分 (50% 擴張得滿分 1.0) |
| `score_oi_mid_change` | Float | OI 中期變動標準化得分 (50% 變動得滿分 1.0) |
| `score_taker` | Float | Taker 比率標準化得分 (1.20 得滿分 1.0) |
| `is_overextended` | Boolean | 是否過度延伸/追高 |
| `ranking_score` | Float | 綜合排序分數 |
| `market_regime` | String | 大盤趨勢 (`BULL` / `BEAR` / `MIXED`) |
| `btc_dist_ma99` | Float | BTC 價格相對其 MA99 的偏離比率 |
| `eth_dist_ma99` | Float | ETH 價格相對其 MA99 的偏離比率 |
| `entry_type` | String | Entry Zone 診斷 (`MA25_NEAR` / `PLATFORM_RETEST` / `MA25_PULLBACK` / `NONE`) |
| `interest_zone_low` | Float/String | 推薦進場區間下限 (無則為空字串) |
| `interest_zone_high` | Float/String | 推薦進場區間上限 (無則為空字串) |
| `entry_distance_pct` | Float/String | 當前價格偏離推薦區中心點的百分比 |
| `future_3d_return` | String | 3 天後實際價格回報率 (由 `updater.py` 回填) |
| `future_7d_return` | String | 7 天後實際價格回報率 (由 `updater.py` 回填) |
| `future_14d_return` | String | 14 天後實際價格回報率 (由 `updater.py` 回填) |

---

## 📐 4. 掃描與指標核心邏輯 (Core Logic)

### 綜合排序分數 (`ranking_score`) 計算公式：
$$\text{ranking\_score} = \text{score\_oi\_breakout} \times 0.40 + \text{score\_oi\_expansion} \times 0.25 + \text{score\_oi\_mid_change} \times 0.20 + \text{score\_taker} \times 0.15$$

若 `is_overextended == True`，則套用懲罰：
$$\text{ranking\_score} = \text{ranking\_score} \times 0.7$$

---

## 📝 5. 待辦任務與改進需求 (TODO & Requirements for Next Agent)

> [!IMPORTANT]
> ### 🚨 任務一：為 `analyze_signals.py` 增加檔案保存功能 (必做需求)
> - **問題/現況**：目前的 `analyze_signals.py` 執行後只會在控制台 (stdout) 使用 `print` 印出統計表格，**不會將報告保存為檔案**，導致無法留存歷史統計紀錄。
> - **需求規格**：
>   1. 修改 `analyze_signals.py`，使每次執行分析時，除了控制台印出外，**自動將漂亮的統計報告保存為文字/Markdown 檔案**。
>   2. 輸出路徑建議存於：`logs/analysis_report_YYYYMMDD_HHMMSS.txt` 或 `logs/latest_analysis_report.md`。
>   3. 報告內容需包含完整表頭、讀取總筆數、以及所有 10 個維度的分組表格。

> [!TIP]
> ### 💡 任務二：V5 策略升級準備 (v5_scanner)
> - 根據 V4 累積的 16,895 筆真實數據，V5 開發時請建立新目錄 `v5_scanner/`（不安裝/不更動 V4）。
> - **硬性過濾**：在 V5 中將 `is_overextended == True`、`entry_distance_pct >= 15%` 與 `funding_rate > 0.0005` 改為硬性剔除（直接 `return None`），不寫入 CSV，防範毒藥標的污染 Top 10。
> - **結構得分反向調節**：V4 數據顯示 `structure_score == 0.0` (超跌) 的 3D 勝率高達 59.75%，而 `100.0` 勝率僅 37.42%。V5 應將結構分反向計入排序，給予超跌標的加權。

---

## 🛠️ 6. 運作與部署說明 (Deployment)

- **排程模式 (Crontab)**：
  - `scanner.py`：每 3 小時單次執行（`0 */3 * * *`），日誌濾除 INFO 只留錯誤/警告。
  - `updater.py`：每日凌晨 02:00 執行（`0 2 * * *`）。
  - `analyze_signals.py`：每週日凌晨 03:00 執行（`0 3 * * 0`）。
