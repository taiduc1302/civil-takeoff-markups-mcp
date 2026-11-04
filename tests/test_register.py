"""Existing legacy traceability-string validator regression tests.

The legacy parser validates structure only. It is not an authoritative saved
register and cannot authenticate a human reviewer.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from validate_register import validate, parse_comment  # noqa: E402

GOOD = ("PLAN_ID=S-M1;SHEET=C-101;SOURCE=SYN-U-0002 rev A;BIDITEM=33.01;"
        "STA=0+005.00-0+078.40;STATUS=MEASURED;SCALE_VERIFIED=Y (independent);"
        "CREATED_BY=MCP;NOTE=synthetic fixture")


class LegacyRegisterTests(unittest.TestCase):
    def test_baseline_valid_structure(self):
        self.assertEqual(validate(GOOD), [])

    def test_missing_field_fails(self):
        self.assertIn("missing or empty", " ".join(validate(GOOD.replace("PLAN_ID=S-M1;", ""))))

    def test_invalid_status_rejected(self):
        self.assertTrue(validate(GOOD.replace("STATUS=MEASURED", "STATUS=READY")))

    def test_unknown_creator_rejected(self):
        self.assertTrue(validate(GOOD.replace("CREATED_BY=MCP", "CREATED_BY=ROBOT")))

    def test_invalid_scale_indicator_rejected(self):
        self.assertTrue(validate(GOOD.replace("SCALE_VERIFIED=Y (independent)", "SCALE_VERIFIED=MAYBE")))

    def test_legacy_parser_preserves_equals_in_note(self):
        self.assertEqual(parse_comment(GOOD + ";NOTE=a=b")["NOTE"], "a=b")

    def test_known_limit_legacy_y_or_n_is_not_qa_evidence(self):
        # A future gated register (#3) must refuse QA_CHECKED with SCALE_VERIFIED=N;
        # do not accidentally confuse current schema-only validator with that gate.
        self.assertEqual(validate(GOOD.replace("STATUS=MEASURED", "STATUS=QA_CHECKED")
                                  .replace("SCALE_VERIFIED=Y (independent)",
                                           "SCALE_VERIFIED=N")), [])


if __name__ == "__main__":
    unittest.main()
