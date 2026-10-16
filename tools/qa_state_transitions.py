#!/usr/bin/env python3
"""
Enforce legal QA state transitions for the lifecycle defined in
docs/qa-lifecycle.md:

    AI_PROPOSED -> MEASURED -> QA_CHECKED -> ESTIMATOR_REVIEWED -> APPROVED
                                                                 -> REJECTED-REWORK -> (AI_PROPOSED | MEASURED)

Usage:
    python qa_state_transitions.py <from_state> <to_state> [--actor human|automation]

Exits 0 if the transition is legal for the given actor, 1 otherwise with a
reason. This is a pure logic check - it does not touch Bluebeam or any
file; it exists so both an agent and any test harness can check a proposed status write before it's actually
sent to `set_markup_property`.
"""
import sys

STATES = [
    "AI_PROPOSED",
    "MEASURED",
    "QA_CHECKED",
    "ESTIMATOR_REVIEWED",
    "APPROVED",
    "REJECTED-REWORK",
]

# Forward progression plus the rework loop.
LEGAL_TRANSITIONS = {
    "AI_PROPOSED": {"MEASURED"},
    "MEASURED": {"QA_CHECKED"},
    "QA_CHECKED": {"ESTIMATOR_REVIEWED"},
    "ESTIMATOR_REVIEWED": {"APPROVED", "REJECTED-REWORK"},
    "APPROVED": set(),  # terminal, short of an explicit human-directed rework
    "REJECTED-REWORK": {"AI_PROPOSED", "MEASURED"},
}

# States that may ONLY be set by a human estimator (or automation executing
# an explicit, logged human instruction) -- never by unattended automation.
HUMAN_ONLY_STATES = {"ESTIMATOR_REVIEWED", "APPROVED"}


def check_transition(from_state: str, to_state: str, actor: str) -> list:
    problems = []

    if from_state not in STATES:
        problems.append(f"unknown from_state '{from_state}' - must be one of {STATES}")
    if to_state not in STATES:
        problems.append(f"unknown to_state '{to_state}' - must be one of {STATES}")
    if problems:
        return problems

    allowed = LEGAL_TRANSITIONS.get(from_state, set())
    if to_state not in allowed:
        problems.append(
            f"illegal transition: {from_state} -> {to_state} "
            f"(legal next states from {from_state}: {sorted(allowed) or 'none - terminal state'})"
        )

    if to_state in HUMAN_ONLY_STATES and actor != "human":
        problems.append(
            f"'{to_state}' may only be set by a human estimator (or automation executing an "
            f"explicit, logged human instruction) - refusing to set it as actor='{actor}'"
        )

    return problems


def main() -> int:
    args = sys.argv[1:]
    if len(args) < 2:
        print(__doc__)
        return 2

    from_state, to_state = args[0], args[1]
    actor = "automation"
    if "--actor" in args:
        idx = args.index("--actor")
        if idx + 1 < len(args):
            actor = args[idx + 1]

    problems = check_transition(from_state, to_state, actor)

    if not problems:
        print(f"LEGAL: {from_state} -> {to_state} (actor={actor})")
        return 0

    print(f"ILLEGAL: {from_state} -> {to_state} (actor={actor})")
    for p in problems:
        print(f"  - {p}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
