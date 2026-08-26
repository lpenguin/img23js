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
| Triangles | 15,040 |
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
```

## Layout

```
object-sculpt-spec.json   the authored spec: 29 components, 5 materials, 5 repetition
                          systems, quality contract, and the full 8-pass review history
assessment.json           pre-spec assessment and quality contract
reference/                layered image analysis and the suitability verdict
src/createBenchViseModel.ts  generated factory — do not hand-edit, see below
src/main.ts               review harness: scene, lighting, articulation, picking, explode
tools/build_spec.py       authors object-sculpt-spec.json from measured landmarks
tools/capture.mjs         headless render capture
tools/export_geometry.mjs world-space geometry + part manifest for the gates
tools/silhouette_metrics.py, tools/sample_patch.py   measured proportions and tones
renders/<pass>/           per-pass review evidence
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

## Fidelity: what is observed and what is not

The reference is a single near-orthographic side view. That fixes a great deal and hides a great
deal, and this section is the honest accounting.

**Measured off the reference** — overall width : height 1.95 (model: 1.946), base disc 0.36 of
overall length (0.356), jaw opening 0.09 (0.093), screw axis height, jaw top, both jaw faces,
the screw tail end, and the thread pitch to about ±2 turns over the long run.

**Inference, not observation** — the entire −Z half is mirrored from the observed +Z half; the
base underside, the nut-boss interior and the slide channel are built to engineering convention;
the base lobes' 45° azimuth is a conventional square four-bolt pattern (the side view fixes only
their longitudinal extent); the absolute scale is a convention (102 mm jaw width), since the
reference carries no scale cue.

**Approximations, stated** — the thread section is round rather than a trapezoidal acme flank;
the knurl is straight, not diamond; serration pitch is below what the reference can resolve; the
jaw-riser scallop is a polyline and facets at close range; a faint periodic noise lattice remains
on the largest flat cast faces under grazing light.

### The one gate that could not run

The reference was supplied as a **conversation attachment with no file on disk**. Every
pixel-level gate in the pipeline therefore never ran on this reconstruction:
`diagnose_render.py` (Tier 1), Divine Eye, `interior_difference.py`, `check_reference_admission.py`
and `extract_pbr_evidence.py` all require reference pixels. There is no true side-by-side sheet
either — `renders/*/review-sheet.png` pairs each render with an **observation panel that states on
its own face that it is not the reference image**, carrying the measured landmarks instead.

So the PBR channel values here are agent-vision observations calibrated against the reference's
specular behaviour, not extracted measurements, and that is weaker evidence. The gates that *are*
reference-free did run clean at every pass: turntable coverage at four azimuths, multi-angle
collapse, self-intersection on the exported world-space geometry, and part coverage.

**If you add the image at `reference/bench-vise.png`, all of those gates become runnable** and the
review can be re-scored against measured pixel evidence rather than observation.
