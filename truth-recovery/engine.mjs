// truth-recovery/engine.mjs — pure RIS/power/sample-size functions extracted VERBATIM from ma-sample-size.html (lines 873-969)
// No DOM dependencies in these functions.

function erf(x) {
  // Abramowitz & Stegun approximation 7.1.26
  var sign = x < 0 ? -1 : 1;
  x = Math.abs(x);
  var t = 1.0 / (1.0 + 0.3275911 * x);
  var y = 1.0 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * Math.exp(-x * x);
  return sign * y;
}

function normalCDF(x) {
  return 0.5 * (1 + erf(x / Math.SQRT2));
}

function normalPPF(p) {
  // Rational approximation for inverse normal CDF
  if (p <= 0) return -Infinity;
  if (p >= 1) return Infinity;
  var a = [0, -3.969683028665376e+01, 2.209460984245205e+02,
            -2.759285104469687e+02, 1.383577518672690e+02,
            -3.066479806614716e+01, 2.506628277459239e+00];
  var b = [0, -5.447609879822406e+01, 1.615858368580409e+02,
            -1.556989798598866e+02, 6.680131188771972e+01,
            -1.328068155288572e+01];
  var c = [-7.784894002430293e-03, -3.223964580411365e-01,
            -2.400758277161838e+00, -2.549732539343734e+00,
             4.374664141464968e+00,  2.938163982698783e+00];
  var d = [7.784695709041462e-03, 3.224671290700398e-01,
            2.445134137142996e+00, 3.754408661907416e+00];
  var plo = 0.02425, phi = 1 - plo;
  var q, r;
  if (p < plo) {
    q = Math.sqrt(-2 * Math.log(p));
    return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) /
           ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1);
  } else if (p <= phi) {
    q = p - 0.5;
    r = q * q;
    return (((((a[1]*r+a[2])*r+a[3])*r+a[4])*r+a[5])*r+a[6])*q /
           (((((b[1]*r+b[2])*r+b[3])*r+b[4])*r+b[5])*r+1);
  } else {
    q = Math.sqrt(-2 * Math.log(1 - p));
    return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) /
             ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1);
  }
}

function sampleSizeBinary(p0, p1, alpha, power) {
  if (p0 === p1) return Infinity;
  var za = normalPPF(1 - alpha / 2);
  var zb = normalPPF(power);
  var n = (za + zb) * (za + zb) * (p0 * (1 - p0) + p1 * (1 - p1)) / ((p0 - p1) * (p0 - p1));
  return Math.ceil(n);
}

function sampleSizeContinuous(delta, sigma, alpha, power) {
  var za = normalPPF(1 - alpha / 2);
  var zb = normalPPF(power);
  var n = 2 * (za + zb) * (za + zb) * sigma * sigma / (delta * delta);
  return Math.ceil(n);
}

function heterogeneityAdjustment(i2Frac) {
  // D^2 = I^2 / (1 - I^2); multiply RIS by (1 + D^2)
  if (i2Frac >= 0.99) return 100;
  var d2 = i2Frac / (1 - i2Frac);
  return 1 + d2;
}

function computePower(N, effectSize, i2Frac, alpha) {
  // Power = Phi(sqrt(N * effectSize^2 / V) - z_alpha/2)
  // V = 1 (unit variance assumed for standardised effect); heterogeneity inflates variance
  var za = normalPPF(1 - alpha / 2);
  var hetAdj = heterogeneityAdjustment(i2Frac);
  // Effective N accounting for heterogeneity
  var Neff = N / hetAdj;
  var ncp = Math.sqrt(Neff) * effectSize / Math.sqrt(2); // two-arm standardised
  return normalCDF(ncp - za);
}

function computeRIS(effectSize, i2Frac, alpha, power) {
  if (!effectSize || effectSize === 0) return Infinity;
  var za = normalPPF(1 - alpha / 2);
  var zb = normalPPF(power);
  var hetAdj = heterogeneityAdjustment(i2Frac);
  // Base N for unit-variance standardised effect (two-arm)
  var n_base = 2 * (za + zb) * (za + zb) / (effectSize * effectSize);
  return Math.ceil(n_base * hetAdj);
}

function mde(N, i2Frac, alpha, power) {
  var za = normalPPF(1 - alpha / 2);
  var zb = normalPPF(power);
  var hetAdj = heterogeneityAdjustment(i2Frac);
  var Neff = N / hetAdj;
  if (Neff <= 0) return Infinity;
  return Math.sqrt(2 * (za + zb) * (za + zb) / Neff);
}

export { erf, normalCDF, normalPPF, sampleSizeBinary, sampleSizeContinuous, heterogeneityAdjustment, computePower, computeRIS, mde };
