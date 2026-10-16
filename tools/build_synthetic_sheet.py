"""Synthetic training sheet v2: linework ONLY (no markups). True 1:500 plan, 1:100 vertical profile.
Every name, number, station and elevation is invented. Also writes markups_v2.json: the geometry an
agent would derive from this sheet's own vector content, in PDF space (origin lower-left, points)."""
import json
import math
import os

import fitz

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples")
W, H = 2448, 1584
K = 72 / 12.7            # 1:500  -> points per metre
KV = 72 / 2.54           # 1:100  -> points per metre (profile vertical)
X0, Y0 = 210.0, 560.0    # plan origin (sta 0+000 on the duct), fitz space (y down)
PX0, PY0, E0 = 210.0, 1380.0, 70.0   # profile origin at elevation 70.00

ALIGN = [(0.0, 0.0), (95.0, 0.0), (175.0, 15.9), (250.0, 0.98)]
CUM = [0.0]
for a, b in zip(ALIGN, ALIGN[1:]):
    CUM.append(CUM[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
TOTAL = CUM[-1]


def P(x, y):
    return fitz.Point(X0 + K * x, Y0 - K * y)


def seg_of(s):
    for i in range(len(ALIGN) - 1):
        if s <= CUM[i + 1] or i == len(ALIGN) - 2:
            return i


def at(s, d=0.0):
    """Point at station s, offset d metres to the left of the direction of travel."""
    i = seg_of(s)
    a, b = ALIGN[i], ALIGN[i + 1]
    L = CUM[i + 1] - CUM[i]
    ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    t = s - CUM[i]
    return (a[0] + ux * t - uy * d, a[1] + uy * t + ux * d)


def ang(s):
    i = seg_of(s)
    a, b = ALIGN[i], ALIGN[i + 1]
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


def offset_line(s1, s2, d):
    """Mitred offset of the alignment between two stations."""
    pts = [at(s1, d)]
    for i in range(1, len(ALIGN) - 1):
        if s1 < CUM[i] < s2:
            a1, a2 = math.radians(ang(CUM[i] - 0.01)), math.radians(ang(CUM[i] + 0.01))
            half = (a2 - a1) / 2
            bis = a1 + half + math.pi / 2
            m = d / math.cos(half)
            pts.append((ALIGN[i][0] + m * math.cos(bis), ALIGN[i][1] + m * math.sin(bis)))
    pts.append(at(s2, d))
    return pts


def sta(s):
    return "%d+%06.2f" % (int(s // 1000), s % 1000)


GREY, LIGHT, RED, BLK = (0.35, 0.35, 0.35), (0.62, 0.62, 0.62), (0.8, 0.05, 0.05), (0, 0, 0)
doc = fitz.open()
pg = doc.new_page(width=W, height=H)
sh = pg.new_shape()


def pline(pts, width=0.7, color=BLK, dashes=None, close=False):
    sh.draw_polyline([P(*p) for p in pts])
    sh.finish(width=width, color=color, dashes=dashes, closePath=close)


def text(x, y, s, size=7, color=BLK, rot=0.0, font="helv"):
    pt = P(x, y)
    pg.insert_text(pt, s, fontsize=size, color=color, fontname=font,
                   morph=(pt, fitz.Matrix(-rot)) if rot else None)


# ---- sheet frame and right-hand strip ----
sh.draw_rect(fitz.Rect(36, 36, W - 36, H - 36)); sh.finish(width=2)
sh.draw_line(fitz.Point(1950, 36), fitz.Point(1950, H - 36)); sh.finish(width=1.2)

# ---- PLAN ----
S0, S1 = 0.0, TOTAL
for d, w, c, dash in ((8.5, 1.1, BLK, None), (-1.5, 1.1, BLK, None),          # curbs
                      (10.5, 0.6, GREY, None), (-3.5, 0.6, GREY, None),        # back of walk
                      (13.0, 0.9, BLK, "[14 4 3 4] 0"), (-6.0, 0.9, BLK, "[14 4 3 4] 0"),  # property line
                      (3.5, 0.5, GREY, "[18 6] 0"),                            # road centreline
                      (5.6, 0.6, LIGHT, "[10 3 2 3] 0"), (-2.6, 0.6, LIGHT, "[4 3] 0")):   # ex. water, ex. gas
    pline(offset_line(S0, S1, d), w, c, dash)
pline(offset_line(S0, S1, 0.0), 1.0, BLK, "[5 3] 0")                           # proposed duct (design line)

for s in range(0, 251, 5):                                                       # stationing
    big = s % 20 == 0
    pline([at(s, -0.6 if not big else -1.1), at(s, 0.6 if not big else 1.1)], 0.5)
    if big:
        x, y = at(s, -9.2)
        text(x, y, sta(s), 6.5, rot=ang(s))
for s, side, lot in ((12, 1, 101), (37, 1, 102), (62, 1, 103), (88, 1, 104), (150, 1, 106), (178, 1, 107), (206, 1, 108), (232, 1, 109),
                     (20, -1, 201), (48, -1, 202), (76, -1, 203), (108, -1, 204), (140, -1, 205), (172, -1, 206), (204, -1, 207), (236, -1, 208)):
    d0 = 13.0 if side > 0 else -6.0
    pline([at(s, d0), at(s, d0 + side * 34)], 0.5, GREY)
    x, y = at(s + 9, d0 + side * 20)
    text(x, y, "LOT %d" % lot, 7, GREY, rot=ang(s))
    x, y = at(s + 7, d0 + side * 15)
    text(x, y, "PLAN SYN-%03d" % (lot // 100), 5.5, GREY, rot=ang(s))
# side street ROAD B (north side)
for s in (112.0, 128.0):
    pline([at(s, 8.5), at(s, 47)], 1.1)
    pline([at(s + (-2 if s < 120 else 2), 13.0), at(s + (-2 if s < 120 else 2), 47)], 0.9, BLK, "[14 4 3 4] 0")
x, y = at(117.5, 30); text(x, y, "ROAD B", 12, GREY, rot=ang(118) + 90)
x, y = at(30, 2.2); text(x, y, "ROAD A", 13, GREY)
x, y = at(205, 2.2); text(x, y, "ROAD A", 13, GREY, rot=ang(205))
x, y = at(14, 6.0); text(x, y, "EX. 250 W", 5.5, LIGHT)
x, y = at(14, -3.2); text(x, y, "EX. 114 G", 5.5, LIGHT)

CROSS = [(40.0, "250 W", 77.55, "ABOVE"), (120.0, "114 G", 78.05, "ABOVE"), (157.0, "300 STM", 77.20, "ABOVE"), (205.0, "200 SAN", 75.10, "BELOW")]
for s, name, _, _ in CROSS:
    pline([at(s - 2, -6.0), at(s + 2, 13.0)], 0.6, LIGHT, "[8 3 2 3] 0")
    x, y = at(s + 3.0, 11.0); text(x, y, name, 5.5, LIGHT, rot=ang(s) + 78)
VAULTS = [(81.2, "V-01"), (167.5, "V-02")]
for s, name in VAULTS:
    pline([at(s - 2.175, 1.265), at(s + 2.175, 1.265), at(s + 2.175, -1.265), at(s - 2.175, -1.265)], 1.2, close=True)
    x, y = at(s - 14, -13.5); text(x, y, "%s PRECAST VAULT 4.35 x 2.53" % name, 6.5, rot=ang(s))
    x, y = at(s - 14, -16.0); text(x, y, "THRU TYPE, DOUBLE ACCESS  STA %s" % sta(s), 6.5, rot=ang(s))
    pline([at(s - 3, -12.2), at(s, -1.4)], 0.4)
for s, pid in ((22, "P-101"), (68, "P-102"), (141, "P-103"), (214, "P-104")):
    x, y = at(s, -4.6)
    sh.draw_circle(P(x, y), 3.2); sh.finish(width=0.8)
    x, y = at(s + 1.2, -5.6); text(x, y, pid, 5.5, GREY)
CALLS = [(30, 3.0, "8-125 C.E."), (110, 3.0, "8-125 C.E."), (215, 3.0, "8-125 C.E."),
         (150.0, 16.5, "START REINF. C.E. STA 0+150.00"), (164.0, 19.5, "END REINF. C.E. STA 0+164.00"),
         (95.0, -20.5, "11.25 DEG HORIZ. BEND STA 0+095.00"), (CUM[2], 22.5, "22.5 DEG HORIZ. BEND STA %s" % sta(CUM[2]))]
for s, d, t in CALLS:
    x, y = at(s, d); text(x, y, t, 6.5, rot=ang(s))
    if abs(d) > 5:
        pline([at(s, d - (1.2 if d > 0 else -1.2)), at(s, 0.9 if d > 0 else -0.9)], 0.4)
for s, other in ((0.0, 1), (TOTAL, 3)):
    pline([at(s, -9), at(s, 16)], 1.8, BLK, "[16 5 4 5] 0")
    x, y = at(s + (1.2 if s == 0 else -2.4), -8); text(x, y, "MATCHLINE - SEE SHEET %d" % other, 7, rot=ang(s) + 90)
pg.insert_text(fitz.Point(210, 110), "PLAN", fontsize=20)
pg.insert_text(fitz.Point(290, 110), "SCALE 1:500", fontsize=10)
sh.draw_line(fitz.Point(430, 106), fitz.Point(430 + 25 * K, 106)); sh.finish(width=2)
pg.insert_text(fitz.Point(428, 98), "0", fontsize=7); pg.insert_text(fitz.Point(424 + 25 * K, 98), "25 m", fontsize=7)
sh.draw_polyline([fitz.Point(1850, 190), fitz.Point(1862, 120), fitz.Point(1874, 190), fitz.Point(1862, 172), fitz.Point(1850, 190)])
sh.finish(width=1, fill=BLK); pg.insert_text(fitz.Point(1856, 112), "N", fontsize=14)


# ---- PROFILE ----
def ground(s):
    return 77.6 + 0.0105 * s + 0.35 * math.sin(s / 38.0)


def invert(s):  # top of concrete encasement
    base = ground(s) - 1.25
    dip = 1.05 * math.exp(-((s - 157.0) / 9.0) ** 2) + 0.75 * math.exp(-((s - 205.0) / 8.0) ** 2)
    return base - dip


def Q(s, e):
    return fitz.Point(PX0 + K * s, PY0 - KV * (e - E0))


for e in range(70, 82):
    sh.draw_line(Q(0, e), Q(TOTAL, e)); sh.finish(width=0.3 if e % 5 else 0.7, color=LIGHT)
    pg.insert_text(Q(-5.5, e - 0.08), "%d" % e, fontsize=6.5); pg.insert_text(Q(TOTAL + 1.5, e - 0.08), "%d" % e, fontsize=6.5)
for s in range(0, 251, 20):
    sh.draw_line(Q(s, 70), Q(s, 81)); sh.finish(width=0.3, color=LIGHT)
    pg.insert_text(Q(s - 3.2, 69.45), sta(s), fontsize=6.5)
sh.draw_polyline([Q(s, ground(s)) for s in range(0, 251, 2)]); sh.finish(width=1.0, closePath=False)
for dz, w in ((0.0, 1.1), (-0.62, 1.1)):
    sh.draw_polyline([Q(s, invert(s) + dz) for s in range(0, 251, 2)]); sh.finish(width=w, color=(0.1, 0.2, 0.7), closePath=False)
for s in range(150, 165):
    sh.draw_line(Q(s, invert(s)), Q(s + 1, invert(s + 1) - 0.62)); sh.finish(width=0.4, color=(0.1, 0.2, 0.7))
pg.insert_text(Q(50, ground(50) + 0.35), "SURFACE GRADE", fontsize=6.5)
pg.insert_text(Q(100, invert(100) - 1.05), "8-125 C.E.", fontsize=6.5, color=(0.1, 0.2, 0.7))
pg.insert_text(Q(140, 71.2), "REINFORCED C.E. STA 0+150.00 TO 0+164.00", fontsize=6.5, color=(0.1, 0.2, 0.7))
for s, name, el, pos in CROSS:
    sh.draw_circle(Q(s, el), 4.2); sh.finish(width=0.9)
    pg.insert_text(Q(s + 1.2, el + (0.25 if pos == "ABOVE" else -0.45)), "%s  INV %.2f" % (name, el), fontsize=6)
for s, name in VAULTS:
    sh.draw_rect(fitz.Rect(Q(s - 2.175, ground(s) - 0.1), Q(s + 2.175, invert(s) - 1.35))); sh.finish(width=1.1)
    pg.insert_text(Q(s - 2.0, ground(s) + 0.55), name, fontsize=7)
pg.insert_text(fitz.Point(210, 1010), "PROFILE", fontsize=20)
pg.insert_text(fitz.Point(330, 1010), "H 1:500   V 1:100", fontsize=10)
sh.commit()

# ---- right-hand strip: notes, legend, schedule, title block ----
PRINTED = [("RUN 1", "S-M1", "0+005.00", "0+078.40", 75.0), ("RUN 2", "S-M2", "0+084.00", "0+150.00", 66.0),
           ("RUN 3", "S-RCE1", "0+150.00", "0+164.00", 14.0), ("RUN 4", "S-M3", "0+171.00", "0+246.00", 75.0)]
x = 1975
pg.insert_text(fitz.Point(x, 80), "GENERAL NOTES", fontsize=11)
notes = ["1. ALL DIMENSIONS IN METRES UNLESS NOTED. STATIONS ALONG DUCT CENTRELINE.",
         "2. MIN. COVER 1.0 m TO TOP OF CONCRETE ENCASEMENT (C.E.).",
         "3. MAINTAIN 0.9 m HORIZONTAL AND 0.3 m VERTICAL SEPARATION FROM OTHER UTILITIES.",
         "4. REINFORCED C.E. REQUIRED WHERE DUCT PASSES BELOW A RIGID UTILITY.",
         "5. STUB DUCTS 1.5 m FROM EACH VAULT WALL.",
         "6. EXISTING UTILITIES SHOWN FOR REFERENCE ONLY. LOCATE BEFORE EXCAVATION.",
         "7. RESTORE TRENCH SURFACE: TRENCH WIDTH PLUS 0.2 m EACH SIDE."]
for i, n in enumerate(notes):
    pg.insert_textbox(fitz.Rect(x, 92 + 30 * i, 2400, 122 + 30 * i), n, fontsize=7)
pg.insert_text(fitz.Point(x, 340), "DUCT SCHEDULE", fontsize=11)
pg.insert_text(fitz.Point(x, 358), "%-7s%-8s%-10s%-10s%9s" % ("RUN", "ID", "FROM", "TO", "LENGTH m"), fontsize=7.5, fontname="cour")
for i, r in enumerate(PRINTED):
    pg.insert_text(fitz.Point(x, 374 + 14 * i), "%-7s%-8s%-10s%-10s%9.1f" % r, fontsize=7.5, fontname="cour")
pg.insert_text(fitz.Point(x, 470), "LEGEND", fontsize=11)
for i, (lab, dash, col, w) in enumerate((("PROPOSED DUCT (C.E.)", "[5 3] 0", BLK, 1.0), ("CURB", None, BLK, 1.1), ("PROPERTY LINE", "[14 4 3 4] 0", BLK, 0.9),
                                        ("EX. WATER", "[10 3 2 3] 0", LIGHT, 0.6), ("EX. GAS", "[4 3] 0", LIGHT, 0.6))):
    yy = 490 + 18 * i
    pg.draw_line(fitz.Point(x, yy), fitz.Point(x + 70, yy), width=w, color=col, dashes=dash)
    pg.insert_text(fitz.Point(x + 82, yy + 3), lab, fontsize=7.5)
pg.draw_rect(fitz.Rect(1962, 1180, 2400, 1300), color=RED, width=1.5)
pg.insert_textbox(fitz.Rect(1970, 1188, 2392, 1296), "SYNTHETIC TRAINING SHEET\nNOT A REAL PROJECT. Every street, lot, station, elevation, structure and "
                  "length on this sheet is invented. No owner, no site, no tender.", fontsize=10, color=RED)
for yy in (1320, 1400, 1460, 1510):
    pg.draw_line(fitz.Point(1950, yy), fitz.Point(W - 36, yy), width=1)
pg.insert_text(fitz.Point(x, 1350), "UNDERGROUND DUCT AND STRUCTURES", fontsize=12)
pg.insert_text(fitz.Point(x, 1372), "ROAD A   STA 0+000 TO 0+%06.2f" % TOTAL, fontsize=10)
pg.insert_text(fitz.Point(x, 1436), "PLAN AND PROFILE", fontsize=12)
pg.insert_text(fitz.Point(x, 1490), "DWG NO.  SYN-U-0002        REV A", fontsize=10)
pg.insert_text(fitz.Point(x, 1536), "SHEET 2 OF 3", fontsize=10)

doc.save(os.path.join(OUT, "synthetic_sheet.pdf"))
pg.get_pixmap(dpi=80).save(os.path.join(OUT, "synthetic_sheet_preview.png"))


# ---- geometry an agent derives from the sheet, in PDF space (origin lower-left) ----
def pdf(pt):
    p = P(*pt)
    return (round(p.x, 2), round(H - p.y, 2))


def path(pts, close=False):
    q = [pdf(p) for p in pts]
    return "M %s %s " % q[0] + " ".join("L %s %s" % p for p in q[1:]) + (" H" if close else "")


def circle_rect(s, r):
    cx, cy = pdf(at(s))
    return "%.2f %.2f %.2f %.2f" % (cx - r, cy - r, 2 * r, 2 * r)


RUNS = [("S-M1", "Duct 8-125 C.E.", 5.0, 78.4), ("S-M2", "Duct 8-125 C.E.", 84.0, 150.0),
        ("S-RCE1", "Duct 8-125 reinforced C.E.", 150.0, 164.0), ("S-M3", "Duct 8-125 C.E.", 171.0, 246.0)]
mk = {"scale": "1 mm = 0.5 m", "printed": {r[1]: r[4] for r in PRINTED}, "runs": [], "resto": [], "points": [], "qa": []}
for pid, desc, s1, s2 in RUNS:
    mk["runs"].append({"id": pid, "subject": "DUCT | %s | %s %s - %s" % (pid, desc, sta(s1), sta(s2)), "path": path(offset_line(s1, s2, 0.0))})
    band = offset_line(s1, s2, 0.95) + offset_line(s1, s2, -0.95)[::-1]
    mk["resto"].append({"id": "R-" + pid, "subject": "RESTO | R-%s | Trench patch 1.9 m %s - %s" % (pid, sta(s1), sta(s2)), "path": path(band, True)})
for i, (s, t) in enumerate(((95.0, "Bend 11.25 deg horiz."), (CUM[2], "Bend 22.5 deg horiz.")), 1):
    mk["points"].append({"id": "F-%02d" % i, "subject": "PARTS | F-%02d | %s %s" % (i, t, sta(s)), "rect": circle_rect(s, 9), "color": "#008C4A"})
for i, (s, name, el, pos) in enumerate(CROSS, 1):
    mk["points"].append({"id": "OBS-%03d" % i, "subject": "CROSSING | OBS-%03d | %s %s %s" % (i, name, pos, sta(s)), "rect": circle_rect(s, 7), "color": "#F28000"})
for s, name in VAULTS:
    mk["points"].append({"id": name, "subject": "VAULT | %s | Precast vault thru type %s" % (name, sta(s)), "rect": circle_rect(s, 16), "color": "#7A2DB3"})
mk["qa"].append({"id": "QA-A", "subject": "QA CHECK - DO NOT SUM | Sample A | reinforced extent vs printed START/END REINF.", "path": path(offset_line(150.0, 164.0, -3.2))})
json.dump(mk, open(os.path.join(OUT, "derived_markups.json"), "w"), indent=1)
print("total", round(TOTAL, 2), "bend2 at", sta(CUM[2]))
