"""Render exported STL parts to shaded PNG previews.
All opaque parts are merged into ONE Poly3DCollection so matplotlib's
painter algorithm depth-sorts globally (per-collection drawing order
otherwise hides parts behind each other)."""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from stl import mesh as stlmesh

OUT = os.path.join(os.path.dirname(__file__), "output")

METAL = {
    "01_midcase":        (0.76, 0.77, 0.80),
    "02_bezel":          (0.68, 0.69, 0.73),
    "04_caseback_ring":  (0.76, 0.77, 0.80),
    "06_crown":          (0.62, 0.63, 0.67),
    "07_crown_tube":     (0.55, 0.56, 0.60),
}
GLASS = {
    "03_crystal":        (0.72, 0.86, 0.94),
    "05_caseback_sapph": (0.72, 0.86, 0.94),
}

L1 = np.array([0.4, -0.5, 0.75]); L1 = L1 / np.linalg.norm(L1)
L2 = np.array([-0.6, 0.3, 0.35]); L2 = L2 / np.linalg.norm(L2)


def shade(tris, base):
    v0, v1, v2 = tris[:, 0], tris[:, 1], tris[:, 2]
    n = np.cross(v1 - v0, v2 - v0)
    ln = np.linalg.norm(n, axis=1, keepdims=True); ln[ln == 0] = 1
    n = n / ln
    d1 = np.abs(n @ L1); d2 = np.abs(n @ L2)
    b = 0.22 + 0.60 * d1 + 0.28 * d2 ** 2
    return np.clip(np.array(base)[None, :] * b[:, None], 0, 1)


def load():
    tris_all, cols_all, pts = [], [], []
    for name, base in METAL.items():
        f = os.path.join(OUT, name + ".stl")
        if not os.path.exists(f):
            continue
        t = stlmesh.Mesh.from_file(f).vectors
        tris_all.append(t)
        cols_all.append(shade(t, base))
        pts.append(t.reshape(-1, 3))
    glass = []
    for name, base in GLASS.items():
        f = os.path.join(OUT, name + ".stl")
        if not os.path.exists(f):
            continue
        t = stlmesh.Mesh.from_file(f).vectors
        glass.append(t)
        pts.append(t.reshape(-1, 3))
    return (np.concatenate(tris_all), np.concatenate(cols_all),
            glass, np.vstack(pts))


def render(title, elev, azim, fname):
    tris, cols, glass, pts = load()
    fig = plt.figure(figsize=(7.2, 7.2), dpi=140)
    ax = fig.add_subplot(111, projection="3d")
    pc = Poly3DCollection(tris, facecolors=cols, edgecolor="none")
    ax.add_collection3d(pc)
    for t in glass:
        g = Poly3DCollection(t, alpha=0.22, facecolor=(0.72, 0.86, 0.94),
                             edgecolor="none")
        ax.add_collection3d(g)
    mn, mx = pts.min(0), pts.max(0)
    ctr = (mn + mx) / 2; rng = (mx - mn).max() / 2 * 1.02
    ax.set_xlim(ctr[0]-rng, ctr[0]+rng)
    ax.set_ylim(ctr[1]-rng, ctr[1]+rng)
    ax.set_zlim(ctr[2]-rng, ctr[2]+rng)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    plt.savefig(os.path.join(OUT, fname), transparent=True)
    plt.close(fig)
    print("wrote", fname)


if __name__ == "__main__":
    render("iso",   26, -58, "prev_iso.png")
    render("side",   4,   0, "prev_side.png")
    render("front",  4,  90, "prev_front.png")
    render("top",   88, -90, "prev_top.png")
    render("back", -88, -90, "prev_back.png")
