"""Assemble output/review.html: inject spec rows, dims, base64 renders, file list."""
import os, base64, glob
import numpy as np
from stl import mesh as sm
import case_model as C

HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "output")
P = C.P


def b64(path):
    with open(path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()


def overall():
    parts = ["01_midcase", "02_bezel", "03_crystal", "04_caseback_ring",
             "06_crown", "07_crown_tube"]
    pts = np.vstack([sm.Mesh.from_file(os.path.join(OUT, f"{p}.stl")).vectors.reshape(-1, 3)
                     for p in parts])
    mn, mx = pts.min(0), pts.max(0)
    return mx[1] - mn[1], mx[2] - mn[2]   # L2L (Y), thickness (Z)


# --- spec table rows (grouped) ---------------------------------------------
GROUPS = [
    ("Overall", [
        ("Case diameter", "39.0 mm"),
        ("Lug-to-lug", "{L2L} mm"),
        ("Overall thickness (crystal apex)", "{THK} mm"),
        ("Lug width / strap", f'{P["lug_width"]:.2f} +0.10/-0 mm'),
        ("Material", P["material"]),
    ]),
    ("Movement — Miyota 9075 (drawing 907500C0)", [
        ("Flange Ø (dial side, widest)", f'{P["mvmt_flange_dia"]:.2f} mm'),
        ("Casing register Ø", f'{P["mvmt_register_dia"]:.2f} mm Js8'),
        ("Total height", f'{P["mvmt_h"]:.2f} mm'),
        ("Stem axis below dial plane", f'{P["stem_below_dial"]:.2f} mm ✓'),
        ("Stem thread", str(P.get("crown_thread_spec", "—")) + " ✓"),
        ("Hand pivot max protrusion", f'{P["hand_pivot_max"]:.2f} mm'),
        ("Hand clearance provided", f'{P["hand_clear"]:.2f} mm'),
        ("Rotor→sapphire clearance", f'{P["rotor_clear"]:.2f} mm'),
    ]),
    ("Crystal — fitting", [
        ("Sapphire Ø × flat thk", f'{P["crystal_dia"]:.2f} × {P["crystal_flat_thk"]:.2f} mm'),
        ("Dome rise", f'{P["crystal_dome_rise"]:.2f} mm'),
        ("Case bore", f'Ø{P["crystal_bore_dia"]:.2f} js8 (±0.020)'),
        ("Gasket", f'I-ring, wall {P["crystal_gasket_wall"]:.2f}, height {P["crystal_gasket_h"]:.2f}'),
        ("Gasket free OD → crush", f'Ø{P["crystal_dia"] + 2 * P["crystal_gasket_wall"]:.2f} → {P["crystal_dia"] + 2 * P["crystal_gasket_wall"] - P["crystal_bore_dia"]:.2f} diametral'),
        ("Seat ledge / lead-in", f'{P["crystal_seat_ledge"]:.2f} radial / {P["crystal_lead_c"]:.2f} × 15–20°'),
        ("Peak stress @12.5 bar", "≈124 MPa (SF ≈2.4 vs 300 MPa MOR)"),
    ]),
    ("Bezel — rotating 24h", [
        ("Type", "Bidirectional, 120 clicks"),
        ("Outer Ø (flush with case)", f'{P["bezel_outer_base"]:.2f} mm'),
        ("Coned top face runs to", f'Ø{P["bezel_bevel_dia"]:.2f}, drop {P["bezel_cone_drop"]:.2f} (≈12°)'),
        ("Polished edge bevel", f'Ø{P["bezel_bevel_dia"]:.2f} → Ø{P["bezel_outer_base"]:.2f}, one long taper'),
        ("Vertical flank", f'{P["bezel_flank_h"]:.2f} mm (svelte edge)'),
        ("Aperture / inner chamfer", f'Ø{P["bezel_aperture"]:.2f} / from Ø{P["bezel_inner_cham"]:.2f}'),
        ("Numerals", f'2–24 even, cap {P["bezel_num_h"]:.2f} at pitch Ø{P["numeral_pitch_dia"]:.2f}'),
        ("Triangles (odd hours)", f'{P["triangle_radial"]:.2f} × {P["triangle_tangential"]:.2f} at Ø{P["triangle_pitch_dia"]:.2f}'),
        ("Engraving depth", f'{P["bezel_engrave_depth"]:.2f} mm, black lacquer fill'),
        ("Lume pip @ 24", f'Ø{P["lume_pip_dia"]:.2f} × {P["lume_pip_depth"]:.2f} deep'),
        ("Grip", f'coin edge, {P["bezel_grip_count"]} × {P["bezel_skirt"]:.2f} mm band'),
        ("Reveal to case shoulder", f'{P["bezel_reveal"]:.2f} mm'),
    ]),
    ("Bezel — retention & click (attachment)", [
        ("Rotates on", f'case boss Ø{P["boss_od"]:.2f} h7, {P["boss_h"]:.2f} tall'),
        ("Running fit", f'bezel bore Ø{P["bezel_inner_wall"]:.2f} H7 = 0.10 diametral'),
        ("RETENTION", f'slit spring ring (part 09), free OD Ø{P["spring_ring_free_od"]:.2f}, {P["spring_ring_cs"]:.2f} section, {P["spring_ring_gap_deg"]:.0f}° slit'),
        ("Boss groove / bezel groove", f'floor Ø{P["groove_floor_dia"]:.2f} / Ø{P["bezel_groove_dia"]:.2f} × {P["bezel_groove_w"]:.2f}'),
        ("Centring O-ring", f'cord {P["bezel_oring_cs"]:.2f}, groove floor Ø{P["bezel_oring_floor"]:.2f} × {P["bezel_oring_w"]:.2f}'),
        ("Click detent", f'{P["detent_count"]} scallops R{P["detent_scallop_r"]:.2f} × {P["detent_scallop_d"]:.2f} deep at Ø{P["detent_ring_dia"]:.2f}'),
        ("Detent balls", f'2 × Ø{P["detent_ball_dia"]:.2f} spring-loaded, pockets {P["detent_pocket_d"]:.2f} deep in the shoulder'),
    ]),
    ("Caseback — attachment & sealing", [
        ("Type", "Threaded sapphire exhibition"),
        ("Thread", f'M{P["cb_thread_dia"]:.0f}×{P["cb_thread_pitch"]:.1f}, ISO 60°, single start, RH'),
        ("Thread note", "non-ISO pitch at this Ø — dimension explicitly on the drawing"),
        ("Engagement", f'≈{P["cb_thread_top_z"] - 2.0:.1f} mm (≈3 turns)'),
        ("O-ring (RADIAL seal)", f'cord {P["cb_oring_cs"]:.2f} ISO 3601-1 Class A'),
        ("O-ring groove", f'{P["cb_oring_groove_w"]:.2f} wide × {P["cb_oring_groove_d"]:.2f} deep (~22% squeeze)'),
        ("Wrench notches", f'{P["cb_notch_count"]} × {P["cb_notch_w"]:.2f} wide × {P["cb_notch_d"]:.2f} deep (NIHS G 60-32)'),
        ("Display sapphire", f'Ø{P["cb_sapphire_view"] + 2.4:.2f} × {P["cb_sapphire_thk"]:.2f}, aperture Ø{P["cb_sapphire_view"]:.2f}'),
        ("Sapphire seating", "pressed from OUTSIDE, bears UP on an inner ledge — pressure seats it"),
        ("Peak stress @12.5 bar", "≈87 MPa (SF ≈3.4)"),
        ("Engraving", f'"{P["cb_engrave_text"].title()}", {P["cb_engrave_depth"]:.2f} deep'),
    ]),
    ("Crown & tube — attachment", [
        ("Crown Ø × length", f'{P["crown_dia"]:.2f} × {P["crown_h"]:.2f} mm'),
        ("Total protrusion past case", "4.00 mm"),
        ("Crown internal thread", str(P.get("crown_thread_spec", "—"))),
        ("Tube thread (crown screws on)", f'Ø{P["tube_thread_dia"]:.2f} × {P["tube_thread_pitch"]:.2f} pitch'),
        ("Tube pressed shank", f'Ø{P["tube_press_dia"]:.2f} s6 into a Ø{P["tube_press_dia"] - P["tube_press_inter"]:.2f} H7 case bore'),
        ("Press interference", f'{P["tube_press_inter"]:.3f} diametral + anaerobic retainer (retainer is the seal)'),
        ("Tube bore (stem clearance)", f'Ø{P["crown_tube_bore"]:.2f} mm'),
        ("Crown gaskets", f'2 × O-ring, cord {P["crown_oring_cs"]:.2f} mm'),
        ("Flutes", f'{P["crown_flute_count"]}, smooth {P["crown_endband"]:.2f} end band'),
        ("Kelsus K", f'{P["logo_depth"]:.2f} deep, from the logo SVG'),
    ]),
    ("Movement ring (part 08)", [
        ("Material", "POM / acetal"),
        ("Register bore", f'Ø{P["ring_bore_dia"]:.2f} +0.05/−0 on the Ø25.60 Js8 band'),
        ("Outer Ø", f'Ø{P["ring_od"]:.2f} ±0.02 in a Ø{P["case_bore_dia"]:.2f} H8 bore'),
        ("Flange pocket", f'Ø{P["ring_flange_pocket"]:.2f} × 0.35 deep'),
        ("Clamp groove", f'Ø{P["ring_clamp_groove"]:.2f}, band dial−2.20 to dial−2.70'),
        ("Assembly", "movement in from the dial side, then the assembly in from the caseback"),
        ("Preload", "make the ring 0.05–0.10 taller than the pocket so the caseback preloads it"),
    ]),
    ("Lugs & bracelet interface", [
        ("Profile", "Ring-cut: revolved lug section, plan-cut to shape"),
        ("Plan taper", f'{3.27:.2f} at the root → {P["lug_tip_w"]:.2f} at the tip'),
        ("Flank leaves the case at", f'{P["lug_tangent_deg"]:.0f}° azimuth, tangent to Ø39'),
        ("Tips lie on", "one concentric circle (ring OD)"),
        ("Top chamfer", f'{P["lug_top_chamfer"]:.2f} mm, continuous around the tip'),
        ("Spring bar hole", f'Ø{P["springbar_dia"]:.2f} drilled through, {P["springbar_from_tip"]:.2f} from tip'),
        ("Spring bar axis", f'z {P["springbar_z"]:.2f} above the caseback plane'),
        ("Tip thickness", "3.55 mm full, tips swoop to z 0.30"),
        ("Lug underside", "leaves the case tangent to the bottom chamfer, crest +0.12 within 0.4 of the edge, then one monotone swoop to the tip "
         "(m -0.20) straight into the tip face — profile-gated in verify_case.py"),
        ("Edge breaks", "bottom tip edge chamfer 0.20 (now machined, was a callout)"),
        ("Countersink", f'90° × Ø{P["springbar_csink"]:.2f}, {P["springbar_csink_d"]:.2f} deep, both faces'),
        ("Bar spec", "Ø2.0 body, Ø1.2 tips (Rolex FB-7895 pattern)"),
        ("Oyster end-link land", f'Ø39.0 cylindrical down to z {P["endlink_land_z"]:.2f}'),
    ]),
]


def spec_rows(l2l, thk):
    rows = []
    for gname, items in GROUPS:
        rows.append(f'<tr class="grouprow"><td colspan="2">{gname}</td></tr>')
        for k, v in items:
            v = v.replace("{L2L}", f"{l2l:.1f}").replace("{THK}", f"{thk:.1f}")
            flag = ""
            if v.endswith("|V"):
                v = v[:-2]
                flag = '<span class="vflag">VERIFY</span>'
            rows.append(f'<tr><td class="k">{k}</td><td class="v">{v}{flag}</td></tr>')
    return "\n".join(rows)


def file_rows():
    order = ["assembly.step",
             "01_midcase", "02_bezel", "03_crystal", "04_caseback_ring",
             "05_caseback_sapph", "06_crown", "07_crown_tube",
             "08_movement_ring", "09_bezel_spring"]
    label = {
        "assembly.step": "Full assembly (incl. movement + dial reference)",
        "01_midcase": "Midcase + lugs + crown boss",
        "02_bezel": "Rotating 24h bezel (engraved, pip pocket)",
        "03_crystal": "Sapphire crystal",
        "04_caseback_ring": "Caseback ring (engraved)",
        "05_caseback_sapph": "Caseback sapphire",
        "06_crown": "Crown (Kelsus K)",
        "07_crown_tube": "Crown tube",
        "08_movement_ring": "Movement ring (9075 register)",
        "09_bezel_spring": "Bezel retention spring ring (slit)",
    }
    out = []
    for o in order:
        if o.endswith(".step"):
            name = o
        else:
            name = o + ".step"
        p = os.path.join(OUT, name)
        if not os.path.exists(p):
            continue
        kb = os.path.getsize(p) / 1024
        out.append(f'<div class="f"><span>{name}</span><span>{label[o]} · {kb:.0f} KB</span></div>')
    return "\n".join(out)


def main():
    l2l, thk = overall()
    tmpl = open(os.path.join(HERE, "review.htmltmpl")).read()
    html = (tmpl
            .replace("{{IMG_ISO}}", b64(os.path.join(OUT, "prev_iso.png")))
            .replace("{{IMG_TOP}}", b64(os.path.join(OUT, "prev_top.png")))
            .replace("{{IMG_SIDE}}", b64(os.path.join(OUT, "prev_side.png")))
            .replace("{{IMG_BACK}}", b64(os.path.join(OUT, "prev_back.png")))
            .replace("{{SPEC_ROWS}}", spec_rows(l2l, thk))
            .replace("{{FILES}}", file_rows())
            .replace("{{L2L}}", f"{l2l:.1f}")
            .replace("{{THK}}", f"{thk:.1f}"))
    dst = os.path.join(OUT, "review.html")
    open(dst, "w").write(html)
    print("wrote", dst, f"({len(html)//1024} KB)  L2L={l2l:.1f} THK={thk:.1f}")
    # standalone copy for GitHub Pages: the artifact host wraps the body
    # fragment in a document; the Pages copy needs the wrapper itself
    docs = os.path.join(HERE, "docs")
    os.makedirs(docs, exist_ok=True)
    page = (
        "<!doctype html>\n<html lang=\"en\">\n<head>\n"
        "<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, "
        "initial-scale=1\">\n"
        "<title>Kelsus Intercontinental - Open Miyota 9075 GMT Case</title>\n"
        "<meta name=\"description\" content=\"Design review for an open, "
        "parametric 39 mm GMT watch case for the Miyota 9075. MIT code, "
        "CERN-OHL-P hardware.\">\n"
        "</head>\n<body style=\"margin:0\">\n" + html + "\n</body>\n</html>\n")
    dst2 = os.path.join(docs, "index.html")
    open(dst2, "w").write(page)
    print("wrote", dst2, f"({len(page)//1024} KB)")


if __name__ == "__main__":
    main()
