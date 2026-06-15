// truth-recovery/test.mjs — node --test. RIS/power formulas vs closed form.
import { test } from 'node:test';
import assert from 'node:assert';
import { normalPPF, sampleSizeBinary, sampleSizeContinuous, heterogeneityAdjustment, computeRIS, computePower } from './engine.mjs';

const approx = (a,b,tol)=>Math.abs(a-b)<tol;

test('normalPPF matches known quantiles (z=1.95996 @0.975, 0.84162 @0.80)', () => {
  assert.ok(approx(normalPPF(0.975), 1.959964, 1e-4));
  assert.ok(approx(normalPPF(0.80), 0.8416212, 1e-4));
});

test('two-proportion RIS = (za+zb)^2 (p0q0+p1q1)/(p0-p1)^2', () => {
  const p0=0.10,p1=0.07,alpha=0.05,power=0.80;
  const za=normalPPF(1-alpha/2), zb=normalPPF(power);
  const expected = Math.ceil((za+zb)**2*(p0*(1-p0)+p1*(1-p1))/(p0-p1)**2);
  assert.strictEqual(sampleSizeBinary(p0,p1,alpha,power), expected);
});

test('continuous RIS = 2(za+zb)^2 sigma^2/delta^2 (= 63/arm for d=0.5)', () => {
  assert.strictEqual(sampleSizeContinuous(0.5,1,0.05,0.80), 63);
});

test('heterogeneity adjustment = 1/(1-I2): doubles @50%, quadruples @75%', () => {
  assert.ok(approx(heterogeneityAdjustment(0.5), 2.0, 1e-9));
  assert.ok(approx(heterogeneityAdjustment(0.75), 4.0, 1e-9));
  assert.ok(approx(heterogeneityAdjustment(0.5), 1/(1-0.5), 1e-9));
});

test('computeRIS inflates by hetAdj (I2=50% doubles base)', () => {
  const base = computeRIS(0.5, 0, 0.05, 0.80);
  const het  = computeRIS(0.5, 0.5, 0.05, 0.80);
  assert.ok(approx(het/base, 2.0, 0.05), `ratio ${het/base}`);
});

test('RIS self-consistency: N=RIS delivers the claimed power (~0.80)', () => {
  const ris = computeRIS(0.5, 0, 0.05, 0.80);
  const delivered = computePower(ris, 0.5, 0, 0.05);
  assert.ok(approx(delivered, 0.80, 0.01), `delivered ${delivered}`);
});
