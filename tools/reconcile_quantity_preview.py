#!/usr/bin/env python3
"""Deterministic, fail-closed synthetic quantity preview; NEVER a BAX handoff.

External metadata are not authenticated native readback or human approval.
The algorithm never permits partial totals if any non-QA line is unresolved.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

HASH = re.compile(r"[a-fA-F0-9]{64}\Z")
TYPES = {"Length": "m", "Area": "m2", "Volume": "m3", "Count": "ea"}
ELIGIBLE_FOR_PREVIEW = {"QA_CHECKED", "ESTIMATOR_REVIEWED", "APPROVED"}


def good_hash(value):
    return isinstance(value, str) and HASH.fullmatch(value) is not None


def good_text(value):
    return isinstance(value, str) and bool(value.strip())


def good_quantity(value):
    try:
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0
    except (OverflowError, TypeError, ValueError):
        return False


def preview_quantities(register, source_control):
    """Return preview totals only if EVERY non-QA row survives all offline gates.

    No status or result here is authorization for commercial output. One active
    source PDF/revision per preview; multi-source reconciliation is a separate task.
    """
    if not isinstance(register, dict) or register.get("schema_version") != 1 or not isinstance(register.get("markups"), list):
        raise ValueError("expected v1 evidence register with markups array")
    if not isinstance(source_control, dict) or not good_hash(source_control.get("sha256")) or not good_text(source_control.get("revision")):
        raise ValueError("controlled source hash and revision required")
    rows = register["markups"]
    errors, excluded = [], []
    seen = set()
    buckets = defaultdict(list)
    units_by_item = defaultdict(set)
    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"row {idx}: invalid record")
            continue
        label = f"row {idx} ({row.get('markup_id', 'no-id')})"
        if row.get("do_not_sum") is True or "DO NOT SUM" in str(row.get("subject", "")).upper():
            excluded.append(f"{label}: QA-only DO NOT SUM excluded")
            continue
        problems = []
        if not isinstance(row.get("do_not_sum"), bool):
            problems.append("do_not_sum must be explicit boolean")
        identifier = (row.get("plan_id"), row.get("markup_id"))
        if not all(good_text(v) for v in identifier):
            problems.append("missing contribution identity")
        elif identifier in seen:
            problems.append("duplicate contribution")
        else:
            seen.add(identifier)
        if row.get("source_sha256") != source_control["sha256"] or row.get("source_revision") != source_control["revision"]:
            problems.append("stale or mismatched source revision/hash")
        if not isinstance(row.get("status"), str) or row["status"] not in ELIGIBLE_FOR_PREVIEW:
            problems.append("not QA_CHECKED or recorded human review")
        kind, unit = row.get("measurement_type"), row.get("unit")
        if not isinstance(kind, str) or kind not in TYPES or TYPES[kind] != unit:
            problems.append("incompatible measurement type/unit")
        if unit != "ea" and (row.get("scale_verified") is not True or not good_text(row.get("scale_basis"))):
            problems.append("independent scale evidence missing")
        if row.get("visual_location_checked") is not True or not good_text(row.get("independent_evidence")):
            problems.append("independent location/quantity evidence missing")
        bid_item = row.get("bid_item_id")
        if not good_text(bid_item):
            problems.append("bid-item mapping unresolved")
        quantity = row.get("computed_quantity")
        if not good_quantity(quantity):
            problems.append("invalid computed quantity")
        receipt = row.get("native_readback")
        if not isinstance(receipt, dict):
            problems.append("structured saved native readback absent")
        elif (not good_hash(receipt.get("saved_pdf_sha256"))
              or receipt.get("native_markup_id") != row.get("markup_id")
              or receipt.get("source_pdf_sha256") != row.get("source_sha256")
              or receipt.get("unit") != unit
              or not good_quantity(receipt.get("quantity"))
              or (good_quantity(quantity) and not math.isclose(float(receipt.get("quantity", -1)), float(quantity), rel_tol=1e-9, abs_tol=1e-6))):
            problems.append("native receipt fields/quantity mismatch")
        if problems:
            errors.append(f"{label}: " + "; ".join(problems))
            continue
        units_by_item[bid_item].add(unit)
        buckets[bid_item].append((unit, float(quantity), str(row["markup_id"])))
    for item, units in units_by_item.items():
        if len(units) != 1:
            errors.append(f"bid item {item}: mixed units {sorted(units)}")
    totals = []
    if not errors:
        for item in sorted(buckets):
            values = buckets[item]
            totals.append({"bid_item_id": item, "unit": values[0][0],
                           "quantity": round(math.fsum(v[1] for v in values), 6),
                           "source_markup_ids": sorted(v[2] for v in values)})
    canonical = json.dumps({"register": register, "source_control": source_control}, sort_keys=True, separators=(",", ":"), allow_nan=True)
    return {"schema_version": 1, "source_register_digest": hashlib.sha256(canonical.encode()).hexdigest(),
            "result": "BLOCKED" if errors else "PREVIEW_ONLY", "preview_totals": totals,
            "unresolved": errors, "excluded": excluded,
            "partial_totals_released": False, "native_receipt_authenticated": False,
            "human_review_authenticated": False, "commercial_handoff_authorized": False,
            "warning": "NOT FOR BID / NOT BAX / NOT APPROVED"}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2:
        print("Usage: python tools/reconcile_quantity_preview.py register.json current_source.json")
        return 2
    try:
        report = preview_quantities(json.loads(Path(argv[0]).read_text(encoding="utf-8")),
                                    json.loads(Path(argv[1]).read_text(encoding="utf-8")))
        print(json.dumps(report, indent=2))
        return 1 if report["result"] == "BLOCKED" else 0
    except (OSError, ValueError, TypeError) as exc:
        print(f"INVALID: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
