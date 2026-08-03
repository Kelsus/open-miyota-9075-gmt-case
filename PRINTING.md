# 3D printing the case

A 1:1 snap-together prototype of the case. It is a form, feel, and
assembly prototype: wrist presence, lug drape, bezel proportions, end
link and dial fit. It is not a functional watch case. The machined
design's fasteners are below FDM resolution (the M30 x 0.5 caseback
thread, the S0.9 crown thread, and the 0.35 mm steel bezel spring ring),
so `print_variant.py` derives adapted parts where every interface is a
snap or press fit sized for plastic. Files are in `output/print/`.

| File | Replaces | How it attaches |
|---|---|---|
| `p00_snap_coupon.stl` | nothing | 20 minute test ring: dial in the caseback snap before the long case print |
| `p01_case.stl` | 01 midcase | snap bore Ø30.30 with a groove replaces the thread; straight Ø2.5 crown hole; boss lead-in chamfer |
| `p02_bezel.stl` | 02 bezel + 09 spring ring | integral snap lip (Ø33.35) clicks over the boss into the retention groove and still rotates |
| `p03_crystal.stl` | 03 crystal + gasket | 6 crush ribs press into the Ø32.0 bore |
| `p04_back.stl` | 04 back + M30 thread | 3 cantilever snap tabs click into the case groove |
| `p05_window.stl` | 05 sapphire | clear disc, 3 crush ribs, presses into the back from outside |
| `p06_crown.stl` | 06 crown + 07 tube | integral Ø2.42 pin presses into the crown hole |
| `p08_movement_ring.stl` | 08 ring | drops into the case bore as designed |

`output/print/` also contains Bambu Studio project files (`*.3mf`) from
a successful print run on a Bambu Lab H2C with a 0.2 mm nozzle. If you
run Bambu Studio, open one of those and skip the setup below.

## Materials and nozzle

- **PETG** for the case, bezel, back, and movement ring. The snaps need
  PETG's strain headroom near 5 percent; PLA whitens or cracks on the
  caseback tabs and the bezel lip.
- **Clear PETG** or PC for the crystal and window. They print
  translucent rather than glass clear. For a clearer window, cut 1.5 mm
  acrylic to Ø23.2 and skip `p05`.
- Crown: any material.
- A **0.2 mm nozzle** is recommended for the bezel, crown, crystal, and
  window (numerals, coin edge, logo, ribs). 0.4 mm works for the case,
  back, coupon, and movement ring. With only a 0.4 mm nozzle everything
  still prints; the engraving detail is what you lose.

## Slicer setup

Settings below are for Bambu Studio and carry over to any modern slicer.
Global for all parts: 0.08 to 0.12 mm layers, 4 walls, 25 percent gyroid
infill, seam position "Aligned" (put it at 12 o'clock on the case so it
hides between the lugs).

Per part:

| Part | Orientation on plate | Supports |
|---|---|---|
| coupon | as exported (flat) | none |
| case | caseback face down (as exported) | tree supports under the lug undersides only; with a dual-nozzle printer, use a support interface material that the body does not bond to, which leaves glassy undersides |
| bezel | skirt down (as exported) | none; the internal ceiling bridges Ø32 to Ø34, enable "thick bridges" |
| back | engraved face down (as exported) | none; the engraving prints into the first layers and stays legible |
| crystal | seat down, dome up | none |
| window | flat down | none |
| crown | logo face down, pin up | none |
| movement ring | flat down | none |

## Print order

1. **Print `p00_snap_coupon` and `p04_back` first.** Click the back into
   the coupon: it should seat with a firm push and a click, and take
   real effort to pry back out (pry at the wrench notches).
   - Too tight or no click: set X-Y hole compensation +0.05 to +0.10 on
     the coupon (and later the case), or sand the three bumps.
   - Too loose: go the other way, or reprint the back scaled 100.3
     percent in X-Y only.
   - Carry the winning compensation into the case print.
2. Print the case (the long print) and the rest in any order.

## Assembly

1. **Movement ring** drops into the case from the back, clamp band up.
2. **Crystal**: press into the top bore with a flat block until it stops
   on the seat. The bore's lead-in chamfer does the guiding.
3. **Bezel**: set it square on the boss and press straight down with
   both thumbs. The lip climbs the boss chamfer, snaps into the groove,
   and the bezel then spins with a little play. The prototype has no
   detent clicks; the 0.18 mm scallops and the ball are below printable
   scale.
4. **Caseback**: align and press until the three tabs click into the
   groove. Remove by pushing from the crystal side with the crystal
   out, or pry at the wrench notches.
5. **Window**: press into the back's pocket from the outside.
6. **Crown**: the printed crown hole comes out near Ø2.3 to 2.4. Run a
   2.4 mm drill through it if available, then press the crown pin in.
   Leave it dry so the depth can be adjusted; a dot of CA glue once it
   is right.
7. **Spring bars**: the Ø1.35 lug holes print near Ø1.15. Open them
   with a 1.4 mm drill, then fit Ø2.0 spring bars and end links as
   normal.

## What this prototype can and cannot tell you

**Good for:** wrist feel at 47.9 x 39 x 12.0, lug drape and stance,
bezel diameter and height proportions, end link and bracelet fit on the
Ø39 land, dial opening at Ø31, crown position and reach.

**Not representative:** thread feel, water resistance (none), bezel
detents, surface finish, weight (a PETG case is near 8 g against 49 g
in steel; add the movement and bracelet for a fairer wrist impression),
and the crystal optics.

**Real movement caution:** the case will hold a Miyota 9075 for a dial
and stem alignment check, but printed plastic sheds static and debris.
Keep the movement in its ring, dust it before it goes back into anything
that matters, and do not force the stem: printed hole tolerances are
plus or minus 0.1 at best.

## Regenerating

After any change to the master model:

```bash
python3 case_model.py && python3 print_variant.py
```
