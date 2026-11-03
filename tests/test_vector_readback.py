"""Independent saved-PDF vector readback; synthetic data only."""
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from vector_readback import inspect_pdf  # noqa: E402


class VectorReadbackTests(unittest.TestCase):
    def test_independently_reopen_saved_pdf_and_extract_vectors(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "synthetic.pdf"
            doc = fitz.open()
            page = doc.new_page(width=500, height=300)
            page.draw_line(fitz.Point(40, 50), fitz.Point(140, 50))
            page.draw_line(fitz.Point(40, 75), fitz.Point(140, 75))  # competing feature
            page.insert_text(fitz.Point(50, 30), "SYNTHETIC DESIGN 100")
            doc.save(path)
            doc.close()

            result = inspect_pdf(path)
            self.assertEqual(result["source_sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertFalse(result["feature_targeting_verified"])
            self.assertFalse(result["scale_verified"])
            lines = [x for x in result["vectors"] if x["type"] == "line"]
            self.assertGreaterEqual(len(lines), 2)
            self.assertIn(
                {"type": "line", "start": [40.0, 50.0], "end": [140.0, 50.0],
                 "drawing_index": 0, "item_index": 0}, lines
            )
            self.assertTrue(any("SYNTHETIC DESIGN" in x["text"] for x in result["text_blocks"]))
            self.assertEqual(result["coordinate_system"], "pymupdf-unrotated-page-points-y-down")
            with self.assertRaises(ValueError):
                inspect_pdf(path, page_index=1)
            with self.assertRaises(ValueError):
                inspect_pdf(path, max_items=1)

    def test_rotation_reported_not_auto_transformed_to_mcp(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rotated.pdf"
            doc = fitz.open()
            page = doc.new_page(width=400, height=300)
            page.set_rotation(90)
            doc.save(path)
            doc.close()
            value = inspect_pdf(path)
            self.assertEqual(value["rotation_degrees"], 90)
            self.assertFalse(value["scale_verified"])


if __name__ == "__main__":
    unittest.main()
