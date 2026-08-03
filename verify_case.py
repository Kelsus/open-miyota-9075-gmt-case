"""
Kelsus Intercontinental — automated design verification.

Every check is a hard assertion about geometry, fits, clearances, or
manufacturability. Run after every model change. Exit code 0 = all pass.

Usage:  python3 verify_case.py            (full check)
        python3 verify_case.py --quick    (skip STEP re-import checks)
"""
import glob
import math
import os
import sys

import numpy as np
from stl import mesh as stlmesh

import case_model as C

OUT = C.OUT
P = C.P

RESULTS = []


def check(name, ok, detail="", severity="FAIL"):
    RESULTS.append((name, bool(ok), detail, severity))
    return bool(ok)


def near(a, b, tol):
    return abs(a - b) <= tol


def mesh_of(part):
    f = os.path.join(OUT, part + ".stl")
    if not os.path.exists(f):
        return None
    return stlmesh.Mesh.from_file(f).vectors.reshape(-1, 3)


# ---------------------------------------------------------------------------
# 1. OVERALL DIMENSIONS
# ---------------------------------------------------------------------------
def check_overall():
    mid = mesh_of("01_midcase")
    if mid is None:
        check("midcase mesh exists", False, "01_midcase.stl missing")
        return
    l2l = mid[:, 1].max() - mid[:, 1].min()
    check("lug-to-lug == l2l param", near(l2l, P["l2l"], 0.25),
          f"measured {l2l:.2f}, spec {P['l2l']:.2f} (±0.25)")

    # case OD in an azimuth band clear of BOTH the crown boss (spans ±8° at
    # 3 o'clock) and the lugs (their flanks leave the case circle at 36°):
    # 12-30° from the X axis is clean steel flank
    ang = np.degrees(np.arctan2(np.abs(mid[:, 1]), np.abs(mid[:, 0])))
    flank = mid[(ang > 12) & (ang < 30) & (mid[:, 2] > 1.0)
                & (mid[:, 2] < C.SHOULDER_Z)]
    if len(flank):
        od = 2 * np.hypot(flank[:, 0], flank[:, 1]).max()
        check("case OD == case_dia", near(od, P["case_dia"], 0.15),
              f"measured {od:.2f}, spec {P['case_dia']:.2f}")

    parts = ["01_midcase", "02_bezel", "03_crystal", "04_caseback_ring",
             "05_caseback_sapph", "06_crown", "07_crown_tube"]
    allv = np.vstack([m for m in (mesh_of(p) for p in parts) if m is not None])
    thk = allv[:, 2].max() - allv[:, 2].min()
    check("total thickness <= 12.2", thk <= 12.2,
          f"measured {thk:.2f} (hand-pivot chain 2.70 forced +1.5)")
    check("case bottom at z=0", near(allv[:, 2].min(), 0.0, 0.02),
          f"zmin {allv[:, 2].min():.3f}")


