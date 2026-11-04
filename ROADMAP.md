# Development roadmap — Civil Takeoff Markups MCP

**Current focus: finish this repository's entire takeoff-quality roadmap before expanding to new project ideas.**

This is the **permanent entry point** for human contributors, AI coding agents, and future sessions. Read it before changing code. Detailed technical audit: [docs/ROADMAP_2026-11-02.md](docs/ROADMAP_2026-11-02.md). Operational rules: [AGENTS.md](AGENTS.md). Contributor guide: [CONTRIBUTING.md](CONTRIBUTING.md).

Updated: **2026-11-02**. Current baseline: method + synthetic fixture + simple scripts, **not** a tested end-to-end Bluebeam takeoff product. Do not report it as production-ready.

## What are we building?

A local-first, reliable civil takeoff workflow:

`approved takeoff scope -> controlled PDF/revision/scale -> geometry candidate -> visible overlay and independent QA -> native Bluebeam markup (MCP if actually proven; GUI otherwise) -> saved quantity readback -> register/exception reconciliation -> estimator review -> controlled BAX/HeavyBid handoff`

No model can make an engineering, commercial, or estimator approval. Live MCP capability is never inferred from vendor documentation alone.

## Integrated partial milestones (not closed)

- 2026-11-04: [PR #9](https://github.com/taiduc1302/civil-takeoff-markups-mcp/pull/9), [PR #10](https://github.com/taiduc1302/civil-takeoff-markups-mcp/pull/10), and [PR #11](https://github.com/taiduc1302/civil-takeoff-markups-mcp/pull/11) merged into `main`. The audit and verification limitations are in [docs/testing/OFFLINE_MERGE_AUDIT_2026-11-04.md](docs/testing/OFFLINE_MERGE_AUDIT_2026-11-04.md). **These are partial deliveries; #2, #3 and #4 remain open and their checkboxes below are intentionally not checked.**

## Required sequence and ownership

**Open issues are the live task board.** They contain authoritative acceptance criteria and up-to-date progress comments. The checkboxes below are a roadmap view, not a substitute for checking the linked issue and related PRs. Update this file in the same PR that closes a stage. An issue stays open when work is blocked or tests have not run.

### P0 — Foundations: finish before expanding features

- [ ] [#2 — Reproducible synthetic baseline and regression tests](https://github.com/taiduc1302/civil-takeoff-markups-mcp/issues/2). Freeze/check candidate counts, source artifacts, units, geometry, malformed records, deterministic fixtures; distinguish generated 17 candidates from historic claims of 21 markup objects. **Can run completely offline.**
- [ ] [#3 — Enforce traceability, scale, and QA gates](https://github.com/taiduc1302/civil-takeoff-markups-mcp/issues/3). Versioned external register, independent scale verification, evidence requirements, no automated human approval; genuine reviewer identity cannot be established by `--actor human`. **Can start offline; live evidence remains separately gated.**

### P1 — Real geometry and trustworthy native markups

- [ ] [#4 — Independent vector PDF extraction and targeting](https://github.com/taiduc1302/civil-takeoff-markups-mcp/issues/4). Read geometry from the saved PDF instead of reproducing generator variables, validate PDF coordinate systems, page labels and multispace scale, detect decoy features, produce overlay previews; scanned drawings use manual fallback. **Use synthetic PDF fixtures and offline tests first.**
- [ ] [#5 — Capability-gated Bluebeam MCP adapter](https://github.com/taiduc1302/civil-takeoff-markups-mcp/issues/5). Dry-run/mock path, actual point-version + supported tool discovery, idempotent write, native readback, failure handling; independent real-Revu disposable acceptance test before any LIVE_TESTED claim. **Live gate stays BLOCKED until tested on supported local Revu.**

### P2 — Revisions and estimator-grade handoff

- [ ] [#6 — Revision lineage, safe aggregation and BAX handoff](https://github.com/taiduc1302/civil-takeoff-markups-mcp/issues/6). Source/geometry hashes, stale quantity invalidation after addenda, double-count protection, explicit exclusions, verifiable evidence bundles, separate downstream BAX reconciliation. **No auto-approval or silent replacement.**

### P3 — Practical local user workflow

- [ ] [#7 — Local estimator UX, contributor onboarding and reporting](https://github.com/taiduc1302/civil-takeoff-markups-mcp/issues/7). Simple takeoff plan -> preview -> markup/readback or GUI fallback -> exceptions -> review -> export; demonstrable offline synthetic path, explicit capability/limitations. **Do not build a large UI before the core is reliable.**

## Dependency / release gates

1. **Gate 0 — Foundation:** #2 and #3 merged, documented and locally tested. Do not call measurement output verified without independent basis.
2. **Gate 1 — Geometry:** #4 exercises PDF parsing on an independently saved synthetic PDF with correct coordinate/scale/feature targeting. Wrong-feature fixtures must fail.
3. **Gate 2 — Native tool:** #5 mock integration and error tests pass; a real native creation and saved readback is marked `LIVE_TESTED` **only with versioned Revu evidence**. Without the host, record the blocker instead of claiming success.
4. **Gate 3 — Quantity handoff:** #6 prevents stale, unapproved, QA-only, duplicate, mismapped or unverified quantities from being rolled into a commercial update. Compare to governed BAX results separately.
5. **Gate 4 — Usability:** #7 delivers a usable local first-run workflow and visible exception/review states; limitations remain explicit.

## Definition of fully complete

The roadmap is complete **only when all six issues #2–#7 are closed by merged reviewable PRs, their issue-level acceptance criteria have linked evidence, the offline regression suite passes, the independent synthetic end-to-end example passes, and any required live Revu gates are evidenced on a documented supported environment.** A blocked host-dependent test is **not** a passing test. The public repository must contain synthetic/sanitized data only.

After reaching those gates: do a **final independent regression/security/documentation review** and fix any remaining failures. Only then propose new adjacent repositories or further product expansion. Closing a task without the evidence does not count.

## How any developer picks up work

1. Read [AGENTS.md](AGENTS.md), [DATA_POLICY.md](DATA_POLICY.md), [technical audit](docs/ROADMAP_2026-11-02.md) and this file.
2. Check all six linked GitHub issues and open PRs; use the **first unclaimed, unblocked** task in dependency order.
3. Comment `CLAIM` on the issue with your branch, scope/files, test plan and any dependencies; re-check immediately before editing. A claim is advisory, not a distributed lock.
4. Make one focused feature branch and PR per task or independently testable portion. No force-push or silent editing of another contributor's scope.
5. Run offline tests and report exact commands/results. Record `BLOCKED` explicitly if current environment lacks Revu. Do not invent live tests or credentials.
6. On completion add a `HANDOFF` comment with commit/PR, tested scope, remaining limitations and next task. Link the PR in the issue.
7. Update this roadmap's task checkboxes **only when** the related acceptance criteria are demonstrated and PRs merged. Re-read `main` after merging to avoid overwriting concurrent changes.

## Privacy, cost and product boundaries

- This is **public**. Never commit real tender documents, actual construction drawings, employer material/activity codebooks, protected BAX, rates, customer information, secrets, auth tokens or real-project registers. Do not copy from private repositories.
- Default implementation/tests must work without GitHub Actions, paid LLM APIs or Bluebeam runtime. Live Revu testing is a separate optional local test step with clear gating; its absence blocks claims, not all development.
- Keep `SCALE_RESOLVED` separate from independently evidenced `SCALE_VERIFIED`; saved native quantity readback does **not** prove the correct feature was selected.
- Automation never sets `ESTIMATOR_REVIEWED` or `APPROVED`. QA-only `DO NOT SUM` markups must never contribute to measured totals.
- Never silently delete existing evidence, supersede a drawing authority, alter native project markups, or commit a guessed commercial quantity.
