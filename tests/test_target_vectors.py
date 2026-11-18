"""Synthetic geometry targeting and non-destructive preview tests."""
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from target_vectors import TargetRefusal, choose_line, preview_line


class TargetVectorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.pdf = Path(self.tmp.name) / "synthetic.pdf"
        self.png = Path(self.tmp.name) / "overlay.png"
        doc = fitz.open()
        page = doc.new_page(width=300, height=180)
        page.draw_line((20, 20), (120, 20))
        page.draw_line((20, 40), (120, 40))  # decoy
        page.insert_text((25, 15), "SYNTHETIC")
        doc.save(self.pdf)
        doc.close()
        self.report = self.read_report()

    def read_report(self):
        with fitz.open(self.pdf) as doc:
            pg = doc[0]
            vectors = []
            for i, drawing in enumerate(pg.get_drawings()):
                for j, item in enumerate(drawing["items"]):
                    if item[0] == "l":
                        vectors.append({"type": "line", "start": list(item[1]), "end": list(item[2]),
                                        "drawing_index": i, "item_index": j})
        return {"coordinate_system": "pymupdf-unrotated-page-points-y-down",
                "source_sha256": hashlib.sha256(self.pdf.read_bytes()).hexdigest(),
                "page_index": 0, "page_label": "1", "vectors": vectors}

    def test_selects_exact_unique_feature_not_nearby_decoy(self):
        sel = choose_line(self.report, (120, 20), (20, 20))
        self.assertEqual(sel["start"], [20., 20.])
        self.assertLessEqual(sel["max_endpoint_deviation_pt"], 1.0)
        self.assertFalse(sel["feature_targeting_verified"])
        self.assertEqual(sel["status"], "AI_PROPOSED")
        self.assertNotEqual(sel["geometry_hash"], "")

    def test_refuses_wrong_feature_and_ambiguous_candidates(self):
        with self.assertRaisesRegex(TargetRefusal, "found 0"):
            choose_line(self.report, (20, 70), (120, 70))
        dupe = dict(self.report)
        dupe["vectors"] = self.report["vectors"] + [self.report["vectors"][0]]
        with self.assertRaisesRegex(TargetRefusal, "found 2"):
            choose_line(dupe, (20, 20), (120, 20))

    def test_bad_coordinate_or_tolerance_fails(self):
        with self.assertRaises(TargetRefusal):
            choose_line(self.report, (20, 20), (20, 20))
        with self.assertRaises(TargetRefusal):
            choose_line(self.report, (20, float("nan")), (120, 20))
        with self.assertRaises(TargetRefusal):
            choose_line(self.report, (20, 20), (120, 20), 25)
        wrong = dict(self.report, coordinate_system="pdf-origin-y-up")
        with self.assertRaises(TargetRefusal):
            choose_line(wrong, (20, 20), (120, 20))

    def test_preview_renders_png_and_never_saves_pdf(self):
        before = self.pdf.read_bytes()
        sel = choose_line(self.report, (20, 20), (120, 20))
        out = preview_line(self.pdf, sel, self.png)
        self.assertTrue(self.png.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertFalse(out["visual_location_checked"])
        self.assertEqual(self.pdf.read_bytes(), before)
        with self.assertRaisesRegex(TargetRefusal, "must be new"):
            preview_line(self.pdf, sel, self.png)

    def test_stale_source_rejects_preview(self):
        sel = choose_line(self.report, (20, 20), (120, 20))
        self.pdf.write_bytes(self.pdf.read_bytes() + b"\n% updated")
        with self.assertRaisesRegex(TargetRefusal, "SHA changed"):
            preview_line(self.pdf, sel, self.png)

    def test_rotated_pdf_remains_unverified_preview(self):
        doc = fitz.open(self.pdf)
        doc[0].set_rotation(90)
        rotated = Path(self.tmp.name) / "rotated.pdf"
        doc.save(rotated)
        doc.close()
        with fitz.open(rotated) as doc:
            self.assertEqual(doc[0].rotation, 90)
        report = self.read_report()
        # Selection geometry must always refer to the same saved source version.
        report["source_sha256"] = hashlib.sha256(rotated.read_bytes()).hexdigest()
        sel = choose_line(report, (20, 20), (120, 20))
        out = preview_line(rotated, sel, self.png)
        self.assertEqual(out["status"], "PREVIEW_ONLY_REVIEW_REQUIRED")


if __name__ == "__main__":
    unittest.main()
