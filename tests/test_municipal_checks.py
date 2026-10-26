"""Stdlib unit tests: python -m unittest discover -s tests -v"""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from validate_municipal_checks import REQUIRED_CHECKS, validate  # noqa: E402


class MunicipalRegisterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.example = json.loads(
            (ROOT / "examples" / "municipal_checks_synthetic.json").read_text(encoding="utf-8")
        )

    def test_example_is_open_not_invalid(self):
        errors, pending = validate(self.example)
        self.assertEqual(errors, [])
        self.assertEqual(set(pending), set(REQUIRED_CHECKS))

    def test_missing_municipal_check_fails(self):
        data = copy.deepcopy(self.example)
        data["checks"].pop()
        errors, _ = validate(data)
        self.assertTrue(any("missing required check" in e for e in errors))

    def test_source_without_date_is_not_evidence(self):
        data = copy.deepcopy(self.example)
        data["checks"][0].update(status="EVIDENCE_FOUND", source_ref="Municipal website")
        errors, _ = validate(data)
        self.assertTrue(any("source_checked_on" in e for e in errors))

    def test_ai_cannot_claim_human_clearance_by_omitting_reviewer(self):
        data = copy.deepcopy(self.example)
        data["checks"][0]["status"] = "HUMAN_CLEARED"
        errors, _ = validate(data)
        self.assertTrue(any("reviewed_by" in e for e in errors))
        self.assertTrue(any("source_ref" in e for e in errors))

    def test_n_a_requires_human_reason(self):
        data = copy.deepcopy(self.example)
        data["checks"][0].update(status="NOT_APPLICABLE", finding="")
        errors, _ = validate(data)
        self.assertTrue(any("finding" in e for e in errors))
        self.assertTrue(any("reviewed_on" in e for e in errors))

    def test_human_review_cannot_predate_latest_evidence(self):
        data = copy.deepcopy(self.example)
        data["checks"][0].update(
            status="HUMAN_CLEARED", authority="Fictional authority",
            source_ref="Official source, section 2", source_checked_on="2026-10-26",
            finding="Fictional review for test", responsible_party="GC",
            reviewed_by="Example Estimator", reviewed_on="2026-10-25",
        )
        errors, _ = validate(data)
        self.assertTrue(any("predates the source" in e for e in errors))

    def test_human_closed_register_passes_structure(self):
        data = copy.deepcopy(self.example)
        for check in data["checks"]:
            check.update(status="NOT_APPLICABLE", finding="Human-reviewed scope exclusion",
                         reviewed_by="Example Estimator", reviewed_on="2026-10-26")
        errors, pending = validate(data)
        self.assertEqual(errors, [])
        self.assertEqual(pending, [])

    def test_source_date_after_as_of_is_rejected(self):
        data = copy.deepcopy(self.example)
        data["checks"][0].update(source_ref="Official source", source_checked_on="2026-10-27")
        errors, _ = validate(data)
        self.assertTrue(any("later than project.checked_on" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
