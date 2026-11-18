# Conservative vector feature selection / preview (issue #4)

Date: 2026-11-17. Status: offline synthetic proof, NOT native takeoff, NOT engineering/scale/semantic approval.

## Why

Existing tools/vector_readback.py reads actual saved PDF vector objects. It intentionally cannot decide which nearby object (leader, existing pipe, proposed pipe, curb line) is intended. This new narrow layer never guesses: the estimator's **two explicit source anchors** must match exactly ONE line within a tightly bounded tolerance. Zero or multiple matches fail closed.

## What changed

- tools/target_vectors.py calls the existing read-only vector reader in its CLI, selects only literal line segments using both endpoints (orientation-independent), and hashes the selected geometry with source hash/page.
- Refuses wrong/ambiguous/overlapping lines, coordinate-frame mismatch, invalid anchors and tolerance >5 PDF points.
- Can render a red **PNG preview** by applying a temporary in-memory PyMuPDF line annotation. It never saves/modifies the original PDF. Output must be a new PNG.
- All outputs explicitly keep status AI_PROPOSED, feature_targeting_verified=false, visual_location_checked=false, scale_verified=false and quantity_eligible_for_handoff=false. This is NOT a native Bluebeam/Open PDF Studio measurement.

## Reproduction

    python -m unittest discover -s tests -p test_target_vectors.py -v
    python tools/target_vectors.py SYNTHETIC_SOURCE.pdf 0 20 20 120 20 --tolerance 1 --preview-png /tmp/new_synthetic_overlay.png

Coordinates are PyMuPDF unrotated, Y-down PDF points. Paths from Bluebeam's MCP write grammar or Open PDF Studio app points must NOT be silently substituted. A manual point selection alone is not proof that the correct design feature has been selected.

## Test evidence

Linux / Python 3.13 / PyMuPDF 1.26.7: 6 PASS, 0 FAIL. Test PDF was generated and saved with two competing horizontal line features. Tested unique reverse-order selection, zero candidate, duplicate/ambiguous candidate refusal, nonfinite endpoints, invalid coordinate frame/tolerance, PNG generation with exact source-byte integrity, changed hash refusal and rotated-page preview still pending QA.

Full exact-branch repository suite NOT RUN because GitHub shell clone could not resolve the host in this environment. No Windows, Revu native, Open PDF Studio native, Bluebeam BAX or estimator acceptance was performed.

## Remaining issue #4 acceptance

- Extract and join polylines, curves, rectangles and boundaries, not just individual two-point strokes.
- CAD viewports/multi-scale, nonzero CropBox, rotation coordinate transforms, dimension checks and correct feature semantics need independent tests.
- Add UI overlay with human visual review evidence and explicit feature classifications (proposed / existing / leader / restoration).
- Scanned or flattened PDFs require manual GUI fallback. Never assert perfect vector semantics or automatically promote to QA_CHECKED.
