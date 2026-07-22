# Crypto Intelligence V5 Statistical Analysis Guide

## Data Source

This report is generated from historical signal performance.

Current dataset:

- Total Signals: 22,243
- Holding Period:
    - 3 Days
    - 7 Days
    - 14 Days

Every generated signal is stored and evaluated after time passes.

This analysis is NOT backtesting.

It is historical statistical grouping.

---

# Goal

Find which features have predictive power.

Not every indicator should increase the score.

Some indicators should instead increase risk.

---

# Statistical Method

Each feature is grouped into buckets.

Example:

Funding

NEGATIVE
NEUTRAL
POSITIVE

Then calculate

- Sample Count
- Win Rate
- Average Return
- Median Return

for

3 Days
7 Days
14 Days

This is repeated for every feature.

---

# Current Features

## Funding Bucket

Purpose:

Measure market sentiment.

Finding:

Funding has weak predictive power.

Positive funding performs the worst.

Action:

Downgrade to Context Feature.

Do NOT use as scoring feature.

---

## Volume Bucket

Purpose:

Measure abnormal trading volume.

Finding:

Extreme volume usually underperforms.

Likely caused by chasing breakouts.

Action:

Use only as supporting information.

---

## Structure Score

Purpose:

Measure trend maturity.

Finding:

Higher score does NOT mean higher probability.

Structure Score 100 performed worse than lower scores.

Action:

Avoid linear scoring.

Use as context.

---

## Overextended

Purpose:

Measure whether price is already too extended.

Finding:

One of the strongest predictors.

Overextended signals consistently perform much worse.

Action:

Do NOT reject signals.

Instead assign HIGH RISK.

---

## Top10 / Top20 Ranking

Purpose:

Highest OI Increase ranking.

Finding:

Top ranked assets significantly underperform.

Likely due to FOMO.

Action:

Convert into Risk Indicator.

Do not reward high ranking.

---

## BTC MA99 Distance

Purpose:

Measure overall market extension.

Finding:

BTC above MA99 performs worse.

Action:

Use as Market Risk Modifier.

---

## ETH MA99 Distance

Finding:

Even stronger than BTC.

ETH > MA99 +5%

produces poor performance.

Action:

Increase risk level.

---

## Entry Distance

Purpose:

Distance between current price and recommended entry.

Finding:

Strongest predictor.

<5%

best performance.

20%+

worst performance.

Action:

This should become a core feature in V5.

---

# V5 Design Philosophy

V4 focused on

Signal Quality.

V5 should focus on

Risk Quality.

Instead of asking

"Is this a good signal?"

Ask

"How dangerous is this signal?"

Every signal should contain

Signal Score

Risk Level

Entry Quality

Market Risk

instead of only

Signal Score.

---

# Priority for V5

★★★★★ Entry Distance

★★★★★ Overextended

★★★★☆ BTC Position

★★★★☆ ETH Position

★★★☆☆ Top Ranking Risk

★★☆☆☆ Structure

★☆☆☆☆ Funding

★☆☆☆☆ Volume Bucket

The objective of V5 is not to filter more signals.

The objective is to classify signal risk more accurately.