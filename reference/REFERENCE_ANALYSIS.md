# Layered image analysis — bench vise (reference: conversation attachment)

> **Reference availability.** The reference was supplied as a conversation attachment and is
> readable by agent vision only; no image file exists on this container's disk. Every pixel-level
> script gate (`probe_image.py`, `check_reference_admission.py`, `build_detail_inventory.py` crops,
> `extract_pbr_evidence.py`, `make_comparison_sheet.py`) is therefore recorded as `skipped` with a
> reason in `.img2threejs/state.json`. Agent-vision observation below is the reference evidence of
> record; render review is done by the agent comparing captured PNGs against the attachment.

## Layer 1 — Identification & classification

- Work type: **machinist's bench vise with swivel base** (слесарные поворотные тиски).
- Broad classification: mechanical workholding tool / screw clamp assembly.
- `primaryDomain`: `object`. Confidence 0.95.
- The reference is itself a studio CG render: seamless off-white backdrop, single soft key,
  soft contact shadow. No brand mark, no inscription, no paint — bare cast metal throughout.

## Layer 2 — Overall form & silhouette

- Bilateral symmetry about the vertical longitudinal plane containing the screw axis.
- Object frame used for the rebuild: **+X = longitudinal (screw axis, movable jaw toward +X)**,
  **+Y = up**, **+Z = lateral (toward camera-front)**. Right-handed.
- Bounding proportion measured off the reference silhouette: width : height ≈ 2.25 : 1;
  base disc diameter ≈ 0.42 × overall width; jaw opening ≈ 0.17 × overall width.
- Primitive vocabulary for the silhouette: extruded profile (both jaw arms), cuboid with chamfers
  (body casting, slide bar), cylinder (screw core, handle bar, base boss), helical sweep
  (acme thread), sphere (handle ball ends), lofted disc stack (swivel base + lobed ears).
- Shape language: geometric-mechanical with cast fillets; no organic surfaces.

## Layer 3 — Macro → meso → micro decomposition

Macro (independent major assemblies):

1. **Swivel base assembly** — lobed base plate, swivel collar, swivel lock bolts.
2. **Body casting (fixed-jaw side)** — main box casting, chamfered top plateau (anvil pad),
   fixed jaw arm, nut boss.
3. **Movable jaw assembly** — jaw arm, slide bar, thrust collar.
4. **Screw & handle assembly** — acme lead screw, knurled thrust ring, T-bar with ball ends.

Meso (sub-parts):

- base: circular foot disc, 4 radial mounting lobes each with a through hole, 2 visible hex bolt
  heads on the front lobes, stepped circular boss, swivel parting seam, swivel lock hex bolt.
- body: box shell with draft, front hex fastener boss near the foot, chamfered top plateau,
  fixed jaw arm (convex outer face, concave inner scallop), fixed jaw plate seat.
- movable jaw: jaw arm mirroring the fixed arm's profile, horizontal slide bar passing through the
  body and protruding on the −X side, rounded thrust lobe at +X carrying the screw.
- screw: threaded section exposed between body face and movable jaw (long run, ≈20 visible turns),
  threaded tail protruding past the −X face of the body (short run, ≈9 visible turns),
  chamfered rod ends.
- handle: fine-knurled thrust ring, smooth collar, cross-drilled screw head, straight bar,
  two spherical ball ends.

Micro (feature groups):

- serrated jaw plates: vertical/cross-hatched gripping teeth on both jaw faces, each plate with a
  small stepped tab standing proud above the arm's top edge.
- cast fillets along every casting edge; chamfers on the body plateau and slide-bar end.
- knurling band (fine axial ridges) on the thrust ring.
- hex fastener heads (base lobes ×2, swivel lock ×1, body foot ×1).

## Layer 4 — Spatial relationships (scene-graph triplets)

