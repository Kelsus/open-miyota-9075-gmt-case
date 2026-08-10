"""Color-coded finishing map for the factory.

Renders the case, bezel, caseback, and crown from the shipped STLs with
every triangle classified by its finish (normal direction and position
decide the class), plus leader-line callouts. Output:
output/finishing_map.pdf

Run: python3 build_finishing_map.py
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Patch
from stl import mesh as stlmesh

HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "output")
EDGE_BAND = None

COLORS = {
    "radial":   ("#7da7d9", "radial / sunburst brush"),
    "linear":   ("#8fbf8f", "linear brush (follow flank / arc)"),
    "circular": ("#b78fd9", "circular brush"),
    "polish":   ("#e8c96a", "polish"),
    "engrave":  ("#3a3a3a", "engraved (black lacquer fill on bezel)"),
}


def load(name):
    f = os.path.join(OUT, name + ".stl")
    if not os.path.exists(f):
        raise SystemExit(f"{f} missing - run case_model.py first")
    return stlmesh.Mesh.from_file(f).vectors.astype(np.float64)


def plan_edge_band(tris, lim=(-26, 26), W=640, band_mm=0.70):
    """Boolean pixel mask of the strip just inside the part's plan
    silhouette. The chamfer along the top boundary chain always lives in
    this strip; the diving lug top is interior."""
    lo, hi = lim
    scale = W / (hi - lo)
    mask = np.zeros((W, W), dtype=bool)
    uu, vv = tris[:, :, 0], tris[:, :, 1]
    for t_u, t_v in zip(uu, vv):
        pu = (t_u - lo) * scale
        pv = (t_v - lo) * scale
        umin, umax = int(max(0, pu.min())), int(min(W - 1, pu.max())) + 1
        vmin, vmax = int(max(0, pv.min())), int(min(W - 1, pv.max())) + 1
        if umin >= umax or vmin >= vmax:
            continue
        gu, gv = np.meshgrid(np.arange(umin, umax) + 0.5,
                             np.arange(vmin, vmax) + 0.5)
        det = ((pu[1] - pu[0]) * (pv[2] - pv[0])
               - (pv[1] - pv[0]) * (pu[2] - pu[0]))
        if abs(det) < 1e-12:
            continue
        w0 = ((pu[1] - gu) * (pv[2] - gv) - (pv[1] - gv) * (pu[2] - gu)) / det
        w1 = ((pu[2] - gu) * (pv[0] - gv) - (pv[2] - gv) * (pu[0] - gu)) / det
        w2 = 1 - w0 - w1
        m = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        mv, mu = np.where(m)
        mask[mv + vmin, mu + umin] = True
    eroded = mask.copy()
    for _ in range(max(1, round(band_mm * scale))):
        e = eroded.copy()
        e[1:, :] &= eroded[:-1, :]; e[:-1, :] &= eroded[1:, :]
        e[:, 1:] &= eroded[:, :-1]; e[:, :-1] &= eroded[:, 1:]
        eroded = e
    return mask & ~eroded, lo, scale


def render(ax, tris, classes, view, lim, flip=False):
    """Z-buffer render colored by finish class. view: 'side' (along -X,
    plot y,z), 'top' (along -Z, plot x,y), 'bottom' (along +Z), or
    'face' (along -X for the crown, plot y,z)."""
    W = H = 900
    (u0, u1, v0, v1) = lim
    if view == "side":
        uu, vv, dd = tris[:, :, 1], tris[:, :, 2], tris[:, :, 0]
    elif view == "top":
        uu, vv, dd = tris[:, :, 0], tris[:, :, 1], tris[:, :, 2]
    elif view == "bottom":
        # viewer outside the back (below, looking up): u=-x, v=+y keeps
        # the engraving reading correctly
        uu, vv, dd = -tris[:, :, 0], tris[:, :, 1], -tris[:, :, 2]
    elif view == "face+x":
        # viewer at +x looking at the crown face: u=+y, v=+z
        uu, vv, dd = tris[:, :, 1], tris[:, :, 2], tris[:, :, 0]
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    nl = np.linalg.norm(n, axis=1)
    ok = nl > 1e-12
    n = n[ok] / nl[ok, None]
    light = np.array([0.4, -0.45, 0.8]); light /= np.linalg.norm(light)
    lum = 0.55 + 0.45 * np.clip(np.abs(n @ light), 0, 1)
    img = np.ones((H, W, 3))
    zbuf = np.full((H, W), -1e9)
    c_pol = np.array(matplotlib.colors.to_rgb(COLORS["polish"][0]))
    c_rad = np.array(matplotlib.colors.to_rgb(COLORS["radial"][0]))
    base = np.array([matplotlib.colors.to_rgb(
                        COLORS[c][0] if c != "auto" else COLORS["radial"][0])
                     for c in classes])[ok]
    is_auto = np.array([c == "auto" for c in classes])[ok]
    xx, yy = tris[:, :, 0][ok], tris[:, :, 1][ok]
    for t_u, t_v, t_d, t_x, t_y, l, col, au in zip(
            uu[ok], vv[ok], dd[ok], xx, yy, lum, base, is_auto):
        pu = (t_u - u0) / (u1 - u0) * W
        pv = (v1 - t_v) / (v1 - v0) * H
        umin, umax = int(max(0, pu.min())), int(min(W - 1, pu.max())) + 1
        vmin, vmax = int(max(0, pv.min())), int(min(H - 1, pv.max())) + 1
        if umin >= umax or vmin >= vmax:
            continue
        gu, gv = np.meshgrid(np.arange(umin, umax) + 0.5,
                             np.arange(vmin, vmax) + 0.5)
        det = ((pu[1] - pu[0]) * (pv[2] - pv[0])
               - (pv[1] - pv[0]) * (pu[2] - pu[0]))
        if abs(det) < 1e-12:
            continue
        w0 = ((pu[1] - gu) * (pv[2] - gv) - (pv[1] - gv) * (pu[2] - gu)) / det
        w1 = ((pu[2] - gu) * (pv[0] - gv) - (pv[2] - gv) * (pu[0] - gu)) / det
        w2 = 1 - w0 - w1
        m = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        if not m.any():
            continue
        depth = w0 * t_d[0] + w1 * t_d[1] + w2 * t_d[2]
        sv, su = np.where(m)
        vi, ui = sv + vmin, su + umin
        dd_ = depth[m]
        upd = dd_ > zbuf[vi, ui]
        zbuf[vi[upd], ui[upd]] = dd_[upd]
        if au and EDGE_BAND is not None:
            band, blo, bscale = EDGE_BAND
            Wb = band.shape[0]
            px = (w0 * t_x[0] + w1 * t_x[1] + w2 * t_x[2])[m][upd]
            py = (w0 * t_y[0] + w1 * t_y[1] + w2 * t_y[2])[m][upd]
            bu = np.clip(((px - blo) * bscale).astype(int), 0, Wb - 1)
            bv = np.clip(((py - blo) * bscale).astype(int), 0, Wb - 1)
            inb = band[bv, bu]
            cols = np.where(inb[:, None], c_pol, c_rad)
            img[vi[upd], ui[upd]] = np.clip(cols * l, 0, 1)
        else:
            img[vi[upd], ui[upd]] = np.clip(col * l, 0, 1)
    ax.imshow(img, extent=(u0, u1, v0, v1))
    ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)


def classify_case(tris):
    """Midcase: up-facing -> radial brush; steep -> linear brush;
    slopes -> polish (chamfers, bevels); down-facing -> linear brush."""
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    nl = np.linalg.norm(n, axis=1); nz = np.zeros(len(n))
    nz[nl > 1e-12] = n[nl > 1e-12, 2] / nl[nl > 1e-12]
    rc = np.hypot(tris[:, :, 0].mean(axis=1), tris[:, :, 1].mean(axis=1))
    xc = tris[:, :, 0].mean(axis=1)
    yc = tris[:, :, 1].mean(axis=1)
    # the polished chamfer is one continuous band along the top boundary
    # chain: case rim AND down every lug edge to the tip. Chamfer surface
    # always lies in the plan-silhouette edge strip; the diving lug top
    # (same normal band) is interior. Facets in the ambiguous normal band
    # are marked "auto" and resolved PER PIXEL in render() against the
    # strip, so the band edge is smooth rather than facet-jagged.
    global EDGE_BAND
    EDGE_BAND = plan_edge_band(tris)
    out = []
    for i in range(len(tris)):
        if abs(nz[i]) < 0.25 or nz[i] < -0.25:
            out.append("linear")
        elif 0.25 < nz[i] < 0.88:
            out.append("auto")
        else:
            out.append("radial")
    return out


def classify_bezel(tris):
    """Bezel: coned top -> sunburst (radial); bevel/chamfers -> polish;
    coin band and walls -> linear; engraving floors (down-facing tiny
    faces high on the part) render dark via the engrave class."""
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    nl = np.linalg.norm(n, axis=1); nz = np.zeros(len(n))
    nz[nl > 1e-12] = n[nl > 1e-12, 2] / nl[nl > 1e-12]
    zc = tris[:, :, 2].mean(axis=1)
    rc = np.hypot(tris[:, :, 0].mean(axis=1), tris[:, :, 1].mean(axis=1))
    zt, ap_r, bev_r, drop = 11.97, 15.95, 18.965, 0.80
    out = []
    for i in range(len(tris)):
        if nz[i] > 0.9 and zc[i] > 10.9 and rc[i] < 19.1:
            z_cone = zt - drop * (rc[i] - ap_r) / (bev_r - ap_r)
            out.append("engrave" if zc[i] < z_cone - 0.10 else "radial")
        elif abs(nz[i]) < 0.3:
            out.append("linear")
        else:
            out.append("polish")
    return out


def classify_back(tris):
    """Caseback: bottom ring face -> circular brush; engraving floors
    (recessed, facing down) -> engrave; everything else neutral polish."""
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    nl = np.linalg.norm(n, axis=1); nz = np.zeros(len(n))
    nz[nl > 1e-12] = n[nl > 1e-12, 2] / nl[nl > 1e-12]
    zc = tris[:, :, 2].mean(axis=1)
    out = []
    for i in range(len(tris)):
        if nz[i] < -0.85 and zc[i] < 0.2:
            out.append("circular")
        elif nz[i] < -0.5 and zc[i] > 0.2:
            out.append("engrave")
        else:
            out.append("polish")
    return out


def classify_crown(tris):
    """Crown: everything polished; the K engraving floor faces +X
    recessed behind the end face."""
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    nl = np.linalg.norm(n, axis=1); nx = np.zeros(len(n))
    nx[nl > 1e-12] = n[nl > 1e-12, 0] / nl[nl > 1e-12]
    xc = tris[:, :, 0].mean(axis=1)
    xmax = tris[:, :, 0].max()
    out = []
    for i in range(len(tris)):
        if nx[i] > 0.8 and xc[i] < xmax - 0.1:
            out.append("engrave")
        else:
            out.append("polish")
    return out


def note(ax, text, xy, xytext):
    ax.annotate(text, xy=xy, xytext=xytext, fontsize=7.5,
                arrowprops=dict(arrowstyle="-", lw=0.7, color="#333"),
                ha="left", va="center", annotation_clip=False,
                clip_on=False)


def sheet(pdf, title, panels, callouts, legend_keys, footnote=None):
    fig = plt.figure(figsize=(11.69, 8.27), dpi=150)
    fig.text(0.05, 0.95, title, fontsize=14, fontweight="bold")
    axes = []
    for i, (tris, classes, view, lim, sub) in enumerate(panels):
        ax = fig.add_axes((0.05 + i * 0.46, 0.24, 0.42, 0.62))
        render(ax, tris, classes, view, lim)
        ax.set_title(sub, fontsize=9, loc="left")
        axes.append(ax)
    for ax_i, text, xy, xytext in callouts:
        note(axes[ax_i], text, xy, xytext)
    handles = [Patch(facecolor=COLORS[k][0], label=COLORS[k][1])
               for k in legend_keys]
    fig.legend(handles=handles, loc="lower left",
               bbox_to_anchor=(0.05, 0.045), fontsize=8, ncol=2,
               frameon=False)
    if footnote:
        fig.text(0.05, 0.115, footnote, fontsize=7, style="italic")
    fig.text(0.05, 0.025,
             "KELSUS INTERCONTINENTAL - FINISHING MAP - colors are finish "
             "classes, geometry per STEP - all edge breaks R0.1 polished",
             fontsize=6.5)
    pdf.savefig(fig); plt.close(fig)
    print(" ", title)


def main():
    case = load("01_midcase")
    bez = load("02_bezel")
    back = load("04_caseback_ring")
    crown = load("06_crown")
    dst = os.path.join(OUT, "finishing_map.pdf")
    with PdfPages(dst) as pdf:
        cc = classify_case(case)
        sheet(pdf, "Sheet 1 - Midcase",
              [(case, cc, "side", (-26, 26, -3, 15), "side"),
               (case, cc, "top", (-26, 26, -26, 26), "top")],
              [(0, "flank + lug flanks:\nlinear brush", (19.4, 5.5), (-25.5, 9.5)),
               (0, "chamfer 0.45: polish,\ncontinuous rim to lug tip", (17.5, 8.0), (-25.5, 13.5)),
               (0, "bottom-edge chamfer\n0.30: polish", (18.5, 1.4), (-25.5, -1.5)),
               (1, "case top + lug tops:\nradial brush", (8, 13), (-25, 23)),
               (1, "lug underside: linear\nbrush along the horn", (-11, -21.5), (-25, -24))],
              ["radial", "linear", "polish"],
              footnote=("The polished chamfer is ONE continuous band: "
                        "case rim, down every lug edge, around the tip "
                        "(0.45), plus the bottom-edge chamfer (0.30)."))
        bc = classify_bezel(bez)
        sheet(pdf, "Sheet 2 - Bezel",
              [(bez, bc, "top", (-21, 21, -21, 21), "top"),
               (bez, bc, "side", (-21, 21, 7.5, 13), "side")],
              [(0, "coned top face:\nsunburst brush", (5, 16.8), (9, 19.6)),
               (0, "scale + triangles: engrave\n0.25, black lacquer fill", (-8, 15.2), (-20.5, 19.2)),
               (0, "lume pip at 24:\nSuper-LumiNova", (0, -16.5), (5, -20.3)),
               (1, "long outer bevel: polish", (19.0, 11.2), (2, 12.6)),
               (1, "coin edge: cut sharp", (19.3, 9.2), (6, 8.3))],
              ["radial", "linear", "polish", "engrave"])
        kc = classify_back(back)
        sheet(pdf, "Sheet 3 - Caseback ring and crown",
              [(back, kc, "bottom", (-16, 16, -16, 16),
                "caseback, outside face (as worn view)"),
               (crown, classify_crown(crown), "face+x", (-4.5, 4.5, 0.2, 9.2),
                "crown end face")],
              [(0, "visible ring:\ncircular brush", (12.5, 6), (8.5, 13.5)),
               (0, "engraving 0.18 deep", (0, 12.8), (-15.5, 15)),
               (0, "wrench notches:\nas machined", (-8.5, -9.5), (-15.8, -14)),
               (1, "entire crown: polish", (2.6, 6.8), (0.6, 8.8)),
               (1, "K logo engraved 0.30,\nvector file supplied", (0.8, 4.6), (1.6, 1.0))],
              ["circular", "polish", "engrave"])
    print("wrote", dst)


if __name__ == "__main__":
    main()
