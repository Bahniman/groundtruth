"""GroundTruth test suite.  Run:  python -m unittest discover tests -v"""
import hashlib
import unittest

from groundtruth.models import WorkItem, Evidence, Certificate
from groundtruth.takeoff import estimate_quantity
from groundtruth.ledger import Ledger
from groundtruth.finance import (Financing, FinancingTerms, advance_rate_for,
                                 status_quo_cost)
from groundtruth.reliability import ReliabilityLedger, SettlementRecord


def make_work(**over):
    kw = dict(description="WBM road", sor_code="RD-104", unit="metre",
              rate=1450.0, sanctioned_qty=300, lat=26.1445, lon=91.7362)
    kw.update(over)
    return WorkItem(**kw)


def make_evidence(work, span=240, lat=None, lon=None, salt="x"):
    return Evidence(work_id=work.id, kind="site_photo",
                    payload_sha256=hashlib.sha256(salt.encode()).hexdigest(),
                    lat=lat if lat is not None else work.lat + 0.0002,
                    lon=lon if lon is not None else work.lon + 0.0002,
                    meta={"measured_span": span})


class TestVerification(unittest.TestCase):
    def test_geo_fence_rejects_remote_evidence(self):
        work = make_work()
        fake = make_evidence(work, lat=26.45, lon=91.55)  # ~39 km away
        with self.assertRaises(ValueError):
            estimate_quantity(work, [fake])

    def test_quantity_capped_at_sanction(self):
        work = make_work(sanctioned_qty=200)
        m = estimate_quantity(work, [make_evidence(work, span=260)])
        self.assertLessEqual(m.quantity, 200)

    def test_confidence_rises_with_corroboration(self):
        work = make_work()
        m1 = estimate_quantity(work, [make_evidence(work, salt="a")])
        m2 = estimate_quantity(work, [make_evidence(work, salt="a"),
                                      make_evidence(work, salt="b")])
        self.assertGreater(m2.confidence, m1.confidence)

    def test_dual_key_requires_evidence(self):
        work = make_work()
        m = estimate_quantity(work, [make_evidence(work)])
        with self.assertRaises(ValueError):
            Certificate.sign(m, [], "JE X", "key", rate=work.rate)

    def test_certificate_verifies_and_detects_tamper(self):
        work = make_work()
        ev = [make_evidence(work, salt="a"), make_evidence(work, salt="b")]
        m = estimate_quantity(work, ev)
        cert = Certificate.sign(m, ev, "JE X", "je-key", rate=work.rate)
        self.assertTrue(cert.verify("je-key"))
        cert.measurement["quantity"] = 999
        self.assertFalse(cert.verify("je-key"))

    def test_certificate_amount(self):
        work = make_work(rate=1450.0)
        ev = [make_evidence(work, span=240)]
        m = estimate_quantity(work, ev)
        cert = Certificate.sign(m, ev, "JE X", "k", rate=work.rate)
        self.assertAlmostEqual(cert.amount, m.quantity * 1450.0, places=2)


class TestLedger(unittest.TestCase):
    def test_chain_and_tamper(self):
        led = Ledger()
        led.record("a", {"x": 1})
        led.record("b", {"x": 2})
        led.record("c", {"x": 3})
        ok, _ = led.verify()
        self.assertTrue(ok)
        led.entries[1]["payload"]["x"] = 99
        ok, bad = led.verify()
        self.assertFalse(ok)
        self.assertEqual(bad, 1)


class TestAdvanceCurve(unittest.TestCase):
    def test_curve_monotone(self):
        scores = [0.50, 0.80, 0.85, 0.90, 0.95, 0.98, 0.99]
        rates = [advance_rate_for(s) for s in scores]
        self.assertEqual(rates, sorted(rates))

    def test_floor_not_financeable(self):
        self.assertEqual(advance_rate_for(0.79), 0.0)

    def test_known_points(self):
        self.assertEqual(advance_rate_for(0.91), 0.60)
        self.assertEqual(advance_rate_for(0.98), 0.85)


