#!/usr/bin/env python3
"""Turn derived geometry into add_markup payloads for an MCP connector.

    python tools/place_markups.py [examples/derived_markups.json]

Prints one JSON array ready to pass as the `markups` argument. Nothing is sent
anywhere: this script has no network and no connector dependency. Review the
payload, then let your agent send it.

Colours and labels are conventions, not requirements. Substitute your own
office palette; keep the subject pattern (see docs/traceability-contract.md).
"""
import json
import os
import sys

STYLE = {
    "duct":      {"type": "PolyLine", "intent": "Perimeter", "label": "Duct", "color": "#1A59D9", "linewidth": 4, "opacity": 0.6},
    "duct_rce":  {"type": "PolyLine", "intent": "Perimeter", "label": "Duct reinforced", "color": "#D91A1A", "linewidth": 4, "opacity": 0.6},
    "resto":     {"type": "Polygon", "intent": "Area", "label": "Restoration", "color": "#7A2DB3", "colorfill": "#7A2DB3", "linewidth": 0.75, "opacityfill": 0.25},
    "point":     {"type": "Circle", "linewidth": 2},
    "qa":        {"type": "PolyLine", "intent": "Perimeter", "label": "QA CHECK", "color": "#00B050", "linewidth": 1.5, "linestyle": "dashed1"},
}


def markup(page, style, subject, shape_key, shape_value, **over):
    props = dict(STYLE[style], subject=subject, **over)
    return {"pageNumber": page, "properties": props, "shape": {shape_key: shape_value}}


def build(mk, page=1):
    out = []
    for r in mk["runs"]:
        out.append(markup(page, "duct_rce" if "RCE" in r["id"] else "duct", r["subject"], "path", r["path"]))
    for r in mk["resto"]:
        out.append(markup(page, "resto", r["subject"], "path", r["path"]))
    for p in mk["points"]:
        out.append(markup(page, "point", p["subject"], "rect", p["rect"],
                          label=p["subject"].split(" | ")[0].title(), color=p["color"]))
    for q in mk["qa"]:
        out.append(markup(page, "qa", q["subject"], "path", q["path"]))
    return out


if __name__ == "__main__":
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "examples", "derived_markups.json")
    mk = json.load(open(src, encoding="utf-8"))
    payload = build(mk)
    print(json.dumps(payload, indent=1))
    print("\n%d markups. Set the page scale to %s first, then send these, then read them back."
          % (len(payload), mk.get("scale", "the sheet's scale")), file=sys.stderr)
