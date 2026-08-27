#!/usr/bin/env node
// Convert an image to PNG through the pre-installed Chromium, because this container has no
// PIL, no ImageMagick and no dwebp -- and every forge gate reads PNG with a stdlib decoder.
// Decodes at native resolution and writes RGBA PNG with no resampling.
import { chromium } from 'playwright';
import { readFile, writeFile } from 'node:fs/promises';

const [input, output] = process.argv.slice(2);
if (!input || !output) {
  console.error('usage: webp_to_png.mjs <input> <output.png>');
  process.exit(2);
}
const dataUrl = `data:image/webp;base64,${(await readFile(input)).toString('base64')}`;
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium', args: ['--no-sandbox'] });
const page = await browser.newPage();
const png = await page.evaluate(async (url) => {
  const img = new Image();
  img.src = url;
  await img.decode();
  const canvas = document.createElement('canvas');
  canvas.width = img.naturalWidth;
  canvas.height = img.naturalHeight;
  canvas.getContext('2d').drawImage(img, 0, 0);
  return { data: canvas.toDataURL('image/png').split(',')[1], w: canvas.width, h: canvas.height };
}, dataUrl);
await writeFile(output, Buffer.from(png.data, 'base64'));
console.log(`${output}  ${png.w}x${png.h}`);
await browser.close();
process.exit(0);