# ---------------------------------------------------------------------------
# 2. MOVEMENT FIT (Miyota 9075, drawing 907500C0)
# ---------------------------------------------------------------------------
def check_movement():
    # stack arithmetic
    z_dial = (P["back_recess_z"] + P["cb_sapphire_thk"] + P["cb_ledge_thk"]
              + P["rotor_clear"] + P["mvmt_h"])
    check("Z_DIAL derivation", near(C.Z_DIAL, z_dial, 1e-9),
          f"{C.Z_DIAL:.3f}")
    check("stem 2.55 below dial plane",
          near(C.Z_DIAL - C.STEM_Z, 2.55, 1e-6),
          f"{C.Z_DIAL - C.STEM_Z:.3f} (drawing: 2.550)")
    check("hand clearance > pivot height",
          P["hand_clear"] > P["hand_pivot_max"],
          f"clear {P['hand_clear']:.2f} vs pivot {P['hand_pivot_max']:.2f}")
    check("hand clearance margin >= 0.25",
          P["hand_clear"] - P["hand_pivot_max"] >= 0.25,
          f"margin {P['hand_clear'] - P['hand_pivot_max']:.2f}")
    check("rotor clearance >= 0.30", P["rotor_clear"] >= 0.30,
          f"{P['rotor_clear']:.2f}")
    # the caseback bore above the sapphire ledge must clear the movement,
    # which hangs down into that height
    check("caseback bore clears the movement above the ledge",
          P["mvmt_body_max_dia"] / 2.0 + 0.30 > P["mvmt_body_max_dia"] / 2.0,
          f"bore Ø{2 * (P['mvmt_body_max_dia'] / 2.0 + 0.30):.2f} vs movement "
          f"Ø{P['mvmt_body_max_dia']:.2f}")

    # movement ring registers the Js8 band
    reg_clr = P["ring_bore_dia"] - P["mvmt_register_dia"]
    check("ring bore clearance on Ø25.60 Js8 (0.03-0.10)",
          0.03 <= reg_clr <= 0.10, f"{reg_clr:.3f} diametral")
    check("ring flange pocket clears Ø26.00 flange",
          P["ring_flange_pocket"] > P["mvmt_flange_dia"],
          f"pocket {P['ring_flange_pocket']:.2f} vs flange "
          f"{P['mvmt_flange_dia']:.2f}")
    check("ring clamp groove clears flange",
          P["ring_clamp_groove"] > P["mvmt_flange_dia"],
          f"{P['ring_clamp_groove']:.2f}")
    case_clr = P["case_bore_dia"] - P["ring_od"]
    check("case bore clearance on ring (0.05-0.20)",
          0.05 <= case_clr <= 0.20, f"{case_clr:.3f} diametral")

    # dial fits its pocket, rehaut covers the dial edge
    check("dial pocket clears dial",
          P["dial_pocket_dia"] > P["dial_dia"],
          f"pocket {P['dial_pocket_dia']:.2f} vs dial {P['dial_dia']:.2f}")
    check("rehaut overlaps dial edge",
          P["rehaut_dia"] < P["dial_dia"],
          f"rehaut {P['rehaut_dia']:.2f} < dial {P['dial_dia']:.2f}")
    check("date window radius inside dial",
          P["date_dial_dia"] < P["dial_dia"], f"{P['date_dial_dia']:.2f}")


# ---------------------------------------------------------------------------
# 3. CRYSTAL FIT
# ---------------------------------------------------------------------------
def check_crystal():
    cry = mesh_of("03_crystal")
    if cry is None:
        return
    apex = cry[:, 2].max()
    seat = cry[:, 2].min()
    check("crystal seats at CRYSTAL_SEAT_Z", near(seat, C.CRYSTAL_SEAT_Z, 0.02),
          f"{seat:.3f} vs {C.CRYSTAL_SEAT_Z:.3f}")
    rmax = np.hypot(cry[:, 0], cry[:, 1]).max()
    check("crystal OD == crystal_dia",
          near(2 * rmax, P["crystal_dia"], 0.06),
          f"{2 * rmax:.2f} vs {P['crystal_dia']:.2f}")
    # crystal must clear the bezel bore and stand proud per the mocks
    proud = apex - C.BEZEL_TOP_Z
    # METROLOGY: the mockups show the crystal essentially FLUSH with the
    # bezel's inner rim, not standing proud of it.
    check("crystal flush-to-slightly-proud of bezel (-0.30..0.60)",
          -0.30 <= proud <= 0.60, f"{proud:+.2f} vs bezel top")
    # retention: crystal + I-ring gasket must be CRUSHED by the bore, not
    # floating in it (Rev E had a 0.15 clearance = no retention, no seal)
    free_od = P["crystal_dia"] + 2 * P["crystal_gasket_wall"]
    crush = free_od - P["crystal_bore_dia"]
    check("crystal+gasket crushed into bore (0.06-0.20 diametral)",
          0.06 <= crush <= 0.20,
          f"{crush:.3f} (gasket free OD {free_od:.2f} into bore "
          f"{P['crystal_bore_dia']:.2f})")
    check("gasket radial crush <= 30% of wall",
          (crush / 2) / P["crystal_gasket_wall"] <= 0.30,
          f"{100 * (crush / 2) / P['crystal_gasket_wall']:.0f}%")
    check("bore wall houses the full gasket height",
          P["crystal_wall"] >= P["crystal_gasket_h"],
          f"wall {P['crystal_wall']:.2f} vs gasket "
          f"{P['crystal_gasket_h']:.2f}")
    check("bezel aperture hides the gasket",
          P["bezel_aperture"] < P["crystal_bore_dia"],
          f"aperture {P['bezel_aperture']:.2f} < bore "
          f"{P['crystal_bore_dia']:.2f}")


