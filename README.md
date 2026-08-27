# Bench vise — procedural Three.js reconstruction

A machinist's swivel-base bench vise, rebuilt from a single reference photograph as
**code-only procedural geometry**: no mesh import, no photogrammetry, no downloaded art.
Every surface is generated at runtime from an extruded profile, a revolved profile, a swept
helix or a primitive, driven by one authored spec.

Built with the [`img2threejs`](https://github.com/img2threejs/img2threejs) skill: an eight-pass
sculpt pipeline (blockout → structural → form → material → surface → lighting → interaction →
optimization), each pass gated on a render review before the next unlocks.

```bash
npm install
npm run dev        # http://127.0.0.1:5173
npm run typecheck
npm run build
```

## What you get

| | |
|---|---|
| Parts | 29 named, individually selectable and separable |
| Triangles | 15,152 |
| Draw calls | 30 (29 meshes + 1 instanced knurl ring) |
| Materials | 5 finishes of one bare-ferrous-metal family, all metalness 1.0 |
| Kinematics | jaw travel, base swivel, screw spin geared to travel, handle slide |

The viewer is driven entirely by the URL, so a headless capture and a human tab share one code
path:

```
?view=front|right|rear|left|top|hero   review viewpoint
?light=reference|neutral|grazing       look-dev lighting mode
?jaw=0..1                              extra jaw opening beyond the reference pose
?swivel=<deg>                          base swivel
?explode=0..1                          exploded assembly
?maps=0                                map-stripped clay render (blockout evidence)
?shadows=0                             shadow-free plate for silhouette measurement
?ui=0                                  hide the control panel
?env= ?exposure= ?shadow=              lighting overrides
?az= ?el= ?zoom= ?panx= ?pany=         camera overrides (used to converge `view=match`)
```

Two views exist for measurement rather than looking: **`match`** reproduces the reference's own
framing (object on the same 0.642 x 0.640 fraction of a 2000x1104 frame, same centre) so a pixel
gate scores shape instead of framing, and **`ortho`** renders at azimuth 0 / elevation 0, where the
projected bounding box IS the model's world X:Y ratio — the control that tells a geometry error
apart from a camera one.

## Layout

```
object-sculpt-spec.json   the authored spec: 29 components, 5 materials, 5 repetition
                          systems, quality contract, and the full review history
assessment.json           pre-spec assessment and quality contract
reference/                the reference image, the layered analysis, the suitability verdict
material-evidence/        extracted reference PBR maps and their confidence reports
src/createBenchViseModel.ts  generated factory — do not hand-edit, see below
src/main.ts               review harness: scene, lighting, articulation, picking, explode
tools/build_spec.py       authors object-sculpt-spec.json from measured landmarks
tools/capture.mjs         headless render capture
tools/export_geometry.mjs world-space geometry + part manifest for the gates
tools/silhouette_metrics.py, tools/object_bbox.py    silhouette measurement
tools/profile_compare.py, tools/mask_overlay.py     shape diff against the reference
tools/sample_patch.py, tools/crop.mjs               tone measurement, detail inspection
tools/webp_to_png.mjs     image conversion through the pre-installed Chromium
renders/<pass>/           per-pass review evidence
renders/reference-gates/  the framing-matched plate, the ortho control, the silhouette
                          difference map and the reference/render comparison sheet
```

### Rebuilding

`src/createBenchViseModel.ts` is **generated**. Reconstruction decisions live in
`tools/build_spec.py`, which writes the spec; the factory is emitted from it. To change the
model, edit the builder, not the factory:

```bash
python3 tools/build_spec.py
python3 .claude/skills/img2threejs/forge/stage2_spec/validate_sculpt_spec.py \
    object-sculpt-spec.json --strict-quality
python3 .claude/skills/img2threejs/forge/stage3_build/generate_threejs_factory.py \
    object-sculpt-spec.json --out src/createBenchViseModel.ts --pass-id optimization-pass --force
```

`build_spec.py` regenerates the skeleton into a temp file and carries `reviewHistory`,
`visualEvidence` and `sculptPipeline` across, so re-running it never erases the pass history the
gate reads.

## How the geometry is made

- **Castings** (body, jaw risers, base plate) are **extruded side profiles**. The identity of
  this vise is in its outline — the hooked jaw with its concave scallop, the chamfered top
  plateau, the four-lobed base plan — and a box stack loses all of it. The base plate's plan is
  the union of a disc and four lobe circles, with the mounting holes as real cut-outs.
- **Anything concentric with an axis** (swivel collar, bosses, thrust ring, screw core, handle
  bar, hex fastener heads) is a **revolved profile**, so it stays circular from every azimuth.
  Hex heads are six-segment revolves — a real hexagonal prism, not a cylinder standing in.
- **The thread** is a **swept helix**: a ridge that advances while it winds cannot be produced
  by any revolve or extrude. Both ends taper out as a real thread run-out does.
- **Jaw serrations** are cut into the plate's extruded outline, not applied as relief, because
  the reference shows the teeth breaking the plate's silhouette edge — a map would leave it
  smooth.
- **The knurl** is 44 instanced ridges in one draw call.
- **The jaw pair is a reflection**, not a rotated copy: `x → 2·1.37 − x` about the jaw-gap
  mid-plane, with the winding flipped back.

Frame: **+X longitudinal** (movable jaw toward +X), **+Y up**, **+Z toward the reference
camera**, right-handed. Origin at the base disc centre on the mounting plane. **1 unit = 100 mm.**

## Fidelity: measured

The reference is a single near-orthographic side view. It was first supplied as a conversation
attachment — readable by eye, not by any script — and the model was built and gated that way through
all eight passes. The image file arrived afterwards, which made every pixel gate runnable and turned
a set of eye estimates into measurements. Both stages are recorded in
`reference/REFERENCE_ANALYSIS.md`; the corrections the file forced are listed there in full.

**What measurement changed.** The jaw riser's inner face is an S-curve, not the arc that was
authored — it falls back to X 0.799 at Y 1.731, bulges to 0.859 at Y 1.580, then returns to the
casting. The jaw plate is 0.234 deep by 0.242 tall, not 0.15 by 0.42. The screw is fatter
(crest radius 0.185) and sits 0.09 lower, resting on the slide bar as the reference's does. The
slide bar is a 0.50 beam, not a 0.22 plate. The tommy bar's lean was the wrong **sign**. Every
authored albedo was cool where the reference measures warm-neutral, and the render was about 25
levels hot.

**What measurement confirmed.** Overall proportion, every macro assembly, the component hierarchy,
the four-lobed base, the two exposed thread runs, the knurled ring and the mirror relationship
between the jaws all survived unchanged. The eye got the structure right and the sizes wrong.

**One trap worth naming.** Converting the reference's horizontal landmarks through its *vertical*
scale would have shortened every X landmark by about 7%, because the reference's unknown camera
elevation inflates measured height without touching width. The `ortho` control render is what
separated the two, and the geometry was left alone.

### Gate results, measured against the reference

| gate | result |
|---|---|
| `check_reference_admission` | **admitted** — coverage 0.266, largest component 0.998 |
| `diagnose_render` (Tier 1) | aspect delta **0.021** (threshold 0.05) ✓ · scale delta **0.007** (0.08) ✓ · silhouette IoU **0.837** (0.85) ✗ |
| `divine_eye` | fidelity 0.681 · `low-confidence` / `probe` · `reconstructionModeSuspected` · SSIM 0.922 · pHash 0.875 · objectness 0.741 |
| `interior_difference` | **0.128** over 12,353 cells, no mask warnings |
| `extract_pbr_evidence` | pass ×4 — 0.716 / 0.784 / 0.794 / 0.86 against 0.70 |
| `turntable_gate` · `diagnose_render_multi_angle` · `self_intersection` · `check_part_coverage` | all clean |

Measured tone at matched patches: body face reference `rgb(122,121,117)` against render
`rgb(119,118,111)`; jaw plate `rgb(131,131,130)` against `rgb(136,134,127)`.

**Silhouette IoU 0.837 is the one gate still short of its 0.85 threshold**, and it is not being
chased. The residual is distributed few-pixel edge offsets plus the reference's own contact shadow,
not one locatable defect, and the skill's own guidance is explicit that for a photo-vs-procedural
pair IoU is dominated by framing and lighting — optimising toward it distorts the model. Divine Eye
reaching `probe` rather than `reject`, via its reconstruction-mode rescue, is the intended outcome
for this class of comparison.

### Still inference, not observation

The entire −Z half is mirrored from the observed +Z half. The base underside, the nut-boss interior
and the slide channel are built to engineering convention. The base lobes' 45° azimuth is a
conventional square four-bolt pattern — the side view fixes only their longitudinal extent. Absolute
scale is a convention (102 mm jaw width); the reference carries no scale cue.

### Known gaps

The jaw plate's two fixing-screw slots are not modelled. The castings have no Z-direction fillets:
the generator extrudes with `bevelEnabled: false`, so only the profile's own corners are rounded.
The body's cast panel line is missing. The thread section is round rather than a trapezoidal acme
flank, and the knurl is straight rather than diamond. Three of the four PBR crops caught backdrop,
so only the cast-iron palette was adopted; no extracted map is applied as a texture, because the
crops are of a lit studio render and would double-light the model.
