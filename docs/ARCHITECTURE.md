# GroundTruth — architecture

## The primitive

```
physical world
   |  sensors + AI            (Observe)
   v
Measurement (prefilled, confidence-scored, geo-checked evidence attached)
   |  accountable human signs (Attest: dual-key)
   v
Certificate { measurement, evidence hashes, engineer signature }
   |  consumed by systems     (Act)
   v
payment release | claim settlement | credit | registry entry
```

Dual-key invariant, enforced in code (`Certificate.sign` refuses without
evidence): the machine cannot certify alone, the human cannot certify
without machine evidence bound into the signature.

## Anti-fraud layers

1. **Geo-consistency before humans**: evidence captured away from the sanctioned site is rejected automatically (`takeoff.estimate_quantity`).
2. **Hash binding**: the engineer signs over the evidence hashes; swapping photos after the fact invalidates the signature.
3. **Chained ledger**: editing any certified entry breaks the chain at that entry, visibly.
4. **(Production) independent cross-check**: claimed assets verified against open geodata and satellite basemaps — an OSM query layer in the spirit of open-source tools like Sightline; random third-party audit sampling.

## Prototype shortcuts, and the production answer

| Shortcut here | Production |
|---|---|
| Takeoff derives quantity from capture metadata (labeled stub) | Photogrammetry / vision measurement per SoR item class, calibrated confidence, model versioning |
| HMAC engineer signature | Ed25519 keys in a registry tied to the department's HR system |
| In-memory ledger | Durable store, periodically anchored to an external timestamp authority |
| One payer, one financier | Financier marketplace bidding on certified receivables (TReDS pattern) |

## Where the money is

- SaaS to departments and contractors (measurement-to-payment days is the KPI: 90 down to 15)
- Basis-point fee on discounted receivables (the financeability layer is the wedge nobody else builds)
- Verification-as-a-service expansion: insurance claims, agri lending, trade docs, carbon — the same primitive with different evidence classes

## Endgame

An open attestation protocol (the UPI/ONDC playbook): states, insurers, banks
and registries adopt a standard, not a vendor. Whoever writes the standard
and holds the trust graph runs the rail.
