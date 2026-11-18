# Offline source-integrity gate: supplemental P0 issue #3 delivery

Date: 2026-11-17 | Scope: source hash, revision, actual page labels and metadata
Status: source-level proof only; issue #3 and #6 REMAIN OPEN.

## Why

A register can declare arbitrary SHA-256, revision and page label. The existing docs/evidence-register-v1.md validator inspects record structure but intentionally does not open the source file. That means a stale addendum or wrong page can look structurally complete. This additive tool checks the declared source identity against the actual saved PDF and refuses stale rows.

## What is implemented

- tools/verify_source_register.py reads a local PDF with PyMuPDF, hashes actual bytes twice (detecting mid-read changes), obtains PDF page labels, rotation, MediaBox and CropBox, and compares each register row's SHA/revision/page index/label.
- Uses existing validate_evidence_register.validate() in the CLI first; invalid structural rows cause exit 2.
- Exit 1 if any register evidence is missing or a row is stale/mismatched; exit 0 means recorded fields and source identity agree, **not** quantity, reviewer, approval or BAX readiness.
- No document editing or network. Source revision is *declared* by the operator/controlled plan and cannot be authenticated from this match alone.
- All result flags reviewer_authenticated, scale_verified, feature_targeting_verified, commercial_handoff_approved are ALWAYS false.

## Run

    python tools/verify_source_register.py register.json source.pdf REVISION
    python -m unittest discover -s tests -p test_source_register.py -v
    python -m unittest discover -s tests -v

The JSON register follows docs/evidence-register-v1.md. For an actual PDF, use its exact page labels; a synthetic sheet's title-block visible text is not automatically its PDF page label. Do not attach any real tender data to this public repository.

## Evidence

On isolated Linux / Python 3.13 / PyMuPDF 1.26.7, six new source-integrity tests PASS, zero fails. A real, synthetic, saved PDF was generated locally for each test. Covered: known source SHA + page + revision, revision-change, byte-change, wrong page index/label, 90-degree rotation metadata, missing source and unsupported register schema. No Revu/OPS host used.

Full repo checkout and full cross-module suite not available in local container because Github shell clone DNS did not resolve. The connected GitHub tool was used to publish code; this is not equivalent to running the entire suite on the pushed Git tree. No merge until relevant acceptance gate is satisfied.

## Next work to close #3

Authenticated reviewer/decision provenance, binding an actual vendor/native saved-readback receipt to source file identity and numeric quantity, independent visible feature/scale checks and explicit state/event audit are still NOT implemented by this source-only check. Further #6 commercial aggregation/revision lineage and BAX handoff must remain separately governed. No automated approvals.
