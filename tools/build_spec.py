#!/usr/bin/env python3
"""Author the ObjectSculptSpec for the bench-vise reconstruction.

Kept as a script rather than a hand-edited JSON blob so every measured number stays
next to the observation it came from, and so a spec refinement is a diff on the
reasoning, not on 8000 lines of generated JSON.

Units: 1 unit = 100 mm.  Frame: +X longitudinal (movable jaw toward +X), +Y up,
+Z toward the reference camera.  Origin: centre of the base disc, on the mounting plane.
All landmark values are converted from pixel measurements on the reference image at
295.5 px/unit, origin px (715, 905).
"""
from __future__ import annotations

import json
import math
from copy import deepcopy
from pathlib import Path

SPEC = Path("object-sculpt-spec.json")

# ---------------------------------------------------------------- landmarks (units)
GROUND = 0.0
BASE_PLATE_TOP = 0.16
BASE_DISC_R = 0.60
LOBE_R = 0.26
LOBE_DIST = 0.72
LOBE_HOLE_R = 0.09
COLLAR_TOP = 0.40
COLLAR_R = 0.50

BODY_BOT = 0.36
BODY_TOP = 1.66
BODY_MINUS_X = -0.61
BODY_PLUS_X = 0.64
BODY_Z = 1.02

SLIDE_Y = 0.96
SLIDE_H = 0.22
SLIDE_Z = 0.62
SLIDE_MINUS_X = -1.05
SLIDE_PLUS_X = 2.24

SCREW_Y = 1.30
SCREW_CORE_R = 0.105
SCREW_CREST_R = 0.135
SCREW_TAIL_END = -1.10
SCREW_HEAD_END = 2.98
THREAD_PITCH = 0.068

JAW_TOP = 2.22
# Slightly narrower than the body casting: at equal width the riser's buried lower
# edge is coplanar with the casting's front face and shows as a seam line across it.
JAW_Z = 0.98
FIXED_JAW_FACE = 1.17
MOVABLE_JAW_FACE = 1.57
MIRROR_X = (FIXED_JAW_FACE + MOVABLE_JAW_FACE) / 2.0  # 1.37

THRUST_LOBE_X0, THRUST_LOBE_X1 = 2.10, 2.70
THRUST_RING_C = 2.88
HEAD_BOSS_C = 3.12
BAR_LEN = 1.24
BAR_R = 0.05
BALL_R = 0.115
BAR_TILT_X = 0.22
BAR_TILT_Z = -0.06
# The bar hangs down through its cross hole in the reference: the top ball sits 0.44 from
# the screw axis and the bottom ball 0.83, so the bar's midpoint is 0.19 below the hole.
BAR_SLIDE = -0.19

HALF_PI = math.pi / 2


# ---------------------------------------------------------------- profile builders
def base_plan_outline(samples: int = 128) -> list[list[float]]:
    """Four-lobed base plan: a disc unioned with four lobes on the 45-degree diagonals.

    Sampled as a radial function because every lobe centre is inside the disc, so the
    union boundary is single-valued in theta.
    """
    lobes = [math.radians(a) for a in (45, 135, 225, 315)]
    pts: list[list[float]] = []
    for i in range(samples):
        th = 2 * math.pi * i / samples
        r = BASE_DISC_R
        for phi in lobes:
            d = th - phi
            s = LOBE_DIST * math.sin(d)
            if abs(s) <= LOBE_R:
                r = max(r, LOBE_DIST * math.cos(d) + math.sqrt(LOBE_R * LOBE_R - s * s))
        pts.append([round(r * math.cos(th), 4), round(r * math.sin(th), 4)])
    return pts


def lobe_holes() -> list[dict[str, float]]:
    out = []
    for a in (45, 135, 225, 315):
        th = math.radians(a)
        out.append({
            "cx": round(LOBE_DIST * math.cos(th), 4),
            "cy": round(LOBE_DIST * math.sin(th), 4),
            "rx": LOBE_HOLE_R, "ry": LOBE_HOLE_R,
        })
    return out


# Body casting side silhouette, authored in world XY then re-based on the pivot.
BODY_PROFILE_WORLD = [
    (-0.44, 0.36), (0.46, 0.36), (0.62, 0.70), (0.64, 1.00), (0.64, 1.47),
    (0.52, 1.62), (0.39, 1.66), (-0.32, 1.66), (-0.61, 1.47), (-0.61, 0.62),
]

# Fixed jaw riser: convex outer face (-X), deep concave inner scallop (+X) closing to a
# broad top fillet -- the identity-defining "hook" of the reference.
FIXED_RISER_WORLD = [
    (0.35, 1.28), (0.39, 1.72), (0.45, 2.02), (0.60, 2.16), (0.78, 2.22),
    (1.09, 2.22), (1.09, 1.80), (1.04, 1.68), (0.95, 1.58), (0.84, 1.52),
    (0.70, 1.50), (0.54, 1.49),
]


