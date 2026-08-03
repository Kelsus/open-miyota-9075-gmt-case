# Xometry order guide: fitment kit

Everything in this folder goes into one Xometry quote. Seven parts, all
1:1 with the master design except three prototype substitutions (coarser
caseback thread, pin crown instead of the threaded crown+tube, acrylic
instead of sapphire). Together they let you fully case a Miyota 9075:
movement + ring into the case, caseback screws in and sets the preload,
dial-side and hand clearance visible through the acrylic crystal, stem
alignment through the tube bore, bezel and crown for the complete look.

## Upload

Instant quote → CNC machining → upload all 7 STEPs. Then **attach
`intercontinental_fitment_kit_drawings.pdf` to every part.** The STEPs
carry no thread geometry; without the drawing you receive smooth bores
instead of threads.

## Per-part settings

| File | Process | Material | Finish | Qty |
|---|---|---|---|---|
| x01_midcase.step | CNC, 5-axis | Aluminum 6061-T6 | As machined (or bead blast) | 1 |
| x02_bezel.step | CNC | Aluminum 6061-T6 | As machined | 1 |
| x04_caseback.step | CNC | Aluminum 6061-T6 | As machined | 1 |
| x06_crown_proto.step | CNC (lathe) | Aluminum 6061 or 303 SS | As machined | 1 |
| x08_movement_ring.step | CNC | Acetal (Delrin/POM) | As machined | 1 |
| x03_crystal_acrylic.step | CNC | Acrylic (PMMA), clear | As machined | 1 |
| x05_window_acrylic.step | CNC | Acrylic (PMMA), clear | As machined | 1 |

Tolerance option: pick the tier that honors attached drawings (their
standard is a blanket ±0.13, which is not enough for the H7/Js8 fits;
the drawing callouts override where noted). Threads: M30×1.0 internal (case) and
external (back) are called out on sheets 1 and 3.

## Expect from DFM review

- Warnings on the tiny cosmetic features (0.25 engravings, 120 scallops,
  coin edge, Ø0.65 ball pocket). All are marked "best effort / may be
  omitted" on the drawings. Accept their recommendation; none affect
  fitment.
- Possible upcharge or pushback on the M30×1.0 internal thread and the
  deep 5-axis lug undersides. Both are legitimate work; pay it or ask
  for their alternative.
- If a part is rejected as unmachinable-at-price (most likely the coin
  edge or crown), drop the feature rather than the part.

## Budget guidance

The midcase (full 5-axis) dominates cost. If the quote shocks you, order
in two waves: **wave 1 = x01 + x04 + x08** (that's the complete movement
fitment test), wave 2 = bezel/crown/acrylics (look and feel). Aluminum
first; reorder the keepers in 316L once the fit is proven. Expect
roughly 3 to 5 times the aluminum price and a longer lead.

## When the parts arrive

1. Deburr check: run a fingernail around the dial pocket and crystal
   seat; any burr there scratches the dial.
2. Drop the 9075 (no dial) into the movement ring, ring into the case.
   It should register with zero rock.
3. Fit the dial (Ø31.0): it must clear the rehaut all round.
4. Stem check: cut a stem to length, thread into the movement, confirm
   it exits the Ø2.48 bore centered with no bind. Slide the crown pin in.
5. Caseback: screw in (M30×1.0). It should seat fully and just clamp the
   movement ring with no rattle. The design carries 0.02 preload; with
   ±0.05 aluminum tolerances expect anything from a light rattle to a
   light pinch. Note which you got, it calibrates the steel run.
6. Hands + acrylic crystal: press hands at 12:00:00, seat the crystal,
   verify hour/minute/GMT/seconds all clear the crystal underside.
7. Bezel: seat it on the boss over the groove. With no spring ring it
   lifts off again; that is expected. Check the reveal band is even and it clears the crystal.
8. Bracelet: spring bars through the Ø1.35 holes, end link against the
   Ø39 land, check for rock.

Log every deviation. That list is what gets tuned before the 316L run
or the factory RFQ.
