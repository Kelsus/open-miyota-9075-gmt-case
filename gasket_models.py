"""Gasket 3D models (free/uncompressed state) for factory DFM.

The spec called out the crystal I-ring and the bezel centring O-ring by
cross-section only; the factory asked for solids. These are the FREE
dimensions -- installed state compresses the I-ring 0.10 diametral and
stretches the O-ring 0.2 onto the boss groove floor.

Run: python3 gasket_models.py  ->  output/10_iring_gasket.step,
output/11_bezel_oring.step
"""
import os

import cadquery as cq
from cadquery import exporters

import case_model as C

P = C.P
OUT = C.OUT


def iring():
    """Crystal I-ring, nylon/PA. Free: wall 0.35, OD = bore + 0.10 crush,
    height just under the crystal's cylindrical band."""
    od = P["crystal_bore_dia"] + 0.10          # 32.10 free, crushed to 32.00
    wall = 0.35
    h = 1.40
    z0 = C.CRYSTAL_SEAT_Z
    ring = (cq.Workplane("XZ")
            .moveTo(od / 2.0 - wall, z0).lineTo(od / 2.0, z0)
            .lineTo(od / 2.0, z0 + h).lineTo(od / 2.0 - wall, z0 + h)
            .close().revolve(360, (0, 0, 0), (0, 1, 0)))
    return ring.val()


def bezel_oring():
    """Bezel centring O-ring, NBR/FKM, cs 0.70. Free ID sits 0.2 under
    the boss groove floor (Ø33.0) for a light stretch fit."""
    cs = P["bezel_oring_cs"]
    free_id = P["bezel_oring_floor"] - 0.20    # 32.80
    R = (free_id + cs) / 2.0                   # torus centreline radius
    zc = C.ORING_Z0 + P["bezel_oring_w"] / 2.0
    tor = (cq.Workplane("XZ")
           .moveTo(R, zc).circle(cs / 2.0)
           .revolve(360, (0, 0, 0), (0, 1, 0)))
    return tor.val()


if __name__ == "__main__":
    for name, sol in (("10_iring_gasket", iring()),
                      ("11_bezel_oring", bezel_oring())):
        sols = 1 if sol.Volume() > 0 else 0
        assert sols == 1
        exporters.export(sol, os.path.join(OUT, name + ".step"))
        print(f"  wrote {name}.step  vol {sol.Volume():.2f}")
