# Weight Optimization Report

Generated: 2026-07-22 20:37

## Evaluation Metric
Top quartile average 7d return (higher = better ranking)

## Results

| Metric | Current | Optimized |
|--------|---------|----------|
| Top Q 7d Avg Return | -999.00% | -999.00% |

## Penalty Weights Comparison

| Penalty | Current | Optimized |
|---------|---------|----------|
| bull_market | -10 | -10 |
| positive_funding | -8 | -8 |
| overextended | -12 | -12 |
| high_structure | -6 | -6 |
| low_volume | -4 | -4 |

## Instructions

1. Review the comparison above
2. If optimized looks better, copy:
   ```bash
   cp C:\AGENT P\alpha_scan v5\analysis_tools\..\v5_scanner\analysis\weights_optimized.json C:\AGENT P\alpha_scan v5\analysis_tools\..\v5_scanner\weights.json
   ```
3. Run `python v5_scanner/scanner.py --dry-run` to verify