- `<base plate, supports, swivel collar>` — flush-with, planar seam visible.
- `<swivel collar, carries, body casting>` — socket, body rotates about +Y at the base axis.
- `<fixed jaw arm, is-part-of, body casting>` — single casting, embedded/continuous.
- `<slide bar, passes-through, body casting>` — sliding socket along +X, tail protrudes at −X.
- `<movable jaw arm, attached-to, slide bar>` — butt/continuous casting at the arm foot.
- `<screw, threads-into, body nut boss>` — helical socket; screw axis is the slide axis, raised.
- `<thrust ring, retains, screw at movable jaw>` — overlap on the +X face of the thrust lobe.
- `<handle bar, passes-through, screw head cross hole>` — embedded, free to slide laterally.
- `<jaw plate, seated-on, jaw arm top>` — overlap, plate stands proud of the arm face.
- Both jaw faces are coplanar-normal (they oppose along X); the gap between them is open ≈ the
  same distance as the exposed mid screw run.

## Layer 5 — Materials & surface (PBR)

One material family — bare ferrous metal — split into four finish variants by machining state:

| id | parts | albedo | metalness | roughness | relief |
|---|---|---|---|---|---|
| `cast-iron-body` | base, body, jaw arms, thrust lobe | mid neutral grey `#8c8f92` | 1.0 | 0.55 | fine cast grain / light pitting |
| `machined-steel` | slide bar, screw core, jaw-plate bodies, fasteners | slightly lighter `#9aa0a4` | 1.0 | 0.34 | directional machining, no pitting |
| `dark-oxide-screw` | acme thread flanks, thrust ring | darker `#6f7377` | 1.0 | 0.42 | thread flank micro-relief |
| `polished-handle` | handle bar, ball ends | lightest `#a8adb2` | 1.0 | 0.24 | smooth, brightest speculars |

- Observation: the brightest specular lobes in the reference sit on the two handle balls and on the
  crest line of the exposed thread; the flattest tonal regions sit on the body's side faces.
  Inference: the castings are unpolished, the handle and screw are turned stock.
- No dielectric surfaces anywhere; no paint, no coating, no transparency.

## Layer 6 — Colour & finish

- Whole object is achromatic: hue undetermined/neutral, mid value, saturation ≈ 0.02.
- Finish per region: castings **satin**; slide bar and screw **machined satin**; handle **near-gloss
  metallic**. No anodizing, no gradient paint, no decal.
- Backdrop: near-white, mid-high value, with a horizon-less vertical falloff; contact shadow is
  soft, low-opacity, spreading toward −Z/+X of the base.

## Layer 7 — Identity-defining features

These are what make the reference *this* vise rather than a generic clamp; each becomes a detail
inventory entry and a `featureReviewTarget`:

1. **Hooked jaw-arm profile** — convex outer face + deep concave inner scallop with a strong fillet.
2. **Serrated jaw plates standing proud with a top tab.**
3. **Two separate exposed thread runs** (long mid run, short −X tail) of an acme (trapezoidal) thread.
4. **Knurled thrust ring** between jaw lobe and handle.
5. **Ball-ended T-handle**, bar tilted out of vertical in the reference view.
6. **Four-lobed swivel base** with visible parting seam and hex swivel-lock bolt.
7. **Chamfered top plateau (anvil pad)** on the body behind the fixed jaw.

## Layer 8 — Uncertainty & single-image limits

- **Hidden:** the entire −Z rear half, the base underside, the interior of the nut boss and the
  slide channel, the 4th base lobe.
- **Occluded:** the fixed-jaw plate's inner face (blocked by the movable jaw arm), the screw where
  it enters the body.
- **Uncertain:** serration pitch and count on the jaw plates; whether the body plateau is a true
  flat anvil or only a cast chamfer; the exact thread pitch (counted from the render, ±2 turns);
  whether the base lobes carry 4 or only 2 fasteners.
- **Undetermined:** absolute scale. The rebuild adopts a conventional 125 mm (5 in) jaw-width vise
  and expresses all dimensions in metres relative to that.
- Rear geometry is reconstructed by **mirroring the observed front half** and is labelled
  inference, not observation.
