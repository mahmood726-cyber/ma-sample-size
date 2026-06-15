# Truth-Recovery Report — ma-sample-size

**Verdict: STRONG-VALIDATION** (one terminology caveat, not a math bug)

## What was tested
`ma-sample-size` computes the Required Information Size (RIS) / Trial-Sequential-Analysis
information size and post-hoc power for a meta-analysis. The pure functions
(`normalPPF`, `sampleSizeBinary`, `sampleSizeContinuous`, `heterogeneityAdjustment`,
`computeRIS`, `computePower`, `mde`, `erf`, `normalCDF`) were extracted VERBATIM from
`ma-sample-size.html` (lines 873-969) into `engine.mjs` (no DOM), then tested against closed form.

## Results (engine output vs closed form)

| Check | Engine | Closed form | Status |
|---|---|---|---|
| normalPPF(0.975) | 1.9599640 | 1.959964 | CORRECT |
| normalPPF(0.80) | 0.8416212 | 0.8416212 | CORRECT |
| Two-proportion RIS (p0=.10,p1=.07) | 1353/arm | (za+zb)^2(p0q0+p1q1)/(p0-p1)^2 = 1353 | CORRECT |
| Continuous RIS (d=0.5) | 63/arm | 2(za+zb)^2 sigma^2/delta^2 = 63 | CORRECT (textbook value) |
| Heterogeneity factor @ I2=50% | 2.0 | 1/(1-I2) = 2.0 | CORRECT |
| Heterogeneity factor @ I2=75% | 4.0 | 1/(1-I2) = 4.0 | CORRECT |
| computeRIS I2=50% vs base | 2.0x | doubles | CORRECT |
| RIS self-consistency | N=RIS -> power 0.8013 | target 0.80 | CORRECT (ceil rounding) |

All 6 node --test assertions PASS.

## Critical formula findings
- RIS closed form `(z_a+z_b)^2 * variance / delta^2`: CORRECT for both binary
  (two-proportion) and continuous (Cohen d) outcomes.
- normalPPF (inverse-normal, Acklam rational approx) is accurate to <1e-4 at the relevant quantiles.
- RIS actually delivers the claimed power: feeding N=RIS back into computePower returns ~0.80
  (0.8013, the small overshoot is integer ceil() rounding of 62.78 -> 63). Self-consistent.
- The heterogeneity inflation: app computes `D^2 = I^2/(1-I^2)` and multiplies RIS by `(1 + D^2)`,
  which equals `1/(1-I^2)`. So RIS_adj = RIS/(1-I^2). This is the standard I^2-based TSA inflation
  (Wetterslev/CTU) and is numerically CORRECT: doubles at I2=50%, quadruples at I2=75%.

## Terminology caveat (NOT a math error)
- The help text and variable name call the factor "Diversity D^2". In the TSA literature
  (Wetterslev 2009), **Diversity (D^2)** is a DISTINCT quantity from I^2 and is generally >= I^2;
  the app's `D^2 = I^2/(1-I^2)` is actually the I^2-to-inflation transform, not the diversity statistic.
  The OPERATION `RIS/(1-I^2)` is a valid and widely-used I^2-adjustment, so the computed RIS is correct.
  The label "Diversity D^2" is a misnomer for what is really an I^2-based inflation. Recommend
  relabelling the help text to "I^2-based inflation = 1/(1-I^2)" to avoid conflating I^2 and true D^2.

## Recommendation
Ship the math as-is (STRONG-VALIDATION). Optionally fix the help-text/label terminology so it does
not claim "Diversity D^2" when it is computing an I^2-based inflation. No numerical correction needed.
