#!/usr/bin/env python3
"""Validate a pre-bid municipal risk register. No live code or permit lookup.

Usage: python tools/validate_municipal_checks.py examples/municipal_checks_synthetic.json
Exit 0: complete record, with human-reviewed disposition for each required check.
Exit 1: structurally valid, but one or more checks still need human review.
Exit 2: invalid or incomplete record. Exit 0 is NOT permit or bid approval.
"""
import json
import sys
from datetime import date
from pathlib import Path

REQUIRED_CHECKS = (
    "permit_requirements",
    "local_code_and_zoning",
    "fees_and_deposits",
    "review_and_inspection_timing",
    "road_occupancy_and_utilities",
)
STATUSES = {"OPEN", "EVIDENCE_FOUND", "FLAGGED", "HUMAN_CLEARED", "NOT_APPLICABLE"}
PENDING = {"OPEN", "EVIDENCE_FOUND", "FLAGGED"}
HUMAN_STATES = {"HUMAN_CLEARED", "NOT_APPLICABLE"}


def has_text(value):
    return isinstance(value, str) and bool(value.strip())


def parse_date(value, name, errors, required=False):
    if not has_text(value):
        if required:
            errors.append(f"{name}: missing date (YYYY-MM-DD)")
        return None
    try:
        parsed = date.fromisoformat(value)
        if parsed.isoformat() != value:
            raise ValueError
        return parsed
    except (ValueError, TypeError):
        errors.append(f"{name}: date must be YYYY-MM-DD")
        return None


def validate(data):
    """Return (structural_errors, pending_check_ids). Never fetches public data."""
    errors, pending = [], []
    if not isinstance(data, dict):
        return ["root must be a JSON object"], []
    project = data.get("project")
    if not isinstance(project, dict):
        return ["project must be an object"], []
    for field in ("name", "jurisdiction", "scope"):
        if not has_text(project.get(field)):
            errors.append(f"project.{field}: required")
    as_of = parse_date(project.get("checked_on"), "project.checked_on", errors, True)

    checks = data.get("checks")
    if not isinstance(checks, list):
        return errors + ["checks must be an array"], []
    seen = set()
    for index, check in enumerate(checks):
        label = f"checks[{index}]"
        if not isinstance(check, dict):
            errors.append(f"{label}: must be an object")
            continue
        check_id = check.get("id")
        if not has_text(check_id):
            errors.append(f"{label}.id: required")
            continue
        label = check_id
        if check_id in seen:
            errors.append(f"{label}: duplicate check id")
        seen.add(check_id)
        status = check.get("status")
        if not isinstance(status, str) or status not in STATUSES:
            errors.append(f"{label}: status must be one of {', '.join(sorted(STATUSES))}")
            continue
        if status in PENDING:
            pending.append(label)

        # A source without a lookup date (or vice versa) cannot be audited.
        source = check.get("source_ref")
        source_date_value = check.get("source_checked_on")
        if bool(has_text(source)) != bool(has_text(source_date_value)):
            errors.append(f"{label}: source_ref and source_checked_on must be supplied together")
        source_date = parse_date(source_date_value, f"{label}.source_checked_on", errors)
        review_date = parse_date(check.get("reviewed_on"), f"{label}.reviewed_on", errors)
        for name, value in (("source_checked_on", source_date), ("reviewed_on", review_date)):
            if as_of and value and value > as_of:
                errors.append(f"{label}.{name}: later than project.checked_on")

        if status in {"EVIDENCE_FOUND", "HUMAN_CLEARED"}:
            for field in ("authority", "source_ref", "source_checked_on", "finding"):
                if not has_text(check.get(field)):
                    errors.append(f"{label}.{field}: required for {status}")
        if status == "FLAGGED" and not has_text(check.get("finding")):
            errors.append(f"{label}.finding: describe the risk")
        if status in HUMAN_STATES:
            for field in ("finding", "reviewed_by", "reviewed_on"):
                if not has_text(check.get(field)):
                    errors.append(f"{label}.{field}: human disposition needs a rationale and reviewer")
            if status == "HUMAN_CLEARED" and not has_text(check.get("responsible_party")):
                errors.append(f"{label}.responsible_party: assign the permit/cost obligation")
            if source_date and review_date and review_date < source_date:
                errors.append(f"{label}.reviewed_on: review predates the source check")

    for required in REQUIRED_CHECKS:
        if required not in seen:
            errors.append(f"missing required check: {required}")
    return errors, pending


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print(__doc__)
        return 2
    try:
        data = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"INVALID: cannot load JSON: {exc}")
        return 2
    errors, pending = validate(data)
    if errors:
        print("INVALID MUNICIPAL CHECK REGISTER")
        for error in errors:
            print(f"  - {error}")
        return 2
    if pending:
        print("REVIEW REQUIRED: no automatic municipal clearance")
        for check_id in pending:
            print(f"  - {check_id}")
        return 1
    print("REGISTER COMPLETE: human dispositions recorded; NOT permit or bid approval")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
