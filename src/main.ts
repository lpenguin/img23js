import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';
import {
  createMachinistBenchViseWithSwivelBaseModel as createViseModel,
  createMachinistBenchViseWithSwivelBaseLookDevLights as createLookDevLights,
  configureMachinistBenchViseWithSwivelBaseRenderer as configureRenderer,
  type ProceduralModelRuntime,
} from './createBenchViseModel';

/**
 * Review harness for the procedural bench-vise reconstruction.
 *
 * The URL drives the whole scene so a headless capture and a human tab share one code
 * path: ?view=front|right|rear|left|top|hero, ?light=reference|neutral|grazing,
 * ?jaw=0..1, ?swivel=deg, ?explode=0..1, ?ui=0. Anything the review gates measure has
 * to be reachable from a query string, or the render a gate scores is not the render a
 * person looked at.
 */

// 1 unit = 100 mm; see object-sculpt-spec.json coordinateFrame.
const MODEL_LENGTH = 4.4;
const JAW_TRAVEL = 0.85;

const params = new URLSearchParams(location.search);
const num = (key: string, fallback: number) => {
  const raw = params.get(key);
  const value = raw === null ? NaN : Number(raw);
  return Number.isFinite(value) ? value : fallback;
};

const VIEWS: Record<string, { azimuth: number; elevation: number; zoom: number;
                              panX?: number; panY?: number }> = {
  // Matches the reference framing: near-orthographic side view, a few degrees above eye
  // level, rotated slightly so a sliver of the front face shows.
  front: { azimuth: 8, elevation: 4, zoom: 1.0 },
  right: { azimuth: 90, elevation: 6, zoom: 1.0 },
  rear: { azimuth: 188, elevation: 4, zoom: 1.0 },
  left: { azimuth: 270, elevation: 6, zoom: 1.0 },
  top: { azimuth: 8, elevation: 78, zoom: 1.0 },
  hero: { azimuth: 38, elevation: 18, zoom: 0.92 },
  // Framing-matched plate for the reference gates. Divine Eye and Tier-1 diagnostics compare
  // pixels, so a framing difference reads as a proportion defect: the object has to land on
  // the same bounding box the reference's does, in a frame of the same size.
  // Converged against reference/bench-vise.png: at azimuth 6 / elevation 2 this geometry
  // projects to aspect 1.80 against the reference's 1.816, and the zoom puts the object on
  // the same 0.642 x 0.640 fraction of the frame so a pixel gate scores shape, not framing.
  match: { azimuth: 6, elevation: 2, zoom: 0.819, panX: -0.0295, panY: 0.0662 },
  // Pure side elevation, no azimuth and no elevation: the projected bbox of this view is the
  // model's own world X:Y ratio (modulo perspective), which is the control that separates a
  // geometry error from a camera error.
  ortho: { azimuth: 0, elevation: 0, zoom: 1.0 },
};

const canvas = document.getElementById('stage') as HTMLCanvasElement;
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
// ?shadows=0 gives a shadow-free plate for silhouette measurement: a cast shadow is
// foreground to any background-difference mask, so a bbox measured with it on is the
// bbox of the object PLUS its shadow.
const shadowsOn = params.get('shadows') !== '0';
renderer.shadowMap.enabled = shadowsOn;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
configureRenderer(renderer);
renderer.toneMappingExposure = num('exposure', 0.90);

const scene = new THREE.Scene();

// Seamless studio backdrop: a vertical value falloff with no horizon line, which is what
// the reference sits on. A flat clear colour would kill the top-edge rim the metal needs.
scene.background = backdropTexture();

const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
pmrem.dispose();
// A metalness-1.0 surface has no diffuse term, so the environment IS its albedo read.
// RoomEnvironment at full strength washes every casting toward the backdrop value and
// collapses the four machining finishes into one bright grey -- the reference's screw sits
// visibly darker than its castings and that separation only survives at reduced intensity.
scene.environmentIntensity = num('env', 0.70);

const model = createViseModel({ castShadow: true, receiveShadow: true });
scene.add(model);
const runtime = model.userData.sculptRuntime as ProceduralModelRuntime;

// Contact shadow only — the backdrop keeps its own gradient, so a lit ground plane would
// paint a second, brighter floor over it.
const ground = new THREE.Mesh(
  new THREE.PlaneGeometry(60, 60),
  // The reference's contact shadow is light and very soft -- a low-contrast smudge under the
  // base, not a silhouette on the floor. At 0.28 the render's shadow was the darkest thing in
  // the frame, which no surface of the object itself is.
  new THREE.ShadowMaterial({ opacity: num('shadow', 0.09) }),
);
ground.rotation.x = -Math.PI / 2;
ground.receiveShadow = true;
if (shadowsOn) scene.add(ground);

