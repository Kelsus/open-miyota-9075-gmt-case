# Getting the case made in metal

Two routes, and they answer different questions.

**Route A: a watch case factory.** You are buying a finished case:
machined, brushed and polished to watch grade, threads cut, sapphires
pressed with gaskets, crown and tube fitted, bezel clicking, water
tested, assembled. The factory sources the companion parts (sapphire,
gaskets, crown, tube, spring bars) from its local ecosystem for a few
dollars each. This is how microbrands work.

**Route B: a prototype CNC shop (Xometry, Protolabs, or similar).** You
are buying the exact geometry in the STEP file, in metal, fast, and
nothing else. No watch finishing (machine shop polishing is not watch
polishing), no gaskets, no sapphire, no assembly, no water resistance.
Everything after the machining is on you, and case finishing and crystal
pressing are hard to do well at home.

**Recommendation: both, in sequence.** Order the midcase from a
prototype shop in aluminum first, to hold the metal shape in hand and
check the bracelet fit, and send the full package to two or three case
factories for samples in parallel. Machining the full set at a prototype
shop in 316L costs more than factory samples and arrives less finished.
The exception is confidentiality: assume anything sent to a case factory
can be reused by them. If that is unacceptable, use Route B for
everything and accept the cost and the finishing work.

---

## The mistake to avoid

**The STEP files contain no thread geometry.** Threaded interfaces are
plain cylinders with the thread carried as a callout, which is standard
CAD/CAM practice. Upload a STEP to a quote engine without the callouts
and you get smooth bores. Every RFQ must carry these:

| Interface | Callout | Where |
|---|---|---|
| Caseback to case | M32 x 0.5, internal 6H (case), external 6g (back) | case bore Ø32.0 region, z 0 to 3.5 |
| Crown to tube | S0.9 x 0.225 (Miyota 9075 stem thread standard) | crown bore |
| Tube to case | press fit: tube shank Ø2.50 s6 into case bore Ø2.48 H7 | crown side, stem axis 4.62 above the back plane |
| Tube thread (crown screws onto it) | Ø3.9 x 0.35, depth 0.22 | tube OD |

## RFQ package contents

Send: `output/*.step` (9 parts plus the assembly), renders or the review
page for finish intent, reference images, and the spec tables below. Say
this in the cover message: the STEP is master geometry; threads and
finishes are per the spec sheet; where marked substitutable, the factory
may propose its standard equivalent parts.

### Critical dimensions (hold these)

| Feature | Dim | Tol |
|---|---|---|
| Case Ø | 39.00 | ±0.05 |
| Lug to lug | 47.90 | ±0.10 |
| Lug gap (bracelet) | 20.00 | +0.15 / −0 |
| Total height (back to crystal apex) | 12.02 | ±0.10 |
| Spring-bar holes | Ø1.35 ±0.05, 90° csk to Ø1.65 | position ±0.05 |
| Ø39.0 cylindrical end-link land | down to z 1.60 from the back plane | |
| Movement: Miyota 9075 | register Ø25.60 Js8, flange relief Ø26.0 x 2.05 deep | per Miyota drawing 907500C0 |
| Dial | Ø31.0; loads from the back through the caseback thread and pass bore, retained by the rehaut ledge | |
| Dial pass bore | Ø31.40 | H8 |
| Crystal bore | Ø32.00 H7; crystal Ø31.40 flat-top domed sapphire, I-ring gasket 0.35 wall, 0.10 diametral crush | |
| Bezel bore and boss | Ø34.10 bore on Ø34.00 boss, retention groove floor Ø32.80 | bore H8, boss h7 |
| Caseback sapphire | Ø23.4 x 1.4, view Ø21.0, pressed from outside against an internal ledge | |
| Stem axis height | 4.62 above the caseback plane | ±0.05 |

### Sealing (target 10 ATM, test to ISO 22810 at 10 bar)

- Caseback: radial O-ring, cs 0.70, in an OD groove (0.9 wide x 0.5 deep)
- Crown: O-ring cs 0.70 inside the crown, gasket at the tube
- Crystal: I-ring gasket, 0.35 wall (nylon or PA)
- Bezel: centring O-ring cs 0.70 in the boss groove (damping, not sealing)

### Bezel action

Bidirectional, 120 clicks. As designed: a spring-loaded ball in the case
shoulder rides 120 scallops (Ø0.50 ball seats, 0.18 deep, on Ø36.4) in
the bezel underside; the bezel is retained by a slit spring ring (part
09, free OD Ø34.6) engaging the boss groove. Substitutable: a factory's
standard ball click and spring washer retention is acceptable if the
bezel height, reveal, and exterior geometry are unchanged.

### Finishing map

`python3 build_finishing_map.py` renders this map as a color-coded PDF
(`output/finishing_map.pdf`) to attach to an RFQ.

