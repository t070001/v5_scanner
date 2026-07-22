# 幣安資金流掃描器 V5 開發交接文件

---

# 專案目標

V5 並不是重新設計一套交易策略。

V5 的目標只有一件事：

> 建立一套可以持續利用歷史數據自我優化的 Scanner。

目前 V4 已經可以：

- Binance 掃描
- OI 分析
- RVOL 分析
- Market Structure
- Funding
- Telegram 推播
- VPS 自動執行
- CSV Database

截至目前已累積：

> 約 22,000+ 筆真實歷史訊號。

這是 V5 最大的資產。

未來所有策略，都必須建立在這些歷史資料之上。

禁止憑主觀修改策略。

---

# V5 核心理念

不要讓人決定策略。

讓資料決定策略。

任何新增規則，都必須可以由歷史資料驗證。

若沒有統計依據，不應新增 Hard Filter。

---

# V4 已完成

✔ Binance Scanner

✔ OI Scanner

✔ RVOL

✔ Structure Analysis

✔ Telegram Bot

✔ VPS 自動排程

✔ Signal Database

✔ Historical Analyzer

---

# V5 開發目標

建立：

v5_scanner/

不得修改 v4_scanner。

V5 完全獨立。

---

# 第一原則

不要刪除資料。

Scanner 的目的不是 Auto Trade。

Scanner 的目的：

找出值得觀察的市場。

因此：

任何訊號

都應該：

• 保留

• 寫入 CSV

• 參與回測

不要因為某條件不好就直接 return None。

---

# Hard Filter 全部取消

V4 分析曾經得到：

• Positive Funding 表現不好

• Overextended 表現不好

• Entry Distance 太遠不好

• Extreme RVOL 不好

但是：

這些都是單變數分析。

目前沒有任何證據表示：

Funding Positive + Bear Market

Funding Positive + High OI

Funding Positive + Low Structure

一定不好。

因此：

V5 禁止使用 Hard Filter。

改用：

Penalty Score。

---

# Penalty Score

所有條件皆保留。

但可以降低排序。

例如：

Funding Positive

↓

-10

Overextended

↓

-20

Bull Market

↓

-8

Structure 100

↓

-6

而不是直接剔除。

---

# Ranking Score

V5 不再使用：

Structure × 倍率。

改用：

固定加減分。

例如：

Structure

0

+8

16

+6

33

+4

50

0

66

-2

83

-4

100

-6

避免倍率造成排名失真。

---

# Market Regime

Market Regime

採固定分數。

Bear

+10

Mixed

0

Bull

-10

避免 ±0.15 幾乎沒有影響。

---

# V5 最重要的新功能

Cross Analysis。

目前 analyzer 都是：

單變數分析。

例如：

Funding

↓

勝率

V5 必須新增：

Funding × Market

Funding × Structure

Funding × OI

Funding × RVOL

Structure × Market

RVOL × OI

Top20 × Market

Entry Distance × Market

等等。

找出真正有效的條件組合。

---

# 未來方向

V5

Cross Analysis

↓

V5.1

Penalty Weight Optimization

↓

V5.2

Feature Importance

(Random Forest / XGBoost)

↓

V5.3

Entry Engine

↓

V5.4

AI Ranking

---

# Agent 工作守則

任何新增規則：

必須：

1.

提出統計依據

2.

可以回測

3.

不得主觀猜測

若沒有資料支持：

不得新增規則。

Scanner 永遠以資料為中心。

---

## 🛠️ 現有 Skills 繼承

我們已在本地為此專案建置了 4 個核心 Skills，放置於：
- [v5_scanner/.agents/skills/](file:///C:/Users/FunZ/.gemini/antigravity/brain/0b2e3a71-264c-423e-a580-38287e50d926/scratch/v4_scanner/.agents/skills/) (您可以直接複製這些技能檔案到新的 `v5_scanner/.agents/skills/` 中)。

請接手的 Agent 務必仔細閱讀這些技能，以確保長對話的高 Token 效率與合約交易的專業水準！
