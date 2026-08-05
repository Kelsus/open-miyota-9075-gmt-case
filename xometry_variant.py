"""Xometry fitment-kit package for the Intercontinental case.

Copies the machinable STEPs into output/xometry/ and generates the one
prototype-substituted part: a crown with an integral slip pin replacing
the (unmachinable at prototype scale) S0.9 threaded crown + tube.

Thread substitutions are drawing callouts, not geometry changes:
  caseback x case  M30x0.5  ->  M30x1.0 (prototype)
Run: python3 xometry_variant.py
"""
import os
import shutil

import cadquery as cq
from cadquery import exporters, importers

import case_model as C

P = C.P
OUT = os.path.join(os.path.dirname(__file__), "output")
XOM = os.path.join(OUT, "xometry")
os.makedirs(XOM, exist_ok=True)

# slip fit: the case's tube bore is Ø2.48 H7; a Ø2.44 pin slides in and
# holds by friction, and pulls back out to free the movement stem
CROWN_PIN = 2.44
PIN_LEN = 5.2


def proto_crown():
    crown = importers.importStep(os.path.join(OUT, "06_crown.step"))
    bb = crown.val().BoundingBox()
    # the fill must INTERFERE with the crown to fuse: oversize it against
    # the bore and run it past the bore bottom into solid metal. (An
    # earlier undersized fill floated inside the bore and the exported
    # STEP contained two disjoint solids; a machine shop flagged it.)
    fill = (cq.Workplane("YZ", origin=(bb.xmin + 0.2, 0, C.STEM_Z))
            .circle(P["crown_bore_dia"] / 2.0 + 0.15)
            .extrude(bb.xmax - bb.xmin - 1.0))
    pin = (cq.Workplane("YZ", origin=(bb.xmin - PIN_LEN, 0, C.STEM_Z))
           .circle(CROWN_PIN / 2.0).extrude(PIN_LEN + 1.0))
    out = crown.union(fill).union(pin).clean()
    sols = out.solids().vals()
    assert len(sols) == 1, f"crown proto must be ONE solid, got {len(sols)}"
    exporters.export(sols[0], os.path.join(XOM, "x06_crown_proto.step"))
    print("  wrote xometry/x06_crown_proto.step (1 solid)")


COPIES = {
    "01_midcase": "x01_midcase",
    "02_bezel": "x02_bezel",
    "04_caseback_ring": "x04_caseback",
    "08_movement_ring": "x08_movement_ring",
    "03_crystal": "x03_crystal_acrylic",
    "05_caseback_sapph": "x05_window_acrylic",
}

if __name__ == "__main__":
    print("xometry package ->", XOM)
    for src, dst in COPIES.items():
        shutil.copy(os.path.join(OUT, src + ".step"),
                    os.path.join(XOM, dst + ".step"))
        print(f"  copied {dst}.step")
    proto_crown()
    print("done")