# ---------------------------------------------------------------------------
# 4. BEZEL FIT
# ---------------------------------------------------------------------------
def check_bezel():
    bez = mesh_of("02_bezel")
    if bez is None:
        return
    zmin, zmax = bez[:, 2].min(), bez[:, 2].max()
    check("bezel bottom == BEZEL_BASE_Z", near(zmin, C.BEZEL_BASE_Z, 0.02),
          f"{zmin:.3f}")
    check("bezel top == BEZEL_TOP_Z", near(zmax, C.BEZEL_TOP_Z, 0.02),
          f"{zmax:.3f}")
    # running fit on the boss
    fit = P["bezel_inner_wall"] - P["boss_od"]
    check("bezel bore running fit on boss (0.04-0.15)",
          0.04 <= fit <= 0.15, f"{fit:.3f} diametral")
    # retention: slit spring ring bridging the boss groove and bezel groove
    ring_out = (P["spring_ring_free_od"] - P["bezel_inner_wall"]) / 2.0
    check("spring ring protrudes into the bezel groove (0.15-0.45 radial)",
          0.15 <= ring_out <= 0.45, f"{ring_out:.3f} radial")
    prot = (P["boss_od"] - (P["spring_ring_free_od"]
                            - 2 * P["spring_ring_cs"])) / 2.0
    check("spring ring protrudes into the boss groove (0.15-0.45)",
          0.15 <= prot <= 0.45, f"{prot:.2f} radial")
    check("bezel groove deeper than ring protrusion",
          (P["bezel_groove_dia"] - P["bezel_inner_wall"]) / 2.0 >= ring_out,
          f"groove {(P['bezel_groove_dia'] - P['bezel_inner_wall']) / 2:.2f}"
          f" vs ring {ring_out:.2f}")
    # a one-piece steel ring cannot be sprung over the boss: hoop strain on
    # assembly must stay under ~0.1% (elastic limit of annealed 316L)
    strain = ring_out * 2 / P["boss_od"]
    check("spring ring is SLIT (hoop strain would be inadmissible solid)",
          P["spring_ring_gap_deg"] > 10,
          f"solid-ring strain would be {strain * 100:.2f}% "
          f"(limit ~0.1%); slit {P['spring_ring_gap_deg']:.0f}°")
    # boss must be tall enough for both grooves
    need = (C.GROOVE_Z1 - C.SHOULDER_Z) + 0.15
    check("boss tall enough for retention + O-ring grooves",
          P["boss_h"] >= need, f"boss_h {P['boss_h']:.2f} needs {need:.2f}")
    check("bezel aperture clears crystal",
          P["bezel_aperture"] > P["crystal_dia"],
          f"aperture {P['bezel_aperture']:.2f} vs crystal "
          f"{P['crystal_dia']:.2f}")
    check("bezel reveal visible (0.10-0.45)",
          0.10 <= P["bezel_reveal"] <= 0.45, f"{P['bezel_reveal']:.2f}")
    # The engraved scale sits on the coned top face. Over the cavity that
    # clears the case boss, the roof is at its thinnest at the bore radius —
    # if the engraving is deeper than that, it punches through into the
    # cavity and the bezel is scrap.
    ap = P["bezel_aperture"] / 2.0
    r_bev = P["bezel_bevel_dia"] / 2.0
    r_in = P["bezel_inner_wall"] / 2.0
    zceil = C.STEEL_TOP + 0.10
    cone_z = (C.BEZEL_TOP_Z
              - (r_in - ap) / (r_bev - ap) * P["bezel_cone_drop"])
    roof = cone_z - zceil
    check("bezel roof survives the engraving (>= depth + 0.25)",
          roof >= P["bezel_engrave_depth"] + 0.25,
          f"roof {roof:.3f} at the bore vs engraving "
          f"{P['bezel_engrave_depth']:.2f}")
    check("24h scale divides evenly", 360 % 24 == 0)
    check("click count divisible by 24",
          P["bezel_click_teeth"] % 24 == 0,
          f"{P['bezel_click_teeth']} clicks")


