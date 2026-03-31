# MASampleSize — Protocol Registration

**Registration ID:** MSS-2026-001
**Tool:** MASampleSize v1.0
**Full title:** MASampleSize: A Browser-Based Prospective Meta-Analysis Sample Size Calculator
**Date registered:** 2026-03-31
**Registered by:** Mahmood Alhusseini

## Repository

- GitHub: https://github.com/mahmood726-cyber/ma-sample-size
- Live tool: https://mahmood726-cyber.github.io/ma-sample-size/
- Protocol paper: https://mahmood726-cyber.github.io/ma-sample-size/docs/protocol.html
- Results paper: https://mahmood726-cyber.github.io/ma-sample-size/docs/results.html

## Tool Description

Single-file HTML application (1,825 lines, 66 KB) for prospective meta-analysis sample size planning. Answers the question: "How many studies and patients are needed before a meta-analysis can be considered conclusive?"

Implements:
- Required Information Size (RIS) for binary and continuous outcomes
- D² heterogeneity adjustment (Wetterslev et al. 2008)
- Studies-needed estimate from average study size
- Real-time power curves (4 Canvas charts)
- Existing evidence adequacy assessment (traffic-light: Green/Yellow/Red)
- JSON export with audit fields

## Primary Outcomes

| Outcome | Definition |
|---------|-----------|
| RIS | Total patients needed, D²-adjusted |
| Studies needed (k) | ceil(RIS / (2 × avgStudySize)) |
| Power at current N | Statistical power given accrued evidence |
| Adequacy rating | GREEN / YELLOW / RED |

## Methods

- Binary: two-proportion z-test
- Continuous: two-sample t-test approximation
- Heterogeneity: D² = I²/(1−I²), RIS × (1 + D²)
- Normal CDF: Abramowitz-Stegun formula 7.1.26 (max error < 1.5×10⁻⁷)
- Normal PPF: Acklam rational approximation (max error < 3×10⁻⁹)

## Validation Status

- [x] Formula verification vs R pwr package (< 0.5% relative error)
- [x] D² adjustment verified vs Wetterslev et al. Table 1
- [x] Safety checks passed (div balance, script integrity, ID uniqueness)
- [x] Three clinical examples validated (statin/anticoagulant/exercise)

## License

MIT License — freely available for academic and clinical use.

## Relationship to Other Tools

Complements **TSA Pro** (github.com/mahmood726-cyber/tsa-pro), which addresses retrospective Trial Sequential Analysis with alpha-spending functions. MASampleSize addresses the prospective planning phase.
