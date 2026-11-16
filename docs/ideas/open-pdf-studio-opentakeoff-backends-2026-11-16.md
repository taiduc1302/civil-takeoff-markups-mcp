# Open PDF Studio alternative backend + OpenTakeoff research (2026-11-16)

Status: RESEARCH / NOT LIVE TESTED. Tracking: #15. This does not replace the active P0-P3 roadmap (#2-#7). Civil 3D visualization is separately tracked in #13 / PR #14.

## Goal and current baseline

Allow an estimator to select an optional Open PDF Studio backend rather than requiring Bluebeam. Both must consume the same vetted geometry proposals, document identity, scale evidence and external QA register. Add OpenTakeoff as an independent building/trade research module for a future universal takeoff tool; do not conflate a floor finish/room workflow with underground utilities.

The repository is an MIT-licensed method + fixtures, not a complete native takeoff app. Any new adapter must respect existing source hash, geometry targeting, independent verification, QA-only exclusions and human-only approvals.

## Source audit (upstream documentation, not a live run)

| Upstream | What is documented | Limitation / next test | License |
|---|---|---|---|
| [Open PDF Studio](https://github.com/OpenAEC-Foundation/open-pdf-studio) | Desktop MCP server, annotations, calibrate/measure/count, CSV quantities with IDs, XFDF, portable Windows ZIP. Desktop [Python client](https://github.com/OpenAEC-Foundation/open-pdf-studio/blob/main/docs/python-library.md) launches/connects to same app's MCP operations. | Browser viewer does not expose desktop MCP. Python client needs the app runtime; verify exact version and live tool schemas. XFDF/CSV != Bluebeam native markups or BAX. | LGPL-3.0-or-later |
| [OpenTakeoff](https://github.com/Kentucky-ai/opentakeoff) | Browser canvas + MCP, scale gate, line/polygon/count, agent proposals, human acceptance, multi-sheet and revision workflows, Excel/CSV/DXF. | One-Click Area feature temporarily gated; building room/finish model is not civil trench/pipe quantity logic. Do not copy AGPL implementation into MIT core without legal decision. | AGPL-3.0 |
| [MutinyBIM civil pack](https://github.com/permitzip/mutinybim/tree/main/packages/bim-pack-civil) | IFC 4.3 hints for storm structures/pipes/catchments and alignments/stations; 3D viewer packages; calculation hooks. | Its civil pack explicitly lacks terrain surfaces, grading, corridors and earthwork. The source 2D markup alone does not provide depth/elevation/CRS needed for defensible 3D. Follow #13 / PR #14. | Apache-2.0 |

## Proposed boundary

```text
approved takeoff scope -> hashed PDF / revision / page -> vector targeting + visual QA
  -> immutable geometry proposal (units, coordinate frame, source feature, confidence)
     -> optional backend selection
        - Revu: existing native MCP/GUI
        - Open PDF Studio: Python client/MCP (EXPERIMENTAL)
        - OpenTakeoff: separate building/trade pack (RESEARCH)
     -> save new output, reopen, read back, independently compare
     -> external evidence register + exception review -> human estimator
```

Interface draft (descriptive, not implemented):
- `capabilities()`: supports read/annotate/length/area/count/scale/export/reopen, exact app version and evidence tier. Unsupported actions refuse explicitly.
- `prepare(disposable_source, source_sha256, revision, page, units, scale_evidence)`: reject absent/ambiguous scope, mismatched source hashes or unverified scale for a verified-result claim.
- `preview(proposals)`: immutable plan overlay with feature IDs and QA-only flags.
- `write(disposable_output, approved_test_intent)`: only after explicit opt-in to synthetic fixture; no edits to originals, no production side effects.
- `readback()`: stable IDs + geometry/quantities, timestamps, units, page, backend version, output checksum, provenance and exceptions.
- `export()`: reject stale, duplicates, QA-only, unreviewed, wrong-feature and mismapped quantities for commercial handoff. Never synthesize approval.

### Important coordinate/identity tests
Convert PDF coordinates (lower-left points), display coordinates (often flipped Y), rotation, CropBox/MediaBox offsets, page indices and unit scale explicitly. Test true physical lengths independently of annotation software, not only tool readback. Establish fixtures and tolerance BEFORE running experiments.

## Disposable-fixture acceptance matrix

1. Record tool version, platform, checksum of fixture, independent benchmark and fixed numeric tolerance.
2. Scale-free drawing refuses quantitative output; independent printed dimension succeeds; wrong scale and wrong feature fail.
3. Measure two pipes (polyline), excavation rectangle (area), structure markers (count), deliberate QA-only shape and duplicate.
4. Save/reopen new PDF; compare measured values, IDs and source geometry against independent expected outputs.
5. Export/import CSV and XFDF, check lost fields / identities and whether annotations retain measurement intent. Do not call these Revu or BAX compatible until tested.
6. Test revision/addendum invalidation and stale quantity exclusion. Annotations/geometry from old revision remain historical, not summed.
7. Verify headless Python/MCP and Windows portable against a **real local app**; report evidence tiers separately: DOCUMENTED, SURFACE_EXPOSED, DISPOSABLE_TESTED, LIVE_TESTED. Browser-only test is not MCP verification.
8. Run offline regression and an independent safety/permissions review. No paid API or GitHub Actions required. Any blocked local-runtime check stays BLOCKED.

## OpenTakeoff research block for a future universal tool

Keep this separate from civil geometry and payment/approval controls:
- candidate reuse concepts: scale gate, proposed-vs-reviewed drawing UX, sheet tree and match-line linking, condition-based schedules, revised quantity delta and export audit;
- optional building-domain schema: room/finish/wall/surface/fixture with sheet and condition references;
- civil needs distinct schema: alignments, pipe invert/rim, station offsets, linear trench, excavation sections, manhole and catch basin counts, topsoil stripping, revision lineage;
- architecture decision needed: consume as standalone tool, use a separately licensed optional sidecar, or reimplement independently from behavior/spec. No direct source copying approved.

## MutinyBIM 2D -> 3D handoff (linked to #13)

A 2D overlay can identify a pipe/path but cannot establish a trustworthy Z coordinate. Require external design profiles, elevation points, invert/rim schedule or LandXML/XYZ surfaces, with units/CRS and source revisions. Produce a clearly labeled **conceptual** visualization when data are incomplete; reject modeled engineering quantities and cut/fill until independent evidence is available. Proposed pilot: synthetic plan/profile of pipe run -> map station/offset + invert endpoints -> 3D cylinder/structures -> linked source IDs -> IFC 4.3 preview. Actual surface grading needs another civil/terrain backend or new pack; MutinyBIM does not advertise it today.

## Outcome

Research document and task accepted as backlog only; no real MCP instance launched, no drawing modified, no adapter code or app regression claimed. Continue current #2-#7 gates before adopting a production backend. Maintain this note when evidence from real disposable runs is available.
