#!/usr/bin/env node
/**
 * Render the observation panel that stands in the reference slot of a review sheet.
 *
 * THIS IS NOT THE REFERENCE PHOTO AND MUST NEVER BE PRESENTED AS ONE. The reference for this
 * reconstruction was supplied as a conversation attachment: the agent can see it, but no image
 * file exists on disk, so no pixel comparison and no true side-by-side sheet is possible. What
 * this panel carries is the written record of what the agent measured off that attachment --
 * the same numbers in reference/REFERENCE_ANALYSIS.md -- so the review sheet documents what the
 * comparison was actually made against instead of leaving the slot empty or, far worse, filling
 * it with something that looks like a photograph.
 *
 *   node tools/evidence_panel.mjs --out renders/<pass>/observation-panel.png --pass <id>
 */
import { chromium } from 'playwright';
import { readFile } from 'node:fs/promises';

const args = process.argv.slice(2);
const opt = (flag, fallback) => { const i = args.indexOf(flag); return i >= 0 ? args[i + 1] : fallback; };
const out = opt('--out', 'renders/observation-panel.png');
const passId = opt('--pass', 'blockout');
const width = Number(opt('--width', 1400));
const height = Number(opt('--height', 800));

const spec = JSON.parse(await readFile('object-sculpt-spec.json', 'utf8'));
const sil = spec.silhouette;
const rows = [
  ['overall width : height', '1.95', 'measured on the attachment silhouette, 1300 x 655 px'],
  ['base disc : overall length', '0.36', 'base spans 470 px of 1300'],
  ['jaw opening : overall length', '0.09', 'gap 120 px of 1300'],
  ['screw axis height', '1.30 u', '520 px from the top of a 655 px figure'],
  ['jaw top', '2.22 u', 'y 250 px'],
  ['fixed jaw face', 'x 1.17 u', 'x 1060 px'],
  ['movable jaw face', 'x 1.57 u', 'x 1180 px'],
  ['screw tail free end', 'x -1.10 u', 'x 390 px'],
  ['thread pitch', '0.068 u', '~20 turns over 480 px, +/- 2 turns'],
  ['scale convention', '1 u = 100 mm', 'no scale cue in the reference; 125 mm jaw adopted'],
];
const features = [
  'hooked jaw-riser profile: convex outer face, deep concave inner scallop, broad top fillet',
  'serrated jaw plates standing proud, each with a stepped tab above the riser edge',
  'two separate exposed acme thread runs (long mid run, short -X tail)',
  'knurled thrust ring between the jaw lobe and the handle',
  'ball-ended tommy bar, tilted a few degrees out of image-vertical',
  'four-lobed swivel base with a recessed circular parting seam and a hex lock bolt',
  'chamfered top plateau behind the fixed jaw',
  'four machining finishes in one bare-metal family: casting, machined stock, dark-oxide screw, polished handle',
];

const html = `<!doctype html><meta charset="utf-8"><style>
  *{box-sizing:border-box} html,body{margin:0;width:${width}px;height:${height}px;background:#fbfbfc;
    font:13px/1.5 ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;color:#23262a}
  .wrap{padding:26px 30px}
  .flag{background:#fff3f2;border:1px solid #e6bcb6;border-radius:8px;padding:10px 14px;margin-bottom:18px}
  .flag b{color:#a2372a;letter-spacing:.02em}
  .flag p{margin:5px 0 0;font-size:12px;color:#5d4340}
  h1{font-size:17px;margin:0 0 3px;letter-spacing:-.01em}
  .sub{margin:0 0 16px;font-size:12px;color:#6d747c}
  h2{font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:#6d747c;margin:16px 0 6px}
  table{border-collapse:collapse;width:100%;font-size:12px}
  td{padding:3px 8px 3px 0;border-bottom:1px solid #eceef0;vertical-align:top}
  td.k{width:210px;color:#4a5058} td.v{width:110px;font-variant-numeric:tabular-nums;font-weight:600}
  td.n{color:#868d95}
  ol{margin:0;padding-left:18px;font-size:12px;color:#3b4046} li{margin:2px 0}
  .neg{font-size:12px;color:#3b4046;margin:4px 0 0}
</style><div class="wrap">
  <div class="flag"><b>NOT THE REFERENCE IMAGE.</b>
    <p>The reference was supplied as a conversation attachment and has no file on disk, so no
    pixel comparison, Divine Eye score or true side-by-side sheet is possible for this
    reconstruction. This panel is the written record of what was measured off that attachment by
    agent vision, standing in the reference slot so the review sheet says what the render was
    actually judged against.</p></div>
  <h1>Bench vise &mdash; reference observation record</h1>
  <p class="sub">pass: ${passId} &middot; source: reference/REFERENCE_ANALYSIS.md &middot; frame: +X longitudinal, +Y up, +Z toward camera, 1 unit = 100 mm</p>
  <h2>Measured landmarks</h2>
  <table>${rows.map(([k, v, n]) => `<tr><td class="k">${k}</td><td class="v">${v}</td><td class="n">${n}</td></tr>`).join('')}</table>
  <h2>Identity-defining features the render must show</h2>
  <ol>${features.map((f) => `<li>${f}</li>`).join('')}</ol>
  <h2>Negative spaces</h2>
  ${sil.negativeSpaces.map((n) => `<p class="neg">&bull; ${n}</p>`).join('')}
</div>`;

const browser = await chromium.launch({
  executablePath: '/opt/pw-browsers/chromium',
  args: ['--no-sandbox'],
});
const page = await browser.newPage({ viewport: { width, height } });
await page.setContent(html, { waitUntil: 'load' });
await page.screenshot({ path: out });
console.log(out);
await browser.close();
process.exit(0);