def mirror_x(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """A left/right pair is a REFLECTION about the jaw-gap mid-plane, never a rotation:
    negate the longitudinal axis about MIRROR_X and nothing else. Winding is reversed so
    the mirrored shape keeps the same face orientation as the original."""
    return [(round(2 * MIRROR_X - x, 4), y) for x, y in reversed(points)]


def jaw_plate_profile(face_x: float, facing: int) -> list[list[float]]:
    """Serrated jaw plate. `facing` is +1 when the teeth point toward +X.

    Teeth are real extruded geometry (horizontal ridges running across the jaw width),
    not a texture: the reference shows them breaking the plate's silhouette edge.
    """
    back = face_x - facing * 0.14
    root = face_x - facing * 0.014
    crest = face_x
    tab = face_x + facing * 0.008
    y_bot, y_top = 1.80, 2.22
    y_teeth0, y_teeth1 = 1.83, 2.17
    pitch = 0.022
    pts: list[tuple[float, float]] = [(back, y_bot), (root, y_bot)]
    y = y_teeth0
    while y + pitch <= y_teeth1 + 1e-9:
        pts.append((crest, round(y + pitch * 0.5, 4)))
        pts.append((root, round(y + pitch, 4)))
        y += pitch
    # stepped top tab: stands proud of the tooth crests, a strong silhouette cue
    pts += [(root, 2.18), (tab, 2.19), (tab, y_top - 0.015), (tab - facing * 0.022, y_top),
            (back, y_top)]
    if facing < 0:
        pts = list(reversed(pts))
    return [[round(x, 4), round(y, 4)] for x, y in pts]


def helix_stations(length: float, radius: float, pitch: float, section: float,
                   per_turn: int = 10) -> list[dict]:
    """Thread ridge as a swept helix about the local +X axis.

    Both ends taper to a point so the run-out reads like a real thread rather than a
    tube cut off mid-air (and so the sweep is a genuine tapered sweep, not a noodle).
    """
    turns = length / pitch
    n = max(8, int(turns * per_turn))
    out = []
    for i in range(n + 1):
        t = i / n
        ang = 2 * math.pi * turns * t
        # taper the first and last 4% of the run to a point (thread run-out)
        edge = min(t, 1.0 - t) / 0.04
        k = max(0.0, min(1.0, edge))
        out.append({
            "position": [round(length * t, 4), round(radius * math.cos(ang), 4),
                         round(radius * math.sin(ang), 4)],
            "rx": round(section * k, 4),
            "rz": round(section * 0.72 * k, 4),
            "twist": 0.0,
        })
    return out


def smooth_groove(radius: float, y0: float, y1: float, depth: float,
                  samples: int = 13) -> list[tuple[float, float]]:
    """A recessed seam ring sampled as a smooth raised-cosine dip.

    A groove cut with straight walls puts a vertex ring exactly on each concave corner, and
    an averaged normal at a concave corner lies almost along the surface -- which makes the
    inside/outside parity test in self_intersection.py return noise there. A revolved
    profile that is strictly monotonic in y with x > 0 provably cannot fold through itself,
    so the fix is to remove the corner, not to argue with the gate.
    """
    out = []
    for i in range(samples):
        t = i / (samples - 1)
        out.append((radius - depth * 0.5 * (1.0 - math.cos(2 * math.pi * t)),
                    y0 + (y1 - y0) * t))
    return out


def lathe(points: list[tuple[float, float]], segments: int = 48) -> dict:
    return {"points": [[round(max(x, 0.0001), 4), round(y, 4)] for x, y in points],
            "segments": segments}


def hex_head(radius: float, seat: float, height: float) -> dict:
    """Hex fastener head as a 6-segment lathe -- a real hexagonal prism, not a cylinder."""
    return lathe([(0.0, seat), (radius, seat), (radius, seat + height * 0.8),
                  (radius * 0.86, seat + height), (0.0, seat + height)], segments=6)


def rebase(points, ox: float, oy: float) -> list[list[float]]:
    return [[round(x - ox, 4), round(y - oy, 4)] for x, y in points]


# ---------------------------------------------------------------- material authoring
def metal(mid: str, name: str, albedo: str, secondary: list[str], rough: float,
          rough_var: float, macro_amp: float, meso_amp: float, micro_amp: float,
          normal_strength: float, notes: str, overrides: list[dict],
          repeat: float = 4.0, meso_freq: float = 34.0, micro_freq: float = 110.0) -> dict:
    """One machining state of the single bare-ferrous-metal family.

    All four keep metalness 1.0: the reference shows no dielectric surface anywhere, so the
    separation between castings, machined stock, screw and handle has to be carried by
    roughness and its variation, never by albedo alone.
    """
    return {
        "id": mid, "name": name, "type": "physical", "materialClass": "metal",
        "shaderModel": "MeshPhysicalMaterial / PBR",
        "baseColor": albedo, "color": albedo,
        "albedo": {"dominant": albedo, "secondary": secondary,
                   "samplingNotes": notes},
        "colorVariation": {"palette": [albedo] + secondary, "pattern": "mottled",
                           "amplitude": macro_amp, "heightCorrelation": 0.35},
        "textureResolution": 2048,
        # repeat matters more here than resolution. The generator writes one square field and
        # samples it through each primitive's own UVs; an extruded casting's cap UVs span the
        # shape's own coordinate range, so at repeat 1 a single low-frequency noise cell covers
        # a whole face and the casting reads as marbled blobs rather than sand-cast grain.
        "textureProjection": {"mode": "triplanar-object-space", "repeat": [repeat, repeat],
                              "anisotropy": 8,
                              "texelDensityIntent": "Constant world-scale texel density so the "
                              "cast grain does not stretch with component scale."},
        "surfaceFrequencyBands": [
            {"id": "macro", "frequency": 2.5, "amplitude": macro_amp,
             "role": "broad tonal and height breakup across a casting face"},
            {"id": "meso", "frequency": meso_freq, "amplitude": meso_amp,
             "role": "sand-cast grain, machining pass marks, thread flank relief"},
            {"id": "micro", "frequency": micro_freq, "amplitude": micro_amp,
             "role": "specular breakup visible only under grazing light"},
        ],
        "roughness": {"base": rough, "variation": rough_var,
                      "map": "independent-procedural-field",
                      "localResponse": "higher roughness in cavities and cast crevices, "
                      "lower roughness on wear-polished edges and crests"},
        "metalness": {"base": 1.0, "variation": 0.0},
        "normal": {"pattern": "derived-from-independent-height-field",
                   "strength": normal_strength, "scale": 26.0, "space": "tangent"},
        "bump": {"pattern": "none", "amplitude": 0.0, "scale": 1.0},
        "displacement": {"pattern": "none", "amplitude": 0.0, "scale": 1.0,
                         "silhouetteAffects": False},
        "ambientOcclusion": {"cavityStrength": 0.32, "contactShadowBias": 0.35,
                             "notes": "Darken the swivel parting seam, the slide-guide mouth, "
                             "the tooth roots and the thread valleys."},
        "wear": {"edgeWear": 0.0, "scratches": [], "chips": []},
        "dirt": {"amount": 0.0, "cavityBias": 0.0, "color": "#2f2f31"},
        "localOverrides": overrides,
        "shaderNotes": [
            "MeshPhysicalMaterial with metalness 1.0; no clearcoat, no transmission, no sheen — "
            "the reference shows bare metal with no coating.",
            "Albedo, roughness and height are generated as independent procedural fields; "
            "albedo is never reused as a roughness or normal source.",
            "envMapIntensity carries most of the metal read: a metal with no environment to "
            "reflect renders as flat grey regardless of its roughness value.",
        ],
        "qualityTier": "reference-fidelity",
    }


MATERIALS = [
    metal("cast-iron", "Unpainted cast-iron casting", "#8c8f92", ["#83868a", "#95999c"],
          0.55, 0.04, 0.012, 0.018, 0.012, 0.05,
          "Sampled from the body side face and the base disc, away from the specular lobe; "
          "the reference's key highlight is not part of the albedo.",
          [{"id": "cast-grain", "region": "all-cast-faces", "roughness": 0.62,
            "roughnessVariation": 0.10, "cavityBias": 0.55,
            "notes": "Low-amplitude mottled sand-cast grain; raises roughness and darkens "
                     "crevices without changing hue."},
           {"id": "parting-seam-crevice", "region": "base-collar-parting-line",
            "roughness": 0.68, "ao": 0.55,
            "notes": "AO-darkened crevice along the circular swivel parting seam."}],
          repeat=12.0, meso_freq=22.0, micro_freq=70.0),
    metal("machined-steel", "Machined steel stock", "#9aa0a4", ["#949a9e", "#a2a8ac"],
          0.36, 0.035, 0.01, 0.02, 0.015, 0.07,
          "Sampled from the slide-bar top face and the jaw-plate flanks; brighter and flatter "
          "than the castings beside them.",
          [{"id": "slide-wear-polish", "region": "slide-bar-top", "roughness": 0.24,
            "notes": "The slide bar's bearing faces are wear-polished by travel; roughness "
                     "drops along the top and bottom faces only."},
           {"id": "tooth-root-ao", "region": "jaw-plate-serrations", "ao": 0.6,
            "roughness": 0.40,
            "notes": "Serration roots hold AO and read rougher than the crests."}],
          repeat=3.0, meso_freq=44.0, micro_freq=130.0),
    metal("oxide-screw", "Dark-oxide lead screw", "#6f7377", ["#696d71", "#787d81"],
          0.42, 0.04, 0.012, 0.02, 0.015, 0.09,
          "Sampled between thread crests on the long exposed run; visibly darker than every "
          "casting in the reference.",
          [{"id": "thread-crest-polish", "region": "thread-crest-line", "roughness": 0.30,
            "notes": "Crest line is burnished by the nut and carries the brightest specular "
                     "in that zone."},
           {"id": "thread-valley-ao", "region": "thread-valleys", "ao": 0.65,
            "roughness": 0.50,
            "notes": "Valleys stay dark and rough; without this the helix reads as a "
                     "painted stripe."}],
          repeat=2.5, meso_freq=48.0, micro_freq=140.0),
    metal("hardened-jaw", "Hardened serrated jaw plate", "#7f8388", ["#797d81", "#888d91"],
          0.52, 0.05, 0.015, 0.03, 0.02, 0.09,
          "Sampled on the jaw plate between tooth crests; the reference shows no flare there, so "
          "the plate is rougher and slightly darker than the machined stock beside it.",
          [{"id": "tooth-crest-polish", "region": "jaw-plate-serrations", "roughness": 0.42,
            "notes": "Crests are burnished by clamping and read a little brighter than the roots."},
           {"id": "tooth-root-cavity", "region": "jaw-plate-serrations", "ao": 0.62,
            "roughness": 0.58,
            "notes": "Roots hold occlusion; without it the tooth row reads as stripes painted on "
                     "a flat plate."}],
          repeat=3.5, meso_freq=46.0, micro_freq=132.0),
    metal("polished-handle", "Near-polished turned handle stock", "#a8adb2",
          ["#a4a9ae", "#b0b5ba"], 0.24, 0.025, 0.006, 0.012, 0.01, 0.05,
          "Sampled off-highlight on the tommy bar; the lightest and flattest albedo in the "
          "reference.",
          [{"id": "ball-hotspot", "region": "handle-ball-ends", "roughness": 0.17,
            "notes": "The two ball ends carry the lowest roughness and the tightest specular "
                     "lobes anywhere in the reference."}]),
]


# ---------------------------------------------------------------- component authoring
def rgba(hex_color: str, alpha: float = 1.0) -> str:
    h = hex_color.lstrip("#")
    return f"rgba({int(h[0:2],16)}, {int(h[2:4],16)}, {int(h[4:6],16)}, {alpha})"


MATERIAL_ALBEDO = {
    "cast-iron": ("#8c8f92", "#7a7d80"),
    "hardened-jaw": ("#7f8388", "#797d81"),
    "machined-steel": ("#9aa0a4", "#8b9195"),
    "oxide-screw": ("#6f7377", "#5e6265"),
    "polished-handle": ("#a8adb2", "#9aa0a5"),
}


def comp(cid, name, level, role, primitive, descriptor, parent, position, *,
         rotation=(0.0, 0.0, 0.0), scale=(1.0, 1.0, 1.0), material="cast-iron",
         topology="assembled-solid", rationale="", importance=0.7, confidence=0.75,
         evidence=("full-object",), local_features=(), details=(), attachment=None,
         animation_role="static-part", pivot_axis=(0, 1, 0), channels=None,
         sockets=(), collider="box", collider_scale=(1, 1, 1), fracture="vise-body",
         surface=None, seams=(), joints=(), fidelity="form-refined"):
    dom, sec = MATERIAL_ALBEDO[material]
    ch = {"translate": False, "rotate": False, "scale": False, "bend": False,
          "twist": False, "detach": True, "visibility": True, "materialState": True}
    ch.update(channels or {})
    return {
        "id": cid, "name": name, "level": level, "role": role,
        "importance": importance, "confidence": confidence,
        "primitive": primitive,
        "topologyClass": topology,
        "topologyRationale": rationale,
        "geometryDescriptor": descriptor,
        "parent": parent,
        "attachment": attachment,
        "dimensions": {"width": scale[0], "height": scale[1], "depth": scale[2],
                       "units": "relative", "confidence": confidence},
        "transform": {"position": [round(v, 4) for v in position],
                      "rotation": [round(v, 5) for v in rotation],
                      "scale": [round(v, 4) for v in scale]},
        "actionProfile": {
            "animationRole": animation_role,
            "pivot": {"mode": "explicit", "localPosition": [0, 0, 0],
                      "axis": list(pivot_axis), "confidence": confidence},
            "transformChannels": ch,
            "sockets": list(sockets),
            "collider": {"type": collider, "offset": [0, 0, 0],
                         "scale": [round(v, 4) for v in collider_scale],
                         "isTrigger": False,
                         "notes": "Convex proxy sized to the component's own extents."},
            "constraints": [],
            "destruction": {"breakable": False, "fractureGroup": fracture,
                            "seamRefs": [], "detachableFragments": [],
                            "breakImpulse": 0.0, "debrisMaterial": material},
        },
        "material": material,
        "materialLayers": [material],
        "colorMaterialRecipe": {
            "dominantAlbedo": rgba(dom), "secondaryAlbedo": rgba(sec),
            "materialClass": "metal", "materialClassConfidence": 0.9,
            # No colorGradient: every surface in the reference is a single flat metal tone
            # whose variation comes from roughness and lighting, not from an albedo ramp.
            "evidenceRefs": list(evidence),
        },
        "deformations": [], "joints": list(joints), "seams": list(seams),
        "localFeatures": list(local_features),
        "surfaceDetail": surface or {
            "macroRoughness": 0.16, "microRoughness": 0.09, "bumpAmplitude": 0.03,
            "normalPattern": "sand-cast grain", "displacementPattern": "none",
            "occlusionPattern": "cavity-darkened cast crevices",
            "edgeWearPattern": "none",
            "notes": "Cast surface: mottled roughness, no directional machining marks.",
        },
        "evidenceRefs": list(evidence),
        "details": list(details),
        "fidelityTier": fidelity,
    }


def feat(fid, name, kind, note, scale="micro"):
    return {"id": fid, "name": name, "kind": kind, "scale": scale, "notes": note}


def attach(parent_id, socket, start, end, contact, overlap, tol=0.005, evidence=("full-object",)):
    return {"parentId": parent_id, "parentSocket": socket,
            "localStart": [round(v, 4) for v in start],
            "localEnd": [round(v, 4) for v in end],
            "contactType": contact, "overlap": overlap, "embedDepth": overlap,
            "gapTolerance": tol, "evidenceRefs": list(evidence)}


def socket(sid, pos, rot=(0, 0, 0), note=""):
    return {"id": sid, "localPosition": [round(v, 4) for v in pos],
            "localRotation": list(rot), "notes": note}


# ------------------------------------------------- world -> local transform resolution
def euler_to_matrix(rx: float, ry: float, rz: float) -> list[list[float]]:
    """three.js default Euler order is XYZ, applied as R = Rx * Ry * Rz."""
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)
    rxm = [[1, 0, 0], [0, cx, -sx], [0, sx, cx]]
    rym = [[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]
    rzm = [[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]
    return mat_mul(mat_mul(rxm, rym), rzm)


def mat_mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def mat_t(a):
    return [[a[j][i] for j in range(3)] for i in range(3)]


def mat_apply(a, v):
    return [sum(a[i][k] * v[k] for k in range(3)) for i in range(3)]


def matrix_to_euler(m) -> tuple[float, float, float]:
    """Inverse of euler_to_matrix for the XYZ order three.js uses."""
    sy = max(-1.0, min(1.0, m[0][2]))
    ry = math.asin(sy)
    if abs(sy) < 0.999999:
        rx = math.atan2(-m[1][2], m[2][2])
        rz = math.atan2(-m[0][1], m[0][0])
    else:
        rx = math.atan2(m[2][1], m[1][1])
        rz = 0.0
    return rx, ry, rz


class Frame:
    """World pivot + world orientation for one component, so the spec can be authored in
    world/object space and the local transform derived, instead of hand-composing nested
    rotations (which is exactly where a mirrored or rotated sub-assembly silently drifts)."""

    def __init__(self):
        self.pos: dict[str, list[float]] = {}
        self.rot: dict[str, list[list[float]]] = {}

    def register(self, cid: str, world_pos, world_euler=(0.0, 0.0, 0.0)):
        self.pos[cid] = [float(v) for v in world_pos]
        self.rot[cid] = euler_to_matrix(*world_euler)

    def local(self, cid: str, parent: str | None):
        if parent is None:
            p = [0.0, 0.0, 0.0]
            r = euler_to_matrix(0, 0, 0)
        else:
            p, r = self.pos[parent], self.rot[parent]
        delta = [self.pos[cid][i] - p[i] for i in range(3)]
        local_pos = mat_apply(mat_t(r), delta)
        local_rot = matrix_to_euler(mat_mul(mat_t(r), self.rot[cid]))
        return local_pos, local_rot

    def to_local_point(self, cid: str, world_point):
        delta = [world_point[i] - self.pos[cid][i] for i in range(3)]
        return mat_apply(mat_t(self.rot[cid]), delta)


# ---------------------------------------------------------------- the component tree
FR = Frame()

BODY_PIVOT = (0.0, 0.40, -BODY_Z / 2)
FIXED_RISER_PIVOT = (0.35, 1.50, -JAW_Z / 2)
MOV_RISER_PIVOT = (2 * MIRROR_X - 0.35, 1.50, -JAW_Z / 2)
PLATE_Z = 0.96
FIXED_PLATE_PIVOT = (FIXED_JAW_FACE, 2.01, -PLATE_Z / 2)
MOV_PLATE_PIVOT = (MOVABLE_JAW_FACE, 2.01, -PLATE_Z / 2)
SLIDE_PIVOT = ((SLIDE_MINUS_X + SLIDE_PLUS_X) / 2, SLIDE_Y, 0.0)
SCREW_PIVOT = ((SCREW_TAIL_END + SCREW_HEAD_END) / 2, SCREW_Y, 0.0)
BAR_PIVOT = (HEAD_BOSS_C, SCREW_Y, 0.0)

X_LATHE = (0.0, 0.0, -HALF_PI)   # lathe axis (local +Y) -> world +X
Z_LATHE = (HALF_PI, 0.0, 0.0)    # lathe axis (local +Y) -> world +Z
PLATE_ROT = (HALF_PI, 0.0, 0.0)  # extrude depth (local +Z) -> world -Y

BOLT_WORLD = [(round(LOBE_DIST * math.cos(math.radians(a)), 4), BASE_PLATE_TOP,
               round(LOBE_DIST * math.sin(math.radians(a)), 4)) for a in (45, 135, 225, 315)]

# (id, world pivot, world euler)
FR.register("base-plate", (0, BASE_PLATE_TOP, 0), PLATE_ROT)
FR.register("base-boss", (0, BASE_PLATE_TOP, 0))
for i, p in enumerate(BOLT_WORLD, 1):
    FR.register(f"base-bolt-{i}", p)
FR.register("swivel-collar", (0, BASE_PLATE_TOP, 0))
FR.register("collar-flange", (0, 0.33, 0))
FR.register("swivel-lock-bolt", (0.19, 0.28, 0.45), Z_LATHE)
FR.register("body-casting", BODY_PIVOT)
FR.register("body-plateau-pad", (-0.04, 1.70, 0))
FR.register("body-foot-fastener", (0.02, 0.52, 0.47), Z_LATHE)
FR.register("nut-boss", (0.70, SCREW_Y, 0), X_LATHE)
FR.register("fixed-jaw-riser", FIXED_RISER_PIVOT)
FR.register("fixed-jaw-gusset", (0.44, 1.34, 0))
FR.register("fixed-jaw-plate", FIXED_PLATE_PIVOT)
FR.register("slide-carriage", SLIDE_PIVOT)
FR.register("movable-jaw-riser", MOV_RISER_PIVOT)
FR.register("movable-jaw-gusset", (2 * MIRROR_X - 0.44, 1.34, 0))
FR.register("movable-jaw-plate", MOV_PLATE_PIVOT)
FR.register("thrust-lobe", ((THRUST_LOBE_X0 + THRUST_LOBE_X1) / 2, SCREW_Y, 0), X_LATHE)
FR.register("thrust-ring", (THRUST_RING_C, SCREW_Y, 0), X_LATHE)
FR.register("screw-head-boss", (HEAD_BOSS_C, SCREW_Y, 0), X_LATHE)
FR.register("tommy-bar", BAR_PIVOT, (BAR_TILT_X, 0.0, BAR_TILT_Z))
FR.register("lead-screw-shaft", SCREW_PIVOT, X_LATHE)
FR.register("screw-thread-mid", (BODY_MINUS_X + 0.03, SCREW_Y, 0))
FR.register("screw-thread-tail", (SCREW_TAIL_END, SCREW_Y, 0))

# The two ball ends live in the tommy bar's own tilted frame, so they are registered from
# bar-local coordinates rather than guessed in world space.
_bar_rot = euler_to_matrix(BAR_TILT_X, 0.0, BAR_TILT_Z)
for sign, tag in ((1, "plus"), (-1, "minus")):
    off = mat_apply(_bar_rot, [0.0, BAR_SLIDE + sign * BAR_LEN / 2, 0.0])
    FR.register(f"bar-ball-{tag}", [BAR_PIVOT[i] + off[i] for i in range(3)],
                (BAR_TILT_X, 0.0, BAR_TILT_Z))


def place(cid: str, parent: str | None):
    p, r = FR.local(cid, parent)
    return tuple(p), tuple(r)


def build_components() -> list[dict]:
    C: list[dict] = []

    def add(cid, parent, **kw):
        pos, rot = place(cid, parent)
        C.append(comp(cid, parent=parent, position=pos, rotation=rot, **kw))

    # ---- base assembly ------------------------------------------------------------
    add("base-plate", None, name="Four-lobed swivel base plate", level="macro",
        role="mounting-plate", primitive="extrude",
        descriptor={
            "topologyIntent": "flat cast plate; lobe outline and bolt holes are real geometry",
            "edgeTreatment": {"type": "chamfer", "bevelRadius": 0.012, "segments": 2},
            "deformationStack": [], "uvStrategy": "generated procedural coordinates",
            "normalStrategy": "vertex normals from generated geometry",
            "profile2D": {"points": base_plan_outline(), "depth": BASE_PLATE_TOP,
                          "ovalHoles": lobe_holes()},
        },
        rationale="A cast plate with a closed planar outline and four through holes: the plan "
                  "curve carries the whole shape and the thickness is uniform, so it is built "
                  "as one extruded solid rather than stacked masses.",
        importance=0.85, confidence=0.7, material="cast-iron",
        evidence=("base-front-lobes", "base-collar-parting-line"),
        local_features=[feat("mount-hole-row", "Four counterbored mounting holes", "hole",
                             "One through hole per lobe, on the 45-degree diagonals at "
                             f"radius {LOBE_DIST}.", "meso"),
                        feat("mount-bolt-row", "Hex mounting bolt heads", "fastener",
                             "One hex head seated at each lobe hole; heads stand proud of the "
                             "plate face.", "meso")],
        animation_role="root", channels={"translate": True, "rotate": True, "detach": False},
        sockets=[socket("swivel-axis", (0, 0, 0), note="Vertical swivel axis of the whole vise.")],
        collider="box", collider_scale=(1.6, 0.14, 1.6), fracture="vise-base",
        fidelity="form-refined")

    add("base-boss", "base-plate", name="Raised swivel seat boss", level="meso",
        role="bearing-seat", primitive="lathe",
        descriptor={"topologyIntent": "turned circular seat the swivel collar rides on",
                    "edgeTreatment": {"type": "fillet", "bevelRadius": 0.008, "segments": 2},
                    "deformationStack": [], "uvStrategy": "cylindrical",
                    "normalStrategy": "vertex normals from generated geometry",
                    "latheProfile": lathe([(0.0, -0.02), (0.57, -0.02), (0.57, 0.06),
                                           (0.53, 0.10), (0.0, 0.10)])},
        rationale="Surface of revolution about the swivel axis; a lathed profile reproduces the "
                  "seat step exactly where a box stack would fake it.",
        importance=0.4, confidence=0.6, material="cast-iron",
        evidence=("base-collar-parting-line",),
        attachment=attach("base-plate", "swivel-axis", (0, 0, 0), (0, 0.10, 0),
                          "flush-seat", 0.04, evidence=("base-collar-parting-line",)),
        collider="cylinder", collider_scale=(1.14, 0.12, 1.14), fracture="vise-base")

    for i in range(1, 5):
        add(f"base-bolt-{i}", "base-plate", name=f"Base mounting bolt head {i}", level="micro",
            role="fastener", primitive="lathe",
            descriptor={"topologyIntent": "hexagonal fastener head as a six-segment lathe",
                        "edgeTreatment": {"type": "chamfer", "bevelRadius": 0.004, "segments": 1},
                        "deformationStack": [], "uvStrategy": "cylindrical",
                        "normalStrategy": "flat-shaded facets",
                        "latheProfile": hex_head(0.088, -0.01, 0.075)},
            rationale="Six flats around one axis: a six-segment revolve is the hex head itself, "
                      "not a cylinder standing in for one.",
            importance=0.3, confidence=0.6, material="machined-steel",
            evidence=("base-front-lobes",),
            attachment=attach("base-plate", "swivel-axis", (0, 0, 0), (0, 0.075, 0),
                              "seated-in-counterbore", 0.02, evidence=("base-front-lobes",)),
            collider="cylinder", collider_scale=(0.18, 0.075, 0.18), fracture="vise-base",
            surface={"macroRoughness": 0.05, "microRoughness": 0.04, "bumpAmplitude": 0.0,
                     "normalPattern": "none", "displacementPattern": "none",
                     "occlusionPattern": "counterbore shadow ring", "edgeWearPattern": "none",
                     "notes": "Machined head: flat facets, no cast grain."})

    add("swivel-collar", "base-plate", name="Swivel collar", level="macro",
        role="turntable", primitive="lathe",
        descriptor={"topologyIntent": "turned collar carrying the parting seam groove",
                    "edgeTreatment": {"type": "fillet", "bevelRadius": 0.01, "segments": 2},
                    "deformationStack": [], "uvStrategy": "cylindrical",
                    "normalStrategy": "vertex normals from generated geometry",
                    # The parting groove is cut with sloped walls rather than square corners.
                    # A square concave corner leaves its ring of vertices with an averaged
                    # normal pointing into the material, which reads as a surface fold to
                    # self_intersection.py -- and a cast seam has relieved corners anyway.
                    "latheProfile": lathe(
                        [(0.0, 0.08), (0.50, 0.08)]
                        + smooth_groove(0.50, 0.098, 0.152, 0.030)
                        + [(0.50, 0.20), (0.455, 0.24), (0.0, 0.24)])},
        rationale="One surface of revolution about the swivel axis; the recessed parting seam is "
                  "a step in the revolved profile, so it holds a real shadow from every angle.",
        importance=0.7, confidence=0.7, material="cast-iron",
        evidence=("base-collar-parting-line", "swivel-collar-front"),
        local_features=[feat("parting-seam", "Circular swivel parting seam", "seam",
                             "Recessed groove ring separating the rotating collar from the fixed "
                             "foot disc; built as profile geometry, never a dark line.", "meso")],
        animation_role="swivel", pivot_axis=(0, 1, 0),
        channels={"rotate": True, "detach": False},
        sockets=[socket("body-seat", (0, 0.24, 0), note="Seat the body casting rides on.")],
        attachment=attach("base-plate", "swivel-axis", (0, 0, 0), (0, 0.24, 0),
                          "rotating-socket", 0.06, evidence=("base-collar-parting-line",)),
        collider="cylinder", collider_scale=(1.00, 0.24, 1.00), fracture="vise-body")

    add("collar-flange", "swivel-collar", name="Swivel collar upper flange", level="meso",
        role="flange", primitive="lathe",
        descriptor={"topologyIntent": "tapered rim visible around the body casting's foot",
                    "edgeTreatment": {"type": "fillet", "bevelRadius": 0.008, "segments": 2},
                    "deformationStack": [], "uvStrategy": "cylindrical",
                    "normalStrategy": "vertex normals from generated geometry",
                    "latheProfile": lathe([(0.0, 0.0), (0.505, 0.0), (0.505, 0.03),
                                           (0.45, 0.07), (0.0, 0.07)])},
        rationale="A revolved taper: the flange reads as a cone frustum in the reference and any "
                  "faceted stand-in would break the circular highlight running around it.",
        importance=0.35, confidence=0.55, material="cast-iron",
        evidence=("base-collar-parting-line",),
        attachment=attach("swivel-collar", "body-seat", (0, 0, 0), (0, 0.07, 0),
                          "flush-seat", 0.03),
        collider="cylinder", collider_scale=(1.01, 0.07, 1.01))

    add("swivel-lock-bolt", "swivel-collar", name="Swivel lock bolt", level="micro",
        role="fastener", primitive="lathe",
        descriptor={"topologyIntent": "hex head on a short boss, protruding toward the camera",
                    "edgeTreatment": {"type": "chamfer", "bevelRadius": 0.004, "segments": 1},
                    "deformationStack": [], "uvStrategy": "cylindrical",
                    "normalStrategy": "flat-shaded facets",
                    "latheProfile": hex_head(0.09, 0.0, 0.10)},
        rationale="Six flats around one axis; the six-segment revolve is the head, so the flats "
                  "catch light individually as they do in the reference.",
        importance=0.3, confidence=0.6, material="machined-steel",
        evidence=("swivel-collar-front",),
        local_features=[feat("lock-bolt", "Swivel lock hex head", "fastener",
                             "Single hex-headed lock bolt on the front of the swivel collar.",
                             "meso")],
        attachment=attach("swivel-collar", "body-seat", (0, 0, 0), (0, 0.10, 0),
                          "threaded-socket", 0.03, evidence=("swivel-collar-front",)),
        collider="cylinder", collider_scale=(0.18, 0.10, 0.18),
        surface={"macroRoughness": 0.05, "microRoughness": 0.04, "bumpAmplitude": 0.0,
                 "normalPattern": "none", "displacementPattern": "none",
                 "occlusionPattern": "boss shadow ring", "edgeWearPattern": "none",
                 "notes": "Machined head: flat facets, no cast grain."})

    # ---- body casting -------------------------------------------------------------
    add("body-casting", "swivel-collar", name="Main body casting", level="macro",
        role="frame", primitive="extrude",
        descriptor={
            "topologyIntent": "constant-width casting; the side silhouette carries the shape",
            "edgeTreatment": {"type": "chamfer", "bevelRadius": 0.02, "segments": 2},
            "deformationStack": [], "uvStrategy": "generated procedural coordinates",
            "normalStrategy": "vertex normals from generated geometry",
            "profile2D": {"points": rebase(BODY_PROFILE_WORLD, BODY_PIVOT[0], BODY_PIVOT[1]),
                          "depth": BODY_Z},
        },
        rationale="The casting's identity is entirely in its side outline — narrow foot, "
                  "straight flanks, chamfered top plateau — and its width is constant, so an "
                  "extruded outline reproduces it where a box stack would lose the chamfer.",
        importance=0.9, confidence=0.75, material="cast-iron",
        evidence=("body-top-plateau", "body-lower-front"),
        local_features=[feat("plateau-chamfer", "Chamfered top plateau edge", "bevel",
                             "Hard chamfer bounding the top plateau; catches the bright grazing "
                             "rim line seen in the reference.", "meso"),
                        feat("foot-fastener", "Body foot hex fastener", "fastener",
                             "Small hex fastener boss on the lower front face.", "micro")],
        sockets=[socket("nut-axis", (BODY_PLUS_X, SCREW_Y - BODY_PIVOT[1], -BODY_PIVOT[2]),
                        note="Where the lead screw threads through the body nut."),
                 socket("slide-channel",
                        (SLIDE_PIVOT[0], SLIDE_Y - BODY_PIVOT[1], -BODY_PIVOT[2]),
                        note="Rectangular guide channel the slide bar runs in."),
                 socket("jaw-riser-root",
                        (FIXED_RISER_PIVOT[0], FIXED_RISER_PIVOT[1] - BODY_PIVOT[1],
                         -BODY_PIVOT[2]),
                        note="Root of the fixed jaw riser where it leaves the casting.")],
        attachment=attach("swivel-collar", "body-seat", (0, 0, 0), (0, 1.30, 0),
                          "flush-seat", 0.04, evidence=("body-lower-front",)),
        collider="box", collider_scale=(1.32, 1.34, BODY_Z))

    add("body-plateau-pad", "body-casting", name="Top plateau anvil pad", level="meso",
        role="pad", primitive="box",
        descriptor={"topologyIntent": "flat raised pad on the casting's top plateau",
                    "edgeTreatment": {"type": "chamfer", "bevelRadius": 0.015, "segments": 2},
                    "deformationStack": [], "uvStrategy": "box",
                    "normalStrategy": "vertex normals from generated geometry"},
        rationale="A flat-topped rectangular pad: a box with chamfered edges is the shape, and "
                  "its top face is the flat the reference shows behind the fixed jaw.",
        scale=(0.52, 0.06, 0.66), importance=0.4, confidence=0.5, material="cast-iron",
        evidence=("body-top-plateau",),
        attachment=attach("body-casting", "jaw-riser-root", (0, 0, 0), (0, 0.06, 0),
                          "flush-overlap", 0.03, evidence=("body-top-plateau",)),
        collider="box", collider_scale=(0.52, 0.06, 0.66))

    add("body-foot-fastener", "body-casting", name="Body foot fastener", level="micro",
        role="fastener", primitive="lathe",
        descriptor={"topologyIntent": "small hex head on the lower front face",
                    "edgeTreatment": {"type": "chamfer", "bevelRadius": 0.003, "segments": 1},
                    "deformationStack": [], "uvStrategy": "cylindrical",
                    "normalStrategy": "flat-shaded facets",
                    "latheProfile": hex_head(0.075, -0.02, 0.10)},
        rationale="Six flats around one axis, so a six-segment revolve is the head rather than "
                  "a rounded approximation of one.",
        importance=0.25, confidence=0.5, material="machined-steel",
        evidence=("body-lower-front",),
        attachment=attach("body-casting", "slide-channel", (0, 0, 0), (0, 0.07, 0),
                          "threaded-socket", 0.02, evidence=("body-lower-front",)),
        collider="cylinder", collider_scale=(0.15, 0.07, 0.15),
        surface={"macroRoughness": 0.05, "microRoughness": 0.04, "bumpAmplitude": 0.0,
                 "normalPattern": "none", "displacementPattern": "none",
                 "occlusionPattern": "boss shadow ring", "edgeWearPattern": "none",
                 "notes": "Machined head: flat facets, no cast grain."})

    add("nut-boss", "body-casting", name="Lead-screw nut boss", level="meso",
        role="bearing-boss", primitive="lathe",
        descriptor={"topologyIntent": "raised collar around the screw where it leaves the body",
                    "edgeTreatment": {"type": "fillet", "bevelRadius": 0.01, "segments": 2},
                    "deformationStack": [], "uvStrategy": "cylindrical",
                    "normalStrategy": "vertex normals from generated geometry",
                    "latheProfile": lathe([(0.0, -0.09), (0.20, -0.09), (0.20, 0.05),
                                           (0.17, 0.09), (0.0, 0.09)])},
        rationale="Concentric with the screw axis; revolving the step profile keeps the collar "
                  "circular from every azimuth, which a boxed stand-in cannot do.",
        importance=0.5, confidence=0.6, material="cast-iron",
        evidence=("mid-screw-run",),
        attachment=attach("body-casting", "nut-axis", (0, 0, 0), (0.20, 0, 0),
                          "socket", 0.06, evidence=("mid-screw-run",)),
        collider="cylinder", collider_scale=(0.18, 0.40, 0.40))

    # ---- fixed jaw ----------------------------------------------------------------
    add("fixed-jaw-riser", "body-casting", name="Fixed jaw riser (hooked)", level="macro",
        role="jaw-riser", primitive="extrude",
        descriptor={
            "topologyIntent": "hooked riser: convex outer face, deep concave inner scallop",
            "edgeTreatment": {"type": "fillet", "bevelRadius": 0.03, "segments": 3},
            "deformationStack": [], "uvStrategy": "generated procedural coordinates",
            "normalStrategy": "vertex normals from generated geometry",
            "profile2D": {"points": rebase(FIXED_RISER_WORLD, FIXED_RISER_PIVOT[0],
                                           FIXED_RISER_PIVOT[1]),
                          "depth": JAW_Z},
        },
        rationale="The hook is a constant-width profile swept across the jaw width: the concave "
                  "underside that the screw passes beneath is part of the outline, so extruding "
                  "the outline is what produces the reference's most recognizable negative space.",
        importance=1.0, confidence=0.8, material="cast-iron",
        evidence=("jaw-gap-upper-center", "jaw-arms-and-body"),
        local_features=[feat("cast-fillet", "Broad top fillet into the scallop", "bevel",
                             "The inner scallop meets the jaw top face through a broad cast "
                             "fillet, never a sharp edge.", "meso")],
        sockets=[socket("jaw-plate-seat",
                        (FIXED_PLATE_PIVOT[0] - FIXED_RISER_PIVOT[0],
                         FIXED_PLATE_PIVOT[1] - FIXED_RISER_PIVOT[1], 0.0),
                        note="Seat for the serrated jaw plate.")],
        attachment=attach("body-casting", "jaw-riser-root", (0, 0, 0), (0, 0.72, 0),
                          "cast-continuous", 0.30,
                          evidence=("jaw-arms-and-body",)),
        collider="box", collider_scale=(0.64, 0.94, JAW_Z))

    add("fixed-jaw-gusset", "fixed-jaw-riser", name="Fixed jaw riser gusset", level="meso",
        role="gusset", primitive="box",
        descriptor={"topologyIntent": "raised rib where the riser leaves the casting",
                    "edgeTreatment": {"type": "chamfer", "bevelRadius": 0.012, "segments": 2},
                    "deformationStack": [], "uvStrategy": "box",
                    "normalStrategy": "vertex normals from generated geometry"},
        rationale="A straight raised rib of constant section; a chamfered box is that rib, and "
                  "nothing about it is curved enough to need a swept surface.",
        scale=(0.16, 0.34, 0.80), importance=0.35, confidence=0.45, material="cast-iron",
        evidence=("jaw-arms-and-body",),
        attachment=attach("fixed-jaw-riser", "jaw-plate-seat", (0, 0, 0), (0, 0.44, 0),
                          "cast-continuous", 0.08),
        collider="box", collider_scale=(0.16, 0.34, 0.80))

    add("fixed-jaw-plate", "fixed-jaw-riser", name="Fixed serrated jaw plate", level="meso",
        role="jaw-plate", primitive="extrude",
        descriptor={
            "topologyIntent": "hardened plate whose gripping teeth break the silhouette edge",
            "edgeTreatment": {"type": "chamfer", "bevelRadius": 0.006, "segments": 1},
            "deformationStack": [], "uvStrategy": "generated procedural coordinates",
            "normalStrategy": "vertex normals from generated geometry",
            "profile2D": {"points": rebase(
                [(x, y) for x, y in jaw_plate_profile(FIXED_JAW_FACE, +1)],
                FIXED_PLATE_PIVOT[0], FIXED_PLATE_PIVOT[1]), "depth": PLATE_Z},
        },
        rationale="Teeth run straight across the jaw width, so the toothed outline extruded "
                  "along that width IS the serration — a relief map would leave the plate's "
                  "silhouette edge smooth, which is exactly where the reference shows the teeth.",
        importance=0.9, confidence=0.65, material="hardened-jaw",
        evidence=("jaw-gap-upper-center",),
        local_features=[feat("serration-row", "Horizontal gripping serrations", "ridge",
                             "Rows of triangular teeth across the jaw width at 0.022 pitch, "
                             "0.014 deep, standing proud of the plate face.", "micro"),
                        feat("top-tab", "Stepped top tab", "ridge",
                             "The plate's top step stands above the tooth crests and above the "
                             "riser's top edge — a strong silhouette cue at the jaw gap.",
                             "meso")],
        attachment=attach("fixed-jaw-riser", "jaw-plate-seat", (0, 0, 0), (0, 0.36, 0),
                          "bolted-overlap", 0.04, evidence=("jaw-gap-upper-center",)),
        collider="box", collider_scale=(0.18, 0.42, PLATE_Z),
        surface={"macroRoughness": 0.06, "microRoughness": 0.05, "bumpAmplitude": 0.0,
                 "normalPattern": "none", "displacementPattern": "none",
                 "occlusionPattern": "tooth-root cavity darkening", "edgeWearPattern": "crest polish",
                 "notes": "Hardened machined plate: flat between teeth, AO in the tooth roots."})

    # ---- movable jaw carriage ------------------------------------------------------
    add("slide-carriage", "body-casting", name="Movable jaw slide bar", level="macro",
        role="carriage", primitive="box",
        descriptor={"topologyIntent": "rectangular slide bar running through the body channel",
                    "edgeTreatment": {"type": "chamfer", "bevelRadius": 0.015, "segments": 2},
                    "deformationStack": [], "uvStrategy": "box",
                    "normalStrategy": "vertex normals from generated geometry"},
        rationale="A prismatic bar of constant rectangular section: a chamfered box is the part, "
                  "and its flat bearing faces are what the reference shows entering the casting.",
        scale=(SLIDE_PLUS_X - SLIDE_MINUS_X, SLIDE_H, SLIDE_Z),
        importance=0.8, confidence=0.7, material="machined-steel",
        evidence=("body-minus-x-face", "mid-screw-run"),
        local_features=[feat("guide-seam", "Slide guide mouth seam", "seam",
                             "The rectangular gap where the bar leaves the body reads as a "
                             "recessed, AO-darkened seam on both faces of the casting.", "meso")],
        animation_role="jaw-travel", pivot_axis=(1, 0, 0),
        channels={"translate": True, "detach": False},
        sockets=[socket("jaw-root", (MOV_RISER_PIVOT[0] - SLIDE_PIVOT[0],
                                     MOV_RISER_PIVOT[1] - SLIDE_PIVOT[1], 0.0),
                        note="Root of the movable jaw riser."),
                 socket("screw-axis", (0.0, SCREW_Y - SLIDE_Y, 0.0),
                        note="Lead-screw axis, collinear with the slide axis.")],
        attachment=attach("body-casting", "slide-channel", (0, 0, 0),
                          (SLIDE_PLUS_X - SLIDE_MINUS_X, 0, 0),
                          "sliding-socket", 0.20, evidence=("body-minus-x-face",)),
        collider="box", collider_scale=(SLIDE_PLUS_X - SLIDE_MINUS_X, SLIDE_H, SLIDE_Z),
        fracture="vise-movable-jaw",
        surface={"macroRoughness": 0.06, "microRoughness": 0.05, "bumpAmplitude": 0.01,
                 "normalPattern": "directional machining pass marks", "displacementPattern": "none",
                 "occlusionPattern": "guide-mouth seam darkening", "edgeWearPattern": "travel polish",
                 "notes": "Machined stock, wear-polished on the top and bottom bearing faces."})

    add("movable-jaw-riser", "slide-carriage", name="Movable jaw riser (hooked)", level="macro",
        role="jaw-riser", primitive="extrude",
        descriptor={
            "topologyIntent": "mirror of the fixed riser about the jaw-gap mid-plane",
            "edgeTreatment": {"type": "fillet", "bevelRadius": 0.03, "segments": 3},
            "deformationStack": [], "uvStrategy": "generated procedural coordinates",
            "normalStrategy": "vertex normals from generated geometry",
            "profile2D": {"points": rebase(mirror_x(FIXED_RISER_WORLD), MOV_RISER_PIVOT[0],
                                           MOV_RISER_PIVOT[1]),
                          "depth": JAW_Z},
        },
        rationale="Same constant-width hook as the fixed riser, reflected about the jaw-gap "
                  "mid-plane — a reflection of the longitudinal axis only, so the pair reads as "
                  "opposed jaws rather than one shape rotated into place.",
        importance=1.0, confidence=0.8, material="cast-iron",
        evidence=("jaw-gap-upper-center", "jaw-arms-and-body"),
        local_features=[feat("cast-fillet-mirror", "Broad top fillet into the scallop", "bevel",
                             "Mirror of the fixed riser's top fillet.", "meso")],
        sockets=[socket("jaw-plate-seat",
                        (MOV_PLATE_PIVOT[0] - MOV_RISER_PIVOT[0],
                         MOV_PLATE_PIVOT[1] - MOV_RISER_PIVOT[1], 0.0),
                        note="Seat for the serrated jaw plate.")],
        attachment=attach("slide-carriage", "jaw-root", (0, 0, 0), (0, 0.72, 0),
                          "cast-continuous", 0.14, evidence=("jaw-arms-and-body",)),
        collider="box", collider_scale=(0.64, 0.94, JAW_Z), fracture="vise-movable-jaw")

    add("movable-jaw-gusset", "movable-jaw-riser", name="Movable jaw riser gusset", level="meso",
        role="gusset", primitive="box",
        descriptor={"topologyIntent": "raised rib mirroring the fixed riser's gusset",
                    "edgeTreatment": {"type": "chamfer", "bevelRadius": 0.012, "segments": 2},
                    "deformationStack": [], "uvStrategy": "box",
                    "normalStrategy": "vertex normals from generated geometry"},
        rationale="Straight raised rib of constant section, mirrored from the fixed side; a "
                  "chamfered box is the rib itself.",
        scale=(0.16, 0.34, 0.80), importance=0.35, confidence=0.45, material="cast-iron",
        evidence=("jaw-arms-and-body",),
        attachment=attach("movable-jaw-riser", "jaw-plate-seat", (0, 0, 0), (0, 0.44, 0),
                          "cast-continuous", 0.08),
        collider="box", collider_scale=(0.16, 0.34, 0.80), fracture="vise-movable-jaw")

    add("movable-jaw-plate", "movable-jaw-riser", name="Movable serrated jaw plate", level="meso",
        role="jaw-plate", primitive="extrude",
        descriptor={
            "topologyIntent": "mirrored hardened plate, teeth opposing the fixed plate",
            "edgeTreatment": {"type": "chamfer", "bevelRadius": 0.006, "segments": 1},
            "deformationStack": [], "uvStrategy": "generated procedural coordinates",
            "normalStrategy": "vertex normals from generated geometry",
            "profile2D": {"points": rebase(
                [(x, y) for x, y in jaw_plate_profile(MOVABLE_JAW_FACE, -1)],
                MOV_PLATE_PIVOT[0], MOV_PLATE_PIVOT[1]), "depth": PLATE_Z},
        },
        rationale="Reflection of the fixed plate about the jaw-gap mid-plane; the teeth face the "
                  "opposing plate, so the pair closes tooth-crest to tooth-crest.",
        importance=0.9, confidence=0.65, material="hardened-jaw",
        evidence=("jaw-gap-upper-center",),
        local_features=[feat("serration-row-mirror", "Horizontal gripping serrations", "ridge",
                             "Mirror of the fixed plate's tooth row, same pitch and depth.",
                             "micro"),
                        feat("top-tab-mirror", "Stepped top tab", "ridge",
                             "Mirror of the fixed plate's stepped top tab.", "meso")],
        attachment=attach("movable-jaw-riser", "jaw-plate-seat", (0, 0, 0), (0, 0.36, 0),
                          "bolted-overlap", 0.04, evidence=("jaw-gap-upper-center",)),
        collider="box", collider_scale=(0.18, 0.42, PLATE_Z), fracture="vise-movable-jaw",
        surface={"macroRoughness": 0.06, "microRoughness": 0.05, "bumpAmplitude": 0.0,
                 "normalPattern": "none", "displacementPattern": "none",
                 "occlusionPattern": "tooth-root cavity darkening", "edgeWearPattern": "crest polish",
                 "notes": "Hardened machined plate: flat between teeth, AO in the tooth roots."})

    # ---- thrust / handle -----------------------------------------------------------
    add("thrust-lobe", "slide-carriage", name="Screw thrust lobe", level="macro",
        role="thrust-boss", primitive="lathe",
        descriptor={"topologyIntent": "rounded cylindrical boss carrying the screw thrust face",
                    "edgeTreatment": {"type": "fillet", "bevelRadius": 0.03, "segments": 3},
                    "deformationStack": [], "uvStrategy": "cylindrical",
                    "normalStrategy": "vertex normals from generated geometry",
                    "latheProfile": lathe([(0.14, -0.30), (0.38, -0.30), (0.41, -0.24),
                                           (0.41, 0.18), (0.37, 0.26), (0.26, 0.30),
                                           (0.14, 0.30)])},
        rationale="A body of revolution about the screw axis: the reference's rounded end lobe "
                  "keeps a circular outline as the vise turns, which only a revolve gives.",
        importance=0.75, confidence=0.65, material="cast-iron",
        evidence=("thrust-ring", "mid-screw-run"),
        sockets=[socket("thrust-face", (0.0, 0.30, 0.0),
                        note="Face the screw's thrust ring bears against.")],
        attachment=attach("slide-carriage", "screw-axis", (0, 0, 0), (0, 0.60, 0),
                          "cast-continuous", 0.13, evidence=("mid-screw-run",)),
        collider="cylinder", collider_scale=(0.82, 0.60, 0.82), fracture="vise-movable-jaw")

    add("thrust-ring", "thrust-lobe", name="Knurled thrust ring", level="meso",
        role="collar", primitive="lathe",
        descriptor={"topologyIntent": "short turned ring carrying an axial knurl band",
                    "edgeTreatment": {"type": "chamfer", "bevelRadius": 0.008, "segments": 2},
                    "deformationStack": [], "uvStrategy": "cylindrical",
                    "normalStrategy": "vertex normals from generated geometry",
                    "latheProfile": lathe([(0.11, -0.10), (0.25, -0.10), (0.26, -0.08),
                                           (0.26, 0.08), (0.25, 0.10), (0.11, 0.10)])},
        rationale="Turned stock revolved about the screw axis; the knurl ridges are instanced "
                  "on top of it rather than carved into the revolve, so the ring stays circular.",
        importance=0.6, confidence=0.6, material="oxide-screw",
        evidence=("thrust-ring",),
        local_features=[feat("knurl-band", "Axial knurl band", "ridge",
                             "Dense axial ridges around the ring; real geometry, because a "
                             "roughness map would leave the ring's silhouette smooth.", "micro")],
        attachment=attach("thrust-lobe", "thrust-face", (0, 0, 0), (0, 0.20, 0),
                          "butt", 0.03, evidence=("thrust-ring",)),
        collider="cylinder", collider_scale=(0.52, 0.20, 0.52), fracture="vise-screw",
        surface={"macroRoughness": 0.08, "microRoughness": 0.06, "bumpAmplitude": 0.02,
                 "normalPattern": "axial knurl", "displacementPattern": "none",
                 "occlusionPattern": "knurl valley darkening", "edgeWearPattern": "crest polish",
                 "notes": "Dark-oxide turned ring; knurl crests read brighter than the valleys."})

    add("screw-head-boss", "thrust-ring", name="Cross-drilled screw head", level="meso",
        role="screw-head", primitive="lathe",
        descriptor={"topologyIntent": "short turned head carrying the tommy-bar cross hole",
                    "edgeTreatment": {"type": "chamfer", "bevelRadius": 0.006, "segments": 2},
                    "deformationStack": [], "uvStrategy": "cylindrical",
                    "normalStrategy": "vertex normals from generated geometry",
                    "latheProfile": lathe([(0.0, -0.10), (0.11, -0.10), (0.11, 0.08),
                                           (0.09, 0.10), (0.0, 0.10)])},
        rationale="Turned round stock on the screw axis; the bar passes through it, so it must "
                  "stay a body of revolution for the bar to read as free to slide.",
        importance=0.5, confidence=0.6, material="oxide-screw",
        evidence=("handle-ball-ends",),
        sockets=[socket("bar-cross-hole", (0.0, 0.0, 0.0),
                        note="Cross hole the tommy bar slides through.")],
        attachment=attach("thrust-ring", "thrust-face", (0, 0, 0), (0, 0.20, 0),
                          "butt", 0.03),
        collider="cylinder", collider_scale=(0.22, 0.20, 0.22), fracture="vise-screw")

    add("tommy-bar", "screw-head-boss", name="Tommy bar", level="macro",
        role="handle", primitive="lathe",
        descriptor={"topologyIntent": "straight turned bar through the screw head cross hole",
                    "edgeTreatment": {"type": "fillet", "bevelRadius": 0.006, "segments": 2},
                    "deformationStack": [], "uvStrategy": "cylindrical",
                    "normalStrategy": "vertex normals from generated geometry",
                    "latheProfile": lathe([(0.0, BAR_SLIDE - BAR_LEN / 2),
                                           (BAR_R * 0.7, BAR_SLIDE - BAR_LEN / 2),
                                           (BAR_R, BAR_SLIDE - BAR_LEN / 2 + 0.03),
                                           (BAR_R, BAR_SLIDE + BAR_LEN / 2 - 0.03),
                                           (BAR_R * 0.7, BAR_SLIDE + BAR_LEN / 2),
                                           (0.0, BAR_SLIDE + BAR_LEN / 2)], segments=20)},
        rationale="Round turned stock of constant diameter revolved about its own axis; it is a "
                  "through-bar, not an L, so it has to be one straight solid with two free ends.",
        importance=0.8, confidence=0.7, material="polished-handle",
        evidence=("handle-ball-ends",),
        animation_role="handle-slide", pivot_axis=(0, 1, 0),
        channels={"translate": True, "rotate": True, "detach": True},
        sockets=[socket("ball-plus", (0, BAR_SLIDE + BAR_LEN / 2, 0), note="Upper ball end seat."),
                 socket("ball-minus", (0, BAR_SLIDE - BAR_LEN / 2, 0), note="Lower ball end seat.")],
        attachment=attach("screw-head-boss", "bar-cross-hole", (0, BAR_SLIDE - BAR_LEN / 2, 0),
                          (0, BAR_SLIDE + BAR_LEN / 2, 0), "through-hole", 0.11,
                          evidence=("handle-ball-ends",)),
        collider="capsule", collider_scale=(2 * BAR_R, BAR_LEN, 2 * BAR_R),
        fracture="vise-handle",
        surface={"macroRoughness": 0.04, "microRoughness": 0.03, "bumpAmplitude": 0.0,
                 "normalPattern": "none", "displacementPattern": "none",
                 "occlusionPattern": "cross-hole contact shadow", "edgeWearPattern": "handling polish",
                 "notes": "Near-polished turned stock: the flattest, brightest surface in the scene."})

    for sign, tag, sock in ((1, "plus", "ball-plus"), (-1, "minus", "ball-minus")):
        add(f"bar-ball-{tag}", "tommy-bar", name=f"Tommy bar ball end ({tag})", level="meso",
            role="knob", primitive="sphere",
            descriptor={"topologyIntent": "spherical end stop upset on the bar",
                        "edgeTreatment": {"type": "none", "bevelRadius": 0.0, "segments": 1},
                        "deformationStack": [], "uvStrategy": "spherical",
                        "normalStrategy": "vertex normals from generated geometry"},
            rationale="A true sphere: the reference's tightest specular lobes sit on these two "
                      "ends, and only a spherical surface produces that highlight shape.",
            scale=(2 * BALL_R, 2 * BALL_R, 2 * BALL_R),
            importance=0.6, confidence=0.75, material="polished-handle",
            evidence=("handle-ball-ends",),
            local_features=[feat(f"ball-hotspot-{tag}", "Tight specular hotspot", "gloss",
                                 "Lowest roughness in the scene; the hotspot position is what "
                                 "makes the ball read as polished rather than painted.")],
            attachment=attach("tommy-bar", sock, (0, 0, 0), (0, sign * BALL_R, 0),
                              "upset-overlap", 0.04, evidence=("handle-ball-ends",)),
            collider="sphere", collider_scale=(2 * BALL_R, 2 * BALL_R, 2 * BALL_R),
            fracture="vise-handle",
            surface={"macroRoughness": 0.03, "microRoughness": 0.02, "bumpAmplitude": 0.0,
                     "normalPattern": "none", "displacementPattern": "none",
                     "occlusionPattern": "neck contact shadow", "edgeWearPattern": "handling polish",
                     "notes": "Polished sphere; roughness 0.17 via the ball-hotspot override."})

    # ---- lead screw ----------------------------------------------------------------
    screw_len = SCREW_HEAD_END - SCREW_TAIL_END
    add("lead-screw-shaft", "slide-carriage", name="Lead screw core shaft", level="macro",
        role="screw", primitive="lathe",
        descriptor={"topologyIntent": "chamfered round core the thread helix winds around",
                    "edgeTreatment": {"type": "chamfer", "bevelRadius": 0.01, "segments": 2},
                    "deformationStack": [], "uvStrategy": "cylindrical",
                    "normalStrategy": "vertex normals from generated geometry",
                    "latheProfile": lathe([
                        (0.0, -screw_len / 2), (SCREW_CORE_R * 0.6, -screw_len / 2),
                        (SCREW_CORE_R, -screw_len / 2 + 0.05),
                        (SCREW_CORE_R, screw_len / 2 - 0.05),
                        (SCREW_CORE_R * 0.6, screw_len / 2), (0.0, screw_len / 2)], segments=24)},
        rationale="Round stock revolved about the screw axis; the thread is swept separately on "
                  "top of it so the core and the helix keep independent radii, as they do on a "
                  "real acme screw.",
        importance=0.85, confidence=0.7, material="oxide-screw",
        evidence=("mid-screw-run", "screw-tail-end"),
        local_features=[feat("end-chamfer", "Chamfered screw ends", "bevel",
                             "Both exposed ends are chamfered rather than square-cut."),
                        feat("thread-helix", "Acme thread helix", "ridge",
                             f"Trapezoidal thread at {THREAD_PITCH} pitch, crest radius "
                             f"{SCREW_CREST_R} over a {SCREW_CORE_R} core, in two exposed runs.",
                             "meso")],
        animation_role="screw-spin", pivot_axis=(1, 0, 0),
        channels={"rotate": True, "detach": True},
        sockets=[socket("thread-run-mid", (0, BODY_MINUS_X + 0.03 - SCREW_PIVOT[0], 0),
                        note="Start of the long thread run; the reference's exposed portion "
                             "begins where it leaves the body's +X face."),
                 socket("thread-run-tail", (0, SCREW_TAIL_END - SCREW_PIVOT[0], 0),
                        note="Start of the short exposed tail run.")],
        attachment=attach("slide-carriage", "screw-axis", (0, 0, 0), (screw_len, 0, 0),
                          "threaded-socket", 0.30, evidence=("mid-screw-run",)),
        collider="cylinder", collider_scale=(screw_len, 2 * SCREW_CREST_R, 2 * SCREW_CREST_R),
        fracture="vise-screw",
        surface={"macroRoughness": 0.10, "microRoughness": 0.08, "bumpAmplitude": 0.02,
                 "normalPattern": "turned pass marks", "displacementPattern": "none",
                 "occlusionPattern": "thread valley darkening", "edgeWearPattern": "crest burnish",
                 "notes": "Dark-oxide turned core, visibly darker than every casting."})

    thread_r = (SCREW_CORE_R + SCREW_CREST_R) / 2
    # Section is wider than half the crest-to-core step so consecutive turns nearly meet:
    # a thread whose turns leave a visible gap over the core reads as a coil spring.
    section = (SCREW_CREST_R - SCREW_CORE_R) / 2 + 0.019
    for tag, run_len, sock, ev in (
            # Runs from just inside the body's -X face, not from its +X face. The thread is
            # cut along the whole screw, and the screw travels with the jaw: a run that starts
            # at the body's +X face leaves bare core between the casting and the thread as soon
            # as the jaw opens. The reference shows two EXPOSED runs; the geometry underneath
            # them is one continuous thread.
            ("mid", THRUST_LOBE_X0 - (BODY_MINUS_X + 0.03), "thread-run-mid", "mid-screw-run"),
            ("tail", BODY_MINUS_X - SCREW_TAIL_END, "thread-run-tail", "screw-tail-end")):
        add(f"screw-thread-{tag}", "lead-screw-shaft",
            name=f"Exposed acme thread run ({tag})", level="meso",
            role="thread", primitive="tapered-sweep",
            descriptor={"topologyIntent": "thread ridge swept along a helix about the screw axis",
                        "edgeTreatment": {"type": "fillet", "bevelRadius": 0.004, "segments": 1},
                        "deformationStack": [], "uvStrategy": "swept-arc-length",
                        "normalStrategy": "vertex normals from generated geometry",
                        "taperedSweep": {"stations": helix_stations(run_len, thread_r,
                                                                    THREAD_PITCH, section),
                                         "radialSegments": 6, "capEnds": True}},
            rationale="A ridge that winds continuously around the axis while advancing along it "
                      "cannot be produced by any revolve or extrude; it needs a section swept "
                      "along a helical spine, tapering out at both ends as a real thread does.",
            importance=0.95, confidence=0.6, material="oxide-screw", evidence=(ev,),
            local_features=[feat(f"thread-runout-{tag}", "Thread run-out", "ridge",
                                 "Both ends of the run taper to a point instead of being cut "
                                 "off square in mid-air.")],
            attachment=attach("lead-screw-shaft", sock, (0, 0, 0), (0, run_len, 0),
                              "swept-overlay", 0.03, evidence=(ev,)),
            collider="cylinder", collider_scale=(run_len, 2 * SCREW_CREST_R, 2 * SCREW_CREST_R),
            fracture="vise-screw",
            surface={"macroRoughness": 0.12, "microRoughness": 0.09, "bumpAmplitude": 0.03,
                     "normalPattern": "thread flank relief", "displacementPattern": "none",
                     "occlusionPattern": "deep valley darkening", "edgeWearPattern": "crest burnish",
                     "notes": "Crest line is the brightest specular in this zone; valleys hold AO."})

    return C


# ---------------------------------------------------------------- spec assembly
VIEW_EVIDENCE = [
    ("full-object", "primary", (0.0, 0.0, 1.0, 1.0),
     ["Near-orthographic side view; screw axis roughly parallel to the image plane.",
      "Overall width : height about 2.0 : 1 measured off the silhouette.",
      "Three negative spaces: the jaw gap, the gap under the exposed mid screw run, and the "
      "gaps between base lobes."], 0.85),
    ("jaw-gap-upper-center", "primary", (0.50, 0.10, 0.22, 0.30),
     ["Both jaw plates stand proud of their risers and carry a stepped tab above the riser edge.",
      "Jaw faces oppose along the screw axis; the open gap measures about 0.17 of overall width.",
      "Serration pitch is below reliable count resolution — approximated."], 0.7),
    ("jaw-arms-and-body", "primary", (0.38, 0.12, 0.34, 0.46),
     ["Each riser has a convex outer face and a deep concave inner scallop closing to a broad "
      "top fillet.",
      "The exposed screw run passes beneath the fixed riser's scallop."], 0.75),
    ("mid-screw-run", "primary", (0.40, 0.36, 0.30, 0.14),
     ["Long exposed thread run between the body face and the movable jaw's thrust lobe.",
      "About 20 turns visible; crest line is the brightest specular in the zone.",
      "A raised collar sits where the screw leaves the body."], 0.7),
    ("screw-tail-end", "primary", (0.02, 0.38, 0.12, 0.12),
     ["Short exposed thread tail past the -X body face, same diameter as the mid run.",
      "End is chamfered rather than square-cut."], 0.6),
    ("thrust-ring", "primary", (0.72, 0.36, 0.10, 0.18),
     ["Fine axial knurl band reading as a dense vertical hatch.",
      "Ring is visibly darker than the casting beside it."], 0.7),
    ("handle-ball-ends", "primary", (0.76, 0.26, 0.14, 0.46),
     ["Straight bar with a sphere at each end, cross-drilled through the screw head.",
      "The two balls carry the tightest, brightest specular lobes in the reference.",
      "Bar is tilted a few degrees out of image-vertical."], 0.8),
    ("body-top-plateau", "primary", (0.28, 0.28, 0.20, 0.12),
     ["Flat plateau behind the fixed jaw bounded by a hard chamfer that catches a bright rim line.",
      "Whether it is a true anvil pad or only a cast chamfer is undetermined."], 0.55),
    ("body-lower-front", "primary", (0.28, 0.58, 0.18, 0.14),
     ["Small hex fastener boss on the lower front face of the casting."], 0.5),
    ("body-minus-x-face", "primary", (0.06, 0.46, 0.14, 0.16),
     ["Slide bar leaves the casting through a rectangular guide mouth; the gap reads as a dark "
      "recessed seam."], 0.6),
    ("base-front-lobes", "primary", (0.18, 0.70, 0.36, 0.16),
     ["Hex bolt heads seated in the front base lobes, brighter than the casting around them."],
     0.65),
    ("base-lobes", "primary", (0.16, 0.68, 0.40, 0.18),
     ["Four radial lobes on a common disc, each with a counterbored through hole.",
      "Only the two front lobes are observed; the rear pair is mirrored inference."], 0.55),
    ("base-collar-parting-line", "primary", (0.20, 0.64, 0.34, 0.08),
     ["Crisp circular parting seam separating the swivel collar from the fixed foot disc."], 0.7),
    ("swivel-collar-front", "primary", (0.30, 0.62, 0.14, 0.08),
     ["Single hex-headed swivel lock bolt on the front of the collar."], 0.55),
    ("slide-bar-top", "primary", (0.42, 0.48, 0.26, 0.06),
     ["Bright flat top face along the slide bar; flatter and lighter than the castings."], 0.6),
    ("jaw-plate-serrations", "primary", (0.52, 0.12, 0.16, 0.14),
     ["Tooth rows break the plate's silhouette edge, so the teeth are geometry, not relief."],
     0.6),
    ("thread-crest-line", "primary", (0.44, 0.38, 0.24, 0.06),
     ["Continuous bright crest line running along the exposed thread."], 0.65),
    ("thread-valleys", "primary", (0.44, 0.40, 0.24, 0.06),
     ["Valleys stay dark and hold occlusion between crests."], 0.6),
    ("all-castings", "primary", (0.10, 0.15, 0.70, 0.75),
     ["Low-amplitude mottled roughness and tone variation across every cast surface.",
      "Absent from machined and turned surfaces."], 0.6),
    ("all-cast-faces", "primary", (0.10, 0.15, 0.70, 0.75),
     ["Same cast grain, sampled per casting face rather than across the whole object."], 0.6),
]


SKILL = Path(".claude/skills/img2threejs")


def regenerate_skeleton() -> dict:
    """Re-derive the starter skeleton from assessment.json so this script is idempotent:
    running it twice must produce the same spec, not compound its own edits.

    Written to a temp path, never over SPEC: a crash anywhere later in this script would
    otherwise leave the real spec as a bare skeleton with reviewHistory erased, and the pass
    gate reads that history -- so a build error would silently re-lock completed passes.
    """
    import subprocess
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "skeleton.json"
        subprocess.run(
            ["python3", str(SKILL / "forge/stage2_spec/new_sculpt_spec.py"),
             "Machinist Bench Vise with Swivel Base", "--image", "reference/REFERENCE_ANALYSIS.md",
             "--assessment", "assessment.json", "--out", str(out), "--force"],
            check=True, capture_output=True)
        return json.loads(out.read_text(encoding="utf-8"))


# Fields the pipeline writes, not this script. Regenerating the skeleton would otherwise
# erase the pass history every time a measurement is refined -- and the pass gate reads that
# history to decide what is unlocked, so losing it silently re-locks completed passes.
CARRIED_OVER = ("reviewHistory", "visualEvidence", "sculptPipeline")


def build_spec() -> dict:
    previous = json.loads(SPEC.read_text(encoding="utf-8")) if SPEC.exists() else {}
    spec = regenerate_skeleton()
    spec.update({k: previous[k] for k in CARRIED_OVER if k in previous})
    components = build_components()
    ids_by_level = {lv: [c["id"] for c in components if c["level"] == lv]
                    for lv in ("macro", "meso", "micro")}
    macro = ids_by_level["macro"]
    macro_meso = macro + ids_by_level["meso"]
    every = macro_meso + ids_by_level["micro"]

    spec["sourceImage"] = "reference/REFERENCE_ANALYSIS.md"
    spec["sourceImageNote"] = (
        "The reference was supplied as a conversation attachment and is readable by agent vision "
        "only; no image file exists on disk. Every measurement in this spec is an agent-vision "
        "reading recorded in reference/REFERENCE_ANALYSIS.md, and every pixel-level script gate "
        "is recorded as skipped-with-reason in .img2threejs/state.json."
    )
    spec["suitability"] = "conditional"
    # 0-3 scale, per grimoire/intake/validation_rubric.md.
    spec["scores"] = {
        "object_isolation": 3,          # single object, empty seamless backdrop
        "silhouette_readability": 3,    # unbroken outline, near-orthographic side view
        "depth_inference": 1,           # one view only; the -Z half is mirrored inference
        "primitive_decomposition": 3,   # extrudes, revolves, one swept helix, spheres
        "material_procedurality": 3,    # bare metal, no pattern finish to project
        "occlusion_risk": 2,            # rear half, base underside and both internal channels
        "interaction_fit": 3,           # two real kinematic axes plus screw spin and bar slide
    }
    spec["coordinateFrame"] = {
        "front": "+Z, the side facing the reference camera",
        "up": "+Y",
        "longitudinal": "+X, with the movable jaw toward +X",
        "handedness": "right-handed",
        "scaleReference": "1 unit = 100 mm; jaw width 1.02 units (102 mm), overall length 4.32 "
                          "units (432 mm). Absolute scale is a convention, not a measurement — "
                          "the reference carries no scale cue.",
        "origin": "centre of the base disc, on the mounting plane (y = 0)",
    }
    spec["referenceCamera"] = {
        "solved": False,
        "fovDegrees": 26.0, "aspect": 1.74,
        "orientation": {"yaw": -14.0, "pitch": 5.0, "roll": 0.0},
        "positionHint": [3.0, 2.4, 11.0],
        "note": "Estimated from the reference by eye, not solved: the object is shown near "
                "orthographic (little perspective convergence along the screw axis) from a few "
                "degrees above eye level, rotated slightly so a sliver of the front face shows. "
                "Not used for projection — this reconstruction takes the procedural-material "
                "route, so an unsolved camera only affects review framing.",
    }
    spec["silhouette"] = {
        "boundingShape": "wide low mass: a chamfered box on a lobed disc, with a hooked jaw pair "
                         "rising at the +X third and a ball-ended bar overhanging the +X end",
        "aspectRatios": [{"axis": "width:height", "value": 2.0},
                         {"axis": "baseDiameter:width", "value": 0.36},
                         {"axis": "jawOpening:width", "value": 0.09}],
        "symmetry": "bilateral about the vertical plane containing the screw axis (the XY plane "
                    "at z = 0); the jaw pair is additionally a reflection about x = 1.37",
        "dominantCurves": ["convex outer face of each jaw riser",
                           "deep concave inner scallop of each jaw riser",
                           "circular outline of the swivel collar and thrust lobe",
                           "helical crest line of the exposed thread"],
        "negativeSpaces": ["the open jaw gap between the two plate faces",
                           "the gap beneath the exposed mid screw run, under the fixed riser's "
                           "scallop and above the slide bar",
                           "the scalloped gaps between the four base lobes",
                           "the two gaps between the tommy bar's ball ends and the screw head"],
        "landmarks": [{"id": "jaw-top", "position": [1.17, 2.22, 0.0]},
                      {"id": "screw-axis", "position": [0.0, 1.30, 0.0]},
                      {"id": "swivel-axis-top", "position": [0.0, 0.40, 0.0]},
                      {"id": "screw-tail-tip", "position": [-1.07, 1.30, 0.0]},
                      {"id": "bar-ball-upper", "position": list(FR.pos["bar-ball-plus"])}],
    }
    spec["viewEvidence"] = [
        {"id": vid, "view": view,
         "imageRegion": {"x": r[0], "y": r[1], "width": r[2], "height": r[3],
                         "units": "normalized"},
         "observations": obs, "confidence": conf}
        for vid, view, r, obs, conf in VIEW_EVIDENCE
    ]
    spec["componentTree"] = components
    spec["materials"] = MATERIALS
    spec["repetitionSystems"] = [
        {"id": "knurl-ridge-ring", "name": "Axial knurl ridge ring", "level": "micro",
         "parent": "thrust-ring", "count": 44, "primitive": "box", "material": "oxide-screw",
         "instanceScale": [0.035, 0.17, 0.035],
         "placement": {"mode": "radial", "axis": [0, 1, 0], "radius": 0.53,
                       "startAngleDeg": 0,
                       "notes": "Axis is the screw axis expressed in the thrust ring's own "
                                "frame; radius is the emitter's diameter-form parameter."},
         "distributionRule": "even 360-degree division; ridge length runs along the ring axis",
         "evidenceRefs": ["thrust-ring"],
         "elementComponentIds": []},
        {"id": "base-mount-bolt-set", "name": "Base mounting bolt set", "level": "micro",
         "parent": "base-plate", "count": 4, "primitive": "lathe", "material": "machined-steel",
         "instanceScale": [0.176, 0.075, 0.176],
         "placement": {"mode": "radial", "axis": [0, 0, 1], "radius": 1.44,
                       "startAngleDeg": -45,
                       "notes": "Authored as four real hex-head components rather than instanced, "
                                "because the emitter's instance primitive cannot carry the "
                                "six-segment revolve that makes the head hexagonal."},
         "distributionRule": "one per lobe on the 45-degree diagonals",
         "evidenceRefs": ["base-front-lobes"],
         "elementComponentIds": [f"base-bolt-{i}" for i in range(1, 5)]},
        {"id": "jaw-serration-rows", "name": "Jaw plate serration rows", "level": "micro",
         "parent": "fixed-jaw-plate", "count": 8, "primitive": "extrude",
         "material": "machined-steel", "instanceScale": [0.014, 0.022, 0.96],
         "placement": {"mode": "linear", "axis": [0, 1, 0], "radius": 0.0,
                       "startAngleDeg": 0,
                       "notes": "Built into each plate's extruded outline: the teeth must break "
                                "the plate's silhouette edge, which instancing on top of a "
                                "smooth plate would not do."},
         "distributionRule": "0.022 pitch up the plate face, teeth 0.014 deep",
         "evidenceRefs": ["jaw-plate-serrations"],
         "elementComponentIds": ["fixed-jaw-plate", "movable-jaw-plate"]},
        {"id": "base-lobe-set", "name": "Four-lobed base outline", "level": "meso",
         "parent": "base-plate", "count": 4, "primitive": "extrude", "material": "cast-iron",
         "instanceScale": [0.52, 0.14, 0.52],
         "placement": {"mode": "radial", "axis": [0, 0, 1], "radius": 1.44,
                       "startAngleDeg": -45,
                       "notes": "Built into the plate's plan outline as a union of one disc and "
                                "four lobe circles, so the scalloped valleys between lobes are "
                                "real edges rather than overlapping instances."},
         "distributionRule": "four lobes at 90-degree spacing on the diagonals",
         "evidenceRefs": ["base-lobes"],
         "elementComponentIds": ["base-plate"]},
        {"id": "thread-turn-set", "name": "Acme thread turns", "level": "meso",
         "parent": "lead-screw-shaft", "count": 26, "primitive": "tapered-sweep",
         "material": "oxide-screw", "instanceScale": [0.03, 0.068, 0.03],
         "placement": {"mode": "helical", "axis": [1, 0, 0], "radius": 0.24,
                       "startAngleDeg": 0,
                       "notes": "A helix is one continuous ridge, not a stack of separate turns; "
                                "it is swept as a single tapered sweep per exposed run."},
         "distributionRule": f"constant {THREAD_PITCH} pitch, shared across both exposed runs",
         "evidenceRefs": ["mid-screw-run", "screw-tail-end"],
         "elementComponentIds": ["screw-thread-mid", "screw-thread-tail"]},
    ]
    return spec, macro, macro_meso, every


FEATURE_TARGETS = [
    ("overall-silhouette-proportion", "Overall silhouette, proportion and negative spaces",
     "critical", ["blockout", "structural-pass"], 0.8,
     ["base-plate", "body-casting", "slide-carriage", "fixed-jaw-riser", "movable-jaw-riser"],
     ["full-object"]),
    ("jaw-hook-profile", "Hooked jaw-riser profile pair", "critical",
     ["blockout", "form-refinement"], 0.8,
     ["fixed-jaw-riser", "movable-jaw-riser"], ["jaw-arms-and-body"]),
    ("jaw-gap-and-plates", "Jaw gap and serrated plates", "critical",
     ["structural-pass", "form-refinement"], 0.78,
     ["fixed-jaw-plate", "movable-jaw-plate"], ["jaw-gap-upper-center", "jaw-plate-serrations"]),
    ("screw-thread-runs", "Two exposed acme thread runs", "critical",
     ["form-refinement", "surface-pass"], 0.78,
     ["lead-screw-shaft", "screw-thread-mid", "screw-thread-tail", "nut-boss"],
     ["mid-screw-run", "screw-tail-end", "thread-crest-line"]),
    ("swivel-base-system", "Four-lobed swivel base and parting seam", "critical",
     ["structural-pass", "form-refinement"], 0.75,
     ["base-plate", "base-boss", "swivel-collar", "collar-flange"],
     ["base-lobes", "base-collar-parting-line"]),
    ("metal-finish-separation", "Four machining finishes within one metal family", "critical",
     ["material-pass", "surface-pass"], 0.75,
     ["body-casting", "slide-carriage", "lead-screw-shaft", "tommy-bar"],
     ["all-castings", "slide-bar-top", "thread-crest-line", "handle-ball-ends"]),
    ("handle-assembly", "Knurled thrust ring and ball-ended tommy bar", "important",
     ["structural-pass", "form-refinement"], 0.7,
     ["thrust-lobe", "thrust-ring", "screw-head-boss", "tommy-bar", "bar-ball-plus",
      "bar-ball-minus"],
     ["thrust-ring", "handle-ball-ends"]),
    ("knurl-and-fasteners", "Knurl band and hex fastener heads", "important",
     ["surface-pass"], 0.65,
     ["thrust-ring", "base-bolt-1", "swivel-lock-bolt", "body-foot-fastener"],
     ["thrust-ring", "base-front-lobes", "swivel-collar-front"]),
    ("lighting-and-contact-shadow", "Studio key/fill/rim and contact shadow", "important",
     ["lighting-pass"], 0.7, ["base-plate", "body-casting"], ["full-object"]),
]

PASS_GOALS = [
    ("blockout", "Match the macro silhouette, the three negative spaces and the proportion "
                 "system with no materials.",
     ["Silhouette reads as this vise, not a generic clamp, without materials.",
      "Jaw gap, under-screw gap and inter-lobe gaps are all present.",
      "Width : height is 2.0 +/- 0.1 and the base disc is 0.36 of overall width.",
      "AI vision comparison score meets selfCorrectLoop.visualAcceptance.threshold."]),
    ("structural-pass", "Build the full component hierarchy: plates, bosses, thrust ring, "
                        "handle, screw core.",
     ["Macro, meso and micro counts meet qualityContract.minimumSpecDepth.",
      "Every attached child declares parentSocket, localStart/localEnd, contactType, "
      "embedDepth or overlap and gapTolerance.",
      "Jaw travel, body swivel, screw spin and handle slide exist as real pivot nodes.",
      "AI vision comparison score meets selfCorrectLoop.visualAcceptance.threshold."]),
    ("form-refinement", "Refine the hook profiles, the thread helices, the knurl band and every "
                        "chamfer and fillet.",
     ["Both jaw risers show the convex/concave hook, not a rectangular upright.",
      "Both thread runs are swept helical geometry with visible relief.",
      "Knurl ridges break the thrust ring's silhouette.",
      "Left/right and fixed/movable pairs are reflections, never rotations.",
      "AI vision comparison score meets selfCorrectLoop.visualAcceptance.threshold."]),
    ("material-pass", "Separate the four machining finishes inside one bare-metal family.",
     ["Castings, machined stock, dark-oxide screw and polished handle are separable by eye.",
      "Roughness carries the separation; all four stay metalness 1.0.",
      "Each material declares macro/meso/micro surface frequency bands and an independent "
      "roughness field.",
      "AI vision comparison score meets selfCorrectLoop.visualAcceptance.threshold."]),
    ("surface-pass", "Add cast grain, thread-valley and tooth-root occlusion, and crest burnish.",
     ["Cast surfaces carry mottled roughness that machined surfaces do not.",
      "Thread valleys and tooth roots hold occlusion; crests read polished.",
      "AI vision comparison score meets selfCorrectLoop.visualAcceptance.threshold."]),
    ("lighting-pass", "Match the reference's studio key/fill/rim, exposure and contact shadow.",
     ["Key from upper-front-left, soft; fill from the opposite side; rim along the top edges.",
      "Environment reflection present — a metal with nothing to reflect renders flat grey.",
      "Soft contact shadow under the base on a near-white seamless backdrop.",
      "AI vision comparison score meets selfCorrectLoop.visualAcceptance.threshold."]),
    ("interaction-pass", "Wire the two real kinematic axes plus explode and click selection.",
     ["Jaw travel and body swivel are driveable with limits.",
      "Every macro and meso part is individually clickable and explodable.",
      "AI vision comparison score meets selfCorrectLoop.visualAcceptance.threshold."]),
    ("optimization-pass", "Reach the triangle and draw-call budget without losing reference "
                          "critical geometry.",
     ["Triangle count within performanceBudget.targetTriangles.",
      "No identity-defining geometry removed to hit the budget."]),
]


def finalize(spec, macro, macro_meso, every) -> dict:
    spec["buildPasses"] = [
        {"id": pid, "goal": goal,
         "componentRefs": (macro if pid == "blockout"
                           else macro_meso if pid == "structural-pass" else every),
         "acceptance": acceptance}
        for pid, goal, acceptance in PASS_GOALS
    ]
    spec["featureReviewTargets"] = [
        {"id": fid, "name": name, "tier": tier, "passIds": passes,
         "minimumScore": score, "mustPass": tier == "critical",
         "componentRefs": refs, "evidenceRefs": ev}
        for fid, name, tier, passes, score, refs, ev in FEATURE_TARGETS
    ]
    spec["qualityTargets"]["targetFidelity"] = 0.78
    spec["qualityTargets"]["reviewViewpoints"] = [
        "reference-match (right side, screw axis across frame)",
        "three-quarter front-right",
        "rear (mirrored half, inference check)",
        "top-down (jaw gap and base lobe pattern)",
        "grazing-light close-up on the thread and knurl",
    ]
    spec["qualityTargets"]["mustMatch"] = [
        "macro silhouette, proportion system and all three negative spaces",
        "hooked jaw-riser profile on both jaws",
        "two exposed acme thread runs as real swept geometry",
        "four-lobed swivel base with a recessed parting seam",
        "roughness separation across the four machining finishes",
    ]
    spec["qualityTargets"]["niceToHave"] = [
        "exact serration pitch and count",
        "cast-surface pitting amplitude",
        "reference-matched studio backdrop falloff",
    ]
    spec["actionReadiness"]["rootMotionNode"] = "base-plate"
    spec["animationAnchors"] = [
        "slide-carriage translates along +X to open and close the jaws; travel limit is the "
        "exposed mid thread run length (0 to 0.85 units of opening)",
        "swivel-collar rotates about +Y to swivel the whole vise on its base",
        "lead-screw-shaft spins about +X, geared to slide-carriage travel by the thread pitch "
        f"({THREAD_PITCH} units per turn)",
        "tommy-bar slides along its own axis through the screw-head cross hole and rotates with "
        "the screw",
        "every macro and meso pivot group supports local transforms without rebuilding geometry",
    ]
    spec["destructionAnchors"] = [
        "vise-base: base plate, seat boss and mounting bolts detach as one group",
        "vise-body: body casting, swivel collar and fixed jaw riser share a fracture group",
        "vise-movable-jaw: slide bar, movable riser, plate and thrust lobe detach together",
        "vise-screw: screw core, both thread runs and the thrust ring detach together",
        "vise-handle: tommy bar and both ball ends detach together",
    ]
    spec["lightingFromPhoto"] = [
        "Key: soft area light from upper-front-left, roughly 35 degrees above the horizon and 40 "
        "degrees off the camera axis; it produces the broad highlight on the body's top plateau "
        "and the bright crest line along the exposed thread.",
        "Fill: low-intensity, large, from the opposite side and slightly below, lifting the "
        "shadowed -Z flank without flattening the roughness read; key:fill ratio about 4:1.",
        "Rim/environment: a bright neutral studio environment map is the main source of the metal "
        "read — a metalness-1.0 surface with nothing to reflect renders as flat grey no matter "
        "what its roughness is. envMapIntensity is the primary exposure control for this scene.",
        "Exposure and tone mapping: ACES filmic tone mapping at about 1.0 exposure; the reference "
        "holds highlight detail on the handle balls rather than clipping them to white.",
        "Contact shadow: soft, low-opacity ground shadow under the base spreading away from the "
        "key, on a near-white seamless backdrop with a gentle vertical falloff and no horizon "
        "line; ambient occlusion carries the crevice darkening independently of it.",
    ]
    spec["assumptions"] = [
        "Rear (-Z) half of every casting is reconstructed by mirroring the observed +Z half; it "
        "is inference, not observation.",
        "Base underside, nut-boss interior and slide-channel interior are built to engineering "
        "convention because they are never visible in the reference.",
        "Jaw-plate serration pitch is set to 0.022 units and tooth depth to 0.014; the reference "
        "pitch is below reliable count resolution.",
        "The chamfered body plateau is modelled as a true flat anvil pad; the reference cannot "
        "distinguish that from a plain cast chamfer.",
        "All four base lobes carry fasteners; only the two front lobes are observed.",
        "Absolute scale is a convention: a 102 mm jaw width, expressed as 1 unit = 100 mm. The "
        "reference carries no scale cue.",
        f"Thread pitch is set to {THREAD_PITCH} units, counted from the reference with about "
        "+/-2 turns of uncertainty across the long run.",
        "Base lobes are placed on the 45-degree diagonals; the side view fixes their longitudinal "
        "extent but not their azimuth, and a square four-bolt pattern is the convention.",
        "The reference is available to agent vision only, as a conversation attachment, so PBR "
        "channel values are observation-derived rather than extracted from pixels.",
    ]
    spec["risks"] = [
        "Single view: no rear, top or bottom evidence. Per-region confidence is recorded in "
        "viewEvidence; the -Z half cannot be verified against anything.",
        "Thread relief is swept geometry at 6 radial segments per turn; at extreme close range "
        "the section will read faceted.",
        "Knurl ridges are instanced boxes rather than a true diamond knurl; correct at review "
        "distance, wrong under a macro lens.",
        "No pixel-level PBR extraction was possible, so the four roughness values are calibrated "
        "by eye against the reference's specular behaviour, not measured.",
    ]
    spec["performanceBudget"] = {
        "qualityPriority": "reference-fidelity",
        # 55000 selects the generator's `standard` tessellation tier instead of `hero`. That
        # tier only drives the segment counts of box/sphere/cylinder primitives -- the lathe
        # profiles and the thread's radial segments are authored in the spec and are untouched
        # -- so it cuts exactly where the waste was: the two handle balls were 4992 triangles
        # each for a 23 mm sphere, more than the whole thread run.
        "targetTriangles": 55000, "maxDrawCalls": 60, "textureSize": 2048, "fpsTarget": 60,
        "optimizationPolicy": "Reach accepted visual fidelity first, then cut only where the "
                              "silhouette does not carry identity. The thread sweeps and the "
                              "authored lathe profiles are silhouette-carrying and are not "
                              "reduced; primitive tessellation is.",
    }
    spec["lodPlan"] = [
        {"tier": "near", "distance": 0,
         "strategy": "full component tree, both thread runs, instanced knurl"},
        {"tier": "mid", "distance": 12,
         "strategy": "drop the knurl instance ring and halve the thread station count"},
        {"tier": "far", "distance": 30,
         "strategy": "merge static castings, replace both thread runs with the bare screw core"},
    ]
    spec["proceduralStrategy"] = [
        "Block out the macro silhouette from measured landmark positions, not from a guessed "
        "bounding box.",
        "Author each casting as an extruded side outline: the outline is what carries the "
        "identity, and a box stack loses the chamfers and the concave scallop.",
        "Revolve everything concentric with an axis (collar, bosses, thrust ring, screw core, "
        "handle) so it stays circular from every azimuth.",
        "Sweep the thread as a helical spine — no revolve or extrude can produce a ridge that "
        "advances while it winds.",
        "Build teeth, knurl and lobes as geometry wherever they break a silhouette edge; use "
        "material response only for what does not.",
        "Separate the four machining finishes by roughness and its variation, never by albedo.",
        "Keep every deterministic procedural field seeded so a rebuild is byte-identical.",
    ]
    contract = spec["qualityContract"]
    contract["minimumSpecDepth"] = {
        "macroComponents": len(macro), "mesoComponents": len(macro_meso) - len(macro),
        "microFeatureGroups": 6, "materialLayers": 5, "repetitionSystems": 4,
        "reviewViewpoints": 5,
    }
    assessment = spec["preSpecAssessment"]
    # Unknowns are resolved into `assumptions` above before implementation, which is what the
    # strict gate is asking for: an unknown that survives into code generation is a guess with
    # no record. Each one is still named there, with what it was resolved to and why.
    assessment["unknownsToResolveBeforeImplementation"] = []
    # Bare feature ids, not "owner/feature". validate_sculpt_spec accepts both forms, but
    # check_part_coverage collects only the bare ids, so the prefixed form passes one gate and
    # dangles in the other. Every feature id below is unique across the spec, so the bare form
    # is unambiguous and satisfies both.
    remap = {
        "fixed-jaw-plate/serration-row": "serration-row",
        "fixed-jaw-plate/top-tab": "top-tab",
        "lead-screw/thread-helix": "thread-helix",
        "thrust-ring/knurl-band": "knurl-band",
        "fixed-jaw-arm/cast-fillet": "cast-fillet",
        "body-casting/plateau-chamfer": "plateau-chamfer",
        "lead-screw/end-chamfer": "end-chamfer",
        "base-plate/mount-bolt-row": "mount-bolt-row",
        "swivel-collar/lock-bolt": "lock-bolt",
        "body-casting/foot-fastener": "foot-fastener",
        "base-plate/mount-hole-row": "mount-hole-row",
        "swivel-collar/parting-seam": "parting-seam",
        "slide-bar/guide-seam": "guide-seam",
        "polished-handle/ball-hotspot": "ball-hotspot",
        "cast-iron-body/cast-grain": "cast-grain",
    }
    for detail in assessment["detailInventory"]["details"]:
        ref = remap.get(detail["mapsTo"], detail["mapsTo"])
        material_override_ids = {o["id"] for m in MATERIALS for o in m["localOverrides"]}
        detail["mapsTo"] = {"ref": ref,
                            "kind": "material.localOverrides" if ref in material_override_ids
                                    else "component.localFeatures"}
    look = spec["lookDevTargets"]["materialPass"]["referencePbrExtraction"]
    look["requiredWhenSourceImagePresent"] = False
    look["acceptedLimitation"] = (
        "Pixel-level extraction is impossible here: the reference exists only as a conversation "
        "attachment with no file on disk, so extract_pbr_evidence.py has nothing to read. PBR "
        "channels are agent-vision observations recorded in reference/REFERENCE_ANALYSIS.md and "
        "calibrated against the reference's specular behaviour, which is weaker evidence than "
        "extraction and is reported as such."
    )
    return spec


def main() -> None:
    spec, macro, macro_meso, every = build_spec()
    spec = finalize(spec, macro, macro_meso, every)
    SPEC.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"componentTree: {len(spec['componentTree'])} "
          f"(macro {len(macro)}, meso {len(macro_meso) - len(macro)}, "
          f"micro {len(every) - len(macro_meso)})")
    print(f"materials: {len(spec['materials'])}  repetitionSystems: "
          f"{len(spec['repetitionSystems'])}")


if __name__ == "__main__":
    main()
