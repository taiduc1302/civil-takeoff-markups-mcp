#!/usr/bin/env python3
"""Read vector geometry and text from a SAVED PDF, independent of fixture source.

Local-only inspection; does NOT identify the intended civil drawing feature or
calibrate a scale. PyMuPDF coordinates are returned in its page coordinate
system, not in Bluebeam MCP write coordinates. Coordinate mapping is a
separate gated task.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path


def _point(point):
    x, y = float(point.x), float(point.y)
    if not math.isfinite(x) or not math.isfinite(y):
        raise ValueError("non-finite vector coordinate")
    return [round(x, 5), round(y, 5)]


def _bbox(box):
    return [round(float(v), 5) for v in box]


def inspect_pdf(path, page_index=0, max_items=10000):
    """Return explicit source-identified candidates, never approved quantities."""
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("PyMuPDF is required: pip install pymupdf") from exc
    path = Path(path)
    if not path.is_file() or path.suffix.lower() != ".pdf":
        raise ValueError("expected an existing .pdf file")
    if not isinstance(page_index, int) or isinstance(page_index, bool):
        raise ValueError("page_index must be an integer")
    if not isinstance(max_items, int) or isinstance(max_items, bool) or not 1 <= max_items <= 100000:
        raise ValueError("max_items must be in 1..100000")
    raw_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    with fitz.open(path) as document:
        if document.needs_pass:
            raise ValueError("password-protected PDF cannot be inspected")
        if page_index < 0 or page_index >= len(document):
            raise ValueError("page index out of bounds")
        page = document[page_index]
        vectors = []
        for drawing_index, drawing in enumerate(page.get_drawings()):
            for item_index, item in enumerate(drawing["items"]):
                if len(vectors) >= max_items:
                    raise ValueError("vector item limit exceeded; inspect a smaller page")
                kind = item[0]
                if kind == "l":
                    shape = {"type": "line", "start": _point(item[1]), "end": _point(item[2])}
                elif kind == "re":
                    shape = {"type": "rectangle", "rect": _bbox(item[1])}
                elif kind == "c":
                    shape = {"type": "bezier", "points": [_point(v) for v in item[1:5]]}
                elif kind == "qu":
                    quad = item[1]
                    shape = {"type": "quad", "points": [_point(getattr(quad, name)) for name in
                                                      ("ul", "ur", "ll", "lr")]}
                else:
                    shape = {"type": "unsupported", "operator": str(kind)}
                shape.update({"drawing_index": drawing_index, "item_index": item_index})
                vectors.append(shape)
        texts = []
        for block in page.get_text("blocks"):
            if len(texts) >= max_items:
                raise ValueError("text block limit exceeded; inspect a smaller page")
            if len(block) > 6 and block[6] != 0:
                continue
            value = block[4].strip()
            if value:
                texts.append({"bbox": _bbox(block[:4]), "text": value})
        return {
            "schema_version": 1,
            "source_sha256": raw_hash,
            "page_index": page_index,
            "page_label": page.get_label() or str(page_index + 1),
            "rotation_degrees": page.rotation,
            "mediabox": _bbox(page.mediabox),
            "cropbox": _bbox(page.cropbox),
            "coordinate_system": "pymupdf-unrotated-page-points-y-down",
            "read_only": True,
            "feature_targeting_verified": False,
            "scale_verified": False,
            "vectors": vectors,
            "text_blocks": texts,
        }


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if len(args) not in (1, 2):
        print("Usage: python tools/vector_readback.py file.pdf [zero-based-page-index]", file=sys.stderr)
        return 2
    try:
        page = int(args[1]) if len(args) == 2 else 0
        report = inspect_pdf(args[0], page_index=page)
    except (ValueError, RuntimeError, OSError) as exc:
        print(f"UNRESOLVED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
