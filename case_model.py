"""
Kelsus Intercontinental — 39mm GMT case for Miyota 9075
Parametric CAD model (CadQuery). This parameter block IS the spec sheet.

Rev D — bezel/case architecture corrected after Fusion import review:
the case top is now a reduced-diameter BOSS (Ø33.4) that the bezel rotates
around, with a snap groove for the bezel's retaining lip and a 0.20 reveal
between the bezel skirt and the case shoulder (Rev C's full-width case top
interpenetrated the bezel shell). Lug/case junctions are filleted, the case
shoulder + lug top edges carry a chamfer, and the whole stack is 0.68 slimmer.

Movement data verified against Miyota drawing 907500C0: height 5.120, stem
axis 2.550 below dial seat, register Ø25.600 Js8, flange Ø26.000. The flange
sits above the register band, so the movement cases via a MOVEMENT RING
(part 08) loaded from the dial side.

All dimensions in millimetres. Origin: case centre, z = 0 at the exterior
caseback face, +z toward crystal. Lugs on ±Y, crown on +X (3 o'clock).
"""
import math
import os
import cadquery as cq
from cadquery import exporters

# ---------------------------------------------------------------------------
# PARAMETERS  (single source of truth)
# ---------------------------------------------------------------------------
P = dict(
    # --- Movement: Miyota 9075 (official drawing 907500C0) ---------------
    mvmt_h              = 5.12,
    mvmt_flange_dia     = 26.00,
    mvmt_register_dia   = 25.60,
    mvmt_body_max_dia   = 25.50,
    stem_below_dial     = 2.55,   # VERIFIED from drawing
    cs_slot_below_dial  = 2.20,
    hand_pivot_max      = 2.70,   # CHAIN total: 1.20 (GMT Ø2.0) + 0.60
                                  # (hour) + 0.45 (minute) + 0.45 (second)
                                  # — the drawing dims stack, they are NOT
                                  # parallel from one datum. 1.20 was only
                                  # the first link; hands would have hit
                                  # the crystal 1.2 mm deep.
    date_dial_dia       = 23.40,
    date_oclock         = 3,

    # --- Dial (locked: 31 mm) ---------------------------------------------
    dial_dia            = 31.00,
    dial_thk            = 0.40,
    dial_ledge_clear    = 0.05,   # gap dial-top to rehaut ledge: the
                                  # dial is held by the movement stack,
                                  # never pinched by the case
    dial_feet_dia       = 0.70,
    rehaut_dia          = 29.50,

    # --- Overall case -----------------------------------------------------
    case_dia            = 39.0,
    lug_width           = 20.0,
    l2l                 = 47.90,  # METROLOGY: 1090 px tip-to-tip
    material            = "316L stainless",

    # --- Vertical stack (slimmed Rev D) -----------------------------------
    back_recess_z       = 0.10,
    cb_sapphire_thk     = 1.40,   # with the Ø21 aperture below this gives
                                  # ~87 MPa at 12.5 bar (ISO 6425 125% of
                                  # 100 m) = SF 3.4 on sapphire's
                                  # conservative 300 MPa MOR
    cb_thread_dia       = 32.0,   # caseback ring thread pilot (M32x0.5).
                                  # REV G: was M30x0.5 -- the factory DFM
                                  # found the Ø31 dial could not pass ANY
                                  # opening; the dial+movement now loads
                                  # from the back through this thread
                                  # (minor Ø31.46) and the pass bore
    cb_thread_top_z     = 3.50,   # taller caseback barrel: a 2.45 mm ring
                                  # could not hold notches + gasket groove
                                  # + real thread engagement. Internal
                                  # only — does not affect total height.
    rotor_clear         = 0.40,
    hand_clear          = 3.00,   # dial plane -> crystal inner face:
                                  # pivot chain 2.70 + hand hub ~0.25 +
                                  # air. Total height grows to ~12.0 —
                                  # honest physics, documented.
    # derived: Z_DIAL = 0.20+1.20+0.40+5.12 = 6.92 ; STEM_Z = 4.37

    # --- Movement bore / ring ---------------------------------------------
    case_bore_dia       = 31.40,  # REV G: dial pass bore (dial Ø31.0 +
                                  # 0.40); runs to the rehaut ledge
    case_step_dia       = 25.30,
    ring_od             = 31.20,  # POM in the Ø31.40 pass bore: 0.20
                                  # goes to interference when warm
    ring_bore_dia       = 25.65,
    ring_flange_pocket  = 26.15,  # relief for the Ø26.00 band — which sits
                                  # 1.70-2.00 BELOW the dial plane (drawing
                                  # vector trace), not at the top
    flange_pocket_depth = 2.05,   # pocket runs this far below the dial
    ring_clamp_groove   = 26.40,
    ring_stem_hole      = 2.00,   # bottom edge stays 0.1 inside the ring
                                  # (2.20 broke through the bottom face)

    # --- Crystal (slimmed) -------------------------------------------------
    crystal_dia         = 31.40,  # METROLOGY: fills the Ø31.90 aperture.
                                  # 30.60 left a 0.65 mm gap that is not
                                  # in the renders.
    crystal_flat_thk    = 1.40,
    crystal_dome_rise   = 0.45,
    crystal_bore_dia    = 32.00,  # crystal Ø31.40 + I-ring wall 0.35 (free
                                  # OD 32.10) crushed 0.10 diametral.
                                  # (Rev E had a 0.15 CLEARANCE here: the
                                  # crystal was neither retained nor sealed.)
    crystal_wall        = 0.90,   # must house the 0.80-tall I-ring

    # --- Bezel architecture (rotates on the case boss) --------------------
    boss_od             = 34.00,  # case boss the bezel turns on. Grew with
                                  # the Ø32.00 crystal bore so the O-ring
                                  # groove keeps a 0.50 wall to the bore.
    boss_h              = 2.80,   # METROLOGY: bezel total height 3.21 (mine
                                  # was 2.15 at boss_h 1.80). Also gives the
                                  # retention + O-ring grooves proper room.
    groove_floor_dia    = 32.80,  # retention groove floor (0.60 deep):
                                  # ring fully compressed (OD = bezel bore
                                  # 34.10) has ID 32.90 — the floor must
                                  # sit below that or install is impossible
    bezel_reveal        = 0.20,   # gap: case shoulder -> bezel skirt bottom
    bezel_outer_base    = 38.90,  # METROLOGY: essentially FLUSH with the
                                  # Ø39 case (0.05/side). Rev E's 36.8 left
                                  # a 1.1 mm case ring that does not exist
                                  # in the renders.
    bezel_bevel_dia     = 37.93,  # brushed top face runs out to here,
                                  # then a polished chamfer to 38.85 and a
                                  # 0.65 mm vertical flank at 38.90
    bezel_chamfer_dia   = 38.85,
    bezel_flank_h       = 0.30,   # short — the edge tapers via one long
                                  # polished bevel instead of a tall wall
    bezel_cone_drop     = 0.80,   # steeper taper (~15°): more svelte edge
    bezel_aperture      = 31.90,  # METROLOGY (polished inner chamfer from
                                  # 31.69)
    bezel_inner_cham    = 31.69,
    bezel_inner_wall    = 34.10,  # H7 over the h7 boss = 0.10 diametral
                                  # running fit; the O-ring does the
                                  # centring and damping
    # Retention is a separate SLIT SPRING RING (part 09), not an integral
    # lip: 0.20 mm radial snap on a one-piece steel bezel is ~1.2% hoop
    # strain, roughly 11x the elastic limit of annealed 316L — it could
    # never be assembled. A slit ring changes diameter by bending instead.
    bezel_groove_dia    = 34.70,  # internal groove in the bezel bore
    bezel_groove_w      = 0.70,
    spring_ring_free_od = 34.60,  # relaxed OD (springs out into the bezel)
    spring_ring_cs      = 0.60,   # square-ish section
    spring_ring_gap_deg = 40.0,   # slit opening
    bezel_rise          = 0.90,   # boss top -> bezel top face. At 0.55 the
                                  # roof over the boss cavity was only 0.216
                                  # thick at the bore radius and the 0.25
                                  # engraving punched THROUGH it. Also puts
                                  # the crystal flush with the bezel rim,
                                  # which is what the mockups show.
    bezel_click_teeth   = 120,
    bezel_skirt         = 0.55,   # coin-edge grip band height
    bezel_grip_count    = 72,
    bezel_num_h         = 1.70,   # METROLOGY: cap height at pitch Ø34.88
    numeral_pitch_dia   = 35.30,  # METROLOGY (2nd pass, mock re-measure)
    triangle_pitch_dia  = 34.80,  # METROLOGY (2nd pass)
    triangle_radial     = 0.87,   # METROLOGY
    triangle_tangential = 0.93,   # METROLOGY
    bezel_engrave_depth = 0.25,   # pockets for black lacquer fill
    lume_pip_dia        = 0.80,
    pip_pitch_dia       = 33.10,  # INBOARD of the numerals (R16.55): the
                                  # band outboard of them is only 0.47 wide,
                                  # and a pip overlapping the '24' glyph
                                  # cuts left a boolean artifact plug
    lume_pip_depth      = 0.35,

    # --- Case flank / edges ------------------------------------------------
    shoulder_chamfer    = 0.45,   # top outer edge, continues over lug roots
    lug_top_chamfer     = 0.45,
    junction_fillet     = 0.50,   # lug-to-case blend
    bottom_edge_r       = 17.9,
    bottom_chamfer      = 0.6,
    case_bottom_ch      = 0.30,   # bottom-edge chamfer at the flank/tuck
                                  # corner — mirrors the top's treatment so
                                  # the lug undersides blend seamlessly.
                                  # 0.30 keeps the Ø39 end-link land down
                                  # to z 1.60 (end link lower lip ~1.6)

    # --- Crown + tube (screw-down, ~100m) --------------------------------
    crown_dia           = 6.25,   # METROLOGY (6.28 top / 6.22 side)
    crown_h             = 3.85,   # total protrusion past the case OD is
                                  # 4.0 per metrology; the tube hides
                                  # inside the crown when screwed down
    crown_endband       = 1.2,
    crown_bore_dia      = 3.95,   # slides over the Ø3.90 tube thread
                                  # (female thread = machining callout)
    crown_gasket_bore   = 4.60,   # counterbore at the mouth: crown O-ring
    crown_gasket_depth  = 0.80,
    crown_case_gap      = 0.30,   # skirt-to-flank gap when screwed down
    crown_tube_od       = 3.6,
    crown_tube_bore     = 2.0,
    crown_tube_ext      = 1.8,
    crown_flute_count   = 28,
    logo_depth          = 0.30,   # Kelsus K from the logo SVG

    # --- Caseback engraving ----------------------------------------------
    cb_engrave_text     = "KELSUS  INTERCONTINENTAL",
    cb_engrave_depth    = 0.18,
    cb_sapphire_view    = 21.0,   # shrinking the clear aperture buys
                                  # safety factor at zero cost in height

    # --- Lugs --------------------------------------------------------------
    lug_thk             = 3.6,
    lug_root_y          = 11.0,   # below the flank tangency (y≈11.5)
    # Spring bars: committed to the SPORTS/Oyster standard — Ø2.0 mm bar
    # with Ø1.2 mm tips (Rolex FB-7895 pattern), so the hole is tip+0.15
    # per ISO 3765's "hole = tip + ~0.2" rule. (Ø1.10 would be the ISO
    # dress-watch bore for a 0.9 mm tip — correct, but under-specced for a
    # GMT on an Oyster bracelet.)
    springbar_dia       = 1.35,
    springbar_z         = 2.70,   # end-link underside finishes flush with
                                  # the lug underside; the bar + countersink
                                  # must also clear the top chamfer band
    lug_tip_top_z       = 3.85,   # tip face 0.30-3.85 = 3.55 thick; also
                                  # keeps the top surface high enough over
                                  # the bar hole that the countersink
                                  # cannot break into the top chamfer
    lug_dive_r0         = 19.4,   # top dive starts past the case edge
    springbar_from_tip  = 2.2,
    springbar_csink     = 1.65,   # 90° countersink Ø on both faces
    springbar_csink_d   = 0.15,
    endlink_land_z      = 1.30,   # Ø39 land carried down to here (Oyster)
    lug_tangent_inset   = 0.06,   # the lug flank arc is solved tangent to a
                                  # circle this much SMALLER than the case, so
                                  # it merges transversally instead of
                                  # tangentially. Exact tangency makes the
                                  # union leave 0.01 mm degenerate sliver
                                  # faces, which STEP translators (Fusion)
                                  # extrapolate into phantom blobs.
    lug_tangent_deg     = 30.0,   # azimuth where the lug flank leaves the
                                  # case circle. Solved for METROLOGY's
                                  # 3.30 root width; 36 gave no taper at all.
    lug_tip_w           = 2.90,   # plan width at the tip before the corner
                                  # rounds (metrology tip 2.74 after)

    # --- ATTACHMENT / SEALING (Rev F) -------------------------------------
    # caseback screw thread + gasket
    cb_thread_pitch     = 0.50,
    cb_thread_depth     = 0.28,   # radial cut depth of the thread relief
    cb_thread_len       = 1.80,   # axial length of the threaded band
    cb_ledge_thk        = 0.15,   # sapphire retaining ledge thickness;
                                  # above it the bore MUST open out to
                                  # clear the rotor
    cb_oring_cs         = 0.70,   # O-ring cross-section Ø
    cb_oring_groove_w   = 0.90,   # groove width
    cb_oring_groove_d   = 0.50,   # groove depth (~22% compression)
    cb_notch_count      = 6,      # case-wrench notches
    cb_notch_w          = 2.00,   # fits a standard 2.0 mm wrench pin
    cb_notch_d          = 1.00,   # inside-notch Ø = OD - 2.0 (tool grips here)
    cb_sapphire_seat_c  = 0.10,   # lead-in chamfer; MUST be < cb_ledge_thk

    # crown tube thread + gaskets
    tube_thread_dia     = 3.90,   # crown screws onto this (Ø3.6 is not a
                                  # size tubes are actually made in)
    tube_thread_pitch   = 0.35,
    tube_thread_depth   = 0.22,
    tube_press_dia      = 2.50,   # pressed shank; case bore Ø2.50 H7, s6
    tube_press_inter    = 0.02,   # s6 interference + anaerobic retainer
                                  # (the retainer, not the fit, is the seal)
    crown_thread_spec   = 'S0.9 x 0.225 (Tap 10)',  # CONFIRMED: Miyota
                                  # drawing sheet 3, setting stem 065-A05
    crown_oring_cs      = 0.70,   # crown O-ring cross-section
    crown_oring_groove_d = 0.50,

    # bezel click detent
    detent_ball_dia     = 1.00,   # spring-loaded ball in the case shoulder
    detent_pocket_d     = 0.65,   # ball proud 0.35 = reveal 0.20 +
                                  # 0.15 engagement into the scallops
                                  # (0.80 left exactly 0.00 engagement)
    bezel_oring_floor   = 33.00,  # centring/damping O-ring groove on boss
    bezel_oring_w       = 0.95,
    bezel_oring_cs      = 0.70,
    detent_ring_dia     = 36.40,  # PCD of the scallop ring on the bezel.
                                  # Must clear the bezel bore (Ø34.10) by
                                  # more than the scallop radius or the
                                  # scallops break through the bore wall
                                  # and split the part.
    detent_scallop_r    = 0.50,   # = ball radius, so the ball nests
    detent_scallop_d    = 0.18,   # footprint Ø0.77 < 0.953 pitch: real
                                  # lands between scallops (Ø1.2 scallops
                                  # overlapped into a continuous groove)
    detent_count        = 120,

    # crystal retention
    crystal_gasket_wall = 0.35,   # I-ring wall (Sternkreuz/Otto Frei stock)
    crystal_gasket_h    = 0.80,   # I-ring height for a 1.40 crystal
    crystal_seat_ledge  = 0.55,   # radial width the crystal rests on
    crystal_lead_c      = 0.25,   # bore lead-in chamfer
)