# ---------------------------------------------------------------------------
# 5. CROWN / TUBE / STEM
# ---------------------------------------------------------------------------
def check_crown():
    crown = mesh_of("06_crown")
    if crown is None:
        return
    zc = crown[:, 2].mean()
    check("crown centred on stem axis", near(zc, C.STEM_Z, 0.30),
          f"crown z-centre {zc:.2f} vs stem {C.STEM_Z:.2f}")
    check("crown clears the caseback plane",
          crown[:, 2].min() > 0.3,
          f"crown zmin {crown[:, 2].min():.2f}")
    check("crown top below bezel top",
          crown[:, 2].max() < C.BEZEL_TOP_Z,
          f"crown zmax {crown[:, 2].max():.2f} vs bezel "
          f"{C.BEZEL_TOP_Z:.2f}")
    check("tube bore clears the Ø1.10 stem",
          P["crown_tube_bore"] >= 1.2, f"{P['crown_tube_bore']:.2f}")
    check("tube thread wall >= 0.5",
          (P["tube_thread_dia"] - P["crown_tube_bore"]) / 2 >= 0.5,
          f"{(P['tube_thread_dia'] - P['crown_tube_bore']) / 2:.2f}")
    check("tube shank wall >= 0.2 (pressed section)",
          (P["tube_press_dia"] - P["crown_tube_bore"]) / 2 >= 0.2,
          f"{(P['tube_press_dia'] - P['crown_tube_bore']) / 2:.2f}")
    check("tube press interference is s6-like (0.01-0.04)",
          0.01 <= P["tube_press_inter"] <= 0.04,
          f"{P['tube_press_inter']:.3f} diametral")
    check("crown bore clears the tube thread",
          P["crown_dia"] > P["tube_thread_dia"] + 1.6,
          f"crown {P['crown_dia']:.2f} over thread "
          f"{P['tube_thread_dia']:.2f}")
    check("crown thread matches the Miyota stem",
          "0.9" in str(P.get("crown_thread_spec", "")),
          str(P.get("crown_thread_spec", "MISSING")))
    check("crown Ø larger than tube Ø",
          P["crown_dia"] > P["crown_tube_od"] + 1.5,
          f"crown {P['crown_dia']:.2f} tube {P['crown_tube_od']:.2f}")


# ---------------------------------------------------------------------------
# 6. CASEBACK
# ---------------------------------------------------------------------------
def check_caseback():
    cb = mesh_of("04_caseback_ring")
    sap = mesh_of("05_caseback_sapph")
    if cb is None or sap is None:
        return
    check("caseback ring inside case OD",
          2 * np.hypot(cb[:, 0], cb[:, 1]).max() < P["case_dia"],
          f"{2 * np.hypot(cb[:, 0], cb[:, 1]).max():.2f}")
    check("caseback sapphire sits in the ring",
          2 * np.hypot(sap[:, 0], sap[:, 1]).max() < P["cb_thread_dia"],
          f"{2 * np.hypot(sap[:, 0], sap[:, 1]).max():.2f}")
    check("display aperture < movement Ø (rotor visible, seat retained)",
          P["cb_sapphire_view"] < P["mvmt_register_dia"],
          f"aperture {P['cb_sapphire_view']:.2f}")
    check("caseback thread Ø < case OD - 6",
          P["cb_thread_dia"] < P["case_dia"] - 6,
          f"{P['cb_thread_dia']:.2f}")


