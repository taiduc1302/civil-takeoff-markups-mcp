"""Offline regression coverage for the existing QA transition helper.

The actor argument is *not* identity verification. No real approval occurs here.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from qa_state_transitions import check_transition, STATES, LEGAL_TRANSITIONS  # noqa: E402


class QATransitionTests(unittest.TestCase):
    def test_automation_can_reach_measured_and_qa_checked_only(self):
        self.assertEqual(check_transition("AI_PROPOSED", "MEASURED", "automation"), [])
        self.assertEqual(check_transition("MEASURED", "QA_CHECKED", "automation"), [])

    def test_automation_never_sets_human_only_states(self):
        for target, previous in (("ESTIMATOR_REVIEWED", "QA_CHECKED"),
                                 ("APPROVED", "ESTIMATOR_REVIEWED")):
            with self.subTest(target=target):
                self.assertTrue(any("human" in problem for problem in
                                    check_transition(previous, target, "automation")))

    def test_human_can_follow_legal_sequence_as_pure_rule_check(self):
        self.assertEqual(check_transition("QA_CHECKED", "ESTIMATOR_REVIEWED", "human"), [])
        self.assertEqual(check_transition("ESTIMATOR_REVIEWED", "APPROVED", "human"), [])

    def test_skip_or_reverse_never_accepted(self):
        for previous, next_state in (("AI_PROPOSED", "APPROVED"),
                                     ("MEASURED", "APPROVED"),
                                     ("QA_CHECKED", "APPROVED"),
                                     ("APPROVED", "MEASURED")):
            self.assertTrue(check_transition(previous, next_state, "human"))

    def test_unknown_state_fails(self):
        self.assertTrue(check_transition("MADE_UP", "QA_CHECKED", "automation"))
        self.assertTrue(check_transition("MEASURED", "MADE_UP", "automation"))

    def test_all_legal_edges_follow_actor_rules(self):
        for source, targets in LEGAL_TRANSITIONS.items():
            for target in targets:
                self.assertEqual(check_transition(source, target, "human"), [],
                                 (source, target))
                if target in {"APPROVED", "ESTIMATOR_REVIEWED"}:
                    self.assertTrue(check_transition(source, target, "automation"))

    def test_no_unknown_legal_edges(self):
        self.assertTrue(all(source in STATES and target in STATES
                            for source, targets in LEGAL_TRANSITIONS.items()
                            for target in targets))


if __name__ == "__main__":
    unittest.main()
