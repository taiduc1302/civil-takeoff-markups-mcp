#!/usr/bin/env python3
"""Conservative line target selection and PNG overlay for SAVED vector PDFs.

All outputs are proposals, never independently verified scale/feature quantities.
No source PDF is written. Ambiguous line candidates are refused, not ranked.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


class TargetRefusal(ValueError):
    pass


def _point(p):
    if not isinstance(p, (tuple, list)) or len(p) != 2:
        raise TargetRefusal("endpoint must have exactly two coordinates")
    if not all(isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) for x in p):
        raise TargetRefusal("non-finite or nonnumeric endpoint")
    return (float(p[0]), float(p[1]))


def choose_line(report, start, end, tolerance_pt=1.0):
    """Find a single line matching BOTH supplied endpoints within tolerance."""
    if not isinstance(report, dict) or report.get("coordinate_system") != "pymupdf-unrotated-page-points-y-down":
        raise TargetRefusal("unrecognized PDF coordinate basis")
    sha = report.get("source_sha256")
    if not isinstance(sha, str) or len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha.lower()):
        raise TargetRefusal("missing source SHA-256")
    if not isinstance(report.get("page_index"), int) or isinstance(report["page_index"], bool) or report["page_index"] < 0:
        raise TargetRefusal("invalid zero-based page index")
    if not isinstance(report.get("page_label"), str) or not report["page_label"]:
        raise TargetRefusal("missing page label")
    if not isinstance(tolerance_pt, (int, float)) or isinstance(tolerance_pt, bool) or not math.isfinite(tolerance_pt) or not 0 < tolerance_pt <= 5:
        raise TargetRefusal("tolerance must be >0 and <=5 PDF points")
    a, b = _point(start), _point(end)
    if math.dist(a, b) < 1e-6:
        raise TargetRefusal("degenerate line anchor")
    candidates = []
    for item in report.get("vectors", []):
        if not isinstance(item, dict) or item.get("type") != "line":
            continue
        p, q = _point(item.get("start")), _point(item.get("end"))
        direct = max(math.dist(p, a), math.dist(q, b))
        reverse = max(math.dist(p, b), math.dist(q, a))
        if min(direct, reverse) <= tolerance_pt:
            candidates.append((item, min(direct, reverse)))
    if len(candidates) != 1:
        raise TargetRefusal(f"expected one unambiguous line; found {len(candidates)} candidates")
    selected, deviation = candidates[0]
    p, q = _point(selected["start"]), _point(selected["end"])
    canonical = sorted([list(p), list(q)])
    context = f'{sha}:{report["page_index"]}:{canonical}'
    geometry_hash = hashlib.sha256(context.encode("utf-8")).hexdigest()
    return {"source_sha256": sha, "page_index": report["page_index"],
            "page_label": report["page_label"], "drawing_index": selected.get("drawing_index"),
            "item_index": selected.get("item_index"), "geometry_hash": geometry_hash,
            "start": list(p), "end": list(q), "max_endpoint_deviation_pt": round(deviation, 5),
            "coordinate_system": report["coordinate_system"], "status": "AI_PROPOSED",
            "feature_targeting_verified": False, "visual_location_checked": False,
            "scale_verified": False, "quantity_eligible_for_handoff": False}


def preview_line(pdf_path, selection, output_png, dpi=120):
    """Overlay selected line in memory, export PNG; NEVER save original PDF."""
    import fitz

    pdf = Path(pdf_path)
    png = Path(output_png)
    if png.suffix.lower() != ".png" or png.exists() or not png.parent.is_dir():
        raise TargetRefusal("output PNG must be new in an existing directory")
    if not pdf.is_file() or pdf.suffix.lower() != ".pdf":
        raise TargetRefusal("source PDF required")
    if not isinstance(dpi, int) or isinstance(dpi, bool) or not 72 <= dpi <= 300:
        raise TargetRefusal("DPI must be 72..300")
    sha = hashlib.sha256(pdf.read_bytes()).hexdigest()
    if sha != selection.get("source_sha256"):
        raise TargetRefusal("source SHA changed since geometry selection")
    page_index = selection.get("page_index")
    with fitz.open(pdf) as doc:
        if doc.needs_pass:
            raise TargetRefusal("encrypted PDF not eligible for preview")
        if not isinstance(page_index, int) or isinstance(page_index, bool) or not 0 <= page_index < len(doc):
            raise TargetRefusal("selection page invalid for PDF")
        page = doc[page_index]
        # Explicitly unsaved annotation: pixels are a preview, not native Revu/OPDS markup.
        ink = page.add_line_annot(fitz.Point(*_point(selection["start"])),
                                 fitz.Point(*_point(selection["end"])))
        ink.set_colors(stroke=(1, 0, 0))
        ink.set_border(width=2)
        ink.update()
        page.get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72), annots=True).save(png)
    if hashlib.sha256(pdf.read_bytes()).hexdigest() != sha:
        raise TargetRefusal("source PDF changed unexpectedly")
    return {"png": str(png), "png_sha256": hashlib.sha256(png.read_bytes()).hexdigest(),
            "source_sha256": sha, "visual_location_checked": False,
            "status": "PREVIEW_ONLY_REVIEW_REQUIRED"}


def main(argv=None):
    from vector_readback import inspect_pdf

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf")
    parser.add_argument("page_index", type=int)
    parser.add_argument("x1", type=float)
    parser.add_argument("y1", type=float)
    parser.add_argument("x2", type=float)
    parser.add_argument("y2", type=float)
    parser.add_argument("--tolerance", type=float, default=1.0)
    parser.add_argument("--preview-png")
    args = parser.parse_args(argv)
    try:
        report = inspect_pdf(args.pdf, page_index=args.page_index)
        choice = choose_line(report, (args.x1, args.y1), (args.x2, args.y2), args.tolerance)
        if args.preview_png:
            choice["preview"] = preview_line(args.pdf, choice, args.preview_png)
        print(json.dumps(choice, indent=2))
        return 0
    except (ValueError, OSError, RuntimeError) as exc:
        print(f"REVIEW REQUIRED: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