OUT = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUT, exist_ok=True)

AXIS = 0.0            # revolve profiles may touch the axis; a 1e-4
                      # offset wrote a 0.2 um pinhole into the crystal
case_r = P["case_dia"] / 2.0
Z_DIAL = (P["back_recess_z"] + P["cb_sapphire_thk"] + P["cb_ledge_thk"]
          + P["rotor_clear"] + P["mvmt_h"])
# REV G: the dial (Ø31.0) loads FROM THE BACK through the M32x0.5 thread
# and the Ø31.40 pass bore, and is retained by the rehaut ledge. The dial
# top stops dial_ledge_clear below the ledge; the movement stack (ring
# preloaded by the caseback) holds it there.
DIAL_LEDGE_Z = Z_DIAL + P["dial_thk"] + P["dial_ledge_clear"]
STEM_Z = Z_DIAL - P["stem_below_dial"]
CRYSTAL_SEAT_Z = Z_DIAL + P["hand_clear"]
STEEL_TOP = CRYSTAL_SEAT_Z + P["crystal_wall"]          # boss top
SHOULDER_Z = STEEL_TOP - P["boss_h"]                    # case shoulder plane
BEZEL_BASE_Z = SHOULDER_Z + P["bezel_reveal"]           # bezel skirt bottom
COIN_TOP_Z = BEZEL_BASE_Z + P["bezel_skirt"]
BEZEL_TOP_Z = STEEL_TOP + P["bezel_rise"]
CRYSTAL_APEX = CRYSTAL_SEAT_Z + P["crystal_flat_thk"] + P["crystal_dome_rise"]
ORING_Z0 = SHOULDER_Z + 0.10           # centring O-ring groove
ORING_Z1 = ORING_Z0 + P["bezel_oring_w"]
GROOVE_Z0 = ORING_Z1 + 0.10            # retention groove ABOVE the O-ring
GROOVE_Z1 = GROOVE_Z0 + 0.60           # groove — hard-coding 0.75 made the
                                       # two grooves overlap 0.30 in z and
                                       # the revolve profile self-intersect
assert ORING_Z1 < GROOVE_Z0 < GROOVE_Z1 < STEEL_TOP - 0.5, "boss grooves"

# expose derived values for the spec-sheet builder
P["steel_top_z"] = STEEL_TOP
P["bezel_base_z"] = BEZEL_BASE_Z
P["bezel_top_z"] = BEZEL_TOP_Z


def keep_largest(wp):
    solids = wp.solids().vals()
    if len(solids) <= 1:
        return wp
    return cq.Workplane(obj=max(solids, key=lambda s: abs(s.Volume())))



def arc_samples(S, M, E, n=9):
    """Sample n points along the circular arc through S, M, E (from S to E).

    Used to replace threePointArc with a SPLINE in REVOLVED profiles.
    Reason: OCCT writes a revolved arc as SURFACE_OF_REVOLUTION whose basis
    curve is the FULL circle. The lug-ring arcs have centers 20-50 mm below
    the watch and their circles CROSS the rotation axis — if a translator
    (Fusion) loses the face trim, it renders the full revolution: a giant
    onion with a downward apex hanging under the case. A spline basis curve
    is inherently bounded, so the untrimmed surface is just the swept band.
    """
    (ax, ay), (bx, by), (cx, cy) = S, M, E
    d = 2.0 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay)
          + (cx * cx + cy * cy) * (ay - by)) / d
    uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx)
          + (cx * cx + cy * cy) * (bx - ax)) / d
    R = math.hypot(ax - ux, ay - uy)
    a0 = math.atan2(ay - uy, ax - ux)
    am = math.atan2(by - uy, bx - ux)
    a1 = math.atan2(cy - uy, cx - ux)
    # sweep from a0 through am to a1
    d1 = (am - a0 + math.pi) % (2 * math.pi) - math.pi
    d2 = (a1 - am + math.pi) % (2 * math.pi) - math.pi
    total = d1 + d2
    return [(ux + R * math.cos(a0 + total * i / (n - 1)),
             uy + R * math.sin(a0 + total * i / (n - 1))) for i in range(n)]


