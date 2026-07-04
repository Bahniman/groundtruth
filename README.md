# GroundTruth

**The verification rail for the physical economy.**

### ▶ Try the live demo (no installation): https://bahniman.github.io/groundtruth.html

---

## In plain English (no jargon)

When a contractor builds a government road in India, an engineer measures the finished work **by hand, in a paper register**, and the contractor then waits 6 to 18 months to get paid while that register slowly crawls through approvals. Meanwhile the contractor is often borrowing money at 18–24% just to survive the wait.

**GroundTruth replaces the paper register.** Photos and AI measure the work; the engineer checks and signs it digitally; and that signed record is solid enough for a bank to pay the contractor **within two days** (the bank then collects from the government later). A road that pays for itself as it's built.

The bigger idea: this same pattern — *a machine observes, an accountable person signs, money moves* — is the bottleneck in insurance (someone must inspect the damage), banking (someone must verify the collateral), and carbon markets (someone must confirm the project is real). Verification is the last thing still done by a human with a clipboard.

## The business, concretely

Today the contractor submits work details and then waits months for human verification, processing, and payment. GroundTruth changes what the submission *produces*: a **verified, bank-grade e-invoice** — evidence-backed, engineer-signed, tamper-proof. Then the money moves like this:

1. **Day 0:** contractor submits; AI cross-checks the evidence; the engineer signs; a verified e-invoice is issued.
2. **Day 1, next morning:** the partner bank validates the instrument's authenticity and **advances 60% of the contracted amount** directly to the contractor, per standing agreement.
3. **The 40% holdback** stays with the bank as its safety net against verification error, disputes, or treasury deductions.
4. **Whenever the treasury pays** (months later), the bank — which now holds a verified receivable from a payer that never defaults, only delays — collects 100%.
5. **The bank releases the balance** minus financing charges (interest on the advance for the actual period + a platform fee).

Worked example on a ₹18.6 lakh invoice: contractor receives ₹11.2 lakh on day 1 and ₹6.9 lakh at settlement — **~97% of invoice value, with liquidity on day 1** — versus ~91% after months of 22% informal borrowing today. The contractor's crew and capital move to the next project immediately; the bank earns near-sovereign yield on a self-liquidating instrument.

**The flywheel that makes it a moat:** the 40% holdback is priced verification risk. Every invoice that settles cleanly is actuarial history; as the model's dispute rate falls, banks can safely advance more — 60% → 75% → 85%. A competitor can copy the app; they cannot copy the settled-invoice history that lets a bank trust an 85% advance.

**Revenue:** platform fee per verified invoice + basis points on financed value + the reliability-score data layer banks underwrite against.

<details>
<summary><b>Jargon decoder</b> (click to expand)</summary>

| Term | What it actually means |
|---|---|
| **Measurement Book** | The physical register where a government engineer hand-writes how much work was done. Every payment depends on it. |
| **Evidence** | Geotagged photos/drone captures — proof with the location and time baked in. |
| **Dual-key certificate** | Two locks on one door: the AI's evidence *and* the human's signature. Neither alone can release money. |
| **Receivable** | Money someone owes you. Here, what the government owes the contractor for certified work. |
| **Discounting** | A bank pays you ~98–99% of that money *today* and collects the full amount later; you get cash now. |
| **Ledger** | The running record of certified work. *Tamper-evident* means editing any entry visibly breaks the record. |
| **Schedule of Rates (SoR)** | The government's official price list per unit of work (e.g. ₹1,450 per metre of road). |

</details>

---

Software runs at digital speed until it touches the physical world. There, trust still moves at the speed of a human with a clipboard: the site engineer measuring a road, the loss adjuster visiting a claim, the bank officer auditing warehouse stock. Verification is the last analog industry, and it quietly blocks enormous amounts of money:

| Industry | Where verification blocks the money |
|---|---|
| Public works | Hand-measured work; India alone has an estimated Rs 1-3 lakh crore stuck in delayed payments and disputes; arbitration averages 7-8 years |
| Insurance | Physical claim inspection; cost and fraud both scale with the delay |
| Trade & banking | Paper bills of lading, collateral audits |
| Carbon & ESG | Verification scandals are the market's central crisis |
| Agriculture | Crop-loss assessment and warehouse receipts gate all lending |

GroundTruth is one primitive applied everywhere:

