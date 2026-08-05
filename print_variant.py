"""FDM print adaptation of the Kelsus Intercontinental case.

Derives snap-together prototype parts from the finished STEP exports in
output/. The machined design's micro-fasteners cannot print (M30x0.5
thread, S0.9 crown thread, 0.35 mm steel spring ring), so each interface
is replaced by a snap feature sized for PETG strain, not steel:

  caseback  M30x0.5 thread      -> 3 cantilever snap tabs into a bore groove
  bezel     slit spring ring    -> integral snap lip over the boss groove
  crystal   I-ring gasket press -> 6 crush ribs into the Ø32.0 bore
  window    press + ledge       -> 3 crush ribs into the back pocket
  crown     S0.9 thread on tube -> integral Ø2.42 press pin into the case

Writes STLs to output/print/.  Run: python3 print_variant.py
"""
import math
import os

import cadquery as cq
from cadquery import exporters, importers

import case_model as C

P = C.P
OUT = os.path.join(os.path.dirname(__file__), "output")
PRT = os.path.join(OUT, "print")
os.makedirs(PRT, exist_ok=True)

# ---- snap dimensioning (PETG, calibrated Bambu ±0.05) ---------------------
CB_BORE = 30.30          # was Ø30.0 thread bore: +0.30 print clearance
CB_GROOVE_ID = 30.95     # snap groove in the case bore
CB_GROOVE_Z = (2.40, 3.40)
CB_BUMP_CREST = 30.60    # 0.15/side interference vs CB_BORE
CB_BUMP_Z = (2.55, 3.25)
CB_TAB_ARC = 26.0        # degrees of barrel per tab
CB_SLIT_W = 1.4
BEZ_LIP_ID = 33.35       # over boss Ø34.0: 1.9% brief hoop strain
CROWN_PIN = 2.42
CROWN_HOLE = 2.50
RIB = 0.16               # crystal crush rib proudness (per side)


def imp(name):
    return importers.importStep(os.path.join(OUT, name + ".step"))


def save(wp, name):
    sols = wp.solids().vals() if hasattr(wp, "solids") else [wp]
    if len(sols) != 1:
        raise RuntimeError(f"{name}: expected ONE fused solid, got "
                           f"{len(sols)} - disjoint bodies print as "
                           f"separate loose pieces")
    exporters.export(sols[0], os.path.join(PRT, name + ".stl"),
                     tolerance=0.01, angularTolerance=0.2)
    print(f"  wrote print/{name}.stl")


def ring_cut(id_d, od_d, z0, z1):
    """Washer-shaped cutting tool."""
    return (cq.Workplane("XZ")
            .moveTo(id_d / 2.0, z0).lineTo(od_d / 2.0, z0)
            .lineTo(od_d / 2.0, z1).lineTo(id_d / 2.0, z1).close()
            .revolve(360, (0, 0, 0), (0, 1, 0)))


# ---------------------------------------------------------------- case ----
def p01_case():
    case = imp("01_midcase")
    # open the caseback thread bore to a smooth snap bore + groove
    case = (case
            .cut(cq.Workplane("XY", origin=(0, 0, -0.6))
                 .circle(CB_BORE / 2.0).extrude(P["cb_thread_top_z"] + 0.6))
            .cut(ring_cut(CB_BORE - 0.2, CB_GROOVE_ID, *CB_GROOVE_Z)))
    # crown hole: one straight Ø2.50 drill through the flank (drill 2.4 and
    # press the crown pin; no tube, no thread)
    case = case.cut(
        cq.Workplane("YZ", origin=(12.5, 0, C.STEM_Z))
        .circle(CROWN_HOLE / 2.0).extrude(10))
    # lead-in chamfer on the boss top edge so the bezel lip can climb it
    r_boss = P["boss_od"] / 2.0
    case = case.cut(
        cq.Workplane("XZ")
        .moveTo(r_boss - 0.35, C.STEEL_TOP + 0.01)
        .lineTo(r_boss + 0.2, C.STEEL_TOP + 0.01)
        .lineTo(r_boss + 0.2, C.STEEL_TOP - 0.56)
        .close().revolve(360, (0, 0, 0), (0, 1, 0)))
    save(case, "p01_case")