def compound(parts):
    """Fuse a list of Workplanes/Shapes into ONE compound for a single
    boolean. Sequential .union() of many small solids accumulates OCCT
    state until the process is killed (SIGKILL, uncatchable) — this is the
    pattern that must be used for glyphs, notches, teeth and drillings."""
    shapes = []
    for p in parts:
        if p is None:
            continue
        shapes.extend(p.vals() if hasattr(p, "vals") else [p])
    return cq.Compound.makeCompound(shapes)


def arc_mid_vtan(S, E):
    """Midpoint of the circular arc from S to E whose tangent at S is
    VERTICAL (parallel to the profile's z axis).

    A free threePointArc bulges outside the chord — that is how the case
    waist crept 0.08 past Ø39 and how the lug horns once grew above the
    case top. Constraining the tangent makes the arc leave S at exactly
    the start radius and curve monotonically inward, so it can never
    exceed it. Centre lies on the horizontal through S.
    """
    (s_r, s_z), (e_r, e_z) = S, E
    dr, dz = e_r - s_r, e_z - s_z
    if abs(dr) < 1e-9:
        return ((s_r + e_r) / 2.0, (s_z + e_z) / 2.0)
    # |C - E| = R with C = (s_r - R*sgn, s_z)  =>  solve for R
    sgn = 1.0 if dr < 0 else -1.0          # centre sits on the inboard side
    R = (dr * dr + dz * dz) / (-2.0 * dr * sgn)
    c_r, c_z = s_r - R * sgn, s_z
    a0 = math.atan2(s_z - c_z, s_r - c_r)
    a1 = math.atan2(e_z - c_z, e_r - c_r)
    da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi   # minor arc
    am = a0 + da / 2.0
    return (c_r + R * math.cos(am), c_z + R * math.sin(am))


class MidpointSelector(cq.selectors.Selector):
    """Select edges by a predicate on the edge object."""
    def __init__(self, pred):
        self.pred = pred

    def filter(self, objectList):
        out = []
        for o in objectList:
            try:
                if self.pred(o):
                    out.append(o)
            except Exception:
                pass
        return out


# ---------------------------------------------------------------------------
# MIDCASE  (revolved; NOTE: revolve axis is workplane-LOCAL (0,1,0) on "XZ")
# ---------------------------------------------------------------------------
def build_midcase_outer():
    """OUTER solid only — no internal bores. Internal cavities are cut AFTER
    the lugs are unioned on (see build_internal_void), because the lug ring
    otherwise leaves slivers of material inside the movement cavity where
    the plan prisms dip below the case circle."""
    p = P
    r_boss = p["boss_od"] / 2.0                # 16.70
    r_grv  = p["groove_floor_dia"] / 2.0       # 16.70
    r_org  = p["bezel_oring_floor"] / 2.0      # 16.50
    ch     = p["shoulder_chamfer"]

    return (
        cq.Workplane("XZ")
        .moveTo(AXIS, 0.0)
        .lineTo(AXIS, STEEL_TOP)                       # axis
        .lineTo(r_boss, STEEL_TOP)                       # boss top face
        .lineTo(r_boss, GROOVE_Z1)                       # boss outer wall
        .lineTo(r_grv, GROOVE_Z1)                        # retention groove
        .lineTo(r_grv, GROOVE_Z0)
        .lineTo(r_boss, GROOVE_Z0)
        .lineTo(r_boss, ORING_Z1)                        # boss wall
        .lineTo(r_org, ORING_Z1)                         # O-ring groove:
        .lineTo(r_org, ORING_Z0)                         # centres and damps
        .lineTo(r_boss, ORING_Z0)                        # the bezel
        .lineTo(r_boss, SHOULDER_Z)
        .lineTo(case_r - ch, SHOULDER_Z)                 # shoulder ledge
        .lineTo(case_r, SHOULDER_Z - ch)                 # top-edge chamfer
        # vertical (cylindrical) flank at Ø39.0 over the whole lug zone —
        # the lugs' plan-tangent flanks then join it seamlessly at EVERY
        # height, no OCCT junction fillet needed (those segfault)
        # Ø39 CYLINDRICAL LAND carried down to endlink_land_z. An Oyster
        # solid end link seats against this with a concave nose of matching
        # radius; if the flank curves away inside the end link's contact
        # band the link rocks and gaps. Previously the land stopped at 4.2,
        # 1.6 above the spring-bar axis, losing 0.8 of radius across the
        # contact height.
        .lineTo(case_r, p["endlink_land_z"] + p["case_bottom_ch"])
        # bottom-edge chamfer: lands on the tuck line so the tuck cone
        # below is unchanged
        .lineTo(case_r - p["case_bottom_ch"],
                p["bottom_chamfer"]
                + ((p["endlink_land_z"] - p["bottom_chamfer"])
                   / (case_r - p["bottom_edge_r"]))
                * (case_r - p["case_bottom_ch"] - p["bottom_edge_r"]))
        # tangent-constrained: leaves the flank vertically at Ø39 and curves
        # monotonically inward, so the waist cannot bulge past the case OD
        # straight conical tuck: the vertical-tangent arc dipped 0.25
        # BELOW its own endpoint, machining an undercut groove all round
        .lineTo(p["bottom_edge_r"], p["bottom_chamfer"])
        .lineTo(p["bottom_edge_r"] - p["bottom_chamfer"], 0.0)
        .close()
        .revolve(360, (0, 0, 0), (0, 1, 0))
    )


def build_internal_void():
    """Cutting tool for every internal cavity: caseback thread bore, movement
    bore, dial pass bore, rehaut, crystal seat. Cut after the lug union."""
    p = P
    r_cb   = p["cb_thread_dia"] / 2.0
    r_bore = p["case_bore_dia"] / 2.0
    r_reh  = p["rehaut_dia"] / 2.0
    r_cry  = p["crystal_bore_dia"] / 2.0

    return (
        cq.Workplane("XZ")
        .moveTo(AXIS, -0.5)
        .lineTo(r_cb, -0.5)
        .lineTo(r_cb, p["cb_thread_top_z"])              # caseback bore
        .lineTo(r_bore, p["cb_thread_top_z"])
        .lineTo(r_bore, DIAL_LEDGE_Z)                    # dial pass bore:
                                                         # dial + movement
                                                         # enter from the
                                                         # back (REV G)
        .lineTo(r_reh, DIAL_LEDGE_Z)                     # rehaut ledge
                                                         # retains the dial
        .lineTo(r_reh, CRYSTAL_SEAT_Z)
        .lineTo(r_cry, CRYSTAL_SEAT_Z)                   # crystal seat
        .lineTo(r_cry, STEEL_TOP - P["crystal_lead_c"])
        .lineTo(r_cry + P["crystal_lead_c"], STEEL_TOP)  # lead-in chamfer:
                                                         # without it the
                                                         # I-ring shears on
                                                         # pressing
        .lineTo(r_cry + P["crystal_lead_c"], STEEL_TOP + 0.5)
        .lineTo(AXIS, STEEL_TOP + 0.5)
        .close()
        .revolve(360, (0, 0, 0), (0, 1, 0))
    )


# ---------------------------------------------------------------------------
# LUGS — horn profile, plan-tapered, chamfered, capped under the bezel
# ---------------------------------------------------------------------------
def _herm(t, z0, m0, z1, m1, L):
    h00 = 2*t**3 - 3*t**2 + 1
    h10 = t**3 - 2*t**2 + t
    h01 = -2*t**3 + 3*t**2
    h11 = t**3 - t**2
    return h00*z0 + h10*L*m0 + h01*z1 + h11*L*m1


def lug_profiles():
    """The lug cross-section curves, shared by build_lugs() AND
    verify_case.py — the checks assert on exactly the math that builds
    the surfaces, so a profile change cannot dodge the gates.

    TOP: flat at the case shoulder through the root, smoothstep dive to
    the tip after clearing the case edge (zero slope both ends).

    UNDERSIDE (the shape that finally landed after three Fusion-review
    defects — the beak, the hump, the acute root wedge):
      * inboard it follows the case's own bottom surfaces at +0.03
        (tuck cone, then the bottom-edge chamfer facet),
      * it leaves the case EXACTLY TANGENT to the chamfer — a slope
        mismatch reads as a beak, a level shelf leaves a knife-edge
        air wedge over the receding chamfer,
      * the climb turns over within 0.40 mm at a crest only 0.10 above
        the case corner — fillet-scale, hugging the case, unlike the
        0.4 mm hollow-climb that read as a hump,
      * then ONE monotone hermite runs to the tip (m1 = -0.20 swoop),
        straight into the tip face at z 0.30 — no under-tip S-curl
        (that curl showed as a bulbous chin under the bar holes)."""
    p = P
    x_in = p["lug_width"] / 2.0
    y_tip = p["l2l"] / 2.0 + 0.48              # corner rounds eat the extremity
    R_ring = math.hypot(x_in, y_tip)           # ring outer radius (~26.4)
    z_flat = SHOULDER_Z - 0.005                # hair below the exclusion cap
    dive_r0 = p["lug_dive_r0"]
    tip_top_z = p["lug_tip_top_z"]

    def z_top(rr):
        if rr <= dive_r0:
            return z_flat
        t = (rr - dive_r0) / (R_ring - dive_r0)
        ss = 3 * t * t - 2 * t ** 3
        return z_flat - (z_flat - tip_top_z) * ss

    tuck_slope = ((p["endlink_land_z"] - p["bottom_chamfer"])
                  / (case_r - p["bottom_edge_r"]))
    ch_b = p["case_bottom_ch"]
    r_ch = case_r - ch_b                       # chamfer facet inner radius
    z_ch0 = (p["bottom_chamfer"]
             + tuck_slope * (r_ch - p["bottom_edge_r"]) + 0.03)
    zb_join = p["endlink_land_z"] + ch_b + 0.03
    ch_slope = (zb_join - z_ch0) / ch_b        # chamfer facet slope
    tip_bot_z = 0.30
    r_crest = case_r + 0.40
    z_crest = zb_join + 0.10

    def z_bot(rr):
        if rr <= r_ch:                         # tuck cone +0.03
            return (p["bottom_chamfer"] + 0.03
                    + tuck_slope * (rr - p["bottom_edge_r"]))
        if rr <= case_r:                       # chamfer facet +0.03
            return z_ch0 + ch_slope * (rr - r_ch)
        if rr <= r_crest:                      # tangent launch, tight crest
            return _herm((rr - case_r) / (r_crest - case_r),
                         zb_join, ch_slope, z_crest, 0.0, r_crest - case_r)
        return _herm((rr - r_crest) / (R_ring - r_crest),
                     z_crest, 0.0, tip_bot_z, -0.20, R_ring - r_crest)

    return dict(R_ring=R_ring, z_flat=z_flat, z_top=z_top, z_bot=z_bot,
                dive_r0=dive_r0, tip_top_z=tip_top_z, tip_bot_z=tip_bot_z,
                zb_join=zb_join, ch_slope=ch_slope, r_ch=r_ch, z_ch0=z_ch0,
                r_crest=r_crest, z_crest=z_crest)


