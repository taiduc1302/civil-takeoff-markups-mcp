"""Offline regression tests for synthetic markup generation and failure cases."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from place_markups import build  # noqa: E402
from validate_candidates import validate_candidates, parse_path  # noqa: E402


class CandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "examples" / "derived_markups.json").read_text(encoding="utf-8"))

    def test_synthetic_baseline_is_structurally_valid(self):
        self.assertEqual(validate_candidates(self.data), [])

    def test_frozen_current_candidate_counts(self):
        self.assertEqual({k: len(self.data[k]) for k in ("runs", "resto", "points", "qa")},
                         {"runs": 4, "resto": 4, "points": 8, "qa": 1})
        self.assertEqual(len(build(self.data)), 17)

    def test_payload_shape_is_stable_and_matches_expected_types(self):
        payload = build(self.data)
        self.assertEqual([p["properties"]["type"] for p in payload],
                         ["PolyLine"] * 4 + ["Polygon"] * 4 + ["Circle"] * 8 + ["PolyLine"])
        self.assertTrue(all(p["pageNumber"] == 1 for p in payload))
        self.assertTrue(all(set(p) == {"pageNumber", "properties", "shape"} for p in payload))
        self.assertEqual(payload[0]["properties"]["subject"], self.data["runs"][0]["subject"])
        self.assertEqual(payload[-1]["properties"]["subject"], self.data["qa"][0]["subject"])

    def test_path_coordinates_are_parsed_in_source_order(self):
        self.assertEqual(parse_path("M 1 2 L 3 4"), [(1.0, 2.0), (3.0, 4.0)])
        self.assertEqual(len(parse_path(self.data["resto"][0]["path"], closed=True)), 4)

    def test_duplicate_id_rejected_across_groups(self):
        item = copy.deepcopy(self.data)
        item["points"][0]["id"] = item["runs"][0]["id"]
        self.assertIn("duplicate ID", " ".join(validate_candidates(item)))

    def test_empty_subject_rejected(self):
        item = copy.deepcopy(self.data)
        item["runs"][0]["subject"] = ""
        self.assertIn("missing subject", " ".join(validate_candidates(item)))

    def test_bad_polyline_rejected(self):
        for path in ("M 0 0", "M 0 0 L 0 0", "M 0 0 L x 1", "M 0 0 L 1 1 H",
                     "L 0 0 L 1 1", "M 0 0 L 1 1 L NaN 2"):
            with self.subTest(path=path):
                item = copy.deepcopy(self.data)
                item["runs"][0]["path"] = path
                self.assertTrue(validate_candidates(item))

    def test_zero_area_polygon_rejected(self):
        item = copy.deepcopy(self.data)
        item["resto"][0]["path"] = "M 0 0 L 1 1 L 2 2 H"
        self.assertIn("zero-area polygon", " ".join(validate_candidates(item)))

    def test_rectangle_dimensions_rejected(self):
        item = copy.deepcopy(self.data)
        item["points"][0]["rect"] = "1 2 -3 4"
        self.assertIn("positive dimensions", " ".join(validate_candidates(item)))

    def test_invalid_page_rejected(self):
        for page in (0, -1, 1.5, True):
            with self.subTest(page=page):
                self.assertTrue(any("page" in p for p in validate_candidates(self.data, page=page)))

    def test_wrong_unit_rejected(self):
        item = copy.deepcopy(self.data)
        item["runs"][0]["unit"] = "ft"
        self.assertIn("unsupported unit", " ".join(validate_candidates(item)))
        item["runs"][0]["unit"] = "m2"
        self.assertIn("unexpected runs unit", " ".join(validate_candidates(item)))

    def test_unhashable_unit_is_rejected_without_crashing(self):
        for bad_unit in ([], {}, ["m"]):
            with self.subTest(bad_unit=bad_unit):
                item = copy.deepcopy(self.data)
                item["runs"][0]["unit"] = bad_unit
                self.assertIn("unsupported unit", " ".join(validate_candidates(item)))
                with self.assertRaises(ValueError):
                    build(item)

    def test_huge_schedule_number_is_rejected_without_overflow(self):
        item = copy.deepcopy(self.data)
        item["printed"]["S-M1"] = 10 ** 400
        self.assertIn("non-finite", " ".join(validate_candidates(item)))

    def test_schedule_nonfinite_rejected(self):
        item = copy.deepcopy(self.data)
        item["printed"]["S-M1"] = float("nan")
        self.assertIn("non-finite", " ".join(validate_candidates(item)))

    def test_qa_cannot_contribute_to_rollup(self):
        item = copy.deepcopy(self.data)
        item["qa"][0]["subject"] = "DUCT | QA-A | test"
        self.assertIn("DO NOT SUM", " ".join(validate_candidates(item)))

    def test_unknown_group_structure_rejected(self):
        item = copy.deepcopy(self.data)
        del item["runs"]
        self.assertIn("expected array", " ".join(validate_candidates(item)))


if __name__ == "__main__":
    unittest.main()
