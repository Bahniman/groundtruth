"""GroundTruth demo: from a road under construction to money in the
contractor's account, with a dual-key certificate in between.

Run:  python demo.py
Zero dependencies. Writes public_ledger_map.html you can open in a browser.
"""
import hashlib

from groundtruth.models import WorkItem, Evidence, Receivable
from groundtruth.takeoff import estimate_quantity
from groundtruth.models import Certificate
from groundtruth.ledger import Ledger
from groundtruth.mapview import write_map

W = 74


def banner(t):
    print("\n" + "=" * W + "\n" + t + "\n" + "=" * W)


def main():
    ledger = Ledger()

    banner("1. A sanctioned work item (what the paper Measurement Book covers)")
    work = WorkItem(
        description="WBM road, village approach, km 3.2-3.5",
        sor_code="SOR-RD-104", unit="metre", rate=1450.0,
        sanctioned_qty=300, lat=26.1445, lon=91.7362)
    ledger.record("work_sanctioned", work)
    print(f"\n  {work.description}")
    print(f"  {work.sor_code} | sanctioned {work.sanctioned_qty} {work.unit} "
          f"at Rs {work.rate:.0f}/{work.unit}")

    banner("2. Field capture: machine evidence, geo-checked before any human sees it")
    ev1 = Evidence(work_id=work.id, kind="site_photo",
                   payload_sha256=hashlib.sha256(b"photo-bytes-1").hexdigest(),
                   lat=26.1447, lon=91.7360, meta={"measured_span": 238})
    ev2 = Evidence(work_id=work.id, kind="drone_pass",
                   payload_sha256=hashlib.sha256(b"drone-strip-1").hexdigest(),
                   lat=26.1444, lon=91.7365, meta={"measured_span": 242})
    for ev in (ev1, ev2):
        ledger.record("evidence", ev)
        print(f"  {ev.kind:<12} {ev.id}  ({ev.distance_m(work.lat, work.lon):.0f} m "
              f"from sanctioned site)  sha256 {ev.payload_sha256[:12]}...")

    print("\n  and a fake capture from 40 km away is rejected automatically:")
    fake = Evidence(work_id=work.id, kind="site_photo",
                    payload_sha256=hashlib.sha256(b"stolen-photo").hexdigest(),
                    lat=26.45, lon=91.55, meta={"measured_span": 300})
    try:
        estimate_quantity(work, [fake])
    except ValueError as e:
        print(f"  REJECTED: {e}")

    banner("3. AI takeoff prefills the measurement; the engineer certifies (dual-key)")
    m = estimate_quantity(work, [ev1, ev2])
    print(f"\n  AI estimate: {m.quantity} {m.unit} (method {m.method}, "
          f"confidence {m.confidence})")

    cert = Certificate.sign(m, [ev1, ev2], engineer="JE R. Sharma",
                            engineer_secret="je-sharma-key", rate=work.rate)
    ledger.record("certificate", cert)
    print(f"  {cert.id}: certified by {cert.engineer}, "
          f"amount Rs {cert.amount:,.0f}")
    print(f"  signature verifies: {cert.verify('je-sharma-key')}")
    print("  dual-key holds: the AI could not certify alone, the engineer could "
          "not certify\n  without evidence hashes bound into the signature.")

    banner("4. The certificate becomes money")
    r = Receivable(certificate_id=cert.id, contractor="M/s Borah Constructions",
                   payer="State PWD Division IV", face_value=cert.amount)
    got = r.discount(financier="Bank of Example", annual_rate=0.09, days_to_pay=45)
    ledger.record("receivable_discounted", r)
    print(f"\n  face value Rs {r.face_value:,.0f}, payable in ~45 days")
    print(f"  bank discounts at 9% p.a. -> contractor receives Rs {got:,.0f} at T+2")
    print("  (today the same contractor borrows this bridge at 18-24% informally)")

    banner("5. The ledger cannot be quietly rewritten")
    ok, _ = ledger.verify()
    print(f"\n  ledger intact: {ok}  ({len(ledger.entries)} entries)")
    ledger.entries[3]["payload"]["quantity"] = 300  # inflate the measurement
    ok, bad = ledger.verify()
    print(f"  someone inflates the certified quantity... ledger intact: {ok} "
          f"(breaks at entry #{bad})")

    banner("6. The citizen view")
    path = write_map("public_ledger_map.html", [{
        "description": work.description, "sor_code": work.sor_code,
        "qty": m.quantity, "unit": m.unit, "engineer": cert.engineer,
        "amount": cert.amount, "status": "CERTIFIED",
        "lat": work.lat, "lon": work.lon}])
    print(f"\n  wrote {path}: every certified work, a pin on a public map.")
    print("""
  Observe (AI) -> Attest (accountable human) -> Act (money moves).
  That is GroundTruth: verification as a rail, not a site visit.
""")


if __name__ == "__main__":
    main()
