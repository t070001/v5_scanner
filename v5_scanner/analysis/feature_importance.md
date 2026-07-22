# Feature Importance Report

Generated: 2026-07-22 20:41

Target: `future_7d_return` | Samples: 150 | Features: 22

## Rankings

| Rank | Feature | RF Importance | XGBoost Importance | Average |
|------|---------|---------------|-------------------|---------|
| 1 | dist_support_low | 0.0833 | 0.0876 | 0.0854 |
| 2 | oi_breakout_strength | 0.0659 | 0.1019 | 0.0839 |
| 3 | dist_ma25 | 0.0718 | 0.0908 | 0.0813 |
| 4 | score_taker | 0.0814 | 0.0606 | 0.0710 |
| 5 | taker_buy_ratio | 0.0513 | 0.0814 | 0.0664 |
| 6 | btc_dist_ma99 | 0.0471 | 0.0718 | 0.0595 |
| 7 | score_oi_mid_change | 0.0538 | 0.0572 | 0.0555 |
| 8 | oi_change_mid | 0.0561 | 0.0499 | 0.0530 |
| 9 | oi_expansion | 0.0445 | 0.0575 | 0.0510 |
| 10 | oi_change_short | 0.0635 | 0.0311 | 0.0473 |
| 11 | volume_ratio | 0.0514 | 0.0404 | 0.0459 |
| 12 | eth_dist_ma99 | 0.0527 | 0.0383 | 0.0455 |
| 13 | dist_ma99 | 0.0485 | 0.0318 | 0.0401 |
| 14 | dist_high | 0.0479 | 0.0253 | 0.0366 |
| 15 | oi_value | 0.0339 | 0.0253 | 0.0296 |
| 16 | market_regime | 0.0119 | 0.0466 | 0.0292 |
| 17 | score_oi_breakout | 0.0407 | 0.0163 | 0.0285 |
| 18 | score_oi_expansion | 0.0384 | 0.0155 | 0.0270 |
| 19 | structure_score | 0.0304 | 0.0234 | 0.0269 |
| 20 | volume_bucket | 0.0097 | 0.0195 | 0.0146 |
| 21 | funding_bucket | 0.0105 | 0.0179 | 0.0142 |
| 22 | is_overextended | 0.0053 | 0.0099 | 0.0076 |

## Interpretation

- **RF Importance**: How much the Random Forest uses this feature for splits
- **XGBoost Importance**: How much XGBoost uses this feature for gain
- **Average**: Combined ranking across both models