def build_lugs():
    """Ring-cut construction (a classic watchmaking approach): revolve the
    lug cross-section into a full ring around the case — 'a metal disc all
    the way around whose cross-section is lug shaped' — then cut away
    everything that isn't lug with the four plan prisms. The root junction
    with the case is circular by construction (both are revolves), so the
    lugs join the body cleanly at every azimuth, and the ring's outer
    cylinder IS the 'tips on a larger circle'. Arc-bounded profiles, no
    mirrors, no OCCT junction fillets (they segfault)."""
    p = P
    x_in   = p["lug_width"] / 2.0
    y_root = p["lug_root_y"]
    tip_w  = p["lug_tip_w"]
    LP = lug_profiles()
    R_ring = LP["R_ring"]
    z_flat = LP["z_flat"]
    dive_r0 = LP["dive_r0"]
    z_top, z_bot = LP["z_top"], LP["z_bot"]
    tip_bot_z = LP["tip_bot_z"]
    zb_join, ch_slope = LP["zb_join"], LP["ch_slope"]
    r_ch, z_ch0 = LP["r_ch"], LP["z_ch0"]

    ease = [dive_r0 + (R_ring - dive_r0) * i / 8.0 for i in range(1, 9)]
    top_pts = ([(y_root, z_flat), (15.0, z_flat), (dive_r0, z_flat)]
               + [(rr, z_top(rr)) for rr in ease])
    # dense samples through the short crest, then the long dive
    ease_b = ([case_r + 0.12, case_r + 0.26, LP["r_crest"]]
              + [LP["r_crest"] + (R_ring - LP["r_crest"]) * i / 8.0
                 for i in range(1, 8)])
    bot_pts = ([(y_root, 0.63), (p["bottom_edge_r"], 0.63),
                (r_ch, z_ch0), (case_r, zb_join)]
               + [(rr, z_bot(rr)) for rr in ease_b]
               + [(R_ring, tip_bot_z)])

    def interp(pts, r):
        for (r0, z0), (r1, z1) in zip(pts, pts[1:]):
            if r <= r1:
                return z0 + (z1 - z0) * (r - r0) / max(r1 - r0, 1e-9)
        return pts[-1][1]

    ring = (
        cq.Workplane("XZ")
        .moveTo(y_root, z_flat)
        # ONE spline for the whole top (collinear flat points + eased dive,
        # end tangents pinned horizontal): a line+spline chain makes the
        # top boundary multi-edge and OCCT's chamfer refuses the chain
        .spline([(14.0, z_flat), (17.0, z_flat), (dive_r0, z_flat)]
                + [(rr, z_top(rr)) for rr in ease],
                tangents=((1.0, 0.0), (1.0, 0.0)),
                includeCurrent=True)
        .lineTo(R_ring, tip_bot_z)             # tip face straight to the
        # bottom — no under-tip S-curl (it read as a bulbous chin).
        # Underside spline: starts tangent-matched to the dive (+0.20
        # inward), ends tangent-matched to the case's bottom chamfer.
        .spline([(rr, z_bot(rr)) for rr in reversed(ease_b)]
                + [(case_r, zb_join)],
                tangents=((-1.0, 0.20), (-1.0, -ch_slope)),
                includeCurrent=True)
        .lineTo(r_ch, z_ch0)                   # follows the case bottom-edge
        .lineTo(p["bottom_edge_r"], 0.63)      # chamfer, then the tuck cone
        .lineTo(y_root, 0.63)                  # buried inside the case
        .close()
        .revolve(360, (0, 0, 0), (0, 1, 0))
    )


    def plan_prism(sx):
        Rc = case_r - p["lug_tangent_inset"]
        theta_p = math.radians(p["lug_tangent_deg"])
        Px, Py = Rc * math.cos(theta_p), Rc * math.sin(theta_p)
        ux, uy = Px / Rc, Py / Rc
        # tip face: arc at Rt, 0.05 inside the ring cylinder (coincident
        # boolean faces are fragile) with plan-view corner rounds — all
        # surfaces here are vertical, so a plan arc IS the 3D round and no
        # OCCT fillet is needed (the tip fillet was the last segfault source)
        Rt = R_ring - 0.05
        rf = 0.8                                     # tip corner round
        Tx = x_in + tip_w
        Ty = math.sqrt(Rt**2 - Tx**2)
        # outer flank arc, tangent to the case circle at P, aimed at T
        TdotU = Tx * ux + Ty * uy
        b = (Tx**2 + Ty**2 - Rc**2) / (2 * TdotU - 2 * Rc)
        R2 = b - Rc
        Cx, Cy = b * ux, b * uy

        # corner A round: tangent to inner face (x = x_in) and tip circle
        Acx = x_in + rf
        Acy = math.sqrt((Rt - rf)**2 - Acx**2)
        A_line = (x_in, Acy)                         # tangent on inner face
        kA = Rt / (Rt - rf)
        A_tip = (Acx * kA, Acy * kA)                 # tangent on tip circle
        angL = math.pi                               # centre -> line tangent
        angT = math.atan2(Acy, Acx)                  # centre -> tip tangent
        angM = angT + ((angL - angT) % (2 * math.pi)) / 2.0
        A_mid = (Acx + rf * math.cos(angM), Acy + rf * math.sin(angM))

        # corner B round: tangent to tip circle and to the flank arc
        # centre: |Bc| = Rt - rf  and  |Bc - C2| = R2 + rf
        d = math.hypot(Cx, Cy)
        r1, r2 = Rt - rf, R2 + rf
        a_ = (r1**2 - r2**2 + d**2) / (2 * d)
        h_ = math.sqrt(max(r1**2 - a_**2, 0.0))
        ux2, uy2 = Cx / d, Cy / d
        Bcx = a_ * ux2 - h_ * uy2                    # +perp side: lug side
        Bcy = a_ * uy2 + h_ * ux2
        kB = Rt / (Rt - rf)
        B_tip = (Bcx * kB, Bcy * kB)                 # tangent on tip circle
        kf = R2 / (R2 + rf)
        B_flank = (Cx + (Bcx - Cx) * kf, Cy + (Bcy - Cy) * kf)
        angBT = math.atan2(B_tip[1] - Bcy, B_tip[0] - Bcx)
        angBF = math.atan2(B_flank[1] - Bcy, B_flank[0] - Bcx)
        dB = (angBF - angBT) % (2 * math.pi)
        if dB > math.pi:
            dB -= 2 * math.pi
        angBM = angBT + dB / 2.0
        B_mid = (Bcx + rf * math.cos(angBM), Bcy + rf * math.sin(angBM))

        # tip arc midpoint between the two corner tangents
        angA = math.atan2(A_tip[1], A_tip[0])
        angB = math.atan2(B_tip[1], B_tip[0])
        angTM = (angA + angB) / 2.0
        T_mid = (Rt * math.cos(angTM), Rt * math.sin(angTM))

        # flank arc midpoint from B_flank down to P
        a_Bf = math.atan2(B_flank[1] - Cy, B_flank[0] - Cx)
        a_P = math.atan2(Py - Cy, Px - Cx)
        da = (a_P - a_Bf) % (2 * math.pi)
        if da > math.pi:
            da -= 2 * math.pi
        a_M = a_Bf + da / 2.0
        Mx, My = Cx + R2 * math.cos(a_M), Cy + R2 * math.sin(a_M)
        # inner-corner blend: arc tangent to BOTH the inner face (x = x_in)
        # and the case circle — both surfaces are near-vertical, so this
        # plan-view arc IS the 3D blend (no fragile OCCT fillet needed)
        Rb = 1.2
        bx = x_in - Rb
        by = math.sqrt((Rc + Rb)**2 - bx**2)
        qx_, qy_ = (Rc / (Rc + Rb)) * bx, (Rc / (Rc + Rb)) * by  # on circle
        a0 = math.atan2(by - by, x_in - bx)          # = 0: line-tangent pt
        a1 = math.atan2(qy_ - by, qx_ - bx)
        am = (a0 + a1) / 2.0 if a1 < a0 else (a0 + a1 - 2 * math.pi) / 2.0
        bmx, bmy = bx + Rb * math.cos(am), by + Rb * math.sin(am)
        return (
            cq.Workplane("XY")
            .moveTo(sx * (qx_ - 0.4), by - Rb - 6.0)  # start deep in the case
            .lineTo(sx * qx_, qy_)                    # up inside the circle
            .threePointArc((sx * bmx, bmy), (sx * x_in, by))  # corner blend
            .lineTo(sx * x_in, A_line[1])             # straight inner face
            .threePointArc((sx * A_mid[0], A_mid[1]),
                           (sx * A_tip[0], A_tip[1]))         # corner A round
            .threePointArc((sx * T_mid[0], T_mid[1]),
                           (sx * B_tip[0], B_tip[1]))         # tip arc
            .threePointArc((sx * B_mid[0], B_mid[1]),
                           (sx * B_flank[0], B_flank[1]))     # corner B round
            .spline([(sx * q[0], q[1]) for q in
                     arc_samples(B_flank, (Mx, My), (Px, Py))[1:]],
                    includeCurrent=True)                      # tangent flank
            .lineTo(sx * (qx_ - 0.4), by - Rb - 6.0)
            .close()
            .extrude(12)
            .translate((0, 0, -0.5))
        )

    # top-boundary edges (top face vs plan-cut flanks + tip), by RADIUS —
    # the ring's top surface is toroidal, z depends on r not y. One chain
    # all the way around the top including the tip arc, so the chamfer
    # cannot stop partway (Fusion review finding).
    def is_top_edge(e):
        pt = e.positionAt(0.5)
        r = math.hypot(pt.x, pt.y)
        if r < 10.6:
            return False
        mid = (interp(top_pts, min(r, R_ring)) +
               interp(bot_pts, min(r, R_ring))) / 2.0
        return pt.z > mid

    # bottom tip edge (underside of the tip face)
    def is_bottom_tip_edge(e):
        pt = e.positionAt(0.5)
        r = math.hypot(pt.x, pt.y)
        if r < R_ring - 1.2:
            return False
        mid = (interp(top_pts, min(r, R_ring)) +
               interp(bot_pts, min(r, R_ring))) / 2.0
        return pt.z < mid

    # cut all four lugs, then finish with exactly TWO chamfer ops — the
    # tip corners are rounded in the plan profile itself, because OCCT
    # fillets on those corners segfault
    lugs = None
    for rot in (0, 180):
        for sx in (+1, -1):
            prism = plan_prism(sx)
            if rot:
                prism = prism.rotate((0, 0, 0), (0, 0, 1), 180)
            lug = ring.intersect(prism)
            print(f"  . lug cut rot={rot} sx={sx:+d}")
            lugs = lug if lugs is None else lugs.union(lug)
    print("  . 4 lugs unioned")

    def _valid(wp):
        # OCCT chamfers on tangent chains sometimes "succeed" into
        # self-intersecting shells — BRepAlgoAPI_Check is the same gate
        # scan_step.py applies to the shipped STEP, so enforce it here
        from OCP.BRepAlgoAPI import BRepAlgoAPI_Check
        for sol in wp.solids().vals():
            if not BRepAlgoAPI_Check(sol.wrapped, True, True).IsValid():
                return False
        return True

    if not _valid(lugs):
        print("  ! lug union INVALID before chamfers")
    for ch in (p["lug_top_chamfer"], 0.35, 0.25):
        try:
            cand = lugs.edges(MidpointSelector(is_top_edge)).chamfer(ch)
            if not _valid(cand):
                print(f"  . top chamfer at {ch} invalid, retrying")
                continue
            lugs = cand
            print(f"  . top chamfer OK at {ch}")
            break
        except Exception:
            continue
    else:
        print("  ! lug top chamfer failed at all sizes")
    for ch in (0.20, 0.15, 0.10):
        try:
            cand = lugs.edges(
                MidpointSelector(is_bottom_tip_edge)).chamfer(ch)
            if not _valid(cand):
                print(f"  . bottom tip chamfer at {ch} invalid, retrying")
                continue
            lugs = cand
            print(f"  . bottom tip chamfer OK at {ch}")
            break
        except Exception:
            continue
    else:
        # cosmetic 0.1 edge break; OCCT refuses the tangent chain here.
        # Carried as a drawing callout instead ("break sharp edges R0.1")
        # — shops apply this by default.
        print("  . bottom tip edge break -> drawing callout")

    # cap: nothing above the shoulder inside the bezel swept envelope —
    # horn wall stands off the bezel skirt so the horns rise in the exposed
    # shoulder band, clearly separated from the rotating bezel
    horn_wall = P["bezel_outer_base"] / 2.0 + 0.40
    excl = (
        cq.Workplane("XZ")
        .moveTo(0.01, SHOULDER_Z)
        .lineTo(horn_wall, SHOULDER_Z)
        .lineTo(horn_wall, COIN_TOP_Z + 0.10)
        .lineTo(P["bezel_bevel_dia"] / 2.0 - 0.15, BEZEL_TOP_Z + 0.20)
        .lineTo(0.01, BEZEL_TOP_Z + 0.20)
        .close()
        .revolve(360, (0, 0, 0), (0, 1, 0))
    )
    return lugs.cut(excl)


