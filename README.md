# GroundTruth

**The verification rail for the physical economy.**

### ▶ Try the live demo (no installation): https://bahniman.github.io/groundtruth.html

---

## In plain English (no jargon)

When a contractor builds a government road in India, an engineer measures the finished work **by hand, in a paper register**, and the contractor then waits 6 to 18 months to get paid while that register slowly crawls through approvals. Meanwhile the contractor is often borrowing money at 18–24% just to survive the wait.

**GroundTruth replaces the paper register.** Photos and AI measure the work; the engineer checks and signs it digitally; and that signed record is solid enough for a bank to pay the contractor **within two days** (the bank then collects from the government later). A road that pays for itself as it's built.

The bigger idea: this same pattern — *a machine observes, an accountable person signs, money moves* — is the bottleneck in insurance (someone must inspect the damage), banking (someone must verify the collateral), and carbon markets (someone must confirm the project is real). Verification is the last thing still done by a human with a clipboard.

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

## Status and roadmap

Working concept prototype.

- [x] Dual-key certificate, geo-checked evidence, chained ledger, receivable discounting, public map
- [ ] Real vision takeoff (photogrammetry against SoR items) with calibrated confidence
- [ ] Ed25519 signatures and engineer key registry
- [ ] PFMS/e-MB integration adapter (the existing government rail)
- [ ] Financier API: query and bid on certified receivables
- [ ] Second vertical: insurance claim attestation with the identical primitive

## License

MIT
