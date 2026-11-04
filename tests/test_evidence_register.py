"""Pure offline contract tests. Never call Bluebeam or assert a real human identity."""
import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from validate_evidence_register import validate  # noqa: E402

ROW = {
    "markup_id": "synthetic-001", "page_index": 0, "page_label": "SYN-C-101",
    "source_sha256": "a" * 64, "source_revision": "A", "plan_id": "S-M1",
    "status": "AI_PROPOSED", "measurement_type": "Length", "unit": "m",
    "scale_resolved": False, "scale_verified": False,
}


def register(row=None):
    return {"schema_version": 1, "markups": [copy.deepcopy(row or ROW)]}


class EvidenceRegisterTests(unittest.TestCase):
    def test_proposed_requires_no_invented_measurement(self):
        self.assertEqual(validate(register()), ([], []))

    def test_measured_needs_native_saved_readback(self):
        d = register()
        d["markups"][0]["status"] = "MEASURED"
        errors, pending = validate(d)
        self.assertEqual(errors, [])
        self.assertTrue(any("readback" in m for m in pending))
        d["markups"][0].update(native_readback=True, computed_quantity=10.0)
        self.assertEqual(validate(d), ([], []))

    def test_qa_checked_needs_independent_scale_location_and_quantity(self):
        d = register()
        d["markups"][0].update(status="QA_CHECKED", native_readback=True, computed_quantity=10.0)
        errors, pending = validate(d)
        self.assertEqual(errors, [])
        self.assertTrue(any("scale" in m for m in pending))
        self.assertTrue(any("location" in m for m in pending))
        self.assertTrue(any("independent" in m for m in pending))
        d["markups"][0].update(scale_resolved=True, scale_verified=True,
                               scale_basis="synthetic 25m independent bar check",
                               visual_location_checked=True,
                               independent_evidence="synthetic plan schedule")
        self.assertEqual(validate(d), ([], []))

    def test_unverified_scale_blocks_qa(self):
        d = register()
        d["markups"][0].update(status="QA_CHECKED", native_readback=True, computed_quantity=10.0,
                               scale_resolved=True, scale_verified=False,
                               scale_basis="unspecified", visual_location_checked=True,
                               independent_evidence="synthetic schedule")
        self.assertIn("scale", " ".join(validate(d)[1]))

    def test_human_approval_needs_logged_review_but_does_not_authenticate(self):
        d = register()
        d["markups"][0].update(status="APPROVED", native_readback=True, computed_quantity=10.0,
                               scale_resolved=True, scale_verified=True,
                               scale_basis="independent synthetic bar",
                               visual_location_checked=True,
                               independent_evidence="synthetic schedule")
        self.assertTrue(any("human" in s for s in validate(d)[1]))
        d["markups"][0]["human_review"] = {
            "reviewer": "Fictional Estimator", "reviewed_on": "2026-11-02",
            "decision_ref": "SYN-REVIEW-001", "decision": "APPROVE",
        }
        self.assertEqual(validate(d), ([], []))

    def test_qa_only_measurement_is_not_eligible_for_approval(self):
        d = register()
        d["markups"][0].update(status="QA_CHECKED", native_readback=True, computed_quantity=1.0,
                               scale_resolved=True, scale_verified=True, scale_basis="independent",
                               visual_location_checked=True, independent_evidence="synthetic",
                               do_not_sum=True)
        self.assertIn("QA-only", " ".join(validate(d)[1]))

    def test_same_native_id_and_page_twice_fails(self):
        d = register()
        d["markups"].append(copy.deepcopy(d["markups"][0]))
        self.assertIn("duplicate", " ".join(validate(d)[0]))

    def test_wrong_hash_or_page_fails(self):
        d = register()
        d["markups"][0]["source_sha256"] = "not-a-hash"
        d["markups"][0]["page_index"] = -1
        errors, _ = validate(d)
        self.assertTrue(any("sha256" in e for e in errors))
        self.assertTrue(any("page_index" in e for e in errors))

    def test_malformed_review_and_unit_fail_closed_not_crash(self):
        d = register()
        d["markups"][0].update(status="APPROVED", unit=["m"], human_review=None)
        errors, pending = validate(d)
        self.assertTrue(any("unit" in e for e in errors))
        self.assertTrue(any("human" in p for p in pending))

    def test_malformed_status_types_are_rejected_without_crashing(self):
        for bad_status in ([], {}, 7, None):
            with self.subTest(status=bad_status):
                d = register()
                d["markups"][0]["status"] = bad_status
                errors, pending = validate(d)
                self.assertIn("status", " ".join(errors))
                self.assertEqual(pending, [])

    def test_unsupported_schema_rejected(self):
        d = register()
        d["schema_version"] = 999
        self.assertIn("schema_version", " ".join(validate(d)[0]))


if __name__ == "__main__":
    unittest.main()