def fillet_lug_junctions(solid):
    """Blend the lug roots into the case flank. OCCT fillets are fragile on
    junction loops (tangent seams have zero dihedral, waist arcs split into
    off-axis segments, boolean slivers abound), so: curated band selection,
    attempted per lug quadrant, falling back to edge-by-edge so impossible
    edges self-select out instead of failing the whole operation."""
    def band(e, qx=None, qy=None):
        c = e.Center()
        if math.hypot(c.x, c.y) < 9:           # axis-centred circles: skip
            return False
        if qx is not None and (c.x * qx < 2 or c.y * qy < 2):
            return False
        if e.Length() < 0.8:                   # boolean slivers
            return False
        pt = e.positionAt(0.5)
        r = math.hypot(pt.x, pt.y)
        az = math.degrees(math.atan2(abs(pt.y), abs(pt.x)))
        # outer-flank junction only (az 36-42°); below z 4.2 the join is
        # near-tangent by construction and needs no fillet; the inner
        # corner (az ~60°) is blended in the plan profile itself
        return (4.2 < pt.z < SHOULDER_Z - 0.5 and 18.3 < r < 19.75
                and 28.0 < az < 53.0)

    # one op across all four lugs on the pristine solid works best
    for rad in (P["junction_fillet"], 0.3):
        try:
            return solid.edges(MidpointSelector(band)).fillet(rad)
        except Exception:
            continue
    # per-quadrant, then edge-by-edge — impossible edges self-select out
    for qx, qy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        sel = MidpointSelector(lambda e, qx=qx, qy=qy: band(e, qx, qy))
        done = False
        for rad in (P["junction_fillet"], 0.3):
            try:
                solid = solid.edges(sel).fillet(rad)
                done = True
                break
            except Exception:
                continue
        if done:
            continue
        mids = [e.positionAt(0.5) for e in sel.filter(solid.edges().vals())]
        n_ok = 0
        for m in mids:
            prox = MidpointSelector(
                lambda e, m=m: (e.positionAt(0.5) - m).Length < 0.25)
            try:
                solid = solid.edges(prox).fillet(0.3)
                n_ok += 1
            except Exception:
                continue
        print(f"  . junction fillet quadrant ({qx:+d},{qy:+d}): "
              f"{n_ok}/{len(mids)} edges blended individually")
    return solid


def build_lugs_isolated():
    """OCCT segfaults nondeterministically when many edge operations run in
    one process (can't be caught as exceptions). Build the lugs in a fresh
    subprocess with retries, hand the result back as STEP."""
    import subprocess
    import sys
    out = os.path.join(OUT, "_lugs_tmp.step")
    if os.path.exists(out):
        os.remove(out)
    for attempt in range(1, 5):
        r = subprocess.run(
            [sys.executable, os.path.abspath(__file__), "--lugs-only", out],
            capture_output=True, text=True, timeout=600)
        for line in (r.stdout or "").splitlines():
            if line.startswith("  !"):
                print(line)
        if r.returncode == 0 and os.path.exists(out):
            from cadquery import importers
            print(f"  lugs built in subprocess (attempt {attempt})")
            return importers.importStep(out)
        print(f"  ! lug subprocess attempt {attempt} failed "
              f"(rc={r.returncode}), retrying")
    raise RuntimeError("lug construction failed after 4 attempts")


def drill_springbars(solid):
    """Drilled-through lug holes with a 90° countersink on both faces.

    ISO 3765 shows an 8-10° conical entry; watchmaking practice is a small
    90° countersink, which guides the spring-bar pin and stops the bore
    mouth wearing oval under bracelet load.
    """
    p = P
    y = p["l2l"] / 2.0 - p["springbar_from_tip"]
    r = p["springbar_dia"] / 2.0
    x_in = p["lug_width"] / 2.0
    x_out = x_in + p["lug_thk"]
    bars = None
    for sy in (+1, -1):
        cyl = (
            cq.Workplane("YZ")
            .center(sy * y, p["springbar_z"])
            .circle(r)
            .extrude(14, both=True)
        )
        bars = cyl if bars is None else bars.union(cyl)
        if p["springbar_csink"] > 0:
            rc = p["springbar_csink"] / 2.0
            d = p["springbar_csink_d"]
            # the lug tapers in plan: its outer face at the bar sits near
            # x 13.0, NOT at x_in + lug_thk = 13.6 — a cone cut at 13.6
            # landed in air and no outer countersink was ever formed. Cut
            # long double-cones that straddle wherever the faces really are.
            for sx in (+1, -1):
                # outer countersink: long cone from outside the widest the
                # face can be (13.6) converging to the bore Ø at 13.0-0.6 —
                # it forms a 90° countersink wherever the face actually is
                cone_out = (
                    cq.Workplane("YZ", origin=(sx * (13.00 + 0.6), 0, 0))
                    .center(sy * y, p["springbar_z"])
                    .circle(rc + 0.6 * (rc - r) / d)
                    .workplane(offset=-sx * (0.6 + d))
                    .circle(r)
                    .loft(combine=True)
                )
                bars = bars.union(cone_out)
                cone_in = (
                    cq.Workplane("YZ", origin=(sx * (x_in - 0.6), 0, 0))
                    .center(sy * y, p["springbar_z"])
                    .circle(rc + 0.6 * (rc - r) / d)
                    .workplane(offset=sx * (0.6 + d))
                    .circle(r)
                    .loft(combine=True)
                )
                bars = bars.union(cone_in)
    return solid.cut(bars)


