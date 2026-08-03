"""
Render the CAD from the same viewpoints as the mockups and build
side-by-side comparison sheets, plus a silhouette-overlap metric.

The mocks are the design ground truth. The side-by-side sheets are the
useful output — use them for design judgement.

CAVEAT on the IoU number: the mocks are product renders with contact
shadows that touch the case, so the extracted silhouette always absorbs
some shadow along the bottom. IoU is therefore INDICATIVE ONLY (expect
~0.8 even for a perfect match) and is deliberately NOT a pass/fail gate.
The hard gate is verify_case.py; exact dimensions come from the metrology
measurements in docs/mock_metrology.md.
"""
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from stl import mesh as stlmesh
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")
MOCKS = os.path.join(HERE, "mocks")
CMP = os.path.join(OUT, "compare")
os.makedirs(CMP, exist_ok=True)

# view name -> (mock file, elev, azim)  [azim/elev tuned to the mock camera]
VIEWS = {
    "top":    ("topdownviewofcase.png",        90.0, -90.0),
    "side":   ("crownsideviewofcase.png",       0.0,   0.0),
    "iso":    ("threequarterviewofcase.png",   34.0, -128.0),
    "iso2":   ("threequarterviewofcase2.png",  36.0,  -58.0),
}

METAL = {
    "01_midcase":        (0.78, 0.79, 0.82),
    "02_bezel":          (0.74, 0.75, 0.79),
    "04_caseback_ring":  (0.78, 0.79, 0.82),
    "06_crown":          (0.68, 0.69, 0.73),
    "07_crown_tube":     (0.58, 0.59, 0.63),
}
GLASS = ("03_crystal", "05_caseback_sapph")

L1 = np.array([0.35, -0.45, 0.82]); L1 /= np.linalg.norm(L1)
L2 = np.array([-0.55, 0.35, 0.40]); L2 /= np.linalg.norm(L2)


def shade(tris, base):
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    ln = np.linalg.norm(n, axis=1, keepdims=True); ln[ln == 0] = 1
    n = n / ln
    b = 0.20 + 0.62 * np.abs(n @ L1) + 0.26 * np.abs(n @ L2) ** 2
    return np.clip(np.array(base)[None, :] * b[:, None], 0, 1)


def load():
    tris, cols, pts, glass = [], [], [], []
    for name, base in METAL.items():
        f = os.path.join(OUT, name + ".stl")
        if not os.path.exists(f):
            continue
        t = stlmesh.Mesh.from_file(f).vectors
        tris.append(t); cols.append(shade(t, base)); pts.append(t.reshape(-1, 3))
    for name in GLASS:
        f = os.path.join(OUT, name + ".stl")
        if not os.path.exists(f):
            continue
        t = stlmesh.Mesh.from_file(f).vectors
        glass.append(t); pts.append(t.reshape(-1, 3))
    return np.concatenate(tris), np.concatenate(cols), glass, np.vstack(pts)


def render_view(elev, azim, size=900, transparent=True):
    tris, cols, glass, pts = load()
    fig = plt.figure(figsize=(size / 130, size / 130), dpi=130)
    ax = fig.add_subplot(111, projection="3d")
    ax.add_collection3d(Poly3DCollection(tris, facecolors=cols,
                                         edgecolor="none"))
    for t in glass:
        ax.add_collection3d(Poly3DCollection(
            t, alpha=0.30, facecolor=(0.72, 0.86, 0.94), edgecolor="none"))
    mn, mx = pts.min(0), pts.max(0)
    ctr = (mn + mx) / 2
    rng = (mx - mn).max() / 2 * 1.02
    ax.set_xlim(ctr[0]-rng, ctr[0]+rng)
    ax.set_ylim(ctr[1]-rng, ctr[1]+rng)
    ax.set_zlim(ctr[2]-rng, ctr[2]+rng)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    path = os.path.join(CMP, f"_cad_{elev:.0f}_{azim:.0f}.png")
    plt.savefig(path, transparent=transparent)
    plt.close(fig)
    return path


