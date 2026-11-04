# Offline integration verification — 2026-11-04

Baseline after merging PRs: `main@c4225dc830323a57be3f29a3d980c7705f08a19b`.

## Integration disposition

| PR | Integration | Evidence | Still open |
| --- | --- | --- | --- |
| [#9](https://github.com/taiduc1302/civil-takeoff-markups-mcp/pull/9) | Merged | 14 candidate tests; regression fixes for unhashable units and huge numbers; current fixture emits 17 candidates | [Issue #2](https://github.com/taiduc1302/civil-takeoff-markups-mcp/issues/2): reconcile historically documented 21 native markups; full independent PDF baseline |
| [#10](https://github.com/taiduc1302/civil-takeoff-markups-mcp/pull/10) | Merged | 10 register tests, plus a new malformed-status regression; validator checks presence/shape only | [Issue #3](https://github.com/taiduc1302/civil-takeoff-markups-mcp/issues/3): authenticated reviewer, actual host readback and event lineage |
| [#11](https://github.com/taiduc1302/civil-takeoff-markups-mcp/pull/11) | Merged | 2 tests reopening separately saved synthetic PDF, SHA-256 and rotation | [Issue #4](https://github.com/taiduc1302/civil-takeoff-markups-mcp/issues/4): correct-feature targeting, multi-space scale/crop/rotation transform and human overlay |

## Verification methodology and limits

The execution container could not resolve `github.com` for `git clone`. GitHub connector file contents were therefore copied into an isolated synthetic-only Python test tree and each transferred Python/JSON file was checked against GitHub's blob SHA using `git hash-object` before execution. Python version was 3.13.5; PyMuPDF was 1.26.7.

- Combined offline test run of the reconstructed PR #9/#10/#11 tree plus existing municipal tests: **48/48 passed**.
- The malformed-input regression updates added to PR #9 were executed in the same reconstruction: **50/50 passed**.
- The subsequent PR #10 one-line status-type guard was checked against 4 malformed inputs; the extra GitHub test file itself **was not included in the 50-test full run**. The combined post-merge `main` must still receive a fresh exact-tree full run; no claim of it having passed is made.
- Real native Bluebeam placement, saved readback, independent drawing-feature check and BAX/HeavyBid reconciliation: **NOT TESTED**.
- No GitHub Actions or paid cloud model runs were used.

## Known boundaries

- Synthetic candidate validation is not proof of geometry targeting or native Bluebeam quantity accuracy.
- `validate_evidence_register.py` checks **presence and structure** of reported native readback and human decision fields. Those fields are not cryptographically or access-control bound to a genuine Revu operation/human user. A passing JSON validator is **not estimator approval**.
- Current generated `examples/derived_markups.json` has 17 proposed objects. The existing marked PDF was historically described as 21 markups; independent comparison is pending and the files must not be conflated.
- Public repository contains synthetic-only data; never commit real project PDFs, BAX, client details or office codebooks.

## Next execution

1. Re-run `python -m unittest discover -s tests -v` on the exact final `main` tree, locally. Add expected-error cases for malformed JSON and large numerical values.
2. Finish #2 acceptance (historic native PDF markup count, independent fixture reconciliation).
3. Harden #3 proof binding and #4 geometry/crop/viewport review. #5 requires a disposable actual supported Revu environment for `LIVE_TESTED`; GUI remains fallback.
4. Keep #2–#7 open until each individual acceptance criterion is satisfied. No checkbox is considered complete just because a partial PR merged.