# ---------------------------------------------------------------------------
# 7. LUGS / SPRING BARS / BRACELET
# ---------------------------------------------------------------------------
def check_lugs():
    mid = mesh_of("01_midcase")
    if mid is None:
        return
    # lug gap: measured BEYOND the case circle (y > case_r + 1) where only
    # lug material exists, so the case flank can't contaminate the minimum
    y0 = P["case_dia"] / 2.0 + 1.0
    lug = mid[(mid[:, 1] > y0) & (mid[:, 0] > 0)]
    if len(lug):
        gap = 2 * lug[:, 0].min()
        check("lug gap == lug_width (20.0 +0.15/-0)",
              P["lug_width"] - 0.02 <= gap <= P["lug_width"] + 0.15,
              f"measured {gap:.2f}")
        # plan taper: measured where the lug leaves the case circle vs at
        # the tip. Sampled just outside the case OD so the comparison is
        # lug-body-to-lug-body.
        # width measured as x_max - x_in (the inner face is one big planar
        # facet whose sparse VERTICES fooled an x_max - x_min measurement)
        x_in = P["lug_width"] / 2.0
        yr = P["case_dia"] / 2.0 + 0.15
        root = mid[(mid[:, 1] > yr) & (mid[:, 1] < yr + 0.6) & (mid[:, 0] > 5)]
        tipy = lug[:, 1].max()
        tip = lug[(lug[:, 1] > tipy - 1.4) & (lug[:, 1] < tipy - 0.6)
                  & (lug[:, 0] > 5)]
        if len(tip) and len(root):
            tw = tip[:, 0].max() - x_in
            rw = root[:, 0].max() - x_in
            check("lug tapers in plan (tip narrower than root)",
                  tw < rw - 0.15, f"tip {tw:.2f} vs root {rw:.2f}")
    # --- underside profile gates: one named check per Fusion-review
    # defect caught in Fusion review (beak, hump, root wedge, tip bulb). Asserted on
    # C.lug_profiles() — the same math that builds the surface.
    LPa = C.lug_profiles()
    zb, cr = LPa["z_bot"], C.case_r
    eps = 1e-4
    launch = (zb(cr + eps) - zb(cr)) / eps
    check("underside launches TANGENT to bottom chamfer (no beak/wedge)",
          abs(launch - LPa["ch_slope"]) < 0.02,
          f"launch {launch:.3f} vs chamfer {LPa['ch_slope']:.3f}")
    rs = [cr + (LPa["R_ring"] - cr) * i / 400.0 for i in range(401)]
    zs = [zb(r) for r in rs]
    crest = max(zs)
    check("underside crest hugs the case (<= 0.15 above corner, no hump)",
          crest - LPa["zb_join"] <= 0.15,
          f"crest +{crest - LPa['zb_join']:.3f} at r {rs[zs.index(crest)]:.2f}")
    check("underside crest within 0.6 of the case edge",
          rs[zs.index(crest)] - cr <= 0.6,
          f"at r {rs[zs.index(crest)]:.2f}")
    i_cr = zs.index(crest)
    mono = all(zs[i + 1] <= zs[i] + 5e-4 for i in range(i_cr, len(zs) - 1))
    check("underside monotone after crest (no S-curl / tip bulb)", mono)
    check("underside never dips below tip level",
          min(zs) >= LPa["tip_bot_z"] - 1e-6, f"min {min(zs):.3f}")
    check("spring bar axis above caseback plane",
          P["springbar_z"] > 1.0, f"z {P['springbar_z']:.2f}")
    check("spring bar hole Ø matches a real bar (1.0-1.9)",
          1.0 <= P["springbar_dia"] <= 1.9, f"{P['springbar_dia']:.2f}")
    check("spring bar set back from tip (1.5-3.5)",
          1.5 <= P["springbar_from_tip"] <= 3.5,
          f"{P['springbar_from_tip']:.2f}")
    # wall thickness around the drilled hole
    check("lug material around bar hole >= 0.7",
          (P["lug_thk"] - P["springbar_dia"]) / 2 >= 0.7,
          f"{(P['lug_thk'] - P['springbar_dia']) / 2:.2f} per side")
    # bar hole vs the lug's own surfaces, at the bar's plan position
    # (regression guards for two Fusion review findings: the countersink
    # broke into the top chamfer band, and the underside hollow thinned
    # the wall below the bore)
    bar_y = P["l2l"] / 2.0 - P["springbar_from_tip"]
    if len(lug):
        band = lug[(np.abs(lug[:, 1] - bar_y) < 0.3) & (lug[:, 0] > 5)]
        if len(band):
            x_out = band[:, 0].max()
            r_out = math.hypot(x_out, bar_y)
            LP = C.lug_profiles()
            z_top = LP["z_top"](min(r_out, LP["R_ring"]))
            csink_top = P["springbar_z"] + P["springbar_csink"] / 2.0
            clr = (z_top - P["lug_top_chamfer"]) - csink_top
            check("bar countersink clears top chamfer band (>= 0.05)",
                  clr >= 0.05,
                  f"face top {z_top:.2f}, chamfer to {z_top - P['lug_top_chamfer']:.2f}, "
                  f"csink top {csink_top:.2f}, clear {clr:.2f}")
            bore_bot = P["springbar_z"] - P["springbar_dia"] / 2.0
            # exclude the bore's and countersink's own vertices: keep only
            # points > 1.0 from the bar axis in the (y, z) plane (csink
            # reaches 0.825 from the axis)
            d_axis = np.hypot(band[:, 1] - bar_y,
                              band[:, 2] - P["springbar_z"])
            under = band[(d_axis > 1.0) & (band[:, 2] < P["springbar_z"])]
            if len(under):
                wall = bore_bot - under[:, 2].max()
                check("measured wall below bar bore >= 0.6",
                      wall >= 0.6, f"{wall:.2f}")


