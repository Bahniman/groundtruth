"""AI quantity takeoff.

STUB, clearly labeled: in this prototype the 'vision model' derives quantity
from evidence metadata (a surveyed span recorded by the capture app). The
production path is photogrammetry / vision measurement against the Schedule
of Rates item, with a calibrated confidence score. The interface is the
point: takeoff produces a Measurement that a human must still attest.
"""
from .models import Measurement, Evidence, WorkItem


def estimate_quantity(work: WorkItem, evidence: list) -> Measurement:
    if not evidence:
        raise ValueError("cannot estimate without evidence")

    # geo-consistency: every capture must sit near the sanctioned site
    for ev in evidence:
        d = ev.distance_m(work.lat, work.lon)
        if d > 500:
            raise ValueError(f"evidence {ev.id} is {d:.0f} m from the sanctioned "
                             f"site: rejected before any human sees it")

    spans = [ev.meta.get("measured_span", 0) for ev in evidence]
    qty = round(sum(spans) / max(len([s for s in spans if s]), 1), 2)
    qty = min(qty, work.sanctioned_qty)  # cannot certify beyond sanction

    # confidence rises with corroborating captures
    confidence = min(0.55 + 0.15 * len(evidence), 0.95)

    return Measurement(
        work_id=work.id, quantity=qty, unit=work.unit,
        method="vision_takeoff_v0_stub",
        evidence_ids=[ev.id for ev in evidence],
        confidence=round(confidence, 2))