def build_crown_tube_bore(solid):
    """Bore at 3 o'clock for the pressed-in crown tube.

    No external boss: the reference renders show the tube emerging from a
    smooth, unbroken case flank. The bore is sized for a press fit
    (tube shank Ø3.00 into a Ø2.97 bore = 0.03 diametral interference),
    stepping down to a stem clearance hole through to the movement cavity.
    """
    p = P
    bore_d = p["tube_press_dia"] - p["tube_press_inter"]   # Ø2.48 for s6
    shank_len = 1.9
    press = (
        cq.Workplane("YZ")
        .workplane(offset=case_r - shank_len)
        .center(0, STEM_Z)
        .circle(bore_d / 2.0)
        .extrude(shank_len + 0.5)
    )
    stem = (
        cq.Workplane("YZ")
        .center(0, STEM_Z)
        .circle(p["crown_tube_bore"] / 2.0 + 0.05)
        .extrude(case_r + 4)
    )
    return solid.cut(press).cut(stem)


# ---------------------------------------------------------------------------
# MOVEMENT RING (part 08)
# ---------------------------------------------------------------------------
def build_bezel_spring_ring():
    """Part 09 — bezel retention spring ring (slit).

    Sits in the case-boss groove and springs OUT into the bezel's internal
    groove, holding the bezel down while letting it rotate. Because it is
    slit, it changes diameter by bending rather than by hoop strain, which
    is the only way a steel retainer can be assembled over the boss at all.
    Assembly: compress the ring into the boss groove, drop the bezel on,
    the ring springs out into the bezel groove.
    """
    p = P
    cs = p["spring_ring_cs"]
    ro = p["spring_ring_free_od"] / 2.0
    ri = ro - cs
    zc = GROOVE_Z0 + (GROOVE_Z1 - GROOVE_Z0) / 2.0
    ring = (
        cq.Workplane("XZ")
        .moveTo(ri, zc - cs / 2.0)
        .lineTo(ro, zc - cs / 2.0)
        .lineTo(ro, zc + cs / 2.0)
        .lineTo(ri, zc + cs / 2.0)
        .close()
        .revolve(360, (0, 0, 0), (0, 1, 0))
    )
    # slit: a wedge removed so the ring can be squeezed closed
    gap = p["spring_ring_gap_deg"]
    # the wedge's chord must lie OUTSIDE the ring OD or a sliver of the
    # ring survives inside the slit and the part exports as 2 solids
    Rw = ro / math.cos(math.radians(gap / 2.0)) + 2.0
    wedge = (
        cq.Workplane("XY", origin=(0, 0, zc - cs))
        .moveTo(0, 0)
        .lineTo(Rw, 0)
        .lineTo(Rw * math.cos(math.radians(gap)),
                Rw * math.sin(math.radians(gap)))
        .close()
        .extrude(cs * 2)
    )
    return ring.cut(wedge)


def build_movement_ring():
    p = P
    ro = p["ring_od"] / 2.0
    ri = p["ring_bore_dia"] / 2.0
    rf = p["ring_flange_pocket"] / 2.0
    rg = p["ring_clamp_groove"] / 2.0
    z0 = p["cb_thread_top_z"] - 0.02       # 0.02 proud: the caseback
                                           # preloads the POM ring, removing
                                           # the 0.25 axial float the audit
                                           # measured
    z1 = Z_DIAL
    # Miyota section CS1-CS2: clamp seating face 2.200 below the dial
    # plane, tab 0.400 thick, 0.100 clearance -> band runs dial-2.20 down
    # to dial-2.70 (was centred on -2.20, i.e. 0.30 too high)
    zg1 = Z_DIAL - p["cs_slot_below_dial"]
    zg0 = zg1 - 0.50
    # flange relief spans the full flange_pocket_depth below the dial plane
    # (the Ø26.00 band sits 1.70-2.00 below it, NOT at the top; the old
    # 0.35 pocket interfered 0.35 diametral and held the movement 1.65 high)
    zf = z1 - p["flange_pocket_depth"]
    pts = [
        (ri, z0), (ri, zg0), (rg, zg0), (rg, zg1), (ri, zg1),
        (ri, zf), (rf, zf), (rf, z1), (ro, z1), (ro, z0),
    ]
    ring = (cq.Workplane("XZ").polyline(pts).close()
            .revolve(360, (0, 0, 0), (0, 1, 0)))
    stem = (cq.Workplane("YZ").center(0, STEM_Z)
            .circle(p["ring_stem_hole"] / 2.0).extrude(ro + 2))
    return ring.cut(stem)


# ---------------------------------------------------------------------------
# ROTATING BEZEL — turns on the case boss, snap lip in the groove
# ---------------------------------------------------------------------------
def build_bezel():
    """Rotating 24h bezel.

    Profile measured off the mockups: a broad brushed top face MILDLY CONED
    (~12° from horizontal, falling outward) that carries the engraved
    scale, running out to Ø37.93; then a polished chamfer to Ø38.85; then a
    short vertical flank at Ø38.90, essentially flush with the Ø39.0 case.
    Below that the coin-edge grip band drops to the reveal.

    Runs on the case boss as a plain H7 bore; held down by the slit spring
    ring (part 09) engaging the internal groove; centred and damped by an
    O-ring in the boss groove.
    """
    p = P
    ro_b  = p["bezel_outer_base"] / 2.0        # 19.45 outer flank
    r_cha = p["bezel_chamfer_dia"] / 2.0       # 19.425 chamfer outer edge
    r_bev = p["bezel_bevel_dia"] / 2.0         # 18.965 coned face ends
    ap    = p["bezel_aperture"] / 2.0          # 15.95
    r_ich = p["bezel_inner_cham"] / 2.0        # 15.845 inner chamfer
    r_in  = p["bezel_inner_wall"] / 2.0
    rg    = p["bezel_groove_dia"] / 2.0
    gw    = p["bezel_groove_w"]
    drop  = p["bezel_cone_drop"]
    zb    = BEZEL_BASE_Z
    zt    = BEZEL_TOP_Z                        # inner (high) edge of the cone
    z_bev = zt - drop                          # outer edge of the coned face
    zceil = STEEL_TOP + 0.10                   # over the boss top
    gzc   = GROOVE_Z0 + (GROOVE_Z1 - GROOVE_Z0) / 2.0
    z_flank = zb + p["bezel_skirt"] + p["bezel_flank_h"]

    prof = (
        cq.Workplane("XZ")
        .moveTo(r_in, zb)                      # bore, skirt bottom
        .lineTo(r_in, gzc - gw / 2.0)
        .lineTo(rg, gzc - gw / 2.0)            # ---- retention groove ----
        .lineTo(rg, gzc + gw / 2.0)
        .lineTo(r_in, gzc + gw / 2.0)          # --------------------------
        .lineTo(r_in, zceil)                   # bore over the boss
        .lineTo(r_ich, zceil)                  # ceiling
        .lineTo(r_ich, zt - 0.20)              # aperture bore (Ø31.69)
        .lineTo(ap, zt)                        # polished inner chamfer, out
                                               # and up to Ø31.90
        .lineTo(r_bev, z_bev)                  # CONED TOP (scale sits here)
        .lineTo(ro_b, z_flank)                 # ONE long polished bevel —
                                               # tapers the edge instead of
                                               # presenting a thick wall
        .lineTo(ro_b, zb)                      # short flank + coin band
        .close()
        .revolve(360, (0, 0, 0), (0, 1, 0))
    )
    bez = bezel_coin_edge(prof, ro_b, zb, p["bezel_skirt"])
    bez = bezel_detent_scallops(bez, zb)
    bez = bezel_markings(bez, r_ich, r_bev, zt, z_bev)
    return bez


def bezel_detent_scallops(bez, zb):
    """120 scallops in the bezel underside. A spring-loaded ball carried in
    the case shoulder rides these, giving one click per 3 minutes / 12
    minutes of 24h scale. Cut as cylinders with a spherical bottom so the
    ball seats without a sharp corner."""
    p = P
    n = p["detent_count"]
    R = p["detent_ring_dia"] / 2.0
    rs = p["detent_scallop_r"]
    d = p["detent_scallop_d"]
    # pushPoints + combine=False builds all 120 as one compound in ~0.5s;
    # unioning them one at a time exhausts memory and kills the process
    pts = [(R * math.cos(2 * math.pi * i / n),
            R * math.sin(2 * math.pi * i / n)) for i in range(n)]
    # sphere centre BELOW the underside face so only `d` bites into the
    # material (zb + rs - d put the centre inside and gouged 0.98 deep)
    tool = (cq.Workplane("XY", origin=(0, 0, zb - rs + d))
            .pushPoints(pts).sphere(rs, combine=False))
    return bez.cut(tool)


def add_detent_ball_pockets(solid):
    """Pockets in the case shoulder for the spring-loaded detent balls.
    Two, diametrically opposed, clear of the crown and the lug roots."""
    p = P
    R = p["detent_ring_dia"] / 2.0
    cuts = None
    for ang_deg in (45.0, 225.0):
        a = math.radians(ang_deg)
        x, y = R * math.cos(a), R * math.sin(a)
        pk = (cq.Workplane("XY",
                           origin=(x, y, SHOULDER_Z - p["detent_pocket_d"]))
              .circle(p["detent_ball_dia"] / 2.0 + 0.05)
              .extrude(p["detent_pocket_d"] + 0.2))
        cuts = pk if cuts is None else cuts.union(pk)
    return solid.cut(cuts)


def bezel_coin_edge(bez, ro_b, z0, skirt):
    n = P["bezel_grip_count"]
    pts = [(ro_b * math.cos(2 * math.pi * i / n),
            ro_b * math.sin(2 * math.pi * i / n)) for i in range(n)]
    tool = (cq.Workplane("XY", origin=(0, 0, z0 - 0.1))
            .pushPoints(pts).circle(0.22)
            .extrude(skirt + 0.45, combine=False))
    return bez.cut(tool)