// ?maps=0 is the blockout gate's evidence render: every material map disabled and the
// albedo flattened to one neutral grey, so the pass is judged on FORM. A procedural albedo
// and roughness field hides exactly the geometry a blockout is supposed to prove.
if (params.get('maps') === '0') {
  model.traverse((child) => {
    const mesh = child as THREE.Mesh;
    if (!mesh.isMesh) return;
    const flat = new THREE.MeshStandardMaterial({
      color: 0xb0b3b6, roughness: 0.85, metalness: 0.0, flatShading: false,
    });
    mesh.material = flat;
  });
}

let lights = createLookDevLights('reference');
tuneLights(lights);
scene.add(lights);
// A broad, low-intensity frontal fill. The reference's front faces sit only slightly below its
// top plateau in value, which a key-plus-hemisphere rig alone cannot do: the hemisphere is
// vertical, so it darkens the front and the side by the same amount.
const frontFill = new THREE.DirectionalLight(0xf4f1ec, 0.5);
frontFill.position.set(1.5, 1.2, 6.0).multiplyScalar(MODEL_LENGTH * 0.6);
scene.add(frontFill);

// 18-degree vertical FOV: the reference shows almost no perspective convergence
// along the screw axis, so a wider lens would splay the jaws that a gate then
// scores as a proportion error.
const camera = new THREE.PerspectiveCamera(18, 1, 0.1, 400);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
// Deterministic capture: OrbitControls' per-frame update() with damping keeps nudging the
// camera after a scripted placement, so two screenshots of the same URL are framed a few
// pixels apart and a gate reads that drift as a proportion change. update() therefore runs
// only once a human has actually grabbed the camera.
let interactive = false;
controls.addEventListener('start', () => { interactive = true; });
controls.minDistance = MODEL_LENGTH * 0.4;
controls.maxDistance = MODEL_LENGTH * 6;
controls.target.set(0.7, 1.1, 0);

const view = { ...(VIEWS[params.get('view') ?? 'front'] ?? VIEWS.front) };
view.zoom *= num('zoom', 1);
// The reference's own camera elevation and azimuth are unknown; these overrides are what
// makes converging the match view onto its framing a search over the CAMERA rather than a
// temptation to bend the geometry until the numbers agree.
view.azimuth = num('az', view.azimuth);
view.elevation = num('el', view.elevation);
placeCamera(view.azimuth, view.elevation, view.zoom);

// ---------------------------------------------------------------- articulation
const restPositions = new Map<string, THREE.Vector3>();
for (const [id, node] of Object.entries(runtime.nodes)) {
  restPositions.set(id, node.position.clone());
}

function setJaw(open: number): void {
  const node = runtime.nodes['slide-carriage'];
  if (!node) return;
  const rest = restPositions.get('slide-carriage');
  if (rest) node.position.x = rest.x + open * JAW_TRAVEL;
  // The screw advances with the jaw, so it spins by the thread pitch it travelled.
  const screw = runtime.nodes['lead-screw-shaft'];
  if (screw) screw.rotation.y = (open * JAW_TRAVEL) / 0.068 * Math.PI * 2;
}

function setSwivel(deg: number): void {
  const node = runtime.nodes['swivel-collar'];
  if (node) node.rotation.y = THREE.MathUtils.degToRad(deg);
}

// Explode by SCALING the layout about the assembly centre, not by pushing every part the
// same distance. A constant push translates the arrangement without opening any gap between
// neighbouring parts, so parts that sit close together stay fused-looking however far the
// whole thing travels.
const restWorld = new Map<string, THREE.Vector3>();
const explodeCentre = new THREE.Box3().setFromObject(model).getCenter(new THREE.Vector3());
{
  const world = new THREE.Vector3();
  for (const [id, node] of Object.entries(runtime.nodes)) {
    node.getWorldPosition(world);
    restWorld.set(id, world.clone());
  }
}

function setExplode(amount: number): void {
  const target = new THREE.Vector3();
  // Parents first: a child's local position is resolved against the parent's already-moved
  // matrix, so walking the tree in any other order feeds a stale parent transform.
  const ordered = Object.entries(runtime.nodes).sort(
    (a, b) => depthOf(a[1]) - depthOf(b[1]),
  );
  for (const [id, node] of ordered) {
    const rest = restPositions.get(id);
    const world = restWorld.get(id);
    if (!rest || !world) continue;
    if (amount === 0) { node.position.copy(rest); continue; }
    target.copy(explodeCentre).addScaledVector(
      world.clone().sub(explodeCentre), 1 + amount * 1.35,
    );
    node.parent?.updateWorldMatrix(true, false);
    node.position.copy(node.parent ? node.parent.worldToLocal(target.clone()) : target);
  }
  if (amount === 0) setJaw(jawValue);
}

