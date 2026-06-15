import { normalPPF, sampleSizeBinary, sampleSizeContinuous, heterogeneityAdjustment, computeRIS, computePower } from './engine.mjs';

function approx(a,b,tol){ return Math.abs(a-b) < tol; }
const report = {};

// --- normalPPF accuracy vs known quantiles ---
report.normalPPF = {
  z975: normalPPF(0.975), expected975: 1.959964,
  z80: normalPPF(0.80), expected80: 0.8416212,
  ok975: approx(normalPPF(0.975), 1.959964, 1e-4),
  ok80: approx(normalPPF(0.80), 0.8416212, 1e-4)
};

// --- Two-proportion RIS closed form (per-arm n) ---
// n = (za+zb)^2 (p0(1-p0)+p1(1-p1)) / (p0-p1)^2
{
  const p0=0.10, p1=0.07, alpha=0.05, power=0.80;
  const za=normalPPF(1-alpha/2), zb=normalPPF(power);
  const expected = Math.ceil((za+zb)**2 * (p0*(1-p0)+p1*(1-p1)) / (p0-p1)**2);
  const got = sampleSizeBinary(p0,p1,alpha,power);
  report.binaryRIS = { got, expected, correct: got===expected };
}

// --- Continuous: n = 2(za+zb)^2 sigma^2 / delta^2 ---
{
  const delta=0.5, sigma=1, alpha=0.05, power=0.80;
  const za=normalPPF(1-alpha/2), zb=normalPPF(power);
  const expected = Math.ceil(2*(za+zb)**2*sigma*sigma/(delta*delta));
  const got = sampleSizeContinuous(delta,sigma,alpha,power);
  report.continuousRIS = { got, expected, correct: got===expected, note: 'Cohen d=0.5 -> ~63/arm is the known textbook value' };
}

// --- Heterogeneity adjustment: app uses 1 + I2/(1-I2) == 1/(1-I2) ---
{
  const i2=0.5;
  const got = heterogeneityAdjustment(i2);
  const as_1_minus = 1/(1-i2);          // I2-based: RIS/(1-I2)  -> 2.0 at I2=50%
  const oneMinusD2_diversity = null;    // diversity D2 distinct from I2 (cannot reproduce without D)
  report.hetAdj = {
    i2, got,
    equals_1_over_1minusI2: approx(got, as_1_minus, 1e-9),
    at50pct_doubles: approx(got, 2.0, 1e-9),
    note: 'App labels factor D^2=I2/(1-I2); numerically hetAdj = 1/(1-I2). Standard I2-inflation (RIS/(1-I2)). NOTE: true TSA Diversity D2 is a DISTINCT quantity from I2; app conflates the symbol but the operation 1/(1-I2) is a valid I2-adjustment.'
  };
  // I2=75% should quadruple
  report.hetAdj.at75pct_quadruples = approx(heterogeneityAdjustment(0.75), 4.0, 1e-9);
}

// --- computeRIS base closed form: n_base = 2(za+zb)^2/d^2, then * hetAdj ---
{
  const d=0.5, i2=0, alpha=0.05, power=0.80;
  const za=normalPPF(1-alpha/2), zb=normalPPF(power);
  const expected = Math.ceil(2*(za+zb)**2/(d*d) * 1);
  const got = computeRIS(d,i2,alpha,power);
  report.computeRIS_noHet = { got, expected, correct: got===expected };
  // with I2=50% should be ~2x
  report.computeRIS_het50 = { got: computeRIS(d,0.5,alpha,power), approxDouble: computeRIS(d,0.5,alpha,power) / got };
}

// --- Round-trip / consistency: does RIS at d deliver the claimed power? ---
// computePower(N=RIS, d, i2, alpha) should return ~target power (0.80)
{
  const d=0.5, i2=0, alpha=0.05, power=0.80;
  const ris = computeRIS(d,i2,alpha,power);
  const deliveredPower = computePower(ris, d, i2, alpha);
  report.powerSelfConsistency = { ris, targetPower: 0.80, deliveredPower, withinTol: approx(deliveredPower, 0.80, 0.01) };
}

console.log(JSON.stringify(report,null,2));