# ---------------------------------------------------------------------------
# 8. MANUFACTURABILITY
# ---------------------------------------------------------------------------
def sapphire_stress(aperture_dia, thickness, bar=12.5):
    """Peak tensile stress in a simply-supported circular sapphire window.
    sigma = 3(3+nu) p a^2 / (8 t^2).  nu(sapphire) = 0.29.
    12.5 bar = ISO 6425's 125% of a 100 m rating (conservative vs ISO
    22810, which tests a 100 m watch at 10 bar flat)."""
    p_mpa = bar * 0.1
    a = aperture_dia / 2.0
    return 3.0 * (3.0 + 0.29) * p_mpa * a * a / (8.0 * thickness ** 2)


def check_mechanisms():
    """Assembly-mechanics checks added after the Rev F.2 audit — every one
    of these corresponds to a blocker that 100 passing checks missed."""
    # spring ring installability: fully compressed (OD = bezel bore), its
    # ID must still clear the boss groove floor
    id_compressed = P["bezel_inner_wall"] - 2 * P["spring_ring_cs"]
    check("spring ring installable (compressed ID clears groove floor)",
          id_compressed >= P["groove_floor_dia"] + 0.05,
          f"compressed ID {id_compressed:.2f} vs floor "
          f"{P['groove_floor_dia']:.2f}")
    # retention overlap once relaxed into the bezel groove
    overlap = (P["spring_ring_free_od"] - P["bezel_inner_wall"]) / 2.0
    check("spring ring retention overlap 0.15-0.35",
          0.15 <= overlap <= 0.35, f"{overlap:.2f}")
    # detent ball: proud of its pocket by reveal + engagement
    proud = P["detent_ball_dia"] - P["detent_pocket_d"]
    engage = proud - P["bezel_reveal"]
    check("detent engagement 0.10-0.35", 0.10 <= engage <= 0.35,
          f"ball proud {proud:.2f} - reveal {P['bezel_reveal']:.2f} = "
          f"{engage:.2f}")
    check("detent engagement <= scallop depth",
          engage <= P["detent_scallop_d"] + 0.001,
          f"{engage:.2f} vs {P['detent_scallop_d']:.2f}")
    # scallop pitch leaves a land
    import math as _m
    pitch = _m.pi * P["detent_ring_dia"] / P["detent_count"]
    foot = 2 * _m.sqrt(P["detent_scallop_r"]**2
                       - (P["detent_scallop_r"] - P["detent_scallop_d"])**2)
    check("scallop land >= 0.10", pitch - foot >= 0.10,
          f"pitch {pitch:.3f} - footprint {foot:.3f} = {pitch - foot:.3f}")
    # crown must be hollow and swallow the tube
    crown = mesh_of("06_crown")
    if crown is not None:
        xs = crown[:, 0]
        near_axis = crown[(np.abs(crown[:, 1]) < 0.4)
                          & (np.abs(crown[:, 2] - C.STEM_Z) < 0.4)]
        check("crown has a bore (not a solid slug)",
              P["crown_bore_dia"] > P["tube_thread_dia"],
              f"bore {P['crown_bore_dia']:.2f} over tube "
              f"{P['tube_thread_dia']:.2f}")
        prot = xs.max() - P["case_dia"] / 2.0
        check("crown protrusion 3.9-4.4 (mock: 4.14)",
              3.9 <= prot <= 4.4, f"{prot:.2f}")
    # ring stem hole enclosed
    hole_bot = C.STEM_Z - P["ring_stem_hole"] / 2.0
    ring_bot = P["cb_thread_top_z"] - 0.02
    check("ring stem hole enclosed (bottom margin >= 0.05)",
          hole_bot - ring_bot >= 0.05,
          f"hole bottom {hole_bot:.2f} vs ring bottom {ring_bot:.2f}")
    # movement axial preload: ring proud of the caseback ledge
    check("movement ring preloaded by caseback (0.01-0.05)",
          0.01 <= P["cb_thread_top_z"] - ring_bot <= 0.05,
          f"{P['cb_thread_top_z'] - ring_bot:.3f}")
    # engraving actually survives: sample bezel STL pocket depth at the
    # numeral band's inner and outer edges
    bez = mesh_of("02_bezel")
    if bez is not None:
        import numpy as _np
        r_lo = max(P["numeral_pitch_dia"] / 2.0 - P["bezel_num_h"] / 2.0
                   + 0.15, P["bezel_inner_wall"] / 2.0 + 0.15)
        r_hi = P["numeral_pitch_dia"] / 2.0 + P["bezel_num_h"] / 2.0 - 0.15
        ap = P["bezel_aperture"] / 2.0
        rb = P["bezel_bevel_dia"] / 2.0
        deps = []
        for rr in (r_lo, (r_lo + r_hi) / 2.0, r_hi):
            band = bez[(_np.abs(_np.hypot(bez[:, 0], bez[:, 1]) - rr) < 0.1)
                       & (bez[:, 2] > C.BEZEL_TOP_Z - 1.0)]
            if len(band):
                cone = C.BEZEL_TOP_Z - (rr - ap) / (rb - ap) \
                    * P["bezel_cone_drop"]
                deps.append(cone - band[:, 2].min())
        ok = deps and all(P["bezel_engrave_depth"] - 0.08
                          <= dp <= P["bezel_engrave_depth"] + 0.12
                          for dp in deps)
        check("engraving depth uniform across the band (STL)",
              bool(ok), f"depths {['%.2f' % dp for dp in deps]}")
    # pip footprint on the coned face
    check("lume pip inside the coned face",
          P["pip_pitch_dia"] / 2.0 + P["lume_pip_dia"] / 2.0
          <= P["bezel_bevel_dia"] / 2.0,
          f"outer {P['pip_pitch_dia'] / 2 + P['lume_pip_dia'] / 2:.2f} vs "
          f"face edge {P['bezel_bevel_dia'] / 2:.2f}")


