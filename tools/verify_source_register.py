#!/usr/bin/env python3
"""Validate external evidence-register source bytes, revision and PDF page labels.

This check does not authenticate reviewers, tool markups or quantity targeting.
Never authorizes a commercial total, downstream BAX, or human approval.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def verify_pdf_source(register, pdf_path, current_revision):
    """Return source integrity evidence and stale reasons without modifying data."""
    import fitz

    if not isinstance(register, dict) or register.get("schema_version") != 1:
        raise ValueError("expected evidence register schema_version=1")
    rows = register.get("markups")
    if not isinstance(rows, list):
        raise ValueError("markups must be an array")
    if not isinstance(current_revision, str) or not current_revision.strip():
        raise ValueError("current_revision must be supplied by the controlled plan")
    source = Path(pdf_path)
    if not source.is_file() or source.suffix.lower() != ".pdf":
        raise ValueError("source must be an existing PDF")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    with fitz.open(source) as doc:
        if doc.needs_pass:
            raise ValueError("encrypted PDF cannot prove page evidence")
        labels = [p.get_label() or str(i + 1) for i, p in enumerate(doc)]
        rotations = [p.rotation for p in doc]
        crop_boxes = [[round(v, 5) for v in p.cropbox] for p in doc]
        media_boxes = [[round(v, 5) for v in p.mediabox] for p in doc]
    if hashlib.sha256(source.read_bytes()).hexdigest() != digest:
        raise ValueError("PDF changed during source verification")
    errors = []
    matched = []
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"markups[{i}]: expected object")
            continue
        reasons = []
        if row.get("source_sha256") != digest:
            reasons.append("source SHA-256 differs from current PDF")
        if row.get("source_revision") != current_revision:
            reasons.append("source revision differs from controlled revision")
        page = row.get("page_index")
        if not isinstance(page, int) or isinstance(page, bool) or not 0 <= page < len(labels):
            reasons.append("page index invalid for current PDF")
        elif row.get("page_label") != labels[page]:
            reasons.append("PDF page label differs from register")
        if reasons:
            errors.append(f"markups[{i}]: " + "; ".join(reasons))
        else:
            matched.append({"row": i, "page_index": page, "page_label": labels[page],
                            "rotation": rotations[page], "cropbox": crop_boxes[page],
                            "mediabox": media_boxes[page]})
    return {"source_sha256_actual": digest, "current_revision_declared": current_revision,
            "document_pages": len(labels), "matched": matched, "unresolved": errors,
            "source_match": not errors, "scale_verified": False,
            "feature_targeting_verified": False, "reviewer_authenticated": False,
            "commercial_handoff_approved": False}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 3:
        print("Usage: python tools/verify_source_register.py register.json source.pdf CURRENT_REVISION")
        return 2
    try:
        from validate_evidence_register import validate
        register = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
        invalid, pending = validate(register)
        if invalid:
            print(json.dumps({"invalid": invalid, "pending": pending}, indent=2))
            return 2
        report = verify_pdf_source(register, argv[1], argv[2])
        report["evidence_gaps"] = pending
        print(json.dumps(report, indent=2))
        return 1 if report["unresolved"] or pending else 0
    except (ValueError, RuntimeError, OSError, ImportError) as exc:
        print(f"INVALID/UNRESOLVED: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
