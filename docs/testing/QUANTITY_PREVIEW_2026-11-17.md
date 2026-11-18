# Quantity reconciliation: preview only, not BAX or approved estimate

Date: 2026-11-17 | Issue #6 | Offline partial milestone only

## Problem

Even a plausible list of quantities cannot be totaled when it includes stale drawing revisions, duplicate markups, mixed units, QA-only geometry, unsupported measurement intentions, unverified scale/feature evidence or incomplete native saved-readback. A silently partial total is worse than a visible refusal.

## Implementation

New tools/reconcile_quantity_preview.py returns a deterministic JSON **NOT FOR BID** preview from a synthetic external evidence register plus a *declared* current single-source PDF hash/revision. Uses no Bluebeam/Open PDF Studio runtime and NEVER authorizes a commercial update.

Acceptance rules:
- Every non-QA row must match declared current PDF hash and revision; status at least QA_CHECKED in the provided register; length/area/volume/count unit matches its type; scale and independent visual evidence fields present.
- Every row requires stable plan + markup ID, bid-item mapping, finite nonnegative numeric quantity, and a structured native receipt with matching ID/source/quantity/units and a saved-output SHA.
- An old boolean native_readback=true does not count.
- Duplicated contributions, mixed units under one bid item, missing mapping, stale revisions or one invalid non-QA row block the ENTIRE preview. No partial totals.
- DO NOT SUM/QA-only rows are explicitly listed in excluded, never added.
- A matching paper receipt and a human_review name are NOT authenticated evidence. Results always explicitly set native_receipt_authenticated=false, human_review_authenticated=false and commercial_handoff_authorized=false. Never auto-approve, print a ready-for-bid verdict or update BAX.

## Run

    python -m unittest discover -s tests -p test_quantity_preview.py -v
    python tools/reconcile_quantity_preview.py synthetic_register.json synthetic_current_source.json

Current source JSON has keys: sha256 (64 hex digits), revision (nonempty string). The register is schema_version=1 and uses docs/evidence-register-v1.md fields plus bid_item_id, do_not_sum, and a structured native_readback object (saved_pdf_sha256, source_pdf_sha256, native_markup_id, unit, quantity). All values in tests are synthetic; **do not copy proprietary drawings/codebooks into this repository**.

## Test evidence

Linux / Python 3.13, 11 local offline tests PASS, 0 FAIL. Covered positive preview aggregation, QA-only exclusion, stale hash/revision, duplicate ID, unmapped bid item, mixed units, insufficient location evidence, boolean-only receipt, forged APPROVED metadata, NaN/Inf/negative numbers, inconsistent numeric receipt and malformed identity/flags without crashing.

This is not a full end-to-end test on the exact GitHub tree. The container cannot resolve GitHub to clone the repo, so the complete repository regression remains NOT RUN. No Windows/Revu/OPS/HeavyBid native tests, no cost data or actual approved human signatures.

## Follow-up

Complete #3 source verification and #4 independent line targeting, #5 real native versioned readback, #6 actual A/B/C lineage and governed BAX reconcile, and #7 operator UX. This tool deliberately does not produce an importable BAX or executable price update.
