# Layered image analysis — bench vise (reference: conversation attachment)

> **Reference availability.** The reference arrived twice: first as a conversation attachment
> readable by agent vision only, then as a file (`reference/bench-vise.png`, 2000x1104, converted
> from the supplied `.webp`). Everything below was written from the attachment; the **Measured**
> section at the end records what changed once the file made pixel measurement possible, and the
> gates it unblocked. Where the two disagree, the measured numbers win and the original wording is
> left in place so the correction is visible rather than quietly overwritten.

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


---

# Measured (after the reference file arrived)

The attachment-only pass got the object right and several dimensions wrong. This section records
what changed and what stayed, so the difference between "observed by eye" and "measured" is legible.

## Method

The object is the largest connected foreground component of the plate at luminance threshold 178,
which is above the contact shadow (the shadow bottoms out around 195, the object's lit surfaces run
110-200). It spans **x 402..1685, y 255..961** in a 2000x1104 frame: **1284 x 707 px, aspect 1.816**.

Two anchors fix the frame against the model: the jaw top is Y 2.22 and the mounting plane is Y 0.
**Vertical** values transfer directly, because both images span the same two semantic landmarks.
**Horizontal** values transfer as a fraction of object width, never through the vertical scale --
the reference's camera carries an unknown elevation, and elevation inflates measured height without
touching width, so one px/unit derived from the vertical would shorten every X landmark by about 7%.

That trap is real and it was nearly walked into. The control that caught it is
`renders/reference-gates/ortho.png`: the same model rendered at azimuth 0, elevation 0, where the
projected bbox IS the world X:Y ratio. It reads 1.866 against 1.731 at the review camera, so the gap
between world aspect and projected aspect is the camera, not the geometry.

## What was wrong

| | attachment-only | measured | effect |
|---|---|---|---|
| jaw plate depth | 0.15 | **0.234** | read as a toothed veneer, not a hardened insert |
| jaw plate height | 0.42 | **0.242** | plate ran most of the jaw face instead of capping it |
| jaw riser inner face | a concave arc | **an S-curve** | the undercut the screw passes through was missing |
| screw crest radius | 0.135 | **0.185** | screw was visibly thin for its jaw |
| screw axis height | 1.30 | **1.21** | screw floated above the slide instead of sitting on it |
| slide bar depth | 0.22 | **0.50** | the bar was a plate where the reference has a beam |
| body bottom / top | 0.36 / 1.66 | **0.45 / 1.71** | body sat too low and too short |
| base half-extent | 0.769 | **0.85** | base read small under the casting |
| tommy bar lean | bottom toward -X | **bottom toward +X** | sign error; the two balls were offset the wrong way |
| cast albedo | cool (B above R) | **warm-neutral (R about 5 above B)** | render read blue against the reference's grey |
| exposure | body face at 149 | **reference is 122** | render was about 25 levels hot |
| contact shadow | cast half the object's length | **reaches only X 2.4 of 3.2** | reference's key is steep; it is a contact smudge |

## What held

Overall proportion, every macro assembly, the component hierarchy, the four-lobed base, the two
exposed thread runs, the knurled ring, the hooked-jaw reading, and the mirror relationship between
the jaws all survived measurement unchanged. The eye got the structure right and the sizes wrong.

## Gates the file unblocked

| gate | result |
|---|---|
| `probe_image.py` | pass, 2000x1104 |
| `check_reference_admission.py` | **admitted**, foreground coverage 0.266, largest component 0.998 |
| `diagnose_render.py` (Tier 1) | aspect delta **0.021** (threshold 0.05), scale delta **0.007** (0.08), silhouette IoU **0.837** (0.85) -- fails on IoU alone |
| `divine_eye.py` | fidelity 0.681, `low-confidence` / `probe`, `reconstructionModeSuspected: true`; SSIM 0.922, pHash 0.875, objectness 0.741 |
| `interior_difference.py` | **0.128** over 12,353 cells, no mask warnings |
| `extract_pbr_evidence.py` | pass on all four crops: cast-iron 0.716, machined-steel 0.784, oxide-screw 0.794, polished-handle 0.86 |

Only the cast-iron crop was cleanly isolated (value range 0.087, wholly inside the body face); its
palette `#7B7A76 #757570 #807F7B` is what the authored albedos were corrected against. The other
three crops caught backdrop, so their palettes are recorded as evidence and not adopted. No extracted
map is applied as a texture: the crops are of a lit studio render, and projecting their albedo onto
geometry this scene lights again would double-light it.
