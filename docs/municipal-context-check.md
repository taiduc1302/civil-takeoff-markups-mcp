# Pre-bid municipal context check

A takeoff can be geometrically correct and still leave the estimator exposed to a permit, fee, inspection or approval-delay risk. This can happen to a human estimator too, especially when bidding in a municipality for the first time.

This is an **optional, separate pre-bid risk check** alongside the quantity takeoff. It is not a new way to measure geometry and does not change a markup's QA status. The goal is to surface questions with evidence before quantities and assumptions are used in an estimate.

## Start with the place, scope and responsibility

Before searching, record the project's jurisdiction, the actual scope of work, the bid/addendum revision and the date of the check. Identify the authority having jurisdiction: a municipal name alone may not cover utility owners, regional authorities, a road authority or provincial/state agencies. Read the tender documents for which party must obtain and pay for each permit.

For each category below, determine whether it applies **to this scope**. A regulation's existence is not proof it applies to this bid.

| Check ID | Questions to investigate |
|---|---|
| `permit_requirements` | Excavation, construction, environmental or other permit triggers; application prerequisites; which party obtains them? |
| `local_code_and_zoning` | Applicable local rules, zoning/site restrictions, relevant code edition and effective date; are there scope-specific exceptions? |
| `fees_and_deposits` | Official fee schedules, deposits, plan reviews, inspection charges, renewals; who carries the cost and where does it appear in the estimate? |
| `review_and_inspection_timing` | Permit review stages, agency/inspection dependencies, lead times and possible schedule/carrying-cost exposure; is the timeline verified or only an estimate? |
| `road_occupancy_and_utilities` | Right-of-way/traffic permits, utility owner approvals, locates, crossings and other authority sign-offs. |

Add a new check ID when a new risk is discovered (for example, owner-specific requirements, prevailing wage, heritage or environmental constraints). The five categories are a starting checklist, **not an exhaustive legal/code matrix**.

## Evidence, not a confident answer

1. Check issued tender documents and addenda, then the **current official** municipal, regulator and utility-owner sources. Record an exact URL or document/page/section and the authority, not just a search result or an AI summary. If available, record the code edition or fee schedule effective date in the finding.
2. Record when the source was checked. As bid dates approach, re-check fee schedules and approval guidance; a published target processing time is not a guaranteed project-specific approval date.
3. Record any mismatch between tender assumptions and official requirements, plus a possible cost/schedule consequence and the party responsible. Flag conflicting, missing or stale sources; ask the authority or design team where needed.
4. **Never treat "no result found" as "not required."** The agent must say which sources/jurisdictions it searched and leave unresolved items open. In particular, avoid repeating unverified headline numbers about cities, approval delays or fees as project facts.
5. A person reviews applicability, exceptions, bid allowances and final disposition. The agent collects evidence and raises questions; it does not issue regulatory clearance, approve the estimate or amend a tender assumption silently.

## Record status and handoff

Store the results in a separate JSON/CSV/workbook register, keyed by jurisdiction and check ID. `examples/municipal_checks_synthetic.json` is a fictional starter with no actual municipal findings.

| Status | Meaning | Human review? |
|---|---|---|
| `OPEN` | Not checked or not enough evidence | Required |
| `EVIDENCE_FOUND` | Source and finding recorded, applicability not yet resolved | Required |
| `FLAGGED` | Potential conflict, missing information, fee or schedule risk | Required |
| `HUMAN_CLEARED` | A human reviewed documented evidence and assigned responsibility | Recorded human review |
| `NOT_APPLICABLE` | A human recorded why this category does not apply | Recorded human review |

Record `source_ref`, `source_checked_on`, `authority`, `finding` and `responsible_party` as applicable. For human dispositions, add `reviewed_by` and `reviewed_on`. The latest official source must be re-evaluated if the project scope or bid date changes. Do not mark a category `NOT_APPLICABLE` merely because the agent failed to find a source.

**The validator checks documentation, not identity or law.** A JSON reviewer name is not secure authentication or proof that a real review happened. These statuses are separate from `ESTIMATOR_REVIEWED` / `APPROVED` in the markup QA lifecycle. Even a fully documented municipal register does **not** approve a permit, a quantity or a bid.

## Try the guardrail

```bash
python tools/validate_municipal_checks.py examples/municipal_checks_synthetic.json
# REVIEW REQUIRED; exits 1 because all five fictional checks are OPEN

python -m unittest discover -s tests -v
# Exercises missing checks, missing sources, human sign-off fields and dates
```

Return codes: `0` means the register has recorded human dispositions for all required check IDs (**not** regulatory approval); `1` means unresolved items; `2` means invalid/missing data. Use code `1` as a review flag, not a machine-imposed bid/no-bid decision.

## Agent instruction to reuse

> Before calling this tender ready, determine the project jurisdiction and the authority for each scope item. Check current official permit, code/zoning, fee, review/inspection timing and right-of-way/utility requirements that could affect the work. Compare them with the tender documents and addenda. For each check, record the source and section, date checked, applicability, responsible party and possible cost or schedule risk. If an answer cannot be verified, leave it OPEN or FLAGGED and say exactly what a person must confirm. Never auto-set HUMAN_CLEARED / NOT_APPLICABLE, approve quantities or assume a search found every requirement.

This check is useful at bid intake, after addenda and before bid review. It is intentionally separate from the native Bluebeam markup creation method in `method.md`.
