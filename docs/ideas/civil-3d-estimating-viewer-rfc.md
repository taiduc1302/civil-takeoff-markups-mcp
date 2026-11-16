# Future RFC: Open-source Civil 3D Estimating Viewer and analytical visualization

> **Status:** IDEA / DEFERRED — not implementation-ready, not a tested tool. Recorded 2026-11-16. Tracking issue: [#13](../../issues/13). **Priority rule:** complete the current [roadmap](../../ROADMAP.md) issues #2–#7 before implementing this proposal. Do not treat this document as permission to reprioritize work. Public repository: synthetic-only data, per [DATA_POLICY.md](../../DATA_POLICY.md).

## 1. Idea origin and evidence

On 2026-11-16, a discussion started from a screenshot of a LinkedIn post by **Hamza Abdul Jabbar**, beginning **“RIP bluebeam.”** The post named free/open-source construction utilities **Open PDF Studio; Blender + Bonsai; FreeCAD; GanttProject; That Open Engine; LibreOffice**. It claimed that on one architectural drawing a 10,315 mm run was measured as 10,279 mm (difference 36 mm, approximately 0.35%). This is the poster's **single, unreplicated test**, not independently verified performance evidence. The screenshot did not provide a canonical post URL; do not invent one.

The subsequent discussion asked whether these tools could also produce **free charts, project-wide 3D visuals and earthwork/utility models**. This suggested a second-tier **read-only, local-first viewer** and visual analytics module connected to the current civil-takeoff workflows. Further candidate tools raised in discussion: **Apache ECharts, Plotly, OpenAEC Open BIM Suite / open-3d-viewer**. The earlier discussion suggested an Open PDF Studio alternative MCP/PDF backend and a standalone “3D Civil Estimating Viewer”, but neither integration has been proven.

This RFC preserves the *idea and source trail* for other developers. **Product claims from source documentation ≠ a successful integration, accuracy test or commercial approval.** Reassess vendor documentation, latest versions and licences at implementation time.

## 2. Problem / desired outcome

Estimators need to understand quantities spatially: where existing and proposed surfaces differ, how trench lines cross terrain, which utilities belong to a source sheet/bid item, and where uncertain or superseded measurements originated. Existing Revu/AGTEK/HeavyBid workflows must stay authoritative. A lightweight viewer could make **source-grounded geometry plus exceptions, QA states and commercial context** easier to inspect.

Proposed outcomes:
- Read-only **Existing vs Design** 3D terrain with layer toggle, section cut, orbit, elevations and a clear scale/units/CRS display.
- Synthetic trench/pipe/site elements with stable element IDs and documented source-sheet/feature lineage.
- Charts of validated quantities, discrepancy/revision counts, construction phases and (later) authorized cost-code/bid-item values.
- Click a 3D object to reveal provenance and linked takeoff/QA evidence rather than an invented engineering quantity.
- Later, optional 4D sequencing (time) and 5D cost contextualization without creating or approving bids.

## 3. Candidate technology research (verify before adopting)

| Candidate | Potential use | Main caution |
| --- | --- | --- |
| [Apache ECharts](https://github.com/apache/echarts) | Local browser chart dashboard; cost/quantity/exception charts | Apache-2.0; maintain validated data contracts |
| [Plotly.js](https://github.com/plotly/plotly.js) | Interactive charts, 3D surfaces, standalone reporting | MIT for core JS; confirm exact package and packaging |
| [That Open Engine](https://github.com/ThatOpen/engine_components) | Interactive web IFC/3D model, element selection, sections | Verify the current packages and licence; IFC ≠ LandXML terrain parser |
| [Blender](https://www.blender.org/) + [Bonsai](https://bonsaibim.org/) | Author/render BIM and geometry; scenario visuals | Different licences; authoring workflow rather than simple web viewer |
| [FreeCAD](https://github.com/FreeCAD/FreeCAD) | Open parametric geometry/CAD prototypes | Format and civil data compatibility must be demonstrated |
| [OpenAEC Open BIM Suite](https://github.com/OpenAEC-Foundation/open-3d-viewer) | Candidate CAD/BIM/terrain/point-cloud viewer with advertised MCP and formats (LandXML/XYZ/IFC etc.) | Verify actual supported versions/import semantics and resource demand against fixtures |
| [Open PDF Studio](https://github.com/OpenAEC-Foundation/open-pdf-studio) | Candidate isolated MCP PDF annotation/measurement and CSV adapter | Not an established substitute for Bluebeam native measurements/BAX/Studio; require saved-state readback |
| [GanttProject](https://www.ganttproject.biz/) | Optional free schedule source | Not a 3D geometry or estimating engine |
| [LibreOffice](https://www.libreoffice.org/) | Optional free document/spreadsheet output | Check formula/format round-trip and downstream compatibility |

The original six-tool LinkedIn list and the additional chart/viewer tools should **not** all become runtime dependencies. Prefer the smallest install footprint. Check transitive license obligations (especially GPL/LGPL), provenance, security posture and offline/no-cost use before copying code or forking anything.

## 4. Architecture sketch / boundaries

```text
controlled source set (synthetic PDF, LandXML, XYZ, IFC, CAD)
  -> ingestion adapters (read only)
  -> provenance registry: SHA-256, revision, sheet, page, units, CRS, elevation basis
  -> geometry / scale / alignment QA (independent checks)
  -> normalized local scene + element-to-source IDs + uncertainty flags
     |-> 3D viewer (layers, selection, sections, surface comparison)
     |-> ECharts / Plotly analytics (approved source-backed vs proposed separate)
     |-> evidence/exception inspector
  -> optional future links to governed takeoff/HeavyBid interfaces (not direct writes)
```

Keep source-of-truth outside the render layer. No conversion from an arbitrary plan PDF into precise 3D without independent grades/elevations, alignment and dimensions. When only an image or 2D geometry is available, label any visualization **CONCEPTUAL / NOT FOR QUANTITIES**.

The current QA lifecycle remains: `AI_PROPOSED -> MEASURED -> QA_CHECKED -> ESTIMATOR_REVIEWED -> APPROVED`; automation stops at `QA_CHECKED`, subject to actual evidence. A pretty 3D render does not establish the correct measured feature, source revision, engineering interpretation or commercial scope. BAX and HeavyBid handoff remain governed separately.

## 5. Proposed phases (AFTER current #2–#7 gates)

| Phase | Deliverable | Exit gate |
| --- | --- | --- |
| R0: feasibility | version/licence matrix; compare no-install browser and local options; define strict source/scene schemas and synthetic expected outputs | documented go/no-go, no feature build without value case |
| R1: minimal 3D | two synthetic LandXML Existing/Design TINs, orbit, layers, vertical exaggeration clearly marked, sections, z readout | reproducible offline viewing; known vertices, triangle counts, elevations and extents match fixtures |
| R2: civil geometry | synthetic pipes/trenches/utilities as explicit 3D objects with station/elevation/source links | units/CRS, missing z, crossing and wrong feature cases fail closed |
| R3: charts / UX | ECharts or Plotly view of verified quantities, exceptions, source revisions and candidate vs approved distinctions | selection/readout matches source registers and independently calculated totals |
| R4: adapter spike | isolated Open PDF Studio and Open BIM Suite read-only / disposable tests | scale, coordinates, saved readback, round trip and error handling proven; no BAX parity assumption |
| R5: optional 4D/5D | mock phase animation; approved/synthetic bid item and cost references | schedule/cost provenance and estimator review intact, no auto-cost approval |

**Prioritize R1 before adding complex BIM or AI.** A simple synthetic surface comparison that opens correctly, reports elevation and highlights discrepancies is a more valuable acceptance target than a decorative 3D demo.

## 6. Test and acceptance design

- Use **fully synthetic, public-safe** datasets only, checked into examples if permitted. No proprietary drawing, AGTEK file, real client rates, tender schedules, identifiers or screenshots in public PRs.
- Include known elevation triangles, cut/fill regions, pipe alignments, station/elevation pairs, alternate units and a deliberate wrong coordinate system. Freeze ground truth separately from generator output.
- Check triangles/vertices and topology; units (m/mm/ft), CRS/origin/rotation, ground elevations, clipping/sections, face orientation, volume sign and method. Set numerical tolerance in advance; compare against independent calculations.
- Regression: altered revision or source hash invalidates dependent scene/quantities; wrong sheet, missing elevation, duplicates, wrong feature and inconsistent scale must not silently produce “verified” data.
- Round-trip: reload/save of any disposable test PDF must preserve annotation IDs, geometry and measured quantities as demonstrated, or declare the unsupported operation.
- Performance: small + medium synthetic datasets; browser memory and load time recorded without promising unsupported large-scale performance.
- User experience: visible legend for `CONCEPTUAL`, `SOURCE_GROUNDED`, `UNVERIFIED`, `QA_CHECKED`, `HUMAN_APPROVED`; missing or conflicting inputs produce explanations and manual review.
- Offline `python -m unittest discover -s tests -v` (or lightweight equivalent) for deterministic checks. No requirement for GitHub Actions, cloud model, external API or Windows host to develop the fixture layer. Real tool compatibility separately requires explicitly versioned on-host test evidence.

## 7. Privacy, security and commercial gates

- Local-first default; prohibit upload of client drawings to third-party services without explicit authorization.
- Treat PDF/CAD/IFC inputs and tool replies as untrusted. Validate parsers, cap resource usage, disallow uncontrolled file writes, report unsupported versions.
- Public repo contains **no** real Tybo/customer files, marks, codebooks, protected PDFs, amounts, or private cross-repo source. Source ideas only may be reused from private repositories; no copying without consent/license.
- A viewer does not change approved Revu markups, AGTEK surfaces, BAX/HeavyBid quantities or a human approval status.
- Code import/fork decision requires dependency/security/license audit. A GitHub star count or a LinkedIn demonstration is not a release-quality evaluation.

## 8. Interfaces to other projects (concepts only)

- `civil-takeoff-markups-mcp`: share synthetic fixture, source evidence/markup ID, geometry and QA-state contracts; **do not** modify current measurement pipeline for this idea.
- `screen2xyz`: possible provenance-aware XYZ exports/coordinate bridge, only if schema and calibration evidence match.
- `canada-tender-finder`: perhaps reuse ECharts UI conventions for opportunity dashboards; it should **not** depend on any 3D/CAD library.
- `ai-model-advisor`: optional future cost/latency/model routing research, *not* needed for rendering deterministic geometry.
- AGTEK/Bluebeam/HeavyBid: preserve existing tools; investigate read-only, controlled export/import boundaries later, no assumed proprietary native file compatibility.

## 9. Exclusions and decision log

**Out of scope now:** standalone repo creation, commercial estimating, engineering sign-off, automatic approval or tender submission, remote hosting, replacing Bluebeam/AGTEK/HeavyBid, commercial dataset ingestion, or autonomous 3D reconstruction of incomplete PDFs.

**2026-11-16 decision:** document and park the idea in GitHub [issue #13](https://github.com/taiduc1302/civil-takeoff-markups-mcp/issues/13) and this RFC; review only after the current takeoff roadmap is independently completed. At that time decide whether a simple viewer belongs here, as a module, or in a separate repo. All claims and dependencies must be reverified.

## 10. Research links

- Source background: LinkedIn screenshot by Hamza Abdul Jabbar shared in the discussion (original canonical post URL not captured).
- [Open PDF Studio source](https://github.com/OpenAEC-Foundation/open-pdf-studio)
- [OpenAEC 3D Viewer source](https://github.com/OpenAEC-Foundation/open-3d-viewer)
- [Bonsai](https://bonsaibim.org/)
- [FreeCAD](https://github.com/FreeCAD/FreeCAD)
- [That Open Engine](https://github.com/ThatOpen/engine_components)
- [Apache ECharts](https://github.com/apache/echarts)
- [Plotly.js](https://github.com/plotly/plotly.js)
- [GanttProject](https://www.ganttproject.biz/)
- [LibreOffice](https://www.libreoffice.org/)