- Case top faces and lug tops: radial brush
- Case flank: horizontal brush; lug flanks: brush following the arc
- All chamfers (shoulder 0.45, lug top, case bottom 0.30): polished
- Bezel coned top face: sunburst brush; long outer bevel: polished; coin edge: cut sharp
- Bezel numerals and triangles: engraved 0.25, black lacquer fill; lume
  pip Ø0.8 at the 24 position, recess 0.35 deep, Super-LumiNova fill
- Caseback ring: circular brush; engraving "KELSUS INTERCONTINENTAL"
  0.18 deep, filled or bare per sample
- Crown: polished, K logo engraved on the end face (SVG artwork in
  `assets/`; do not redraw it)
- Edge breaks everywhere else: R0.1 ("break sharp edges")

### Substitutable against not negotiable

The factory may substitute, with equivalents proposed in DFM: gaskets
and O-rings; the crown and tube as a bought-in assembly (with the K logo
face); the bezel click mechanism; the movement ring material (POM or
brass); the spring ring. Not negotiable: the exterior geometry and the
dimensions above, the movement interfaces, dial Ø31.0, stem height, the
bracelet interface, sapphire plus exhibition back, screw-down crown, and
the finishes.

---

## Route A: case factory, step by step

1. Shortlist 2 or 3 watch case factories rather than trading companies.
   Ask: do you machine in house, and can we video call the shop floor?
   Ask for microbrand references and a photo of a case they made with a
   coned engraved bezel and an exhibition back.
2. Send the RFQ package. Ask for DFM feedback, sample price and lead
   time, production MOQ and unit price at 50, 100, and 300, and a
   written change log. Factories normalize geometry to house standards
   without telling you; require every deviation from the STEP to be
   listed for approval.
3. Expect sample pricing in the rough range of $200 to $800 per complete
   case and 4 to 8 weeks (verify; these numbers move). Pay for samples
   from two factories in parallel; the extra cost is small and the
   comparison is worth it.
4. When samples arrive, inspect against the checklist below with a 9075
   and a dial blank on hand.
5. Then discuss production. Typical case MOQs are 50 to 100; some shops
   do 20 to 30 at a premium.

On IP: an NDA with a case factory is worth asking for and worth little.
Assume the geometry can end up in their catalog. If that is
unacceptable, use Route B at higher cost, or split parts across
suppliers.

## Route B: prototype CNC shop, step by step

A real data point first (August 2026): Xometry's instant quote for the
midcase alone, aluminum 6061, quantity 1, standard ±0.13 tolerance and
no threads, was $670. The threads and the tight fits from the drawings
would raise that. If a printed prototype has already answered the form
and fit questions, Route A samples deliver more per dollar; a US
instant-quote shop at quantity 1 is the most expensive way to hold this
case in metal. Cheaper metal options: overseas instant-quote CNC
services (JLCCNC, PCBWay, RapidDirect) quote the same uploads at a
fraction of the US price, and an SLM 316L metal print of the midcase
(rough surface, no working fits, real steel weight) runs cheaper still.

1. Upload `01_midcase.step`, and `02_bezel.step` if the look matters for
   this round. Process: CNC machining, 5-axis. Material: aluminum
   6061 for a fit check round; 316L later runs near 3 to 5 times the
   price and slower.
2. Attach a drawing or manufacturing notes PDF carrying the thread
   callouts and criticals from the tables above. Without an attached
   drawing everything defaults to a blanket tolerance near ±0.13 and
   smooth bores. `output/xometry/` contains a ready-made fitment kit
   with per-part drawing sheets.
3. Finish: as machined or bead blast. Do not pay for shop polishing on a
   fit check.
4. Skip at the prototype shop: crown, tube, spring ring, gaskets, and
   sapphires. These are bought parts (crown and tube from a watch parts
   supplier, sapphires from a sapphire house).

## Sample inspection checklist (either route)

- [ ] 9075 plus movement ring drops into the register; no rock; clamp screws reach
- [ ] Stem hole aligns with the movement stem (height 4.62, no bind on a real stem)
- [ ] Dial Ø31.0 seats in the pocket; no rehaut shadowing at the edge
- [ ] Caseback threads in for 4 or more full turns, seats with the gasket, notches take a wrench
- [ ] Crystal pressed flush, no gasket extrusion visible, no stress rings
- [ ] Bezel: 120 clean clicks, no wobble, even reveal all round
- [ ] Crown: screws down and engages 3 or more turns (ask for orientation-timed threading only if the K angle matters; it costs)
- [ ] Bracelet: end link seats on the Ø39 land without rocking; spring bars go in and out without force
- [ ] Water test certificate at 10 bar
- [ ] Finish: brush grain directions per the map, lacquer fill clean in the numerals, engraving depth even
- [ ] Weight near 49 g for the bare 316L case
