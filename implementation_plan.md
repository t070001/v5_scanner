# V5 Scanner Implementation Plan

---

# 專案目的

建立新一代 Data Driven Scanner。

V5 不追求更多規則。

V5 追求：

更多資料、

更多分析、

更好的排序。

---

# Step 1

建立：

v5_scanner/

複製：

scanner.py

indicator.py

telegram_bot.py

updater.py

analyzer.py

保持與 V4 完全獨立。

---

# Step 2

重新整理 Ranking Score

建立：

Penalty Score System

而不是：

Hard Filter。

例如：

Funding

Penalty

Overextended

Penalty

Bull Market

Penalty

High Structure

Penalty

最後：

Final Score

=

Base Score

+

Bonus

-

Penalty

---

# Step 3

新增 Cross Analyzer

新增：

analyze_cross.py

至少分析：

Funding × Market

Funding × Structure

Funding × RVOL

Funding × OI

Structure × Market

OI × RVOL

Entry Distance × Market

Top20 × Market

等等。

輸出：

勝率

平均

中位數

Sample Size

CSV

Markdown Report

---

# Step 4

新增 Weight Analyzer

依據：

Cross Analysis

重新計算：

Penalty Weight

不要人工指定。

---

# Step 5

加入：

Feature Importance

可使用：

Random Forest

XGBoost

Logistic Regression

分析：

哪些欄位最重要。

---

# Step 6

更新 Telegram

除了目前訊號外。

新增：

Daily Summary

例如：

今日：

掃描

127

符合

18

Watchlist

5

Average OI

Average RVOL

Funding Distribution

Market Regime

方便快速閱讀。

---

# Step 7

Analyzer 全部改為 Markdown

每次分析：

自動輸出：

analysis_report.md

方便閱讀。

---

# Step 8

建立 Version

V5-BETA-1

V5-BETA-2

V5-RC

V5

方便比較回測結果。

---

# Verification

完成後：

需確認：

✓ Scanner 正常

✓ Telegram 正常

✓ VPS 正常

✓ CSV 正常

✓ Cross Analysis 正常

✓ Weight Analysis 正常

✓ Markdown Report 正常

全部通過後：

才可進入：

V5.1。