def bezel_markings(bez, r_inner, r_outer, z_top, z_outer):
    """Engraved 24h scale on the coned top face: even numerals + odd
    triangles, radial orientation (tops outboard, so the lower half reads
    inverted exactly like a classic GMT bezel). Pockets are cut normal to
    the cone at engrave depth, ready for black lacquer fill. Round lume-pip
    pocket outboard of the 24.

    METROLOGY targets: numeral cap height 1.70 at pitch Ø34.88 (R 17.44);
    triangles 0.87 radial x 0.93 tangential at pitch Ø34.43 (R 17.215).
    """
    p = P
    d = p["bezel_engrave_depth"]
    # cone angle and the z of the surface at any radius
    beta = math.degrees(math.atan2(z_top - z_outer, r_outer - r_inner))

    def z_at(r):
        t = (r - r_inner) / (r_outer - r_inner)
        return z_top + t * (z_outer - z_top)

    def place(wp, theta_deg, R, extra_sink=0.0, flip=False):
        # cone falls OUTWARD (+y at the 12 o'clock construction pose), so
        # the cutter tilts by MINUS beta — plus beta made pockets deepen
        # inboard and vanish before the numerals' outer edge
        if flip:
            wp = wp.rotate((0, 0, 0), (0, 0, 1), 180.0)
        s = wp.rotate((0, 0, 0), (1, 0, 0), -beta)
        s = s.translate((0, R, z_at(R) - d - extra_sink))
        return s.rotate((0, 0, 0), (0, 0, 1), theta_deg - 90.0)

    R_num = p["numeral_pitch_dia"] / 2.0       # 17.44 (metrology)
    R_tri = p["triangle_pitch_dia"] / 2.0      # 17.215 (metrology)
    tri_r = p["triangle_radial"] / 2.0         # 0.435
    tri_t = p["triangle_tangential"] / 2.0     # 0.465

    cuts = []
    for h in range(1, 25):
        theta = 90.0 - h * 15.0
        # mock: lower-half glyphs read upright (tops inboard), upper half
        # tops outboard — flip the glyph on the lower semicircle
        low = math.sin(math.radians(theta)) < -1e-9
        if h % 2 == 0:
            g = (cq.Workplane("XY")
                 .text(str(h), p["bezel_num_h"], d + 0.4,
                       halign="center", valign="center"))
            cuts.append(place(g, theta, R_num, flip=low))
        else:
            g = (cq.Workplane("XY")
                 .polyline([(0, tri_r), (-tri_t, -tri_r), (tri_t, -tri_r)])
                 .close().extrude(d + 0.4))
            cuts.append(place(g, theta, R_tri, flip=low))
    bez = bez.cut(compound(cuts))
    # pip cut SEPARATELY: overlapping cutters inside one compound make the
    # general-fuse leave artifact bodies
    pip = (cq.Workplane("XY").circle(p["lume_pip_dia"] / 2.0)
           .extrude(p["lume_pip_depth"] + 0.4))
    return bez.cut(place(pip, 90.0, p["pip_pitch_dia"] / 2.0,
                         extra_sink=p["lume_pip_depth"] - d))


# ---------------------------------------------------------------------------
# CRYSTAL
# ---------------------------------------------------------------------------
def build_crystal():
    """Single revolve: flat disc + spherical dome. NOT a loft — a loft's
    underlying surface extends to a closed teardrop, and STEP translators
    that lose the face trim render the whole balloon (seen in Fusion)."""
    p = P
    r = p["crystal_dia"] / 2.0
    z0 = CRYSTAL_SEAT_Z
    z1 = z0 + p["crystal_flat_thk"]
    dome = p["crystal_dome_rise"]
    R = (r**2 + dome**2) / (2.0 * dome)         # dome sphere radius
    rm = r / 2.0
    zm = z1 + dome - (R - math.sqrt(R**2 - rm**2))   # arc mid at half radius
    prof = (
        cq.Workplane("XZ")
        .moveTo(AXIS, z0)
        .lineTo(r, z0)
        .lineTo(r, z1)
        .spline(arc_samples((r, z1), (rm, zm), (AXIS, z1 + dome))[1:],
                includeCurrent=True)
        .lineTo(AXIS, z0)
        .close()
        .revolve(360, (0, 0, 0), (0, 1, 0))
    )
    return prof


# ---------------------------------------------------------------------------
# CASEBACK + engraving
# ---------------------------------------------------------------------------
def build_caseback():
    """Threaded sapphire exhibition back.

    Sealing/assembly logic: the sapphire is pressed in from OUTSIDE and
    bears UP against an internal ledge, so external water pressure seats it
    harder rather than pushing it out. The O-ring is a RADIAL seal in a
    groove on the ring's OD below the thread band. Six notches in the
    bottom face take a standard case wrench.

    Threads are represented as plain cylinders with the callout carried in
    the spec sheet (M32x0.5) — modelling helical geometry bloats the STEP
    and CAM treats it as a callout anyway.
    """
    p = P
    ro     = p["cb_thread_dia"] / 2.0 - 0.05   # 14.95 thread major (clearance)
    z0     = p["back_recess_z"]                # bottom face
    z1     = p["cb_thread_top_z"]              # top face
    view   = p["cb_sapphire_view"] / 2.0       # visible aperture
    r_sap  = view + 1.2 + 0.02                 # sapphire bore (+0.02 clr)
    z_seat = z0 + p["cb_sapphire_thk"]         # sapphire top bears here
    z_led  = z_seat + p["cb_ledge_thk"]        # top of the retaining ledge
    # above the ledge the bore MUST clear the movement, which hangs down
    # into this height: rotor max radius + clearance
    r_clr  = p["mvmt_body_max_dia"] / 2.0 + 0.30
    gz     = z0 + 0.95 + p["cb_oring_groove_w"] / 2.0   # groove clear of notches
    gw     = p["cb_oring_groove_w"]
    gd     = p["cb_oring_groove_d"]
    # the lead-in chamfer must fit INSIDE the retaining ledge: with
    # c > ledge the profile rose to z_seat+c then reversed DOWN to z_led,
    # a 0.05 doubling-back that self-intersected the shell
    c      = min(p["cb_sapphire_seat_c"], p["cb_ledge_thk"] - 0.05)
    assert c > 0, "seat chamfer must fit inside the retaining ledge"

    prof = (
        cq.Workplane("XZ")
        .moveTo(r_sap, z0)                          # sapphire bore, bottom
        .lineTo(r_sap, z_seat)                      # sapphire pocket wall
        .lineTo(view + c, z_seat)                   # retaining ledge
        .lineTo(view, z_seat + c)                   # lead-in chamfer
        .lineTo(view, z_led)                        # aperture bore
        .lineTo(r_clr, z_led)                       # step out to clear rotor
        .lineTo(r_clr, z1)                          # inner wall
        .lineTo(ro, z1)                             # top face
        .lineTo(ro, gz + gw / 2.0)                  # OD, thread band above
        .lineTo(ro - gd, gz + gw / 2.0)             # ---- O-ring groove ----
        .lineTo(ro - gd, gz - gw / 2.0)
        .lineTo(ro, gz - gw / 2.0)                  # -----------------------
        .lineTo(ro, z0 + 0.20)
        .lineTo(ro - 0.20, z0)                      # bottom edge chamfer
        .close()
        .revolve(360, (0, 0, 0), (0, 1, 0))
    )
    prof = caseback_wrench_notches(prof, ro, z0)
    return engrave_caseback_ring(prof), None


def caseback_wrench_notches(ring, ro, z0):
    """Radial slots in the bottom face for a standard 3-pin case wrench."""
    p = P
    n = p["cb_notch_count"]
    w = p["cb_notch_w"]
    d = p["cb_notch_d"]
    # height limited so the notches never reach the O-ring groove above —
    # overlapping them cuts the sealing land into disconnected pieces
    h = 0.85
    cuts = [
        cq.Workplane("XY", origin=(0, 0, z0 - 0.1))
        .center(ro - d / 2.0 + 0.05, 0)
        .rect(d + 0.2, w)
        .extrude(h)
        .rotate((0, 0, 0), (0, 0, 1), i * 360.0 / n)
        for i in range(n)
    ]
    return ring.cut(compound(cuts))


def engrave_caseback_ring(ring):
    p = P
    z_face = p["back_recess_z"]
    depth = p["cb_engrave_depth"]
    R = (p["cb_sapphire_view"] / 2.0 + p["cb_thread_dia"] / 2.0) / 2.0 + 0.3
    h = 1.7

    def arc_text(text, center_deg, span_deg, flip):
        n = len(text)
        out = []
        for i, ch in enumerate(text):
            if ch == " ":
                continue
            frac = (i - (n - 1) / 2.0) / max(n - 1, 1)
            # top-arc words progress clockwise, bottom-arc words counter-
            # clockwise: both then read left-to-right in the as-worn view
            # (the bottom word ran right-to-left for every rev before this
            # -- caught by the finishing map's as-worn rendering)
            ang = (center_deg + frac * span_deg if flip
                   else center_deg - frac * span_deg)
            rad = math.radians(ang)
            x, y = R * math.cos(rad), R * math.sin(rad)
            rot = ang - 90 if not flip else ang + 90
            g = (
                cq.Workplane("XY", origin=(0, 0, z_face - 0.01))
                .text(ch, h, depth + 0.02, kind="regular",
                      halign="center", valign="center")
                .translate((x, y, 0))
                .rotate((x, y, 0), (x, y, 1), rot)
            )
            # the caseback is READ FROM BELOW (outside the watch): the
            # physical engraving must be the mirror image of the
            # +z-readable layout, or every letter engraves backwards
            out.append(g.mirror("YZ"))
        return out

    glyphs = (arc_text("KELSUS", 90, 70, flip=False)
              + arc_text("INTERCONTINENTAL", 270, 150, flip=True))
    return ring.cut(compound(glyphs))


def build_cb_sapphire():
    p = P
    r = p["cb_sapphire_view"] / 2.0 + 1.2
    z0 = p["back_recess_z"]
    return (cq.Workplane("XY", origin=(0, 0, z0))
            .circle(r).extrude(p["cb_sapphire_thk"]))


