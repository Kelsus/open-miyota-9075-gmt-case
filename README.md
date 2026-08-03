# Open Miyota 9075 GMT case

A complete, parametric watch case for the Miyota 9075 GMT movement,
written in [CadQuery](https://cadquery.readthedocs.io/) and verified by
a 113-assertion test suite. The repository contains everything needed to
study the design, rebuild it from parameters, 3D print a snap-together
prototype, or send it to a machine shop: STEP files for all nine parts,
drawing callouts for the features STEP cannot carry, print-adapted STLs,
and the scripts that generate all of it.

The code is MIT licensed. The hardware design is licensed under
CERN-OHL-P v2, which is the hardware equivalent of MIT. You can build,
modify, and sell cases from these files. See [Licensing](#licensing).

## The design

A 39 mm GMT sports watch case with a bidirectional 120-click 24-hour
bezel, sapphire crystal, screw-down crown, and a threaded exhibition
caseback. The bezel top is coned so the watch wears thinner than its
stack height. The lugs are cut from a revolved ring, so their junction
with the case is circular by construction and needs no fillets.

| | |
|---|---|
| Movement | Miyota 9075 (GMT, 24 h hand), cased on a machined movement ring |
| Diameter | 39.0 mm |
| Lug to lug | 47.9 mm |
| Height | 12.0 mm to the crystal apex |
| Lug width | 20 mm, drilled, Ø1.35 spring-bar holes |
| Dial | Ø31.0 |
| Crystal | Ø31.4 flat-top domed sapphire, I-ring gasket |
| Caseback | M30 x 0.5 threaded ring, Ø21 sapphire window |
| Bezel | steel 24 h, bidirectional, 120 clicks, ball detent |
| Water resistance | designed to 10 ATM (untested; see Status) |
| Material | 316L |

Dimensions that interact with the movement come from the official Miyota
9075 casing drawing (907500C0): 5.12 mm height, stem at 2.55 below the
dial plane, Ø25.60 register, and a hand-pivot chain of 2.70 above the
dial seat. The drawing is copyrighted, so it is not in this repository.
Get it from [Miyota](https://www.miyotamovement.com/).

## Repository map

| Path | What it is |
|---|---|
| `case_model.py` | The design. One parameter dict is the spec sheet; everything downstream regenerates from it. |
| `verify_case.py` | 113 hard assertions: stack heights, fits, clearances, sapphire stress, thread and gasket geometry, mesh-level regression checks. Run it after any change. |
| `scan_step.py` | Screens exported STEP files for geometry that breaks CAD importers (degenerate faces, self-intersecting shells). |
| `output/*.step` | The nine parts plus an assembly, ready for CAD or quoting. |
| `print_variant.py`, `PRINTING.md`, `output/print/` | FDM adaptation: snap fits replace the threads and the spring ring. Prints on a standard 0.4 mm nozzle; 0.2 mm recommended for the small parts. |
| `xometry_variant.py`, `xometry_drawings.py`, `output/xometry/` | CNC prototype kit with drawing sheets carrying the thread callouts and critical fits. |
| `MANUFACTURING.md` | How to get it made in metal: factory RFQ package and prototype-shop instructions. |
| `compare_mocks.py`, `mocks/` | Reference renders and a silhouette comparison harness used during design. |
| `render.py`, `build_review.py` | Preview renders and a single-file HTML design review page. |

## Building from source

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 case_model.py     # writes output/*.step and *.stl
python3 verify_case.py    # 113 checks; exit 0 means all pass
```

The lug construction runs in a subprocess because OCCT segfaults are not
catchable in-process. If the build dies partway, run it again; the
subprocess retries are part of the design.

Two facts about the exports that will save you a bad afternoon:

1. **Threads are not modeled.** Threaded interfaces are plain cylinders
   at nominal diameter with the callout carried in drawings and comments
   (M30 x 0.5 caseback, S0.9 x 0.225 crown, tube press fits). If you
   send a STEP to a machine shop without the callouts, you get smooth
   bores.
2. **Exports are screened, not trusted.** OCCT booleans sometimes
   produce shells that import as phantom geometry in other CAD packages.
   `scan_step.py` gates every export; run it if you regenerate.

## 3D printing

`output/print/` contains a print-adapted variant: the caseback thread
becomes three cantilever snap tabs, the bezel spring ring becomes an
integral snap lip, the crystal and window get crush ribs, and the crown
gets a press pin. Print the included test coupon first to dial in your
printer's fit, then the case. PETG for the snap parts; PLA cracks.
Full instructions in [PRINTING.md](PRINTING.md).

## Making it in metal

[MANUFACTURING.md](MANUFACTURING.md) covers both routes: a watch case
factory (finished, polished, water-tested cases; this is how microbrands
work) and a prototype CNC shop (bare accurate metal, fast, no watch
finishing). `output/xometry/` is a ready-to-upload fitment kit for the
second route, with per-part drawing sheets and prototype substitutions
where true watch parts exceed general machining: a coarser caseback
thread, a pin crown instead of the threaded crown and tube, acrylic
instead of sapphire.

## Status

What has been done: the geometry is complete for all nine parts, passes
its 113 checks, imports into Fusion 360 without artifacts, and 3D prints
as a snap-together prototype. Every attachment is engineered and
documented: crystal gasket, bezel retention and detent, caseback thread
and O-ring, crown tube press fit, movement ring, spring bars.

What has not been done: no metal case has been machined from these files
yet, water resistance is a design target rather than a test result, and
the dial and hands are out of scope. Treat the design as a reviewed,
verified starting point, not a production-proven one. If you machine or
print it, open an issue with what you learn either way.

## Licensing

- **Software** (all `.py` files, the HTML template, and the docs): [MIT](LICENSE).
- **Hardware design** (the parametric geometry, STEP and STL files, and
  drawings; anything you manufacture from them):
  [CERN-OHL-P v2](LICENSE-HARDWARE), a permissive license that is the
  hardware equivalent of MIT.
- **Trademarks are not licensed.** The Kelsus name, the K monogram
  (`assets/kelsus-logo-k.svg`, also engraved on the crown and caseback),
  and the name Intercontinental identify Kelsus, Inc. If you make and
  distribute your own cases from this design, remove or replace the K
  and the names. The `kelsus_k_wire()` function and the engraving text
  parameters in `case_model.py` are the two places to change.

Both licenses disclaim warranty. A watch case holds a movement and sits
on a wrist; check the numbers yourself before trusting either.