# ------------------------------------------------------------- caseback ----
def p04_back():
    back = imp("04_caseback_ring")
    ro = P["cb_thread_dia"] / 2.0 - 0.05
    # fill the O-ring groove (no gasket on the print variant): it crosses
    # the snap-tab feet, and with it open each tab hangs on a 0.05 sliver
    # that the boolean severs into a loose piece
    gz = P["back_recess_z"] + 0.95 + P["cb_oring_groove_w"] / 2.0
    gw = P["cb_oring_groove_w"]
    gd = P["cb_oring_groove_d"]
    back = back.union(
        cq.Workplane("XZ")
        .moveTo(ro - gd - 0.05, gz - gw / 2.0 - 0.01)
        .lineTo(ro - 0.001, gz - gw / 2.0 - 0.01)
        .lineTo(ro - 0.001, gz + gw / 2.0 + 0.01)
        .lineTo(ro - gd - 0.05, gz + gw / 2.0 + 0.01)
        .close().revolve(360, (0, 0, 0), (0, 1, 0)))
    # 3 snap bumps: partial-revolve wedge ribs on the barrel OD, 40 deg
    # lead chamfer below, square shoulder above
    z0, z1 = CB_BUMP_Z
    crest = CB_BUMP_CREST / 2.0
    lead = (crest - ro) * 1.2
    for ang in (90, 210, 330):
        bump = (cq.Workplane("XZ")
                .moveTo(ro - 0.05, z0 - lead)
                .lineTo(crest, z0)
                .lineTo(crest, z1)
                .lineTo(ro - 0.05, z1)
                .close()
                .revolve(CB_TAB_ARC - 4.0, (0, 0, 0), (0, 1, 0))
                .rotate((0, 0, 0), (0, 0, 1), ang - (CB_TAB_ARC - 4.0) / 2.0))
        back = back.union(bump)
    # slit the barrel beside each bump -> cantilever tabs (fixed at the
    # disc, free at the top). Slits stop above the wrench notches.
    slits = []
    for ang in (90, 210, 330):
        for side in (-1, +1):
            a = math.radians(ang + side * CB_TAB_ARC / 2.0)
            x, y = math.cos(a) * (ro - 0.6), math.sin(a) * (ro - 0.6)
            slits.append(
                cq.Workplane("XY", origin=(x, y, 1.05))
                .rect(CB_SLIT_W, CB_SLIT_W)
                .extrude(P["cb_thread_top_z"])
                .rotate((x, y, 0), (x, y, 1), math.degrees(a)))
    # cut the slits as one compound, then the relief wedges as another:
    # the wedges OVERLAP the slit boxes at the tab edges, and OCCT
    # fragments a boolean whose compound tool self-overlaps (same
    # failure class as the lume-pip artifact in the master model)
    back = back.cut(C.compound([s.val() for s in slits]))
    # thin the wall behind each tab so the tab can flex (relief pocket)
    wedges = []
    for ang in (90, 210, 330):
        wedges.append(
            (cq.Workplane("XZ")
             .moveTo(ro - 1.3, 1.05).lineTo(ro - 0.55, 1.05)
             .lineTo(ro - 0.55, 3.55).lineTo(ro - 1.3, 3.55).close()
             .revolve(CB_TAB_ARC, (0, 0, 0), (0, 1, 0))
             .rotate((0, 0, 0), (0, 0, 1), ang - CB_TAB_ARC / 2.0)))
    back = back.cut(C.compound([w.val() for w in wedges])).clean()
    save(back, "p04_back")


# ---------------------------------------------------------------- bezel ----
def p02_bezel():
    bez = imp("02_bezel")
    # integral snap lip inside the skirt bore, replacing the spring ring:
    # 45 deg lead on the bottom (climbs the boss), square retention
    # shoulder on top (sits under the boss groove's upper wall)
    r_lip = BEZ_LIP_ID / 2.0                    # 16.675
    # anchor the lip INSIDE the bezel's internal spring-ring groove: at
    # this height the bore wall is recessed to the groove (floor Ø34.7),
    # so the lip must reach past it to fuse. (A lip anchored at the
    # nominal bore radius floated in the groove as a separate loose
    # ring; the single-solid guard in save() now catches this class.)
    r_anchor = P["bezel_groove_dia"] / 2.0 + 0.05
    z0 = C.GROOVE_Z0 + 0.05
    lip = (cq.Workplane("XZ")
           .moveTo(r_anchor, z0)
           .lineTo(r_lip, z0 + 0.35)            # lead-in under the boss
           .lineTo(r_lip, z0 + 0.50)
           .lineTo(r_anchor, z0 + 0.50)
           .close()
           .revolve(360, (0, 0, 0), (0, 1, 0)))
    save(bez.union(lip).clean(), "p02_bezel")


