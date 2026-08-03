"""
STEP-file translator-safety scan.

The lesson of the 'water balloon' / 'torpedo': geometry that OCCT reads
back perfectly can still render as phantom blobs in another translator
(Fusion), because STEP surfaces are written UNBOUNDED and rely on face
trims. If a trim is lost, the viewer renders the basis surface out to its
defining anchors. So we scan the file TEXT: every CARTESIAN_POINT outside
the model envelope is traced to the entity that owns it.

  - PLANE / LINE / VECTOR owners: harmless (viewers handle untrimmed
    planes; anchors are arbitrary).
  - CIRCLE / CONICAL / SPHERICAL / TOROIDAL / SURFACE_OF_REVOLUTION owners
    outside the envelope: DANGEROUS — a lost trim becomes a lathe blob.
    These fail the scan.

Usage: python3 scan_step.py [--all]      (default scans output/*.step)
Exit 0 = no dangerous anchors anywhere.
"""
import glob
import math
import os
import re
import sys

ENV_ZMIN, ENV_ZMAX, ENV_RMAX = -1.0, 12.6, 30.0

PT = re.compile(r"#(\d+)\s*=\s*CARTESIAN_POINT\s*\(\s*[^,]*,\s*\(\s*"
                r"([-0-9.Ee+]+)\s*,\s*([-0-9.Ee+]+)\s*,\s*([-0-9.Ee+]+)")
ENT = re.compile(r"#(\d+)\s*=\s*([A-Z0-9_]+)\s*\(")
REF = re.compile(r"#(\d+)")

SAFE_OWNERS = {"PLANE", "LINE", "VECTOR", "AXIS2_PLACEMENT_3D",
               "AXIS1_PLACEMENT", "DIRECTION", "VERTEX_POINT",
               "CARTESIAN_POINT", "PRESENTATION", "STYLED_ITEM"}


def scan(path):
    txt = open(path, errors="ignore").read()
    # entity table + reverse reference index
    lines = {}
    for m in re.finditer(r"#(\d+)\s*=\s*([A-Z0-9_]+)\s*\(([^;]*)\);",
                         txt, re.S):
        lines[int(m.group(1))] = (m.group(2), m.group(3))
    refs = {}          # id -> list of ids that reference it
    for eid, (kind, body) in lines.items():
        for r in REF.findall(body):
            refs.setdefault(int(r), []).append(eid)

    def owners(eid, depth=0):
        """Walk up the reference graph to geometric owners."""
        if depth > 4:
            return set()
        out = set()
        for parent in refs.get(eid, []):
            kind = lines[parent][0]
            if kind in ("PLANE", "CIRCLE", "ELLIPSE", "CONICAL_SURFACE",
                        "SPHERICAL_SURFACE", "TOROIDAL_SURFACE",
                        "CYLINDRICAL_SURFACE", "SURFACE_OF_REVOLUTION",
                        "SURFACE_OF_LINEAR_EXTRUSION", "LINE",
                        "B_SPLINE_SURFACE_WITH_KNOTS",
                        "B_SPLINE_CURVE_WITH_KNOTS", "VERTEX_POINT",
                        "VECTOR"):
                out.add(kind)
            else:
                out |= owners(parent, depth + 1)
        return out

    danger, benign = [], []
    for m in PT.finditer(txt):
        eid = int(m.group(1))
        x, y, z = (float(m.group(2)), float(m.group(3)), float(m.group(4)))
        r = math.hypot(x, y)
        if ENV_ZMIN <= z <= ENV_ZMAX and r <= ENV_RMAX:
            continue
        own = owners(eid) or {"?"}
        rec = (eid, x, y, z, r, ",".join(sorted(own)))
        # CIRCLE/ELLIPSE that serve as EDGE geometry are bounded by their
        # vertices — translators cannot inflate them into surfaces. They
        # are dangerous only as the basis of a surface.
        curve_kinds = {"CIRCLE", "ELLIPSE"}
        surface_kinds = {"SURFACE_OF_REVOLUTION",
                         "SURFACE_OF_LINEAR_EXTRUSION"}
        if own <= SAFE_OWNERS or own == {"?"}:
            benign.append(rec)
        elif own <= (curve_kinds | SAFE_OWNERS) and not (
                own & surface_kinds):
            benign.append(rec)
        else:
            danger.append(rec)
    return danger, benign


def brep_gates(path):
    """OCCT-level gates BRepCheck cannot see: (a) self-intersecting shells
    within one solid (BOPAlgo_SelfIntersect), (b) analytic faces with
    sub-feature radii (< 0.01 mm) that write as needle geometry."""
    from cadquery import importers
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Check
    from OCP.BRepAdaptor import BRepAdaptor_Surface
    from OCP.GeomAbs import GeomAbs_SurfaceType
    problems = []
    shp = importers.importStep(path)
    for si, sol in enumerate(shp.solids().vals()):
        chk = BRepAlgoAPI_Check(sol.wrapped, True, True)
        if not chk.IsValid():
            problems.append(f"solid {si}: BRepAlgoAPI_Check invalid "
                            f"(self-intersection or bad topology)")
        for face in sol.Faces():
            ad = BRepAdaptor_Surface(face.wrapped)
            t = ad.GetType()
            r = None
            if t == GeomAbs_SurfaceType.GeomAbs_Cylinder:
                r = ad.Cylinder().Radius()
            elif t == GeomAbs_SurfaceType.GeomAbs_Cone:
                r = ad.Cone().RefRadius()
            elif t == GeomAbs_SurfaceType.GeomAbs_Sphere:
                r = ad.Sphere().Radius()
            if r is not None and r < 0.01:
                problems.append(f"solid {si}: needle face radius {r:.2e}")
    return problems


def main():
    fails = 0
    for f in sorted(glob.glob(os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "output", "*.step"))):
        danger, benign = scan(f)
        brep = [] if f.endswith("assembly.step") else brep_gates(f)
        tag = "FAIL" if (danger or brep) else "PASS"
        print(f"[{tag}] {os.path.basename(f):28s} "
              f"dangerous={len(danger)} brep={len(brep)} "
              f"benign(plane-anchor)={len(benign)}")
        for eid, x, y, z, r, own in danger[:6]:
            print(f"        #{eid} ({x:.2f},{y:.2f},{z:.2f}) r={r:.1f} <- {own}")
        for msg in brep[:6]:
            print(f"        {msg}")
        fails += bool(danger or brep)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
