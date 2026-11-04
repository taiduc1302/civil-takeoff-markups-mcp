#!/usr/bin/env python3
"""Validate a versioned *external* markup evidence register (offline, no approvals).

This is a structural/evidence-presence gate, NOT proof of drawing correctness,
Bluebeam live capability or authenticated human identity.
Exit codes: 0 valid recorded evidence, 1 unresolved, 2 malformed.
"""
from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

STATES = ("AI_PROPOSED", "MEASURED", "QA_CHECKED",
          "ESTIMATOR_REVIEWED", "APPROVED", "REJECTED-REWORK")
LATER = {"QA_CHECKED", "ESTIMATOR_REVIEWED", "APPROVED"}
HUMAN = {"ESTIMATOR_REVIEWED", "APPROVED"}
HASH = re.compile(r"[0-9a-fA-F]{64}\Z")
UNITS = {"m", "m2", "m3", "ea"}
KEYS = ("markup_id", "page_index", "page_label", "source_sha256", "source_revision",
        "plan_id", "status", "measurement_type", "unit", "scale_resolved", "scale_verified")


def nonempty(x):
    return isinstance(x, str) and bool(x.strip())


def validate(record):
    """Return (fatal structural errors, evidence gaps); never change state."""
    errors, pending = [], []
    if not isinstance(record, dict):
        return ["root must be an object"], []
    if record.get("schema_version") != 1:
        errors.append("schema_version: expected 1")
    entries = record.get("markups")
    if not isinstance(entries, list):
        return errors + ["markups: expected array"], []
    seen = set()
    for index, item in enumerate(entries):
        ctx = f"markups[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{ctx}: expected object")
            continue
        for key in KEYS:
            if key not in item:
                errors.append(f"{ctx}.{key}: missing")
        if any(key not in item for key in KEYS):
            continue
        for key in ("markup_id", "page_label", "source_revision", "plan_id"):
            if not nonempty(item[key]):
                errors.append(f"{ctx}.{key}: required nonempty string")
        if not isinstance(item["page_index"], int) or isinstance(item["page_index"], bool) or item["page_index"] < 0:
            errors.append(f"{ctx}.page_index: expected nonnegative zero-based integer")
        if not isinstance(item["source_sha256"], str) or not HASH.fullmatch(item["source_sha256"]):
            errors.append(f"{ctx}.source_sha256: expected 64 hex digits")
        if not isinstance(item["status"], str) or item["status"] not in STATES:
            errors.append(f"{ctx}.status: unsupported")
            continue
        if not nonempty(item["measurement_type"]):
            errors.append(f"{ctx}.measurement_type: required")
        if not isinstance(item["unit"], str) or item["unit"] not in UNITS:
            errors.append(f"{ctx}.unit: unsupported")
        for field in ("scale_resolved", "scale_verified"):
            if not isinstance(item[field], bool):
                errors.append(f"{ctx}.{field}: must be boolean")
        identity = (str(item["source_sha256"]), str(item["page_index"]), str(item["markup_id"]))
        if identity in seen:
            errors.append(f"{ctx}: duplicate markup source/page/id")
        seen.add(identity)
        status = item["status"]
        if status in LATER or status == "MEASURED":
            if not item.get("native_readback"):
                pending.append(f"{ctx}: native saved readback absent")
            q = item.get("computed_quantity")
            if not isinstance(q, (int, float)) or isinstance(q, bool) or not (0 <= q < float("inf")):
                pending.append(f"{ctx}: finite nonnegative native computed quantity absent")
        if status in LATER:
            if item["unit"] != "ea" and (item["scale_resolved"] is not True or item["scale_verified"] is not True
                                         or not nonempty(item.get("scale_basis"))):
                pending.append(f"{ctx}: independently verified scale absent")
            if item.get("visual_location_checked") is not True:
                pending.append(f"{ctx}: rendered-location check absent")
            if not nonempty(item.get("independent_evidence")):
                pending.append(f"{ctx}: independent quantity/feature evidence absent")
            if item.get("do_not_sum") is True:
                pending.append(f"{ctx}: QA-only markup is not eligible for quantity approval")
        if status in HUMAN:
            review = item.get("human_review")
            if not isinstance(review, dict) or not all(nonempty(review.get(k)) for k in
                                                        ("reviewer", "decision_ref", "reviewed_on")):
                pending.append(f"{ctx}: documented human decision absent (identity not authenticated)")
        if status == "APPROVED" and (not isinstance(item.get("human_review"), dict) or item["human_review"].get("decision") != "APPROVE"):
            pending.append(f"{ctx}: recorded explicit APPROVE decision absent")
    return errors, pending


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print(__doc__)
        return 2
    try:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"INVALID: {exc}")
        return 2
    errors, pending = validate(doc)
    for msg in errors:
        print("INVALID:", msg)
    for msg in pending:
        print("REVIEW REQUIRED:", msg)
    if errors:
        return 2
    if pending:
        return 1
    print("EVIDENCE STRUCTURE RECORDED — NOT authenticated approval or quantity correctness")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
