# AGENTS.md — instructions for human developers and AI coding agents

This file applies to the **entire repository**. The user/owner's standing direction is to finish the [Civil Takeoff Markups MCP roadmap](ROADMAP.md) before starting additional initiatives.

## Read before any edits

1. [ROADMAP.md](ROADMAP.md): current goal, priority order, acceptance and dependencies.
2. [docs/ROADMAP_2026-11-02.md](docs/ROADMAP_2026-11-02.md): audited baseline, risks and cross-repository architecture.
3. [DATA_POLICY.md](DATA_POLICY.md): non-negotiable public-repository confidentiality rules.
4. [docs/method.md](docs/method.md), [docs/traceability-contract.md](docs/traceability-contract.md), [docs/qa-lifecycle.md](docs/qa-lifecycle.md), [docs/mcp-notes.md](docs/mcp-notes.md).
5. Current open issues [#2–#7](https://github.com/taiduc1302/civil-takeoff-markups-mcp/issues) and open PRs before choosing work. **GitHub issue discussion is the live task board**; this file is permanent policy.

## Pick up, implement and hand off

- Work in stage order: **#2 -> #3 -> #4 -> #5 -> #6 -> #7**, allowing independent small PRs where dependencies are clear. Complete open roadmap work before unrelated feature ideas.
- **CLAIM** in the relevant issue before editing: agent/developer, optional non-sensitive environment alias, feature branch, files/scope, tests and dependencies. Recheck existing claims and PRs before overlapping files. A comment is coordination, not an atomic lock.
- Prefer one issue/PR and minimal changed files. If another agent changes the same path, pull/rebase/reconcile rather than replacing their content. Do not force push, rewrite published history or directly commit unreviewed feature code to `main`.
- Use a branch name such as `test/fixture-regressions-issue-2`. Write source-backed test cases **before or with** fixes.
- At each meaningful checkpoint post `PROGRESS` in the claimed issue, with PR/commit, exact passing and failing tests, new evidence and blockers. When blocked, say what can still be done offline.
- End each work session with `HANDOFF` in the issue: branch, commit/PR link, changed files, exact test commands/results, discovered problems, remaining acceptance items, next action. Keep source task open until its definition of done is met.
- Before merging confirm no new conflicting claims/PRs, that the PR's scope matches its issue and that local tests pass. When an issue is fully satisfied and merged, close it and synchronize the checkbox in `ROADMAP.md`.
- No GitHub Actions or paid service is needed. It is fine to add CI **later** as a separate scoped enhancement, but no stage should depend on unapproved billing or workflow runs.
- If a native Bluebeam tool/GUI cannot be accessed, work only on safe local/dry-run/synthetic components. Record a remaining real-runtime acceptance gate; **never** fabricate a live result.

## Local baseline (dependency-light)

```bash
python -m unittest discover -s tests -v
python tools/qa_state_transitions.py AI_PROPOSED APPROVED --actor automation
python tools/validate_municipal_checks.py examples/municipal_checks_synthetic.json
```

The final two commands intentionally refuse success (nonzero exit code) for the forbidden approval and the unresolved fictional jurisdiction checks. The commands do not make a real estimate ready. PyMuPDF is currently needed for `tools/build_synthetic_sheet.py`; the municipal tests are standard library only.

## Civil takeoff safety contracts (fail closed)

- Register the **exact PDF SHA-256, file revision, page label/index and measurement context**. Any new addendum or source/geometry hash change must invalidate or explicitly re-review dependent quantities.
- **Scale resolution is not scale verification.** A page-level scale field, a successful GUI calibration or a nonzero computed quantity does not itself establish dimensional correctness. Require independent scale evidence for scale-dependent QA.
- Geometry extraction and targeting are separate: reading the correct coordinates is not evidence that they belong to the right feature. Render overlays and require independent drawing evidence/human review where needed. Scans are manual fallback; never claim vector precision from raster pixels.
- Bluebeam capability claims require a strict tier: `PRODUCT_DOCUMENTED`, `CURRENT_SURFACE_EXPOSED`, `LIVE_TESTED` (with reproducible actual-version native saved readback receipt). Count support is version/connector-specific; circles are not native Count.
- The authoritative traceability register stays **outside mutable markup comments**; use stable markup ID/page/source evidence. Never use plain `--actor human` to authenticate an approval.
- Lifecycle: `AI_PROPOSED -> MEASURED -> QA_CHECKED -> ESTIMATOR_REVIEWED -> APPROVED` with explicit rework. An agent can reach at most `QA_CHECKED` and only with required evidence. Never manufacture human approvals.
- Exclude `QA CHECK - DO NOT SUM`, duplicate items, stale revisions, unverified or unmapped measurements and static counts from commercial totals. BAX reconciliation is a separate governed approval boundary.
- Never modify actual Bluebeam project documents in automated integration tests; use disposable synthetic data and explicit opt-in.

## Privacy and cross-repo use

- Treat this as a public MIT repository with **synthetic-only** examples. No employer/client data, quotes, private workflows, real BAX/PDFs, material codebooks, email, secrets or tool libraries.
- Other user-owned **private** repositories are research references only: no copying private code, datasets or fixtures into public history. For public repos, check licences and imported code provenance before using any files.
- Keep PR tests/diffs inspectable. Do not call the product production-ready or validated by an estimator without real verification evidence.
