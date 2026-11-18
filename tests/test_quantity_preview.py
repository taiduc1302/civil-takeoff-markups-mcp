"""Guardrails for synthetic preview only, never actual bid quantities."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from reconcile_quantity_preview import preview_quantities

SOURCE = {"sha256": "a" * 64, "revision": "A"}


def line(name, quantity=10.0):
    return {"schema_version": 1, "markup_id": name, "plan_id": "SYN-PLAN",
            "source_sha256": "a" * 64, "source_revision": "A",
            "status": "QA_CHECKED", "measurement_type": "Length", "unit": "m",
            "scale_verified": True, "scale_basis": "independent SYN dimension",
            "visual_location_checked": True, "independent_evidence": "synthetic schedule and preview",
            "computed_quantity": quantity, "bid_item_id": "SYN-PIPE",
            "native_readback": {"saved_pdf_sha256": "b" * 64, "native_markup_id": name,
                                "source_pdf_sha256": "a" * 64, "unit": "m", "quantity": quantity},
            "do_not_sum": False}


def doc(*rows):
    return {"schema_version": 1, "markups": list(rows)}


class PreviewTests(unittest.TestCase):
    def test_two_good_rows_preview_only_never_authorized(self):
        r = preview_quantities(doc(line("L-1"), line("L-2", 15)), SOURCE)
        self.assertEqual(r["result"], "PREVIEW_ONLY")
        self.assertEqual(r["preview_totals"][0]["quantity"], 25)
        self.assertFalse(r["commercial_handoff_authorized"])
        self.assertFalse(r["human_review_authenticated"])

    def test_qa_only_is_excluded_not_summed(self):
        qa = line("QA")
        qa.update(do_not_sum=True, subject="QA CHECK - DO NOT SUM")
        r = preview_quantities(doc(line("L-1"), qa), SOURCE)
        self.assertEqual(r["preview_totals"][0]["quantity"], 10)
        self.assertEqual(len(r["excluded"]), 1)

    def test_stale_revision_blocks_all_other_totals(self):
        stale = line("L-2")
        stale["source_revision"] = "B"
        r = preview_quantities(doc(line("L-1"), stale), SOURCE)
        self.assertEqual(r["result"], "BLOCKED")
        self.assertEqual(r["preview_totals"], [])
        self.assertIn("stale", " ".join(r["unresolved"]))

    def test_duplicate_contribution_blocks_all(self):
        r = preview_quantities(doc(line("L-1"), line("L-1")), SOURCE)
        self.assertEqual(r["preview_totals"], [])
        self.assertIn("duplicate", " ".join(r["unresolved"]))

    def test_missing_mapping_and_unverified_location_block(self):
        bad = line("L-2")
        bad["bid_item_id"] = ""
        bad["visual_location_checked"] = False
        r = preview_quantities(doc(line("L-1"), bad), SOURCE)
        self.assertEqual(r["result"], "BLOCKED")
        self.assertIn("mapping", " ".join(r["unresolved"]))

    def test_mixed_units_same_bid_item_block(self):
        area = line("A-1", 25)
        area.update(measurement_type="Area", unit="m2")
        area["native_readback"]["unit"] = "m2"
        r = preview_quantities(doc(line("L-1"), area), SOURCE)
        self.assertEqual(r["result"], "BLOCKED")
        self.assertIn("mixed units", " ".join(r["unresolved"]))

    def test_bool_native_receipt_no_longer_suffices(self):
        bad = line("L-1")
        bad["native_readback"] = True
        r = preview_quantities(doc(bad), SOURCE)
        self.assertEqual(r["preview_totals"], [])
        self.assertIn("readback", " ".join(r["unresolved"]))

    def test_forged_approval_is_not_authentication(self):
        approved = line("L-1")
        approved["status"] = "APPROVED"
        approved["human_review"] = {"reviewer": "Someone", "decision": "APPROVE"}
        r = preview_quantities(doc(approved), SOURCE)
        self.assertEqual(r["result"], "PREVIEW_ONLY")
        self.assertFalse(r["human_review_authenticated"])
        self.assertFalse(r["commercial_handoff_authorized"])

    def test_nonfinite_quantities_fail_closed(self):
        for val in (float("nan"), float("inf"), -1, None, True):
            with self.subTest(value=val):
                bad = line("L-1")
                bad["computed_quantity"] = val
                r = preview_quantities(doc(bad), SOURCE)
                self.assertEqual(r["result"], "BLOCKED")

    def test_inconsistent_receipt_rejected(self):
        bad = line("L-2")
        bad["native_readback"]["quantity"] = 50
        r = preview_quantities(doc(line("L-1"), bad), SOURCE)
        self.assertEqual(r["preview_totals"], [])
        self.assertIn("receipt", " ".join(r["unresolved"]))

    def test_malformed_identity_and_flags_refuse_without_crash(self):
        bad = line("L-1")
        bad["plan_id"] = []
        bad["do_not_sum"] = "false"
        bad["status"] = []
        r = preview_quantities(doc(bad), SOURCE)
        self.assertEqual(r["result"], "BLOCKED")
        self.assertEqual(r["preview_totals"], [])
        self.assertIn("identity", " ".join(r["unresolved"]))


if __name__ == "__main__":
    unittest.main()
