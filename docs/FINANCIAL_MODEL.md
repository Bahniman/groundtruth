# GroundTruth — the financial model

The complete money mechanics, with formulas, worked numbers, and who carries
which risk. Everything here is implemented in `groundtruth/finance.py` and
`groundtruth/reliability.py`, and asserted by the test suite.

## 1. The instrument

A **verified e-invoice**: certified quantity × Schedule-of-Rates price,
where "certified" means (a) geo-fenced machine evidence, (b) an accountable
engineer's signature binding the evidence fingerprints, (c) an entry in a
hash-chained ledger. The payer is a government treasury — a counterparty that
delays but does not default. That combination (verifiable claim + sovereign
credit + predictable delay) is what makes the receivable financeable.

## 2. The advance

Per standing agreement, the bank advances a fraction of the invoice at T+1:

```
advance = invoice_value × advance_rate(reliability_score)
holdback = invoice_value − advance
```

The advance-rate curve (a credit-committee artifact, deliberately step-shaped
and conservative):

| Reliability score | Advance rate | Credit story |
|---|---|---|
| ≥ 0.98 | 85% | dispute rate near zero across a long settled history |
| ≥ 0.95 | 75% | established relationship, strong evidence quality |
| ≥ 0.90 | 60% | standard rate for a verified but young relationship |
| ≥ 0.85 | 55% | early history, thin file |
| ≥ 0.80 | 50% | minimum financeable |
| < 0.80 | — | not financeable; verification quality must improve first |

## 3. The holdback: whose risk it absorbs

The holdback is the bank's buffer, in priority order:

1. **Treasury deductions** (audit cuts, penalties) — absorbed by the holdback
   first; the contractor's day-one advance is never clawed back.
2. **Financing interest** on the advance for actual days outstanding.
3. **Platform fee** on invoice value.
4. Remainder → released to the contractor at settlement.

```
interest = advance × annual_rate × days/365
balance_released = max(0, holdback − interest − platform_fee − deduction)
```

The engine enforces conservation (tested): advance + balance + interest +
fee + deduction = invoice value.

## 4. Worked example (default terms: 11% p.a., 0.35% platform fee)

Invoice ₹18,63,900 · score 0.91 → 60% advance · treasury settles day 148:

| Line | Amount |
|---|---|
| Advance at T+1 | ₹11,18,340 |
| Holdback | ₹7,45,560 |
| Interest (11% × 148/365 on advance) | −₹49,879 |
| Platform fee (0.35%) | −₹6,524 |
| Balance released at settlement | ₹6,89,157 |
| **Contractor total** | **₹18,07,497 (97.0%)** |

Status quo for the same invoice: first rupee on day 148, and if the wait is
bridged at 22% informal credit, the bridge costs ≈ ₹1,66,300 → the contractor
nets ≈ 91.1%, five months later, with capital frozen the whole time.

## 5. Unit economics per invoice

- **Contractor:** pays ~3.0% all-in for day-one liquidity (vs ~8.9% for
  informal bridging), and unlocks working capital to bid the next package.
- **Bank:** earns the financing rate (11% p.a. here) on a self-liquidating,
  holdback-buffered, near-sovereign instrument. Yield is asserted in tests.
- **GroundTruth:** platform fee (35 bps on invoice value) + SaaS to
  departments and contractors + the reliability data layer.

## 6. The flywheel (implemented in `reliability.py`)

```
score = 0.88 (base)
      + 0.012 × log2(1 + clean_settlements)     # diminishing returns
      − 0.03  × disputed_settlements            # asymmetric: disputes hurt 
      + up to ±0.015 for evidence quality       # capture completeness
clamped to [0.50, 0.99]
```

Properties the tests assert: monotone advance curve; disputes hurt more than
cleans help (banks are asymmetric); clean history moves a contractor up the
advance curve. **This is the moat:** the settled-history ledger that justifies
an 85% advance cannot be copied by a competitor who has financed nothing.

## 7. Risk register

| Risk | Carrier | Control |
|---|---|---|
| Over-certification (fraud) | GroundTruth → bank | dual-key certificates, geo-fencing, chained ledger, random audit; disputes crater the score (−3 pts each) |
| Treasury deduction | holdback | absorbed before any contractor balance |
| Treasury delay beyond expectation | bank (duration risk) | interest accrues on actual days; sovereign payer |
| Verification-model error | GroundTruth | conservative curve floor; score capped at 0.99, never 1.0 |
| Contractor concentration | bank | per-contractor exposure caps (bank-side policy, out of scope here) |

## 8. What is deliberately NOT in the prototype

Real SoR rate tables, bank APIs, PFMS integration, and the vision model are
integration work, not research risk — the prototype proves the *mechanics*
(certificates, waterfall, flywheel) with the exact arithmetic production
would use.