def silhouette(img_path):
    """Binary mask of the object.

    CAD renders have real alpha. The mocks are product shots on a smooth
    GRADIENT backdrop with soft shadows, so a flat-colour threshold floods
    the whole frame. Instead grow a background region inward from the
    border, accepting a neighbour only if it is close to its own local
    neighbourhood — that tracks the gradient but stops at the watch's hard
    edge. Whatever the background cannot reach is the object.
    """
    from scipy import ndimage
    im = Image.open(img_path).convert("RGBA")
    a = np.array(im)
    if a[..., 3].min() < 250:                     # CAD render: use alpha
        return a[..., 3] > 128

    g = np.array(Image.open(img_path).convert("L")).astype(float)
    # local gradient magnitude: smooth backdrop ~0, object edges high
    gx = ndimage.sobel(g, axis=1)
    gy = ndimage.sobel(g, axis=0)
    edge = np.hypot(gx, gy)
    smooth = edge < 12.0                          # candidate background

    # flood the smooth region from the frame border
    lbl, n = ndimage.label(smooth)
    border = set(np.unique(np.concatenate([
        lbl[0, :], lbl[-1, :], lbl[:, 0], lbl[:, -1]])))
    border.discard(0)
    bg = np.isin(lbl, list(border))

    # NO closing here: a closing kernel bridges the gap between the lugs and
    # swallows the very feature we are trying to compare.
    obj = ~bg
    obj = ndimage.binary_opening(obj, np.ones((3, 3)))     # despeckle first
    # keep the largest blob BEFORE filling, so the drop shadow (a separate
    # blob touching the frame bottom) never merges into the case
    lbl2, n2 = ndimage.label(obj)
    if n2 > 1:
        sizes = ndimage.sum(obj, lbl2, range(1, n2 + 1))
        obj = lbl2 == (int(np.argmax(sizes)) + 1)
    obj = ndimage.binary_fill_holes(obj)                   # solid interior
    return obj


def bbox_of(mask):
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return None
    return xs.min(), xs.max(), ys.min(), ys.max()


def normalise(mask, size=560):
    """Crop to the silhouette bbox and scale to a fixed box, preserving
    aspect — so CAD and mock are compared on shape, not framing."""
    bb = bbox_of(mask)
    if bb is None:
        return np.zeros((size, size), bool)
    x0, x1, y0, y1 = bb
    sub = mask[y0:y1+1, x0:x1+1]
    h, w = sub.shape
    s = (size - 20) / max(h, w)
    im = Image.fromarray((sub * 255).astype(np.uint8)).resize(
        (max(int(w * s), 1), max(int(h * s), 1)), Image.NEAREST)
    arr = np.array(im) > 128
    canvas = np.zeros((size, size), bool)
    hh, ww = arr.shape
    oy, ox = (size - hh) // 2, (size - ww) // 2
    canvas[oy:oy+hh, ox:ox+ww] = arr
    return canvas


def main():
    report = []
    for view, (mockfile, elev, azim) in VIEWS.items():
        mock_path = os.path.join(MOCKS, mockfile)
        if not os.path.exists(mock_path):
            continue
        cad_path = render_view(elev, azim)
        m_mask = normalise(silhouette(mock_path))
        c_mask = normalise(silhouette(cad_path))
        inter = np.logical_and(m_mask, c_mask).sum()
        union = np.logical_or(m_mask, c_mask).sum()
        iou = inter / union if union else 0.0
        report.append((view, iou))

        # comparison sheet: mock | cad | overlay
        fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.8), dpi=115)
        axes[0].imshow(Image.open(mock_path)); axes[0].set_title(
            f"MOCK — {view}", fontsize=10)
        axes[1].imshow(Image.open(cad_path)); axes[1].set_title(
            f"CAD — elev {elev:.0f}, azim {azim:.0f}", fontsize=10)
        ov = np.zeros((*m_mask.shape, 3))
        ov[..., 0] = m_mask * 0.95           # mock = red
        ov[..., 1] = c_mask * 0.85           # cad  = green
        ov[..., 2] = np.logical_and(m_mask, c_mask) * 0.5
        axes[2].imshow(ov)
        axes[2].set_title(f"overlay — IoU {iou:.3f} "
                          f"(red=mock only, green=CAD only)", fontsize=10)
        for a in axes:
            a.set_xticks([]); a.set_yticks([])
        plt.tight_layout()
        p = os.path.join(CMP, f"compare_{view}.png")
        plt.savefig(p, facecolor="white")
        plt.close(fig)
        print(f"{view:6s} IoU={iou:.3f}  -> {os.path.basename(p)}")

    if report:
        avg = sum(r[1] for r in report) / len(report)
        print(f"\nmean silhouette IoU vs mocks: {avg:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