1. **Observe** — sensors and AI capture physical state (geotagged imagery, drone passes, vision-based quantity assessment).
2. **Attest** — an accountable human certifies the AI-prepared observation. **Dual-key**: no certificate without machine evidence, no action without a human signature. AI provides scale; the human provides legal standing.
3. **Act** — the certificate is a portable, tamper-evident object other systems consume instantly: release a payment, settle a claim, extend credit.

## Quickstart

Python 3.9+, zero dependencies.

```bash
python demo.py
```

The demo walks the beachhead scenario end to end — an Indian public-works measurement:

- a sanctioned road work item (Schedule-of-Rates line, sanctioned quantity, site coordinates)
- geo-checked field evidence (a capture from 40 km away is rejected before any human sees it)
- AI quantity takeoff prefills the measurement; the Junior Engineer signs a dual-key certificate binding the evidence hashes
- the certificate becomes a **bank-financeable receivable**: discounted at 9% p.a., the contractor is paid at T+2 instead of borrowing at 18-24% for six months
- the hash-chained ledger breaks visibly when someone inflates a certified quantity
- `public_ledger_map.html` — every certified work as a pin on a public map (open it in a browser)

## Why the beachhead is public works

Every rupee of Indian government construction moves on a handwritten Measurement Book. Contractors wait 6-18 months; the government overpays because bids price in the delay; disputes take 7-8 years because a paper register cannot prove what was done and when. The state has already half-committed: the central works department (CPWD) runs an electronic measurement book paying ~Rs 20,000 crore/year digitally, while state departments remain on paper. GroundTruth completes that journey and adds the layer nobody has built: **a certified measurement as a financeable asset**. A road that pays for itself as it is built.

## Repository layout

```
groundtruth/
  models.py    WorkItem, Evidence, Measurement, dual-key Certificate, Receivable
  takeoff.py   AI quantity estimation (labeled stub; interface is the point)
  ledger.py    hash-chained certificate ledger
  mapview.py   Leaflet map generator (the citizen view)
demo.py        the full flow, measurement to money
docs/ARCHITECTURE.md
```

## What's in v0.2 (still zero-dependency)

| Capability | Where | Notes |
|---|---|---|
| **Financing engine** | `groundtruth/finance.py` | The full waterfall: advance at T+1 per the reliability curve, holdback as the bank's buffer, interest on actual days outstanding, platform fee, treasury deductions absorbed by the holdback first, conservation enforced. Bank yield and contractor all-in cost computed and tested. |
| **Reliability scoring** | `groundtruth/reliability.py` | Settled history → score → advance rate. Monotone curve; disputes hurt 2.5× more than cleans help (banks are asymmetric); score clamped [0.50, 0.99]. **The flywheel is code, not a slide.** |
| **Advance-rate curve** | `finance.py::ADVANCE_CURVE` | 0.80→50% … 0.98→85%; below 0.80 the instrument is not financeable. Step-shaped on purpose — it's a credit-committee artifact. |
| **Dual-key certificates** | `groundtruth/models.py` | Machine evidence + engineer signature; geo-fencing rejects remote captures before any human sees them; chained ledger breaks visibly at any edited entry. |
| **CLI** | `python -m groundtruth` | `demo`, `curve`, `finance --invoice … --score … --days …`, `compare` (GroundTruth vs status quo for any invoice). |
| **Three-invoice demo** | `demo.py` | Invoice 1: full pipeline. Invoice 2: a treasury deduction absorbed by the holdback. Invoice 3: clean history raises the score and the advance rate steps up — the moat, live. |
| **Test suite** | `tests/` | 22 tests: geo-fence, dual-key, tamper detection, waterfall arithmetic & conservation, deduction absorption, curve monotonicity, flywheel movement. `python -m unittest discover tests` |
| **Financial model doc** | `docs/FINANCIAL_MODEL.md` | Formulas, worked example, unit economics for all three parties, risk register. |

## Roadmap

- [ ] Real vision takeoff (photogrammetry against SoR items) with calibrated confidence
- [ ] Ed25519 signatures and engineer key registry (the construction exists in the sibling [Surety](https://github.com/Bahniman/surety) project)
- [ ] PFMS/e-MB integration adapter (the existing government rail)
- [ ] Financier API: query and bid on certified receivables (TReDS pattern)
- [ ] Second vertical: insurance claim attestation with the identical primitive

## License

MIT
