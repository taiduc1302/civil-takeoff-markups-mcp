# Independent saved-PDF vector readback (research-stage)

`tools/vector_readback.py` inspects a **saved PDF** using PyMuPDF rather than reusing `tools/build_synthetic_sheet.py`'s generator variables. It prints JSON containing the local source SHA-256, exact zero-based page index, page label, rotation, MediaBox/CropBox, vector primitives and text blocks.

```bash
pip install pymupdf
python tools/vector_readback.py examples/synthetic_sheet.pdf > /tmp/synthetic-vector-readback.json
python -m unittest discover -s tests -v
```

**The key distinction:** a vector primitive in the PDF is not an approved takeoff line. A sheet can contain several visually plausible polylines (kerb, property, existing utility, leader). This tool does **not** select between them. Every report declares `feature_targeting_verified=false` and `scale_verified=false`. Do not feed the extracted PyMuPDF `y-down` coordinates straight into the Bluebeam MCP `y-up` payloads without a separately verified transform.

The report is local and read-only; no network, no Bluebeam modification, no automatic quantity. Preserve user PDFs in private local storage only; report JSON containing drawing geometry is also **not suitable for this public repository** unless synthetically generated. Limits protect against unbounded vector/text arrays.

This is a partial implementation of [Issue #4](https://github.com/taiduc1302/civil-takeoff-markups-mcp/issues/4). Remaining: robust crop/rotation/Space/viewport coordinate mapping, controlled scale, candidate targeting, semantic disambiguation, and a rendered overlay that can be independently reviewed. Neither a parsed line nor a matching schedule value establishes correct feature targeting.
