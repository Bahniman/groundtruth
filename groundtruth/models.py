"""Core objects: work item -> evidence -> measurement -> dual-key certificate
-> financeable receivable.

The dual-key rule is the heart of the system:
  no certificate without machine evidence,
  no action without a human signature.
"""
import hashlib
import hmac
import json
import time
import uuid
from dataclasses import dataclass, field, asdict


def _canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass
class WorkItem:
    """A sanctioned unit of work with its Schedule-of-Rates line."""
    description: str
    sor_code: str            # Schedule of Rates item code
    unit: str                # metre, cubic metre, number...
    rate: float              # sanctioned rate per unit
    sanctioned_qty: float
    lat: float
    lon: float
    id: str = field(default_factory=lambda: "work_" + uuid.uuid4().hex[:10])


@dataclass
class Evidence:
    """Machine-captured proof of physical state."""
    work_id: str
    kind: str                # site_photo | drone_pass | sensor
    payload_sha256: str      # hash of the raw capture (image bytes, etc.)
    lat: float
    lon: float
    captured_at: float = field(default_factory=time.time)
    meta: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: "ev_" + uuid.uuid4().hex[:10])

    def distance_m(self, lat: float, lon: float) -> float:
        # small-angle approximation, fine at site scale
        dy = (self.lat - lat) * 111_320
        dx = (self.lon - lon) * 102_470
        return (dx * dx + dy * dy) ** 0.5


@dataclass
class Measurement:
    """AI-prefilled quantity against the work item, awaiting attestation."""
    work_id: str
    quantity: float
    unit: str
    method: str              # e.g. vision_takeoff_v0
    evidence_ids: list
    confidence: float
    id: str = field(default_factory=lambda: "m_" + uuid.uuid4().hex[:10])


@dataclass
class Certificate:
    """The dual-key attestation: machine evidence + accountable human signature."""
    measurement: dict
    evidence_hashes: list
    engineer: str
    engineer_sig: str
    certified_at: float
    amount: float
    id: str = field(default_factory=lambda: "cert_" + uuid.uuid4().hex[:10])

    @staticmethod
    def sign(measurement: Measurement, evidence: list, engineer: str,
             engineer_secret: str, rate: float) -> "Certificate":
        if not evidence:
            raise ValueError("dual-key violation: no machine evidence attached")
        ev_hashes = sorted(e.payload_sha256 for e in evidence)
        body = {"measurement": asdict(measurement),
                "evidence_hashes": ev_hashes, "engineer": engineer}
        sig = hmac.new(engineer_secret.encode(), _canonical(body).encode(),
                       hashlib.sha256).hexdigest()
        return Certificate(
            measurement=asdict(measurement), evidence_hashes=ev_hashes,
            engineer=engineer, engineer_sig=sig, certified_at=time.time(),
            amount=round(measurement.quantity * rate, 2))

    def verify(self, engineer_secret: str) -> bool:
        body = {"measurement": self.measurement,
                "evidence_hashes": self.evidence_hashes, "engineer": self.engineer}
        expected = hmac.new(engineer_secret.encode(), _canonical(body).encode(),
                            hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, self.engineer_sig)


@dataclass
class Receivable:
    """What the bank sees: a certified, timestamped claim on a government payer."""
    certificate_id: str
    contractor: str
    payer: str
    face_value: float
    status: str = "OPEN"     # OPEN -> DISCOUNTED -> SETTLED
    discounted_value: float = None
    financier: str = None

    def discount(self, financier: str, annual_rate: float, days_to_pay: int):
        haircut = self.face_value * annual_rate * days_to_pay / 365
        self.discounted_value = round(self.face_value - haircut, 2)
        self.financier = financier
        self.status = "DISCOUNTED"
        return self.discounted_value
