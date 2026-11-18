"""Offline synthetic-only Open PDF Studio bridge tests; no vendor app or paid API."""
import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from open_pdf_studio_adapter import AdapterRefusal, execute_synthetic, plan_operations


class FakeAnnotations:
    def __init__(self, database):
        self.database = database

    def add(self, kind, page, **props):
        annotation_id = f"native-{len(self.database) + 1}"
        self.database[annotation_id] = {"id": annotation_id, "type": kind, "page": page,
                                        "measureText": "10.00 m" if kind != "count" else ""}
        return annotation_id

    def get(self, native_id):
        return self.database.get(native_id)


class FakeTools:
    def set_measure_scale(self, ppu, unit):
        if ppu <= 0 or unit != "m":
            raise RuntimeError("bad scale")


class FakeDoc:
    def __init__(self, store, path):
        self.store, self.path = store, path
        self.annotations, self.tools = FakeAnnotations(store), FakeTools()

    def save(self, path):
        Path(path).write_bytes(Path(self.path).read_bytes() + b"\n% synthetic annotations")

    def close(self, save=False):
        if save:
            raise AssertionError("test must not save in place")


class FakeApp:
    def __init__(self, store):
        self.store = store

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def open(self, path):
        return FakeDoc(self.store, path)


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.source = Path(self.tmp.name) / "synthetic_plan.pdf"
        self.target = Path(self.tmp.name) / "synthetic_marked.pdf"
        self.source.write_bytes(b"%PDF-1.7\n% synthetic PDF placeholder")
        self.plan = {
            "synthetic_fixture": True, "source_pdf": str(self.source), "output_pdf": str(self.target),
            "source_sha256": hashlib.sha256(self.source.read_bytes()).hexdigest(),
            "source_revision": "A", "page_index": 0, "page_label": "SYN-C-101",
            "coordinate_space": "opds-native-page-points-at-100-percent",
            "scale_reference": {"page_points": [[0, 0], [100, 0]], "known_length": 10,
                                "unit": "m", "basis": "synthetic independent 10 m drawn dimension"},
            "features": [
                {"id": "PIPE-1", "kind": "Length", "points": [[50, 50], [150, 50]], "do_not_sum": False},
                {"id": "EXC-1", "kind": "Area", "points": [[0, 0], [50, 0], [50, 10], [0, 10]], "do_not_sum": False},
                {"id": "MH-1", "kind": "Count", "points": [[50, 50]], "do_not_sum": False},
                {"id": "QA-1", "kind": "Length", "points": [[0, 1], [10, 1]], "do_not_sum": True},
            ],
        }

    def test_dry_run_produces_one_based_page_and_vendor_types_no_approval(self):
        ops = plan_operations(self.plan)
        self.assertEqual(ops["pixels_per_unit"], 10)
        self.assertEqual([a["type"] for a in ops["actions"]],
                         ["measureDistance", "measureArea", "count", "measureDistance"])
        self.assertTrue(all(a["page"] == 1 for a in ops["actions"]))
        self.assertFalse(ops["scale_verified"])
        self.assertFalse(self.target.exists())

    def test_save_and_reopen_mock_not_an_approval(self):
        ops = plan_operations(self.plan)
        result = execute_synthetic(ops, lambda: FakeApp({}))
        self.assertEqual(result["status"], "AI_PROPOSED")
        self.assertFalse(result["readback"]["MH-1"]["numeric_quantity_available"])
        self.assertTrue(result["review_required"])
        self.assertFalse(result["quantity_eligible_for_bax"])
        self.assertIsNone(result["human_review"])
        self.assertEqual(len(result["readback"]), 4)
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(), ops["source_sha256"])
        with self.assertRaisesRegex(AdapterRefusal, "already exists"):
            execute_synthetic(ops, lambda: FakeApp({}))

    def test_refuse_wrong_source_revision_and_output_collision(self):
        variants = []
        v = copy.deepcopy(self.plan); v["source_sha256"] = "a" * 64; variants.append(v)
        v = copy.deepcopy(self.plan); v["source_revision"] = ""; variants.append(v)
        v = copy.deepcopy(self.plan); v["output_pdf"] = str(self.source); variants.append(v)
        v = copy.deepcopy(self.plan); v["synthetic_fixture"] = False; variants.append(v)
        for v in variants:
            with self.subTest(v=v):
                with self.assertRaises(AdapterRefusal):
                    plan_operations(v)

    def test_refuse_wrong_coordinates_scale_bad_geometry_duplicates(self):
        variants = []
        v = copy.deepcopy(self.plan); v["coordinate_space"] = "pymupdf-y-down"; variants.append(v)
        v = copy.deepcopy(self.plan); v["scale_reference"]["known_length"] = 0; variants.append(v)
        v = copy.deepcopy(self.plan); v["features"][0]["points"] = [[0, 0], [0, 0]]; variants.append(v)
        v = copy.deepcopy(self.plan); v["features"][1]["points"] = [[0, 0], [1, 1], [2, 2]]; variants.append(v)
        v = copy.deepcopy(self.plan); v["features"][1]["id"] = "PIPE-1"; variants.append(v)
        v = copy.deepcopy(self.plan); v["features"][0]["do_not_sum"] = None; variants.append(v)
        v = copy.deepcopy(self.plan); v["features"][0]["points"][1][0] = float("nan"); variants.append(v)
        v = copy.deepcopy(self.plan); v["page_index"] = True; variants.append(v)
        v = copy.deepcopy(self.plan); v["features"][0]["kind"] = []; variants.append(v)
        v = copy.deepcopy(self.plan); v["scale_reference"]["unit"] = []; variants.append(v)
        for v in variants:
            with self.subTest(v=repr(v)[-120:]):
                with self.assertRaises(AdapterRefusal):
                    plan_operations(v)

    def test_source_modified_between_preflight_and_vendor_write(self):
        ops = plan_operations(self.plan)
        self.source.write_bytes(self.source.read_bytes() + b"changed")
        with self.assertRaisesRegex(AdapterRefusal, "source changed"):
            execute_synthetic(ops, lambda: FakeApp({}))
        self.assertFalse(self.target.exists())

    def test_nonexistent_native_readback_fails_closed(self):
        class MissingReadback(FakeAnnotations):
            def get(self, native_id):
                return None
        class BadDoc(FakeDoc):
            def __init__(self, store, path):
                super().__init__(store, path)
                self.annotations = MissingReadback(store)
        class BadApp(FakeApp):
            def open(self, path):
                return BadDoc(self.store, path)
        with self.assertRaisesRegex(AdapterRefusal, "saved readback missing"):
            execute_synthetic(plan_operations(self.plan), lambda: BadApp({}))


    def test_numeric_native_measurement_still_needs_independent_qa(self):
        plan = copy.deepcopy(self.plan)
        plan["features"] = plan["features"][:1]
        class NumericAnnotations(FakeAnnotations):
            def add(self, kind, page, **props):
                native_id = super().add(kind, page, **props)
                self.database[native_id].update(measureValue=10.0, measureUnit="m")
                return native_id
        class NumericDoc(FakeDoc):
            def __init__(self, store, path):
                super().__init__(store, path)
                self.annotations = NumericAnnotations(store)
        class NumericApp(FakeApp):
            def open(self, path):
                return NumericDoc(self.store, path)
        result = execute_synthetic(plan_operations(plan), lambda: NumericApp({}))
        self.assertEqual(result["status"], "MEASURED")
        self.assertTrue(result["review_required"])
        self.assertFalse(result["quantity_eligible_for_bax"])
        self.assertEqual(result["readback"]["PIPE-1"]["quantity"], 10)

    def test_native_type_mismatch_refused(self):
        class WrongTypeAnnotations(FakeAnnotations):
            def get(self, native_id):
                row = super().get(native_id)
                return dict(row, type="line") if row else None
        class WrongTypeDoc(FakeDoc):
            def __init__(self, store, path):
                super().__init__(store, path)
                self.annotations = WrongTypeAnnotations(store)
        class WrongTypeApp(FakeApp):
            def open(self, path):
                return WrongTypeDoc(self.store, path)
        with self.assertRaisesRegex(AdapterRefusal, "type changed"):
            execute_synthetic(plan_operations(self.plan), lambda: WrongTypeApp({}))


if __name__ == "__main__":
    unittest.main()
