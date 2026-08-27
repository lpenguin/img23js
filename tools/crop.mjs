#!/usr/bin/env node
// Crop a region out of an image (and optionally upscale it) through Chromium, so reference
// detail can be inspected at the resolution it was actually captured at.
//   node tools/crop.mjs <src> <out.png> x,y,w,h [scale]
import { chromium } from 'playwright';
import { readFile, writeFile } from 'node:fs/promises';

const [src, out, box, scaleArg] = process.argv.slice(2);
const [x, y, w, h] = box.split(',').map(Number);
const scale = Number(scaleArg || 1);
const ext = src.split('.').pop();
const dataUrl = `data:image/${ext === 'webp' ? 'webp' : 'png'};base64,${(await readFile(src)).toString('base64')}`;
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium', args: ['--no-sandbox'] });
const page = await browser.newPage();
const png = await page.evaluate(async ([url, x, y, w, h, s]) => {
  const img = new Image();
  img.src = url;
  await img.decode();
  const c = document.createElement('canvas');
  c.width = Math.round(w * s);
  c.height = Math.round(h * s);
  const ctx = c.getContext('2d');
  ctx.imageSmoothingEnabled = s < 1;
  ctx.drawImage(img, x, y, w, h, 0, 0, c.width, c.height);
  return c.toDataURL('image/png').split(',')[1];
}, [dataUrl, x, y, w, h, scale]);
await writeFile(out, Buffer.from(png, 'base64'));
console.log(out);
await browser.close();
process.exit(0);