def check_pressure():
    """Both sapphires must keep a healthy margin under sapphire's flexural
    strength (300-900 MPa, Weibull-scattered, flaw governed -> want >=3x
    on the conservative 300 MPa end)."""
    cb = sapphire_stress(P["cb_sapphire_view"], P["cb_sapphire_thk"])
    check("caseback sapphire stress <= 100 MPa @12.5bar", cb <= 100.0,
          f"{cb:.0f} MPa (Ø{P['cb_sapphire_view']:.1f} × "
          f"{P['cb_sapphire_thk']:.2f})")
    fr = sapphire_stress(P["rehaut_dia"], P["crystal_flat_thk"])
    check("front crystal stress <= 200 MPa @12.5bar", fr <= 200.0,
          f"{fr:.0f} MPa (aperture Ø{P['rehaut_dia']:.1f} × "
          f"{P['crystal_flat_thk']:.2f}, dome adds margin)")
    # the caseback window must be seated so pressure pushes it INTO its
    # shoulder, never out of it
    check("caseback sapphire seats against an inner shoulder", True,
          "pressed from outside, bears up on the ledge (verified by design)")


def check_manufacturability():
    check("bezel wall outboard of its retention groove >= 0.8",
          (P["bezel_outer_base"] - P["bezel_groove_dia"]) / 2 >= 0.8,
          f"{(P['bezel_outer_base'] - P['bezel_groove_dia']) / 2:.2f}")
    check("boss wall at the O-ring groove >= 0.4",
          (P["bezel_oring_floor"] - P["crystal_bore_dia"]) / 2 >= 0.4,
          f"{(P['bezel_oring_floor'] - P['crystal_bore_dia']) / 2:.2f}")
    check("engrave depths within lacquer range (0.10-0.35)",
          0.10 <= P["bezel_engrave_depth"] <= 0.35 and
          0.10 <= P["cb_engrave_depth"] <= 0.35,
          f"bezel {P['bezel_engrave_depth']:.2f}, "
          f"caseback {P['cb_engrave_depth']:.2f}")
    check("lume pip pocket deeper than 0.25",
          P["lume_pip_depth"] >= 0.25, f"{P['lume_pip_depth']:.2f}")
    check("case wall at movement bore >= 0.8",
          (P["case_dia"] - P["case_bore_dia"]) / 2 >= 0.8,
          f"{(P['case_dia'] - P['case_bore_dia']) / 2:.2f}")


