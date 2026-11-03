# Contributing

This is a public, synthetic-only research/method repository. Contributions are welcome when they improve the accuracy, auditability, reproducibility or usability of civil takeoff.

**Start here:** [Development roadmap](ROADMAP.md) -> [AGENTS.md](AGENTS.md) -> [technical analysis](docs/ROADMAP_2026-11-02.md). The numbered issues [#2–#7](https://github.com/taiduc1302/civil-takeoff-markups-mcp/issues) hold scoped, acceptance-tested tasks. Prioritize existing roadmap tasks over unrelated features.

## Proposed contribution workflow

1. Find an open task, read prior comments and open PRs, and post `CLAIM` with your intended scope, branch and tests. Do not assume an old claim is a hard lock or that a quiet agent has stopped working.
2. Work on a feature branch. Keep code, tests, documentation and traceability together in a focused change.
3. Use synthetic drawings and fixtures; do not commit anything generated from a client's tender, project PDF, BAX, estimate, protected licence or private repository.
4. Run `python -m unittest discover -s tests -v`, plus tests relevant to your change. Attach **exact commands, outcomes and version/environment limitations**. Dry-run mocks are not evidence of live Revu compatibility.
5. Submit a PR linked to the issue. Include: what changed; risks; tests performed; changes to approved measurement or review logic (if any); the remaining live/field evidence needed; and privacy considerations.
6. Post `HANDOFF` in the issue with PR/commit and next step. Leave unresolved or environment-blocked checks open. Checkboxes in `ROADMAP.md` change only after verified acceptance and merge.

## Non-negotiable review rules

The agent cannot approve quantities, select a winning quantity when independent evidence conflicts, or treat a computed measurement as proof that the chosen line lies on the correct drawing feature. Keep source revision, scale basis, independent location checks, native saved readback, registration, and human review separate. Count support and measurement creation depend on the actual Revu environment; document specific test evidence.

No paid API, GitHub Actions runtime or active Revu installation is required for standard offline development, but a task requiring native end-to-end success cannot be marked complete based on a mock test alone.

See [DATA_POLICY.md](DATA_POLICY.md) for the exact publication restrictions. If uncertain whether an artifact is safe to publish, **do not commit it**.
