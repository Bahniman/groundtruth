"""Reliability scoring: the moat, expressed as arithmetic.

A contractor/division pair earns a verification reliability score from its
settled history. The score feeds the advance-rate curve in finance.py, so
clean history literally buys more day-one liquidity - and a new entrant
without history cannot offer banks the same instrument.

Scoring model (prototype - transparent and monotone, which is what a credit
committee needs before it needs sophistication):

  score = base
        + weight_clean   * f(clean settlements)
        - weight_dispute * g(disputed settlements)
        + evidence_bonus * (avg evidence quality - baseline)

  clamped to [0.50, 0.99]. New relationships start at `base` (0.88): good
  enough to finance at 55-60%, with headroom to earn more.
"""
import math
from dataclasses import dataclass, field


@dataclass
class SettlementRecord:
    invoice_value: float
    disputed: bool = False
    deduction: float = 0.0
    evidence_quality: float = 0.9   # 0..1, from capture completeness checks


@dataclass
class ReliabilityLedger:
    base: float = 0.88
    records: list = field(default_factory=list)

    def record(self, rec: SettlementRecord):
        self.records.append(rec)

    @property
    def clean_count(self) -> int:
        return sum(1 for r in self.records if not r.disputed and r.deduction == 0)

    @property
    def disputed_count(self) -> int:
        return sum(1 for r in self.records if r.disputed)

    @property
    def dispute_rate(self) -> float:
        return self.disputed_count / len(self.records) if self.records else 0.0

    def score(self) -> float:
        s = self.base
        # diminishing returns on clean history: log2(1+n) * 1.2 points
        s += 0.012 * math.log2(1 + self.clean_count)
        # disputes hurt fast: 3 points each, linear (banks are asymmetric)
        s -= 0.03 * self.disputed_count
        # evidence quality vs a 0.85 baseline, up to +/- 1.5 points
        if self.records:
            avg_q = sum(r.evidence_quality for r in self.records) / len(self.records)
            s += 0.015 * (avg_q - 0.85) / 0.15
        return round(min(0.99, max(0.50, s)), 4)