class TestFinancing(unittest.TestCase):
    def test_waterfall_arithmetic(self):
        fin = Financing(1863900, 0.91).advance().settle(148)
        # 60% advance
        self.assertAlmostEqual(fin.advance_amount, 1118340.0, places=2)
        self.assertAlmostEqual(fin.holdback, 745560.0, places=2)
        # interest = advance * 11% * 148/365
        expected_interest = round(1118340 * 0.11 * 148 / 365, 2)
        self.assertAlmostEqual(fin.interest_charge, expected_interest, places=2)
        # conservation: advance + balance + charges + deduction == invoice
        total_out = (fin.advance_amount + fin.balance_released
                     + fin.interest_charge + fin.platform_fee
                     + fin.treasury_deduction)
        self.assertAlmostEqual(total_out, fin.invoice_value, places=1)

    def test_deduction_absorbed_by_holdback(self):
        fin = Financing(1000000, 0.91).advance().settle(120, treasury_deduction=50000)
        no_ded = Financing(1000000, 0.91).advance().settle(120)
        self.assertAlmostEqual(no_ded.balance_released - fin.balance_released,
                               50000, places=2)
        # advance untouched
        self.assertEqual(fin.advance_amount, no_ded.advance_amount)

    def test_balance_never_negative(self):
        fin = Financing(100000, 0.91).advance().settle(120, treasury_deduction=10**7)
        self.assertEqual(fin.balance_released, 0.0)

    def test_not_financeable_below_floor(self):
        fin = Financing(100000, 0.60).advance()
        self.assertFalse(fin.financeable)
        with self.assertRaises(ValueError):
            fin.settle(100)

    def test_negative_deduction_rejected(self):
        fin = Financing(100000, 0.91).advance()
        with self.assertRaises(ValueError):
            fin.settle(100, treasury_deduction=-5)

    def test_contractor_beats_status_quo(self):
        fin = Financing(1863900, 0.91).advance().settle(148)
        sq = status_quo_cost(1863900, 148)
        self.assertGreater(fin.contractor_net_pct, sq["net_pct"])

    def test_bank_yield_matches_terms(self):
        fin = Financing(1000000, 0.91,
                        FinancingTerms(annual_interest=0.11)).advance().settle(146)
        self.assertAlmostEqual(fin.bank_yield_annualized(), 11.0, delta=0.1)


class TestReliability(unittest.TestCase):
    def test_new_relationship_base(self):
        led = ReliabilityLedger()
        self.assertAlmostEqual(led.score(), 0.88, places=2)

    def test_clean_history_raises_score(self):
        led = ReliabilityLedger()
        s0 = led.score()
        for _ in range(6):
            led.record(SettlementRecord(500000, evidence_quality=0.94))
        self.assertGreater(led.score(), s0)

    def test_disputes_hurt_more_than_cleans_help(self):
        led = ReliabilityLedger()
        led.record(SettlementRecord(500000))                      # clean
        up = led.score() - ReliabilityLedger().score()
        led2 = ReliabilityLedger()
        led2.record(SettlementRecord(500000, disputed=True))
        down = ReliabilityLedger().score() - led2.score()
        self.assertGreater(down, up)

    def test_score_clamped(self):
        led = ReliabilityLedger()
        for _ in range(500):
            led.record(SettlementRecord(1, evidence_quality=1.0))
        self.assertLessEqual(led.score(), 0.99)
        led2 = ReliabilityLedger()
        for _ in range(50):
            led2.record(SettlementRecord(1, disputed=True))
        self.assertGreaterEqual(led2.score(), 0.50)

    def test_flywheel_moves_advance_rate(self):
        led = ReliabilityLedger()
        r0 = advance_rate_for(led.score())
        for _ in range(6):
            led.record(SettlementRecord(500000, evidence_quality=0.95))
        r1 = advance_rate_for(led.score())
        self.assertGreater(r1, r0)


if __name__ == "__main__":
    unittest.main()