# -------------------------------------------------------------- crystal ----
def p03_crystal():
    cry = imp("03_crystal")
    # 6 crush ribs on the cylindrical band: forgiving press into Ø32.0
    r = P["crystal_dia"] / 2.0                  # 15.70
    for i in range(6):
        a = i * 60.0
        # 0.6 deep x 1.0 wide box whose radial crest sits at r + RIB,
        # overlapping the band so it unions solidly
        rc = r + RIB - 0.30
        rib = (cq.Workplane("XY", origin=(rc, 0, C.CRYSTAL_SEAT_Z))
               .rect(0.6, 1.0).extrude(1.4)
               .rotate((0, 0, 0), (0, 0, 1), a))
        cry = cry.union(rib)
    save(cry, "p03_crystal")


# ------------------------------------------------------ exhibition window --
def p05_window():
    view = P["cb_sapphire_view"] / 2.0
    r = view + 1.2 - 0.08                       # Ø23.24 vs pocket Ø23.44
    t = P["cb_sapphire_thk"] - 0.02
    z0 = P["back_recess_z"]
    win = (cq.Workplane("XZ")
           .moveTo(0.005, z0).lineTo(r - 0.25, z0)
           .lineTo(r, z0 + 0.25)                # outer-edge lead chamfer
           .lineTo(r, z0 + t).lineTo(0.005, z0 + t).close()
           .revolve(360, (0, 0, 0), (0, 1, 0)))
    for i in range(3):
        a = i * 120.0
        rc = r + 0.12 - 0.30
        rib = (cq.Workplane("XY", origin=(rc, 0, z0 + 0.3))
               .rect(0.6, 1.0).extrude(t - 0.4)
               .rotate((0, 0, 0), (0, 0, 1), a))
        win = win.union(rib)
    save(win, "p05_window")


# ---------------------------------------------------------------- crown ----
def p06_crown():
    crown = imp("06_crown")
    bb = crown.val().BoundingBox()
    # crown axis is +X at z STEM_Z; inner face at bb.xmin. Fill the S0.9
    # bore, then grow the press pin toward the case.
    # oversized against the bore and driven past the bore bottom so the
    # union truly fuses (an undersized fill left the crown as a separate
    # loose body)
    fill = (cq.Workplane("YZ", origin=(bb.xmin + 0.2, 0, C.STEM_Z))
            .circle(P["crown_bore_dia"] / 2.0 + 0.15)
            .extrude(bb.xmax - bb.xmin - 1.0))
    pin = (cq.Workplane("YZ", origin=(bb.xmin - 5.2, 0, C.STEM_Z))
           .circle(CROWN_PIN / 2.0).extrude(5.4))
    save(crown.union(fill).union(pin).clean(), "p06_crown")


# --------------------------------------------------------- movement ring ---
def p08_ring():
    save(imp("08_movement_ring"), "p08_movement_ring")


# ------------------------------------------------- snap-fit test coupon ----
def p00_coupon():
    """4 mm tall ring reproducing the case's snap bore + groove. Print this
    (20 min) and click p04_back into it BEFORE printing the 5 h case."""
    z_off = 0.5                                 # case bore starts at z -0.5
    ring = (cq.Workplane("XZ")
            .moveTo(CB_BORE / 2.0, 0).lineTo(18.0, 0)
            .lineTo(18.0, 4.0).lineTo(CB_BORE / 2.0, 4.0).close()
            .revolve(360, (0, 0, 0), (0, 1, 0))
            .cut(ring_cut(CB_BORE - 0.2, CB_GROOVE_ID,
                          CB_GROOVE_Z[0] + z_off, CB_GROOVE_Z[1] + z_off)))
    save(ring, "p00_snap_coupon")


if __name__ == "__main__":
    print("print variant ->", PRT)
    p00_coupon()
    p01_case()
    p02_bezel()
    p03_crystal()
    p04_back()
    p05_window()
    p06_crown()
    p08_ring()
    print("done")
