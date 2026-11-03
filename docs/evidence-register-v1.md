# External markup evidence register (schema version 1)

**Status:** initial offline safety contract. This is a structured evidence-presence validator, **not** an authentication service, proof of drawing correctness, proof of successful native measurement, or commercial approval.

The register lives **outside Bluebeam's mutable measurement Comment field**. This deliberately coexists with legacy `tools/validate_register.py`, which only checks a semicolon-separated string and must not be treated as a source of approval.

## Minimal format

```json
{
  "schema_version": 1,
  "markups": [
    {
      "markup_id": "SYN-001",
      "page_index": 0,
      "page_label": "SYN-C-101",
      "source_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "source_revision": "A",
      "plan_id": "S-M1",
      "status": "AI_PROPOSED",
      "measurement_type": "Length",
      "unit": "m",
      "scale_resolved": false,
      "scale_verified": false
    }
  ]
}
```

`python tools/validate_evidence_register.py path/to/synthetic-register.json`

- Exit **2**: structurally invalid record.
- Exit **1**: recorded evidence is incomplete and human review/field evidence is needed.
- Exit **0**: record has the required *fields*, not that the quantity is true, reviewer authenticated, or the bid approved.
- The documented page index is **zero-based** here. The vendor MCP creation tool may require a **one-based** page number, so an adapter must explicitly convert and verify it.

## State-specific fields

- `AI_PROPOSED`: no quantity needs to be invented.
- `MEASURED`: record `native_readback` and finite `computed_quantity` from the host; this initial validator checks field presence only.
- `QA_CHECKED`: additionally for scale-dependent measurements require `scale_resolved=true`, `scale_verified=true`, nonempty `scale_basis`, `visual_location_checked=true`, and nonempty `independent_evidence`.
- `ESTIMATOR_REVIEWED` and `APPROVED`: additionally log `human_review` with `reviewer`, `reviewed_on` and `decision_ref`. `APPROVED` requires `decision=APPROVE`. **Names and flags are not authenticated**: no agent may self-authorize these statuses. True signed/access-controlled decisions remain a separate integration gate.
- `do_not_sum=true` with a QA or later state remains an unresolved quantity-eligibility problem. QA-only markup geometry must never contribute to rollups.

## Limitations and next work

This initial validator does **not** check whether the PDF bytes match the supplied SHA-256, whether a purported readback actually came from Revu, whether the independent evidence is independent, whether status transitions were legally followed, or who controlled the reviewer identity. These are intentionally separate acceptance gates in [Issue #3](https://github.com/taiduc1302/civil-takeoff-markups-mcp/issues/3), [Issue #5](https://github.com/taiduc1302/civil-takeoff-markups-mcp/issues/5) and [Issue #6](https://github.com/taiduc1302/civil-takeoff-markups-mcp/issues/6).

Only synthetic fixtures are publishable. Real tender data and native readback receipts must remain private.
