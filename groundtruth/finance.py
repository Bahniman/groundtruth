"""The financing engine: how a verified certificate becomes money.

The model (the heart of the business):

  1. A verified e-invoice is issued for certified work.
  2. Per standing agreement, the bank advances `advance_rate` percent of the
     invoice the next morning (T+1). The advance rate is a FUNCTION OF THE
     VERIFICATION RELIABILITY SCORE - better verification history buys
     contractors more day-one liquidity. This is the flywheel.
  3. The holdback (1 - advance_rate) stays with the bank as its buffer
     against verification error, disputes, and treasury deductions.
  4. When the treasury settles (typically months later), the bank collects
     the full invoice value and releases the holdback minus:
       - financing interest on the advance for the actual days outstanding
       - a platform fee on the invoice value
  5. Deductions by the treasury (audit cuts, penalties) come out of the
     holdback first - that is what the holdback is for.

Every number this engine produces is itemized; nothing is a black box.
"""
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Advance-rate curve: reliability score -> fraction the bank will advance.
# Piecewise-linear, conservative at the bottom, capped at the top. The
# calibration story: each segment is what a credit committee would actually
# sign, given the dispute rate implied by the score (see reliability.py).
# ---------------------------------------------------------------------------
ADVANCE_CURVE = [
    # (min_score, advance_rate)
    (0.98, 0.85),
    (0.95, 0.75),
    (0.90, 0.60),
    (0.85, 0.55),
    (0.80, 0.50),
    (0.00, 0.00),   # below 0.80 the instrument is not financeable
]


def advance_rate_for(score: float) -> float:
    for floor, rate in ADVANCE_CURVE:
        if score >= floor:
            return rate
    return 0.0


@dataclass
class FinancingTerms:
    annual_interest: float = 0.11      # bank's financing rate on the advance
    platform_fee_rate: float = 0.0035  # GroundTruth fee on invoice value
    expected_days_to_settle: int = 150


@dataclass
class Financing:
    """The full lifecycle of one financed invoice, every rupee itemized."""
    invoice_value: float
    reliability_score: float
    terms: FinancingTerms = field(default_factory=FinancingTerms)

    # populated by advance()
    advance_rate: float = 0.0
    advance_amount: float = 0.0
    holdback: float = 0.0
    financeable: bool = False

    # populated by settle()
    settled: bool = False
    days_outstanding: int = 0
    interest_charge: float = 0.0
    platform_fee: float = 0.0
    treasury_deduction: float = 0.0
    balance_released: float = 0.0

    def advance(self) -> "Financing":
        self.advance_rate = advance_rate_for(self.reliability_score)
        self.financeable = self.advance_rate > 0
        self.advance_amount = round(self.invoice_value * self.advance_rate, 2)
        self.holdback = round(self.invoice_value - self.advance_amount, 2)
        return self

    def settle(self, days_outstanding: int,
               treasury_deduction: float = 0.0) -> "Financing":
        if not self.financeable:
            raise ValueError("cannot settle an unfinanced invoice")
        if treasury_deduction < 0:
            raise ValueError("deduction cannot be negative")
        self.days_outstanding = days_outstanding
        self.interest_charge = round(
            self.advance_amount * self.terms.annual_interest * days_outstanding / 365, 2)
        self.platform_fee = round(
            self.invoice_value * self.terms.platform_fee_rate, 2)
        self.treasury_deduction = round(treasury_deduction, 2)
        # deductions eat the holdback first; balance cannot go below zero
        self.balance_released = round(max(
            0.0,
            self.holdback - self.interest_charge - self.platform_fee
            - self.treasury_deduction), 2)
        self.settled = True
        return self

    # ------------------------------------------------------------- readouts
    @property
    def contractor_total(self) -> float:
        return round(self.advance_amount + self.balance_released, 2)

    @property
    def contractor_net_pct(self) -> float:
        return round(self.contractor_total / self.invoice_value * 100, 2)

    @property
    def effective_cost_pct(self) -> float:
        """All-in cost to the contractor as % of invoice value."""
        return round(100 - self.contractor_net_pct, 2)

    def bank_yield_annualized(self) -> float:
        """Bank's return on the advance, annualized, net of nothing (interest
        is its revenue; credit risk is buffered by the holdback)."""
        if not self.settled or self.advance_amount == 0 or self.days_outstanding == 0:
            return 0.0
        period_return = self.interest_charge / self.advance_amount
        return round(period_return * 365 / self.days_outstanding * 100, 2)

    def waterfall(self) -> list:
        """The settlement, line by line - what the demo and the bank see."""
        rows = [
            ("Verified invoice value", self.invoice_value),
            (f"Advance at T+1 ({self.advance_rate*100:.0f}% @ score "
             f"{self.reliability_score:.2f})", self.advance_amount),
            ("Holdback (bank's buffer)", self.holdback),
        ]
        if self.settled:
            rows += [
                (f"Interest on advance ({self.terms.annual_interest*100:.0f}% p.a. "
                 f"x {self.days_outstanding} days)", -self.interest_charge),
                (f"Platform fee ({self.terms.platform_fee_rate*100:.2f}%)",
                 -self.platform_fee),
            ]
            if self.treasury_deduction:
                rows.append(("Treasury deduction (absorbed by holdback)",
                             -self.treasury_deduction))
            rows += [
                ("Balance released at settlement", self.balance_released),
                ("Contractor receives in total", self.contractor_total),
            ]
        return rows


def status_quo_cost(invoice_value: float, days: int,
                    informal_rate: float = 0.22) -> dict:
    """What waiting actually costs a contractor today: bridge borrowing at
    informal rates for the full wait."""
    cost = round(invoice_value * informal_rate * days / 365, 2)
    return {"bridge_cost": cost,
            "net": round(invoice_value - cost, 2),
            "net_pct": round((invoice_value - cost) / invoice_value * 100, 2),
            "first_rupee_day": days}
