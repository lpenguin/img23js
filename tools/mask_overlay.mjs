#!/usr/bin/env node
// Colour-coded silhouette difference: where does the render's outline leave the reference's?
//   magenta = reference only (missing geometry)   cyan = render only (extra geometry)
//   grey    = both                                white = neither
// Drawn in the browser so it needs no image library, and written as a PNG for inspection.
import { chromium } from 'playwright';
import { readFile, writeFile } from 'node:fs/promises';

const [refPath, rndPath, outPath, thrArg] = process.argv.slice(2);
const thr = Number(thrArg || 190);
const b64 = async (p) => `data:image/png;base64,${(await readFile(p)).toString('base64')}`;
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium', args: ['--no-sandbox'] });
const page = await browser.newPage();
const png = await page.evaluate(async ([a, b, t]) => {
  const load = async (src) => { const i = new Image(); i.src = src; await i.decode(); return i; };
  const [ia, ib] = [await load(a), await load(b)];
  const w = Math.max(ia.naturalWidth, ib.naturalWidth);
  const h = Math.max(ia.naturalHeight, ib.naturalHeight);
  const grab = (img) => {
    const c = document.createElement('canvas'); c.width = w; c.height = h;
    const x = c.getContext('2d'); x.fillStyle = '#fff'; x.fillRect(0, 0, w, h);
    x.drawImage(img, 0, 0);
    return x.getImageData(0, 0, w, h).data;
  };
  const [da, db] = [grab(ia), grab(ib)];
  const out = document.createElement('canvas'); out.width = w; out.height = h;
  const ctx = out.getContext('2d');
  const img = ctx.createImageData(w, h);
  const lum = (d, i) => 0.2126 * d[i] + 0.7152 * d[i + 1] + 0.0722 * d[i + 2];
  for (let i = 0; i < w * h * 4; i += 4) {
    const A = lum(da, i) < t, B = lum(db, i) < t;
    let c;
    if (A && B) c = [150, 152, 156];
    else if (A) c = [214, 60, 160];
    else if (B) c = [40, 175, 200];
    else c = [248, 248, 250];
    img.data[i] = c[0]; img.data[i + 1] = c[1]; img.data[i + 2] = c[2]; img.data[i + 3] = 255;
  }
  ctx.putImageData(img, 0, 0);
  return out.toDataURL('image/png').split(',')[1];
}, [await b64(refPath), await b64(rndPath), thr]);
await writeFile(outPath, Buffer.from(png, 'base64'));
console.log(outPath);
await browser.close();
process.exit(0);
