"""Manufacturing-notes drawing sheets for the Xometry fitment kit.

One A4-landscape sheet per part: silhouette views from the actual STEP
geometry + the callout table (threads, fits, criticals) that STEP files
cannot carry. These are notes sheets to attach to the quote, not full
GD&T drawings: geometry is per the STEP model.

Run: python3 xometry_drawings.py  ->  output/xometry/intercontinental_fitment_kit_drawings.pdf
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.collections import PolyCollection

import cadquery as cq
from cadquery import importers, exporters

HERE = os.path.dirname(__file__)
XOM = os.path.join(HERE, "output", "xometry")

GENERAL = ("GENERAL: dims in mm. Geometry per attached STEP (master). "
           "Untoleranced machined dims ±0.05. Break sharp edges R0.1 "
           "unless noted. Engravings are cosmetic: best effort, do not "
           "quote polishing/filling.")

SHEETS = [
    ("x01_midcase", "MIDCASE", "Aluminum 6061-T6 (round 2: 316L)", [
        ("Caseback thread", "M32 x 1.0 - 6H internal, full depth z 0-3.5 "
         "(PROTOTYPE substitution for the design's M32 x 0.5; mate with "
         "x04 external thread)"),
        ("Crystal bore", "Ø32.00 H7, seat depth per STEP"),
        ("Dial pass bore", "Ø31.40 H8 (dial loads from the back)"),
        ("Dial pocket", "Ø31.30 +0.05/-0"),
        ("Crown / tube bore", "Ø2.48 H7 through flank at z 4.62 from "
         "back plane; inner Ø2.00 stem clearance per STEP"),
        ("Spring-bar holes", "Ø1.35 ±0.05 thru, both lugs, 90° "
         "csk to Ø1.65 both faces; position ±0.05"),
        ("Detent ball pocket", "Ø0.65 pocket in shoulder: best effort, "
         "may be omitted on prototype"),
        ("Criticals", "case Ø39.00 ±0.05; lug gap 20.00 +0.15/-0; "
         "lug-to-lug 47.90 ±0.10"),
        ("Finish", "as machined or light bead blast; no polishing"),
    ]),
    ("x02_bezel", "BEZEL 24H", "Aluminum 6061-T6", [
        ("Bore", "Ø34.10 H8 (rotates on case boss Ø34.00)"),
        ("Internal groove", "per STEP (Ø34.70 x 0.70) - spring ring "
         "omitted on prototype, groove still required"),
        ("Numerals / triangles", "engraved 0.25 deep: cosmetic, best "
         "effort, no lacquer fill"),
        ("Underside scallops", "120 x R0.50 x 0.18 deep: cosmetic on "
         "prototype, may be omitted"),
        ("Coin edge", "per STEP; best effort"),
        ("Finish", "as machined"),
    ]),
    ("x04_caseback", "CASEBACK RING", "Aluminum 6061-T6 (round 2: 316L)", [
        ("Thread", "M32 x 1.0 - 6g external on Ø32 band (PROTOTYPE "
         "substitution for M32 x 0.5; mate with x01 internal thread)"),
        ("O-ring groove", "on OD per STEP: retain (gasket not fitted on "
         "prototype)"),
        ("Window pocket", "Ø23.42 +0.05/-0 x 1.40 deep, internal "
         "retaining ledge per STEP (mates x05 acrylic window)"),
        ("Wrench notches", "6x per STEP"),
        ("Engraving", "KELSUS INTERCONTINENTAL, 0.18 deep: cosmetic, best "
         "effort"),
        ("Finish", "as machined"),
    ]),
    ("x08_movement_ring", "MOVEMENT RING", "Acetal / Delrin (POM), white or black", [
        ("Movement register", "Ø25.60 Js8 - CRITICAL, this locates "
         "the Miyota 9075"),
        ("Flange seat", "Ø26.00 relief per STEP"),
        ("OD", "Ø31.20 (slips into dial pass bore Ø31.40 H8)"),
        ("Stem slot", "per STEP, aligns with case tube bore"),
        ("Finish", "as machined"),
    ]),
    ("x03_crystal_acrylic", "CRYSTAL (PROTOTYPE)", "Acrylic PMMA, clear", [
        ("OD", "Ø31.40 -0.05 (design uses a gasket; prototype is a "
         "slip fit into Ø32.00 bore, retained with adhesive by "
         "customer)"),
        ("Profile", "flat-top dome per STEP"),
        ("Finish", "machine finish acceptable; vapor polish if offered"),
    ]),
    ("x05_window_acrylic", "EXHIBITION WINDOW (PROTOTYPE)", "Acrylic PMMA, clear", [
        ("Disc", "Ø23.40 -0.05 x 1.40 (slip into x04 pocket, customer "
         "retains with adhesive)"),
        ("Finish", "machine finish acceptable"),
    ]),
    ("x06_crown_proto", "CROWN (PROTOTYPE)", "Aluminum 6061 or 303/316 stainless", [
        ("Pin", "Ø2.44 -0.02 x 5.2 long, integral (slips into case "
         "tube bore Ø2.48 H7; friction fit, removable). PROTOTYPE "
         "substitution for the threaded crown + tube."),
        ("Body", "Ø6.25 x 3.85 per STEP; coin edge best effort"),
        ("K logo on end face", "engraved: cosmetic, best effort, may be "
         "omitted"),
        ("Finish", "as machined"),
    ]),
]


def silhouettes(step_path):
    """Two projected silhouettes (front XZ, plan XY) from the STEP."""
    shp = importers.importStep(step_path)
    tmp = step_path + ".stl"
    exporters.export(shp.val(), tmp, tolerance=0.05, angularTolerance=0.3)
    from stl import mesh as stlmesh
    tris = stlmesh.Mesh.from_file(tmp).vectors
    os.remove(tmp)
    return tris


def sheet(pdf, idx, fname, title, material, rows):
    tris = silhouettes(os.path.join(XOM, fname + ".step"))
    fig = plt.figure(figsize=(11.69, 8.27), dpi=150)
    # views: front (x,z) and plan (x,y)
    for i, (cols, vt) in enumerate((( [0, 2], "front (X-Z)"),
                                    ([0, 1], "plan (X-Y)"))):
        ax = fig.add_axes((0.04, 0.55 - i * 0.40, 0.42, 0.36))
        proj = tris[:, :, cols]
        ax.add_collection(PolyCollection(proj, facecolors="#67707a",
                                         edgecolors="none"))
        lo = proj.reshape(-1, 2).min(axis=0) - 2
        hi = proj.reshape(-1, 2).max(axis=0) + 2
        ax.set_xlim(lo[0], hi[0]); ax.set_ylim(lo[1], hi[1])
        ax.set_aspect("equal")
        ax.set_title(vt, fontsize=8, loc="left")
        ax.tick_params(labelsize=6)
        ax.grid(alpha=0.25, linewidth=0.4)
    # callout table
    axt = fig.add_axes((0.50, 0.16, 0.48, 0.74)); axt.axis("off")
    y = 1.0
    for k, v in rows:
        axt.text(0.0, y, k.upper(), fontsize=8.5, fontweight="bold",
                 va="top", family="sans-serif")
        wrapped = "\n".join(_wrap(v, 58))
        axt.text(0.02, y - 0.035, wrapped, fontsize=8, va="top",
                 family="sans-serif")
        y -= 0.045 + 0.032 * (wrapped.count("\n") + 1)
    # title block
    axb = fig.add_axes((0.04, 0.02, 0.94, 0.10)); axb.axis("off")
    axb.add_patch(plt.Rectangle((0, 0), 1, 1, fill=False, linewidth=0.8))
    axb.text(0.01, 0.72, f"KELSUS INTERCONTINENTAL - FITMENT PROTOTYPE KIT",
             fontsize=9, fontweight="bold")
    axb.text(0.01, 0.38, f"SHEET {idx}/7   PART: {title}   FILE: {fname}.step"
             f"   MATERIAL: {material}   QTY: 1", fontsize=8)
    axb.text(0.01, 0.08, GENERAL, fontsize=6.2)
    pdf.savefig(fig); plt.close(fig)
    print(f"  sheet {idx}: {title}")


def _wrap(s, n):
    out, line = [], ""
    for w in s.split():
        if len(line) + len(w) + 1 > n:
            out.append(line); line = w
        else:
            line = w if not line else line + " " + w
    out.append(line)
    return out


if __name__ == "__main__":
    dst = os.path.join(XOM, "intercontinental_fitment_kit_drawings.pdf")
    with PdfPages(dst) as pdf:
        for i, (f, t, m, r) in enumerate(SHEETS, 1):
            sheet(pdf, i, f, t, m, r)
    print("wrote", dst)