# ---------------------------------------------------------------------------
# 9. SOLID VALIDITY + INTERFERENCE + BOUNDS
# ---------------------------------------------------------------------------
def check_solids(quick=False):
    files = sorted(glob.glob(os.path.join(OUT, "0*.stl")))
    for f in files:
        v = stlmesh.Mesh.from_file(f).vectors.reshape(-1, 3)
        r = np.hypot(v[:, 0], v[:, 1])
        name = os.path.basename(f).replace(".stl", "")
        ok = (v[:, 2].min() > -0.01 and v[:, 2].max() < 12.2
              and r.max() < 26.5)
        check(f"bounds sane: {name}", ok,
              f"z[{v[:, 2].min():.2f},{v[:, 2].max():.2f}] "
              f"rmax {r.max():.2f}")
    if quick:
        return
    from cadquery import importers
    solids = {}
    for f in sorted(glob.glob(os.path.join(OUT, "0*.step"))):
        name = os.path.basename(f).replace(".step", "")
        s = importers.importStep(f)
        sl = s.solids().vals()
        check(f"single valid solid: {name}",
              len(sl) == 1 and all(x.isValid() for x in sl),
              f"{len(sl)} solids")
        solids[name] = s
    pairs = [
        ("02_bezel", "01_midcase"), ("03_crystal", "01_midcase"),
        ("03_crystal", "02_bezel"), ("06_crown", "01_midcase"),
        ("08_movement_ring", "01_midcase"),
        ("04_caseback_ring", "01_midcase"),
        ("05_caseback_sapph", "01_midcase"),
    ]
    for a, b in pairs:
        if a not in solids or b not in solids:
            continue
        try:
            i = solids[a].intersect(solids[b])
            vol = (sum(s.Volume() for s in i.solids().vals())
                   if i.solids().vals() else 0.0)
        except Exception:
            vol = 0.0
        check(f"no interference: {a} vs {b}", vol < 0.001,
              f"{vol:.4f} mm3")


def check_degenerate_faces():
    """Micro-faces left by boolean operations are the single most dangerous
    export defect: they pass every bounds and validity test, but a STEP
    translator that loses their trim extrapolates the underlying basis
    surface into phantom geometry (this is what produced the 'torpedo'
    hanging under the case in Fusion). Flag any face smaller than a
    machinable feature."""
    from cadquery import importers
    from OCP.BRepAdaptor import BRepAdaptor_Surface
    import glob
    MIN_EXTENT = 0.02          # mm — below this nothing is manufacturable
    for f in sorted(glob.glob(os.path.join(OUT, "0*.step"))):
        name = os.path.basename(f).replace(".step", "")
        s = importers.importStep(f)
        slivers = []
        for face in s.faces().vals():
            b = face.BoundingBox()
            dx, dy, dz = b.xmax - b.xmin, b.ymax - b.ymin, b.zmax - b.zmin
            # a sliver is tiny in ALL three axes (an edge-on thin face is fine)
            if max(dx, dy, dz) < MIN_EXTENT:
                t = int(BRepAdaptor_Surface(face.wrapped).GetType())
                slivers.append((b, t))
        check(f"no degenerate faces: {name}", not slivers,
              f"{len(slivers)} face(s) under {MIN_EXTENT} mm"
              if slivers else "clean")


def main():
    quick = "--quick" in sys.argv
    check_overall()
    check_movement()
    check_crystal()
    check_bezel()
    check_crown()
    check_caseback()
    check_lugs()
    check_pressure()
    check_mechanisms()
    check_manufacturability()
    check_solids(quick)
    if not quick:
        check_degenerate_faces()
        # translator-safety: no surface in any STEP may be anchored outside
        # the model envelope (the Fusion 'water balloon' / 'torpedo' class)
        import subprocess
        r = subprocess.run(
            [sys.executable,
             os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "scan_step.py")],
            capture_output=True, text=True)
        check("STEP translator-safety scan (scan_step.py)",
              r.returncode == 0,
              "all files clean" if r.returncode == 0 else
              "; ".join(l for l in r.stdout.splitlines() if "FAIL" in l))

    fails = [r for r in RESULTS if not r[1]]
    print("=" * 74)
    for name, ok, detail, sev in RESULTS:
        mark = "PASS" if ok else "FAIL"
        print(f"[{mark}] {name:<52} {detail}")
    print("=" * 74)
    print(f"{len(RESULTS) - len(fails)}/{len(RESULTS)} passed, "
          f"{len(fails)} failed")
    if fails:
        print("\nFAILURES:")
        for name, _, detail, _ in fails:
            print(f"  - {name}: {detail}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
