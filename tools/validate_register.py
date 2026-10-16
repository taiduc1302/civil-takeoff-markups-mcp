#!/usr/bin/env python3
"""
Validate a Bluebeam markup Comment string against the standardized
traceability contract defined in docs/traceability-contract.md.

Usage:
    python validate_traceability_contract.py "PLAN_ID=S-M1;SHEET=C-101;SOURCE=SYN-U-0002 rev A;BIDITEM=33.01;STA=0+005.00-0+078.40;STATUS=MEASURED;SCALE_VERIFIED=Y (page-level);CREATED_BY=MCP;NOTE=reconciled against printed schedule"

Exits 0 and prints "VALID" if every required field is present and STATUS is
a legal state; exits 1 and lists missing/invalid fields otherwise.

This script is deliberately dependency-free (stdlib only) so it can run in
any environment (any agent sandbox or CI) without a
package install step.
"""
import sys

REQUIRED_FIELDS = [
    "PLAN_ID",
    "SHEET",
    "SOURCE",
    "BIDITEM",
    "STA",
    "STATUS",
    "SCALE_VERIFIED",
    "CREATED_BY",
]

LEGAL_STATES = {
    "AI_PROPOSED",
    "MEASURED",
    "QA_CHECKED",
    "ESTIMATOR_REVIEWED",
    "APPROVED",
    "REJECTED-REWORK",
}

LEGAL_CREATED_BY = {"MCP", "GUI"}


def parse_comment(comment: str) -> dict:
    """Parse a `KEY=value;KEY=value;...` comment string into a dict.

    Values are allowed to contain '=' (e.g. a NOTE with an equation in it);
    only the first '=' in each ';'-separated segment is treated as the
    delimiter. Trailing/leading whitespace around keys/values is stripped.
    """
    fields = {}
    for segment in comment.split(";"):
        segment = segment.strip()
        if not segment:
            continue
        if "=" not in segment:
            continue
        key, _, value = segment.partition("=")
        fields[key.strip().upper()] = value.strip()
    return fields


def validate(comment: str) -> list:
    """Return a list of human-readable problems; empty list means valid."""
    problems = []
    fields = parse_comment(comment)

    for req in REQUIRED_FIELDS:
        if req not in fields or fields[req] == "":
            problems.append(f"missing or empty required field: {req}")

    status = fields.get("STATUS", "")
    if status and status not in LEGAL_STATES:
        problems.append(
            f"STATUS '{status}' is not a legal state - must be one of {sorted(LEGAL_STATES)}"
        )

    created_by = fields.get("CREATED_BY", "")
    if created_by and created_by not in LEGAL_CREATED_BY:
        problems.append(
            f"CREATED_BY '{created_by}' must be one of {sorted(LEGAL_CREATED_BY)}"
        )

    scale_verified = fields.get("SCALE_VERIFIED", "")
    if scale_verified and not (
        scale_verified.upper().startswith("Y") or scale_verified.upper().startswith("N")
    ):
        problems.append(
            f"SCALE_VERIFIED '{scale_verified}' should start with Y or N (with a basis, e.g. 'Y (page-level)')"
        )

    return problems


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2

    comment = sys.argv[1]
    problems = validate(comment)

    if not problems:
        print("VALID")
        return 0

    print("INVALID")
    for p in problems:
        print(f"  - {p}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
