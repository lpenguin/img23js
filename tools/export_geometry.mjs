#!/usr/bin/env node
// Export the live scene's measured geometry for the reference-free gates.
//
// The gates must measure what actually renders, not what the spec claims, so this reads the
// real THREE scene graph in a browser rather than re-deriving anything from the spec:
//   --measured  <path>  id -> world position, for attachment_anchor.py
//   --meshes    <path>  per-mesh world-space {vertices, indices}, for self_intersection.py
import { chromium } from 'playwright';
import { writeFile } from 'node:fs/promises';
import { createServer } from 'vite';

const args = process.argv.slice(2);
const opt = (flag, fallback) => { const i = args.indexOf(flag); return i >= 0 ? args[i + 1] : fallback; };
const measuredPath = opt('--measured', 'renders/measured.json');
const meshesPath = opt('--meshes', 'renders/meshes.json');
const manifestPath = opt('--manifest', '');
const query = opt('--query', 'view=front&ui=0');

const server = await createServer({ server: { port: 5198, host: '127.0.0.1' }, logLevel: 'warn' });
await server.listen();
const browser = await chromium.launch({
  executablePath: '/opt/pw-browsers/chromium',
  args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--no-sandbox'],
});
const page = await browser.newPage({ viewport: { width: 800, height: 500 } });
page.on('pageerror', (e) => { console.error('PAGE ERROR:', e.message); process.exitCode = 1; });
await page.goto(`http://127.0.0.1:5198/?${query}`, { waitUntil: 'domcontentloaded', timeout: 120000 });
await page.waitForFunction('window.__VISE_READY__ === true', null, { timeout: 60000 });

const data = await page.evaluate(() => {
  const THREE = window.__THREE__;
  const root = window.__VISE_MODEL__;
  const runtime = root.userData.sculptRuntime;
  root.updateWorldMatrix(true, true);

  const measured = {};
  const v = new THREE.Vector3();
  for (const [id, node] of Object.entries(runtime.nodes)) {
    node.getWorldPosition(v);
    measured[id] = [v.x, v.y, v.z];
  }

  const meshes = [];
  for (const [id, mesh] of Object.entries(runtime.meshes)) {
    const geo = mesh.geometry;
    const pos = geo.getAttribute('position');
    if (!pos) continue;
    // Normals are exported, not left to the gate's centroid fallback. On a long flat slab
    // the centroid-outward direction from a mid-face vertex lies almost IN the face plane, so
    // stepping along it never leaves the surface and the inside/outside parity test returns
    // noise -- which reads as a self-intersection that is not there.
    const nrm = geo.getAttribute('normal');
    const normalMatrix = new THREE.Matrix3().getNormalMatrix(mesh.matrixWorld);
    const n = new THREE.Vector3();
    const vertices = [];
    const normals = [];
    for (let i = 0; i < pos.count; i++) {
      v.set(pos.getX(i), pos.getY(i), pos.getZ(i)).applyMatrix4(mesh.matrixWorld);
      vertices.push([v.x, v.y, v.z]);
      if (nrm) {
        n.set(nrm.getX(i), nrm.getY(i), nrm.getZ(i)).applyMatrix3(normalMatrix).normalize();
        normals.push([n.x, n.y, n.z]);
      }
    }
    const index = geo.getIndex();
    const indices = index ? Array.from(index.array)
      : Array.from({ length: pos.count }, (_, i) => i);
    meshes.push(normals.length ? { name: id, vertices, normals, indices }
                            : { name: id, vertices, indices });
  }
  // Part manifest for check_part_coverage.py. "A part" here is exactly what the viewer's
  // click-picking and explode both act on -- a named pivot node with its own mesh -- so the
  // structure gate scores the same definition the interaction does. Any mesh with no name is
  // counted separately rather than quietly folded into a neighbour.
  const parts = [];
  let unnamedMeshes = 0;
  let integralMeshes = 0;
  for (const [id, mesh] of Object.entries(runtime.meshes)) {
    const geo = mesh.geometry;
    const index = geo.getIndex();
    const posAttr = geo.getAttribute('position');
    const triangles = Math.round((index ? index.count : (posAttr ? posAttr.count : 0)) / 3);
    if (!mesh.name) { unnamedMeshes += 1; continue; }
    const component = mesh.userData.sculptComponent || {};
    parts.push({ name: id, label: mesh.name, kind: 'part',
                 module: component.parent || 'root', level: component.level || 'macro',
                 triangles });
  }
  root.traverse((child) => {
    if (child.isInstancedMesh) integralMeshes += 1;
  });
  return { measured, meshes, manifest: { model: root.name, parts, unnamedMeshes, integralMeshes } };
});

await writeFile(measuredPath, JSON.stringify(data.measured, null, 1));
await writeFile(meshesPath, JSON.stringify({ meshes: data.meshes }));
console.log(`${measuredPath}  ${Object.keys(data.measured).length} nodes`);
console.log(`${meshesPath}  ${data.meshes.length} meshes`);
if (manifestPath) {
  await writeFile(manifestPath, JSON.stringify(data.manifest, null, 1));
  console.log(`${manifestPath}  ${data.manifest.parts.length} named parts, `
    + `${data.manifest.unnamedMeshes} unnamed, ${data.manifest.integralMeshes} instanced`);
}
await browser.close();
await server.close();
process.exit(0);
