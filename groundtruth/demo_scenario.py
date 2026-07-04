"""GroundTruth guided demo: three invoices, one contractor, and the flywheel.

Invoice 1: the full pipeline - evidence, dual-key certificate, financing.
Invoice 2: a treasury deduction absorbed by the holdback (the buffer working).
Invoice 3: clean history has raised the reliability score - the advance rate
           steps up, and day-one liquidity grows. That is the moat, live.
"""
import hashlib

from .models import WorkItem, Evidence, Certificate
from .takeoff import estimate_quantity
from .ledger import Ledger
from .finance import Financing, status_quo_cost
from .reliability import ReliabilityLedger, SettlementRecord

W = 76


def banner(t):
    print("\n" + "=" * W + "\n" + t + "\n" + "=" * W)


def _inr(x):
    return f"Rs {x:,.0f}"


def certify_work(ledger, description, sor, unit, rate, sanctioned, spans):
    work = WorkItem(description=description, sor_code=sor, unit=unit,
                    rate=rate, sanctioned_qty=sanctioned,
                    lat=26.1445, lon=91.7362)
    ledger.record("work_sanctioned", work)
    evidence = []
    for i, span in enumerate(spans):
        ev = Evidence(work_id=work.id, kind="site_photo" if i % 2 == 0 else "drone_pass",
                      payload_sha256=hashlib.sha256(f"{work.id}-{i}".encode()).hexdigest(),
                      lat=26.1446, lon=91.7363, meta={"measured_span": span})
        evidence.append(ev)
        ledger.record("evidence", ev)
    m = estimate_quantity(work, evidence)
    cert = Certificate.sign(m, evidence, engineer="JE R. Sharma",
                            engineer_secret="je-sharma-key", rate=work.rate)
    ledger.record("certificate", cert)
    return work, m, cert


def run():
    ledger = Ledger()
    history = ReliabilityLedger()

    banner("GROUNDTRUTH v0.2: three invoices, one contractor, the flywheel")
    print("\n  Contractor: M/s Borah Constructions | Payer: State PWD Division IV")
    print("  Bank: Bank of Example | standing agreement: advance per reliability curve")

    # ------------------------------------------------------- invoice 1
    banner("Invoice 1 - the full pipeline")
    work, m, cert = certify_work(
        ledger, "WBM road, village approach, km 3.2-3.5", "RD-104",
        "metre", 1450.0, 300, [238, 242])
    print(f"\n  evidence geo-checked, AI estimate {m.quantity} {m.unit} "
          f"(confidence {m.confidence}), JE signs")
    print(f"  dual-key certificate {cert.id}: {_inr(cert.amount)}")

    score = history.score()
    fin1 = Financing(cert.amount, score).advance()
    print(f"\n  reliability score {score:.2f} (new relationship) "
          f"-> advance rate {fin1.advance_rate*100:.0f}%")
    print(f"  T+1, 9:00 AM: {_inr(fin1.advance_amount)} credited; "
          f"holdback {_inr(fin1.holdback)}")

    fin1.settle(days_outstanding=148)
    print("\n  Day 148 - treasury settles. The waterfall:")
    for label, amount in fin1.waterfall()[3:]:
        sign = "+" if amount >= 0 else "-"
        print(f"    {label:<56} {sign}{_inr(abs(amount))}")
    sq = status_quo_cost(cert.amount, 148)
    print(f"\n  contractor nets {fin1.contractor_net_pct:.1f}% with day-1 liquidity"
          f"  (status quo: {sq['net_pct']:.1f}% after {sq['first_rupee_day']} days"
          f" of 22% bridge debt)")
    history.record(SettlementRecord(cert.amount, evidence_quality=0.92))

    # ------------------------------------------------------- invoice 2
    banner("Invoice 2 - a deduction hits; the holdback absorbs it")
    work2, m2, cert2 = certify_work(
        ledger, "CC drain, ward 7, 410 m", "DR-221", "metre", 980.0, 420, [408, 412])
    score = history.score()
    fin2 = Financing(cert2.amount, score).advance()
    print(f"\n  certificate {cert2.id}: {_inr(cert2.amount)} | score {score:.2f}"
          f" -> advance {fin2.advance_rate*100:.0f}% = {_inr(fin2.advance_amount)} at T+1")
    fin2.settle(days_outstanding=131, treasury_deduction=18000)
    print(f"  treasury applies an audit deduction of {_inr(18000)}")
    print(f"  the deduction comes out of the HOLDBACK, not the advance:"
          f" balance released {_inr(fin2.balance_released)}")
    print(f"  the contractor's day-1 money was never at risk - that is what"
          f" the holdback is for")
    history.record(SettlementRecord(cert2.amount, deduction=18000,
                                    evidence_quality=0.90))

    # ------------------------------------------------------- invoice 3
    banner("Invoice 3 - clean history moves the advance rate up")
    for _ in range(4):   # a season of clean settlements
        history.record(SettlementRecord(500000, evidence_quality=0.94))
    work3, m3, cert3 = certify_work(
        ledger, "PCC pavement, market road, 640 sq.m", "RD-233",
        "sq.m", 2075.0, 660, [636, 644])
    score3 = history.score()
    fin3 = Financing(cert3.amount, score3).advance()
    print(f"\n  after a season of clean settlements: score {score3:.2f}")
    print(f"  certificate {cert3.id}: {_inr(cert3.amount)}"
          f" -> advance rate {fin3.advance_rate*100:.0f}%"
          f" = {_inr(fin3.advance_amount)} at T+1")
    print(f"\n  Same contractor, same bank. The verification history itself")
    print(f"  bought {fin3.advance_rate*100 - fin1.advance_rate*100:.0f} extra"
          f" points of day-one liquidity. A competitor without the")
    print(f"  settled-history ledger cannot offer a bank this curve.")

    # ------------------------------------------------------- integrity
    banner("And the ledger still cannot be rewritten")
    ok, _ = ledger.verify()
    print(f"\n  {len(ledger.entries)} entries, chain intact: {ok}")
    ledger.entries[2]["payload"]["quantity"] = 999
    ok, bad = ledger.verify()
    print(f"  someone inflates an old certificate... chain intact: {ok}"
          f" (breaks at entry #{bad})")
    print("\n  Observe (AI) -> Attest (accountable human) -> Act (money moves).\n")