function depthOf(node: THREE.Object3D): number {
  let depth = 0;
  for (let p = node.parent; p; p = p.parent) depth += 1;
  return depth;
}

// 0 = the reference's own jaw opening, which is what every review render must
// reproduce; the slider opens FURTHER from there.
let jawValue = THREE.MathUtils.clamp(num('jaw', 0), 0, 1);
setJaw(jawValue);
setSwivel(num('swivel', 0));
setExplode(THREE.MathUtils.clamp(num('explode', 0), 0, 1));

// ---------------------------------------------------------------- UI
const ui = document.getElementById('ui') as HTMLDivElement;
if (params.get('ui') !== '0') {
  ui.hidden = false;
  bindUI();
}

function bindUI(): void {
  const jaw = document.getElementById('jaw') as HTMLInputElement;
  const swivel = document.getElementById('swivel') as HTMLInputElement;
  const explode = document.getElementById('explode') as HTMLInputElement;
  const lighting = document.getElementById('lighting') as HTMLSelectElement;
  const outJaw = document.getElementById('out-jaw') as HTMLOutputElement;
  const outSwivel = document.getElementById('out-swivel') as HTMLOutputElement;
  const outExplode = document.getElementById('out-explode') as HTMLOutputElement;

  jaw.value = String(jawValue);
  swivel.value = String(num('swivel', 0));
  explode.value = String(num('explode', 0));
  lighting.value = params.get('light') ?? 'reference';

  const sync = () => {
    outJaw.textContent = `${(Number(jaw.value) * JAW_TRAVEL * 100).toFixed(0)} mm`;
    outSwivel.textContent = `${swivel.value}°`;
    outExplode.textContent = Number(explode.value).toFixed(2);
  };
  jaw.oninput = () => { jawValue = Number(jaw.value); setJaw(jawValue); sync(); };
  swivel.oninput = () => { setSwivel(Number(swivel.value)); sync(); };
  explode.oninput = () => { setExplode(Number(explode.value)); sync(); };
  lighting.onchange = () => setLighting(lighting.value as 'reference' | 'neutral' | 'grazing');
  sync();

  const label = document.getElementById('pass-label') as HTMLSpanElement;
  const evidence = model.userData.reconstructionEvidence as { buildPass?: string } | undefined;
  label.textContent = evidence?.buildPass ?? 'unknown pass';

  let triangles = 0;
  model.traverse((child) => {
    const mesh = child as THREE.Mesh;
    if (!mesh.isMesh) return;
    const index = mesh.geometry.getIndex();
    const count = index ? index.count : mesh.geometry.getAttribute('position').count;
    triangles += (count / 3) * ((mesh as THREE.InstancedMesh).count ?? 1);
  });
  (document.getElementById('stats') as HTMLDivElement).textContent =
    `${Object.keys(runtime.nodes).length} parts · ${Math.round(triangles).toLocaleString()} triangles`;

  const picked = document.getElementById('picked') as HTMLDivElement;
  const raycaster = new THREE.Raycaster();
  renderer.domElement.addEventListener('pointerdown', (event) => {
    const rect = renderer.domElement.getBoundingClientRect();
    raycaster.setFromCamera(new THREE.Vector2(
      ((event.clientX - rect.left) / rect.width) * 2 - 1,
      -((event.clientY - rect.top) / rect.height) * 2 + 1,
    ), camera);
    const hit = raycaster.intersectObject(model, true)[0];
    if (!hit) { picked.textContent = 'Click a part to identify it.'; return; }
    const spec = hit.object.userData.sculptComponent as
      { name?: string; level?: string; material?: string } | undefined;
    picked.innerHTML = spec
      ? `<b>${spec.name}</b><br>${spec.level} · ${spec.material}`
      : `<b>${hit.object.name}</b>`;
  });
}

function setLighting(mode: 'reference' | 'neutral' | 'grazing'): void {
  scene.remove(lights);
  lights = createLookDevLights(mode);
  tuneLights(lights);
  scene.add(lights);
}
setLighting((params.get('light') as 'reference' | 'neutral' | 'grazing') ?? 'reference');

