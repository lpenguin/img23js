#!/usr/bin/env node
// Headless capture for the review gates. Every shot goes through the same URL contract the
// interactive page uses, so a gate never scores a render a person could not reproduce.
//
//   node tools/capture.mjs [--out renders] [--width 1400] [--height 800] shot=<query> ...
//
// A shot argument is "<name>=<query string>", e.g. front=view=front&light=reference.
import { chromium } from 'playwright';
import { mkdir } from 'node:fs/promises';
import { createServer } from 'vite';

const args = process.argv.slice(2);
const opt = (flag, fallback) => {
  const i = args.indexOf(flag);
  return i >= 0 ? args[i + 1] : fallback;
};
const outDir = opt('--out', 'renders');
const width = Number(opt('--width', 1400));
const height = Number(opt('--height', 800));
const shots = args.filter((a) => a.includes('=') && !a.startsWith('--'))
  .map((a) => {
    const at = a.indexOf('=');
    return { name: a.slice(0, at), query: a.slice(at + 1) };
  });
if (shots.length === 0) shots.push({ name: 'front', query: 'view=front&light=reference' });

await mkdir(outDir, { recursive: true });
const server = await createServer({ server: { port: 5199, host: '127.0.0.1' }, logLevel: 'warn' });
await server.listen();
const base = `http://127.0.0.1:5199/`;

const browser = await chromium.launch({
  executablePath: '/opt/pw-browsers/chromium',
  args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--no-sandbox'],
});
const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 1 });
page.on('pageerror', (e) => { console.error('PAGE ERROR:', e.message); process.exitCode = 1; });
page.on('console', (m) => { if (m.type() === 'error') console.error('CONSOLE:', m.text()); });

for (const shot of shots) {
  const url = `${base}?${shot.query}&ui=0`;
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 120000 });
  await page.waitForFunction('window.__VISE_READY__ === true', null, { timeout: 60000 });
  // Two extra rAF ticks: the first frame is drawn before OrbitControls damping settles the
  // camera, and a shot taken there is framed a few pixels off from every later shot.
  await page.evaluate(() => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r))));
  const path = `${outDir}/${shot.name}.png`;
  await page.screenshot({ path, omitBackground: false });
  console.log(`${path}  <-  ${url}`);
}

await browser.close();
await server.close();

process.exit(0);
