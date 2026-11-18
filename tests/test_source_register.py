"""Local source SHA/revision/page readback, never an approval test."""
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from verify_source_register import verify_pdf_source


class SourceRegisterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.pdf = Path(self.tmp.name) / "synthetic.pdf"
        doc = fitz.open()
        doc.new_page(width=400, height=300)
        doc.set_page_labels([{"startpage": 0, "prefix": "SYN-C-", "style": "D", "firstpagenum": 101}])
        doc.save(self.pdf)
        doc.close()
        self.hash = hashlib.sha256(self.pdf.read_bytes()).hexdigest()
        self.row = {"source_sha256": self.hash, "source_revision": "A", "page_index": 0, "page_label": "SYN-C-101"}
        self.register = {"schema_version": 1, "markups": [self.row]}

    def test_identical_bytes_page_and_revision_match_without_approval(self):
        r = verify_pdf_source(self.register, self.pdf, "A")
        self.assertTrue(r["source_match"])
        self.assertEqual(r["matched"][0]["page_label"], "SYN-C-101")
        self.assertEqual(r["matched"][0]["rotation"], 0)
        self.assertFalse(r["commercial_handoff_approved"])
        self.assertFalse(r["reviewer_authenticated"])
        self.assertFalse(r["scale_verified"])

    def test_revised_bytes_block_old_markup(self):
        self.pdf.write_bytes(self.pdf.read_bytes() + b"\n% synthetic revision B")
        r = verify_pdf_source(self.register, self.pdf, "A")
        self.assertFalse(r["source_match"])
        self.assertIn("SHA-256", " ".join(r["unresolved"]))

    def test_mismatched_revision_block(self):
        r = verify_pdf_source(self.register, self.pdf, "B")
        self.assertFalse(r["source_match"])
        self.assertIn("revision", " ".join(r["unresolved"]))

    def test_wrong_page_label_and_page_index_block(self):
        self.row["page_label"] = "SYN-C-999"
        self.assertIn("page label", " ".join(verify_pdf_source(self.register, self.pdf, "A")["unresolved"]))
        self.row["page_index"] = 99
        self.assertIn("page index", " ".join(verify_pdf_source(self.register, self.pdf, "A")["unresolved"]))

    def test_rotated_page_reports_real_metadata_no_target_qa(self):
        doc = fitz.open(self.pdf)
        doc[0].set_rotation(90)
        doc.save(self.pdf.with_name("rotated.pdf"))
        doc.close()
        rotated = self.pdf.with_name("rotated.pdf")
        self.row["source_sha256"] = hashlib.sha256(rotated.read_bytes()).hexdigest()
        r = verify_pdf_source(self.register, rotated, "A")
        self.assertEqual(r["matched"][0]["rotation"], 90)
        self.assertFalse(r["feature_targeting_verified"])

    def test_malformed_or_missing_source_fails(self):
        with self.assertRaises(ValueError):
            verify_pdf_source({"schema_version": 2, "markups": []}, self.pdf, "A")
        with self.assertRaises(ValueError):
            verify_pdf_source(self.register, self.pdf.with_name("missing.pdf"), "A")
        with self.assertRaises(ValueError):
            verify_pdf_source(self.register, self.pdf, "")


if __name__ == "__main__":
    unittest.main()