// ---------------------------------------------------------------- helpers
function tuneLights(group: THREE.Group): void {
  // The generated shadow camera is sized for a unit-scale object; this model is 4.4 units
  // long, so without widening it the base's contact shadow is clipped mid-plate.
  group.traverse((child) => {
    const hemi = child as THREE.HemisphereLight;
    // The generated hemisphere light is sized for a scene with no environment map; on top of
    // one it flattens the shaded flank the reference clearly shows.
    if (hemi.isHemisphereLight) {
      hemi.intensity *= 0.45;
      hemi.color.setHex(0xf7f5f1);
      hemi.groundColor.setHex(0x45423e);
    }
    const light = child as THREE.DirectionalLight;
    if (!light.isDirectionalLight) return;
    // Measured on the reference: its shadow reaches only about X 2.4 while the object runs to
    // X 3.2, so it is a short contact smudge under the base, not a cast silhouette of the whole
    // vise. That means a steep key. At the generated 48-degree elevation the render threw a
    // shadow half the object's length, and the Tier-1 mask read it as part of the object --
    // aspect delta 0.181 against a 0.05 threshold, entirely from the shadow.
    if (light.castShadow) light.position.set(-1.3, 11.0, 2.2);
    // The 'reference' look-dev mode ships a warm tungsten key (0xffcf8a). This reference is a
    // neutral studio plate -- its greys are achromatic to within a couple of points -- so a warm
    // key tints every casting brown and the finish separation stops reading as metal.
    light.color.setHex(light.intensity > 1 ? 0xfffcf6 : 0xf6f3ee);
    light.position.multiplyScalar(MODEL_LENGTH * 0.6);
    if (!light.castShadow) return;
    light.shadow.radius = 14;
    light.shadow.blurSamples = 32;
    const cam = light.shadow.camera;
    cam.left = -MODEL_LENGTH * 0.8;
    cam.right = MODEL_LENGTH * 0.8;
    cam.top = MODEL_LENGTH * 0.8;
    cam.bottom = -MODEL_LENGTH * 0.8;
    cam.far = MODEL_LENGTH * 12;
    cam.updateProjectionMatrix();
  });
}

function backdropTexture(): THREE.Texture {
  const c = document.createElement('canvas');
  c.width = 4;
  c.height = 256;
  const ctx = c.getContext('2d')!;
  const grad = ctx.createLinearGradient(0, 0, 0, 256);
  grad.addColorStop(0.0, '#f7f8f9');
  grad.addColorStop(0.62, '#eceef0');
  grad.addColorStop(1.0, '#dcdfe2');
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, 4, 256);
  const texture = new THREE.CanvasTexture(c);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.mapping = THREE.EquirectangularReflectionMapping;
  return texture;
}

function placeCamera(azimuthDeg: number, elevationDeg: number, zoom: number): void {
  const box = new THREE.Box3().setFromObject(model);
  const size = box.getSize(new THREE.Vector3());
  const centre = box.getCenter(new THREE.Vector3());
  const fov = (camera.fov * Math.PI) / 180;
  const fitH = size.y / (2 * Math.tan(fov / 2));
  const fitW = size.x / (2 * Math.tan(fov / 2) * camera.aspect);
  const distance = (Math.max(fitH, fitW) + size.z * 0.5) * 1.16 / zoom;
  const az = THREE.MathUtils.degToRad(azimuthDeg);
  const el = THREE.MathUtils.degToRad(elevationDeg);
  // Sub-pixel framing nudges, in fractions of the frame, so a match view can be converged
  // onto the reference's bounding box without moving the model itself.
  centre.x += size.x * num('panx', view.panX ?? 0);
  centre.y += size.y * num('pany', view.panY ?? 0);
  camera.position.set(
    centre.x + Math.sin(az) * Math.cos(el) * distance,
    centre.y + Math.sin(el) * distance,
    centre.z + Math.cos(az) * Math.cos(el) * distance,
  );
  controls.target.copy(centre);
  camera.near = Math.max(0.05, distance - size.length());
  camera.far = distance + size.length() * 3;
  camera.updateProjectionMatrix();
  controls.update();
}

function resize(): void {
  const width = canvas.clientWidth || innerWidth;
  const height = canvas.clientHeight || innerHeight;
  renderer.setSize(width, height, false);
  camera.aspect = width / height;
  placeCamera(view.azimuth, view.elevation, view.zoom);
}
addEventListener('resize', resize);
resize();

renderer.setAnimationLoop(() => {
  if (interactive) controls.update();
  renderer.render(scene, camera);
});

// The capture script waits on this rather than on a fixed timeout: a screenshot taken
// before the first frame is a black PNG that every gate then scores as a real render.
renderer.render(scene, camera);
// Handles for tools/export_geometry.mjs: the reference-free gates must measure what
// actually renders, not what the spec claims it will render.
Object.assign(window as unknown as Record<string, unknown>, {
  __VISE_READY__: true,
  __VISE_MODEL__: model,
  __THREE__: THREE,
});