# ---------------------------------------------------------------------------
# CROWN with Kelsus K (from the real logo SVG — never the render's mark)
# ---------------------------------------------------------------------------
def kelsus_k_wire(scale, cx, cy):
    poly = [(276.02, 322.79), (216.27, 322.79), (137.63, 196.32),
            (215.9, 77.21), (271.7, 77.21), (188.28, 194.27),
            (276.02, 322.79)]
    rect = [(75.05, 271.77), (146.48, 271.77), (146.48, 322.79),
            (75.05, 322.79)]

    def xf(pts):
        return [((x - 351.07 / 2.0) * scale + cx,
                 -(y - 400 / 2.0) * scale + cy) for x, y in pts]
    return xf(poly), xf(rect)


def build_crown():
    """Crown at its SCREWED-DOWN position: skirt 0.30 off the case flank,
    swallowing the tube. Bored Ø3.95 over the Ø3.90 tube thread (female
    thread is a machining callout), with a gasket counterbore at the mouth.
    The audit found the previous crown was a solid slug — unfittable."""
    p = P
    r = p["crown_dia"] / 2.0
    z = STEM_Z
    x0 = case_r + p["crown_case_gap"]
    xface = x0 + p["crown_h"]
    body = (cq.Workplane("YZ", origin=(x0, 0, z))
            .circle(r).extrude(p["crown_h"]))
    # bore: swallows the tube, leaves a solid head behind the K face
    bore_depth = p["crown_h"] - 1.0
    body = body.cut(
        cq.Workplane("YZ", origin=(x0 - 0.1, 0, z))
        .circle(p["crown_bore_dia"] / 2.0).extrude(bore_depth + 0.1))
    # gasket counterbore at the mouth (crown O-ring seals on the tube)
    body = body.cut(
        cq.Workplane("YZ", origin=(x0 - 0.1, 0, z))
        .circle(p["crown_gasket_bore"] / 2.0)
        .extrude(p["crown_gasket_depth"] + 0.1))
    flute_len = p["crown_h"] - p["crown_endband"]
    flutes = None
    for i in range(p["crown_flute_count"]):
        ang = i * (360.0 / p["crown_flute_count"])
        f = (
            cq.Workplane("YZ", origin=(x0, 0, z))
            .center(r, 0).circle(0.26).extrude(flute_len)
            .rotate((x0, 0, z), (x0 + 1, 0, z), ang)
        )
        flutes = f if flutes is None else flutes.union(f)
    body = body.cut(flutes)
    scale = (p["crown_dia"] * 0.69) / 351.07   # K ~79% of the face Ø,
                                               # near edge-to-edge (was 0.62)
    poly, rect = kelsus_k_wire(scale, 0, 0)
    body = body.cut(
        cq.Workplane("YZ", origin=(xface, 0, z))
        .polyline(poly).close().extrude(-p["logo_depth"]))
    body = body.cut(
        cq.Workplane("YZ", origin=(xface, 0, z))
        .polyline(rect).close().extrude(-p["logo_depth"]))
    # Tube: pressed-in shank inside the case (Ø3.00 +0.03 interference),
    # stepping out to the Ø3.60 threaded portion the crown screws onto.
    shank_len = 1.9
    tube = (cq.Workplane("YZ", origin=(case_r - shank_len, 0, z))
            .circle(p["tube_press_dia"] / 2.0)
            .extrude(shank_len))                       # pressed shank
    tube = tube.union(
        cq.Workplane("YZ", origin=(case_r, 0, z))
        .circle(p["tube_thread_dia"] / 2.0)
        .extrude(p["crown_tube_ext"]))                 # threaded protrusion
    tube = tube.faces(">X").workplane().circle(
        p["crown_tube_bore"] / 2.0).cutThruAll()
    return body, tube


# ---------------------------------------------------------------------------
# REFERENCE PARTS (assembly only)
# ---------------------------------------------------------------------------
def build_movement_ref():
    p = P
    return (cq.Workplane("XY", origin=(0, 0, Z_DIAL - p["mvmt_h"]))
            .circle(p["mvmt_body_max_dia"] / 2.0).extrude(p["mvmt_h"]))


def build_dial_ref():
    p = P
    return (cq.Workplane("XY", origin=(0, 0, Z_DIAL))
            .circle(p["dial_dia"] / 2.0).extrude(p["dial_thk"]))


def build_iring_installed():
    """Crystal I-ring at INSTALLED dimensions: wall compressed to the
    0.30 annulus between crystal and bore. Free-state solid for the
    gasket vendor is 10_iring_gasket.step (gasket_models.py)."""
    p = P
    z0 = CRYSTAL_SEAT_Z
    return (cq.Workplane("XZ")
            .moveTo(p["crystal_dia"] / 2.0, z0)
            .lineTo(p["crystal_bore_dia"] / 2.0, z0)
            .lineTo(p["crystal_bore_dia"] / 2.0, z0 + 1.40)
            .lineTo(p["crystal_dia"] / 2.0, z0 + 1.40)
            .close().revolve(360, (0, 0, 0), (0, 1, 0)))


def build_bezel_oring_installed():
    """Bezel centring O-ring at INSTALLED shape: elliptical section
    (area-preserving squash of the cs 0.70 circle) seated on the boss
    groove floor, clear of the bezel bore. Free-state solid is
    11_bezel_oring.step (gasket_models.py)."""
    p = P
    a_rad, b_ax = 0.26, 0.47                   # section half-axes
    r_c = p["bezel_oring_floor"] / 2.0 + a_rad
    z_c = ORING_Z0 + p["bezel_oring_w"] / 2.0
    # absolute-coordinate section polygon: .center() would shift the
    # workplane-local revolve axis into the profile (the revolve-axis
    # gotcha) and the revolve fails
    pts = [(r_c + a_rad * math.cos(t), z_c + b_ax * math.sin(t))
           for t in [i * 2 * math.pi / 60 for i in range(60)]]
    return (cq.Workplane("XZ").polyline(pts).close()
            .revolve(360, (0, 0, 0), (0, 1, 0)))


# ---------------------------------------------------------------------------
# BUILD + EXPORT
# ---------------------------------------------------------------------------
def main():
    print(f"stack: Z_DIAL={Z_DIAL:.2f} STEM_Z={STEM_Z:.2f} "
          f"SEAT={CRYSTAL_SEAT_Z:.2f} SHOULDER={SHOULDER_Z:.2f} "
          f"BOSS_TOP={STEEL_TOP:.2f} BEZEL={BEZEL_BASE_Z:.2f}-{BEZEL_TOP_Z:.2f} "
          f"APEX={CRYSTAL_APEX:.2f}")
    print("Building midcase...")
    mid = build_midcase_outer()
    mid = mid.union(build_lugs_isolated())
    mid = mid.cut(build_internal_void())      # AFTER lugs — see docstring
    mid = build_crown_tube_bore(mid)
    mid = add_detent_ball_pockets(mid)
    mid = drill_springbars(mid)
    mid = keep_largest(mid)

    print("Building bezel...")
    bez = build_bezel()
    print("Building crystal...")
    cry = build_crystal()
    print("Building caseback...")
    cb_ring, _ = build_caseback()
    cb_sap = build_cb_sapphire()
    print("Building crown...")
    crown, tube = build_crown()
    print("Building movement ring...")
    mring = build_movement_ring()
    print("Building bezel spring ring...")
    spring = build_bezel_spring_ring()

    parts = {
        "01_midcase":        mid,
        "02_bezel":          bez,
        "03_crystal":        cry,
        "04_caseback_ring":  cb_ring,
        "05_caseback_sapph": cb_sap,
        "06_crown":          crown,
        "07_crown_tube":     tube,
        "08_movement_ring":  mring,
        "09_bezel_spring":   spring,
    }
    for name, part in parts.items():
        # clean() runs ShapeUpgrade_UnifySameDomain: merges co-surface faces
        # and removes the degenerate slivers that boolean ops leave behind.
        # Without it those micro-faces ship into the STEP and translators
        # extrapolate their basis surfaces into phantom geometry.
        try:
            part = part.clean()
        except Exception as e:
            print(f"  ! clean() failed on {name}: {e}")
        shape = part.val() if hasattr(part, "val") else part
        nsol = len(part.solids().vals()) if hasattr(part, "solids") else 1
        exporters.export(shape, os.path.join(OUT, name + ".step"))
        exporters.export(shape, os.path.join(OUT, name + ".stl"))
        print(f"  exported {name}  (solids={nsol})")

    asm = cq.Assembly()
    asm.add(mid,     name="midcase",       color=cq.Color(0.72, 0.73, 0.75))
    asm.add(bez,     name="bezel",         color=cq.Color(0.62, 0.63, 0.66))
    asm.add(cry,     name="crystal",       color=cq.Color(0.7, 0.85, 0.95, 0.35))
    asm.add(cb_ring, name="caseback_ring", color=cq.Color(0.72, 0.73, 0.75))
    asm.add(cb_sap,  name="caseback_sap",  color=cq.Color(0.7, 0.85, 0.95, 0.35))
    asm.add(crown,   name="crown",         color=cq.Color(0.62, 0.63, 0.66))
    asm.add(tube,    name="tube",          color=cq.Color(0.6, 0.6, 0.62))
    asm.add(mring,   name="movement_ring", color=cq.Color(0.55, 0.56, 0.58))
    asm.add(spring,  name="bezel_spring",  color=cq.Color(0.45, 0.46, 0.50))
    asm.add(build_movement_ref(), name="movement_ref",
            color=cq.Color(0.85, 0.75, 0.35, 0.5))
    asm.add(build_dial_ref(), name="dial_ref",
            color=cq.Color(0.15, 0.45, 0.5, 0.8))
    asm.add(build_iring_installed(), name="iring_gasket_installed",
            color=cq.Color(0.9, 0.9, 0.85, 0.8))
    asm.add(build_bezel_oring_installed(), name="bezel_oring_installed",
            color=cq.Color(0.2, 0.2, 0.2, 0.9))
    tmp = os.path.join(OUT, "_lugs_tmp.step")
    if os.path.exists(tmp):
        os.remove(tmp)
    asm.save(os.path.join(OUT, "assembly.step"))
    print("  exported assembly.step")
    print("Done.")


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 3 and sys.argv[1] == "--lugs-only":
        lugs = build_lugs()
        exporters.export(lugs.val(), sys.argv[2])
    else:
        main()
