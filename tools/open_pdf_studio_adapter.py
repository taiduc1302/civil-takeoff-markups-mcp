#!/usr/bin/env python3
"""Experimental synthetic-only Open PDF Studio bridge.

Default is read-only dry run. Real execution is explicitly opt-in and uses an
isolated vendor Python-library app instance; no existing Revu/OPS sessions.
Saved readback is NEVER a semantic target check or human approval.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path


class AdapterRefusal(ValueError):
    """Stop rather than guessing a scale, source, tool, or quantity."""


def finite_positive(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value > 0


def point(value):
    if not isinstance(value, (list, tuple)) or len(value) != 2 or any(
        not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(v) for v in value
    ):
        raise AdapterRefusal("each geometry point must be two finite numeric coordinates")
    return (float(value[0]), float(value[1]))


def plan_operations(plan):
    """Validate source identity and return safe proposed vendor operations.

    Geometry is already in Open PDF Studio's 100%-zoom page coordinates; this
    function deliberately does not guess a PyMuPDF/PDF-origin transform.
    """
    if not isinstance(plan, dict):
        raise AdapterRefusal("plan must be an object")
    if plan.get("synthetic_fixture") is not True:
        raise AdapterRefusal("only explicitly marked disposable synthetic plans are accepted")
    if plan.get("coordinate_space") != "opds-native-page-points-at-100-percent":
        raise AdapterRefusal("unsupported/unknown coordinate space; no implicit Y flip or crop rotation")
    try:
        source = Path(plan["source_pdf"]).resolve(strict=True)
        output = Path(plan["output_pdf"]).resolve()
    except (KeyError, TypeError, OSError) as exc:
        raise AdapterRefusal("valid source_pdf and output_pdf paths required") from exc
    if not source.is_file() or source.suffix.lower() != ".pdf":
        raise AdapterRefusal("source must be an existing PDF")
    if output.suffix.lower() != ".pdf" or output == source or output.exists():
        raise AdapterRefusal("output must be a new, separate PDF; never overwrite")
    if not output.parent.is_dir():
        raise AdapterRefusal("output directory does not exist")
    with source.open("rb") as stream:
        if stream.read(5) != b"%PDF-":
            raise AdapterRefusal("source has no PDF header")
        stream.seek(0)
        digest = hashlib.sha256()
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    source_sha256 = digest.hexdigest()
    if plan.get("source_sha256") != source_sha256:
        raise AdapterRefusal("source SHA-256 mismatch; revision may be stale")
    if not isinstance(plan.get("source_revision"), str) or not plan["source_revision"].strip():
        raise AdapterRefusal("nonempty source revision required")
    if not isinstance(plan.get("page_index"), int) or isinstance(plan["page_index"], bool) or plan["page_index"] < 0:
        raise AdapterRefusal("page_index must be nonnegative and zero-based")
    if not isinstance(plan.get("page_label"), str) or not plan["page_label"].strip():
        raise AdapterRefusal("page_label required")

    ref = plan.get("scale_reference")
    if not isinstance(ref, dict) or not isinstance(ref.get("unit"), str) or ref["unit"] not in {"m", "mm", "ft"} or not finite_positive(ref.get("known_length")):
        raise AdapterRefusal("known length, length unit and independent scale basis required")
    if not isinstance(ref.get("basis"), str) or not ref["basis"].strip():
        raise AdapterRefusal("nonempty scale basis required")
    try:
        a, b = [point(p) for p in ref["page_points"]]
    except (KeyError, TypeError, ValueError) as exc:
        raise AdapterRefusal("scale_reference.page_points must contain two finite points") from exc
    ppu = math.dist(a, b) / float(ref["known_length"])
    if not finite_positive(ppu):
        raise AdapterRefusal("degenerate scale reference")

    features = plan.get("features")
    if not isinstance(features, list) or not features:
        raise AdapterRefusal("nonempty features list required")
    seen = set()
    actions = []
    for i, feat in enumerate(features):
        if not isinstance(feat, dict):
            raise AdapterRefusal(f"features[{i}] must be an object")
        feature_id = feat.get("id")
        if not isinstance(feature_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,79}", feature_id) or feature_id in seen:
            raise AdapterRefusal(f"features[{i}] has missing, invalid or duplicate id")
        seen.add(feature_id)
        typ = feat.get("kind")
        if not isinstance(typ, str) or typ not in {"Length", "Area", "Count"}:
            raise AdapterRefusal(f"features[{i}] has unsupported measurement kind")
        vertices = feat.get("points")
        if not isinstance(vertices, list) or len(vertices) < {"Length": 2, "Area": 3, "Count": 1}[typ]:
            raise AdapterRefusal(f"features[{i}] has insufficient points")
        coords = [point(v) for v in vertices]
        if typ == "Count" and len(coords) != 1:
            raise AdapterRefusal("Count needs exactly one location")
        if len(set(coords)) < {"Length": 2, "Area": 3, "Count": 1}[typ]:
            raise AdapterRefusal(f"features[{i}] has degenerate geometry")
        if typ == "Area":
            area2 = sum(coords[j][0] * coords[(j + 1) % len(coords)][1]
                        - coords[(j + 1) % len(coords)][0] * coords[j][1]
                        for j in range(len(coords)))
            if abs(area2) < 1e-9:
                raise AdapterRefusal("zero-area polygon")
        if not isinstance(feat.get("do_not_sum"), bool):
            raise AdapterRefusal("do_not_sum must be explicit boolean for each feature")
        if typ == "Length" and len(coords) == 2:
            tool_type = "measureDistance"
            props = dict(zip(("startX", "startY", "endX", "endY"), (*coords[0], *coords[1])))
        elif typ == "Length":
            tool_type = "measurePerimeter"  # open polyline, not closed perimeter
            props = {"points": [dict(x=x, y=y) for x, y in coords], "closed": False}
        elif typ == "Area":
            tool_type = "measureArea"
            props = {"points": [dict(x=x, y=y) for x, y in coords]}
        else:
            tool_type = "count"  # native count quantity needs an independent check
            props = {"x": coords[0][0], "y": coords[0][1]}
        props["text"] = f"SYN {feature_id}"  # annotation text is NOT authoritative ID
        actions.append({"id": feature_id, "page": plan["page_index"] + 1, "type": tool_type,
                        "props": props, "do_not_sum": feat["do_not_sum"]})
    return {"source_pdf": str(source), "output_pdf": str(output), "source_sha256": source_sha256,
            "source_revision": plan["source_revision"], "page_label": plan["page_label"],
            "pixels_per_unit": ppu, "unit": ref["unit"], "scale_basis": ref["basis"],
            "actions": actions, "status": "AI_PROPOSED", "scale_verified": False,
            "feature_targeting_verified": False}


def _native_id(value):
    if isinstance(value, str) and value:
        return value
    if isinstance(value, dict):
        for field in ("id", "annotationId"):
            if isinstance(value.get(field), str) and value[field]:
                return value[field]
    raise AdapterRefusal("vendor did not return a stable annotation ID")


def execute_synthetic(operations, app_factory):
    """Run on an *isolated* vendor app, save to new PDF and reopen for readback.

    app_factory is injected for offline mocking; only caller-supplied opt-in
    can invoke this function. Output NEVER receives APPROVED/QA_CHECKED.
    """
    if operations.get("status") != "AI_PROPOSED":
        raise AdapterRefusal("only an unapproved proposal can be dispatched")
    source, output = Path(operations["source_pdf"]), Path(operations["output_pdf"])
    if not source.is_file() or hashlib.sha256(source.read_bytes()).hexdigest() != operations["source_sha256"]:
        raise AdapterRefusal("source changed between preflight and dispatch")
    if output.exists():
        raise AdapterRefusal("output already exists; refusing duplicate/retry")
    ids = {}
    with app_factory() as app:
        doc = app.open(str(source))
        doc.tools.set_measure_scale(operations["pixels_per_unit"], operations["unit"])
        for a in operations["actions"]:
            ids[a["id"]] = _native_id(doc.annotations.add(a["type"], page=a["page"], **a["props"]))
        doc.save(str(output))
        if not output.is_file():
            raise AdapterRefusal("vendor save did not create output PDF")
        doc.close(save=False)
        saved = app.open(str(output))
        readback = {}
        numeric_complete = True
        for action in operations["actions"]:
            feature_id = action["id"]
            native_id = ids[feature_id]
            value = saved.annotations.get(native_id)
            if not isinstance(value, dict) or value.get("id") != native_id:
                raise AdapterRefusal(f"saved readback missing annotation {feature_id}; REVIEW REQUIRED")
            if value.get("type") != action["type"]:
                raise AdapterRefusal(f"saved annotation type changed for {feature_id}; REVIEW REQUIRED")
            # Count marker presence is not proof of a counted quantity.
            if action["type"] == "count":
                measure, unit = None, None
            elif action["type"] == "measureArea" and isinstance(value.get("area"), dict):
                measure, unit = value["area"].get("value"), value["area"].get("unit")
            else:
                measure, unit = value.get("measureValue"), value.get("measureUnit")
            numeric_ok = finite_positive(measure) and isinstance(unit, str) and bool(unit.strip())
            numeric_complete = numeric_complete and numeric_ok
            readback[feature_id] = {"native_id": native_id, "type": value.get("type"),
                                    "numeric_quantity_available": numeric_ok,
                                    "quantity": float(measure) if numeric_ok else None,
                                    "unit": unit if numeric_ok else None,
                                    "do_not_sum": action["do_not_sum"]}
        saved.close(save=False)
    if hashlib.sha256(source.read_bytes()).hexdigest() != operations["source_sha256"]:
        raise AdapterRefusal("original changed unexpectedly; investigate immediately")
    return {"status": "MEASURED", "review_required": True,
            "source_sha256": operations["source_sha256"],
            "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
            "readback": readback, "scale_verified": False, "feature_targeting_verified": False,
            "quantity_eligible_for_bax": False, "human_review": None}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", help="JSON plan with synthetic-only source and external controls")
    parser.add_argument("--execute-synthetic", action="store_true", help="requires installed Open PDF Studio Python library/app; never uses existing user session")
    args = parser.parse_args(argv)
    try:
        ops = plan_operations(json.loads(Path(args.plan).read_text(encoding="utf-8")))
        if args.execute_synthetic:
            try:
                import open_pdf_studio as vendor
            except ImportError as exc:
                raise AdapterRefusal("Open PDF Studio Python package unavailable; dry-run remains possible") from exc
            result = execute_synthetic(ops, vendor.launch)
        else:
            result = ops
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, OSError) as exc:
        print(f"REVIEW REQUIRED: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
