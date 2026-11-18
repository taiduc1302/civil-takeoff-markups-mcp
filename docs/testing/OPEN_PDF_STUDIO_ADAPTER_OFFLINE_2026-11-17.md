# Open PDF Studio adapter: offline evidence and next verification

Date: 2026-11-17 | Tracking: issue #15 | Branch: research/open-pdf-studio-adapter-20261117

STATUS: EXPERIMENTAL / MOCK-TESTED ONLY. No actual Open PDF Studio process, Windows/Revu host, or live quantity was tested. This code does not complete issues #3–#7 and does not replace Bluebeam.

## Delivered

- tools/open_pdf_studio_adapter.py is a dependency-free **dry-run by default** backend plan for SYNTHETIC PDFs.
- Exact PDF SHA-256, explicit revision, correct source/output separation, page index, separate scale reference, valid geometry, unique IDs and QA-only flags are checked before dispatch. Incorrect or ambiguous inputs fail closed.
- Converts zero-based evidence page index to one-based documented vendor API page.
- Documented upstream annotation kinds: measureDistance; measurePerimeter (open polyline); measureArea; count.
- Optional --execute-synthetic calls vendor Python library via an **isolated new app instance**, creates a NEW marked PDF and reopens it to read IDs. It will not attach to an existing personal application session. Never produces an approval.
- Native ID readback alone cannot verify the semantic feature, actual numeric quantity, scale or BAX compatibility.

## Command

    python -m unittest discover -s tests -v

For standalone new tests:

    python -m unittest discover -s tests -p test_open_pdf_studio_adapter.py -v

The JSON dry-run requires an existing synthetic PDF and its **actual** SHA-256:

    {
      "synthetic_fixture": true,
      "source_pdf": "/absolute/path/synthetic_plan.pdf",
      "output_pdf": "/absolute/path/synthetic_plan_NEW.pdf",
      "source_sha256": "COMPUTE_ACTUAL_64_CHAR_SHA256",
      "source_revision": "A",
      "page_index": 0,
      "page_label": "SYN-C-101",
      "coordinate_space": "opds-native-page-points-at-100-percent",
      "scale_reference": {
        "page_points": [[0,0],[100,0]],
        "known_length": 10,
        "unit": "m",
        "basis": "independent synthetic 10 m reference"
      },
      "features": [
        {"id":"SYN-PIPE-1","kind":"Length",
         "points":[[50,50],[150,50]],"do_not_sum":false}
      ]
    }

    python tools/open_pdf_studio_adapter.py /absolute/path/plan.json

By default this emits JSON, changes no PDF and uses no vendor app. The following has NOT yet passed live vendor acceptance; do not run on proprietary/client source PDFs:

    python tools/open_pdf_studio_adapter.py /absolute/path/plan.json --execute-synthetic

The synthetic_fixture flag is an operator assertion, NOT an authentication mechanism.

## Remaining gates

1. Confirm specific Windows/portable app version, signing, matching Python package and actual live tool schemas in a disposable instance.
2. Establish tested geometric transform between PyMuPDF unrotated Y-down coordinates and Open PDF Studio 100%-zoom application points. Never assume they are equivalent, especially with crop/rotation.
3. Against independently dimensioned synthetic drawing, create length, area, count; reject wrong-feature, duplicate, NTS, mixed scales, and stale source revisions.
4. After saving/reopening, compare actual **numeric quantities and units** and target overlay against independent benchmark. Annotation ID alone is insufficient.
5. Test CSV/XFDF identity fidelity, revision deltas and BAX/native Bluebeam interoperability separately. No human approval or automatic commercial rollup.
6. Run full offline repository suite and Windows native acceptance on exact head. A missing host is BLOCKED, not PASS.

## Evidence and limitations

On Linux / Python 3.13, six mock adapter tests passed, zero failures; no paid APIs, GitHub Actions or network required. Only new adapter tests ran, not the complete repository suite: this environment cannot clone GitHub via its shell (hostname unavailable). The fake app verifies control flow and safety checks, NOT vendor math or rendering. These limits are deliberately retained in this PR.

Upstream sources: https://github.com/OpenAEC-Foundation/open-pdf-studio ; https://github.com/OpenAEC-Foundation/open-pdf-studio/blob/main/docs/python-library.md ; https://github.com/OpenAEC-Foundation/open-pdf-studio/blob/main/mcp-stdio/tools.json
