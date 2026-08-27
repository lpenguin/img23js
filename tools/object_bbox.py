#!/usr/bin/env python3
"""Bounding box of the largest connected foreground component.

A plain threshold bbox is the union of the object, its cast shadow and any corner artifact in
the plate; the object is the largest connected component, so that is what gets measured.
"""
import argparse, json, sys
from collections import deque
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from silhouette_metrics import read_png  # noqa: E402

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("image", type=Path)
ap.add_argument("--threshold", type=float, default=200.0, help="luminance below this is foreground")
ap.add_argument("--json", action="store_true")
args = ap.parse_args()

w, h, px = read_png(args.image)
lum = lambda p: 0.2126 * p[0] + 0.7152 * p[1] + 0.0722 * p[2]
mask = bytearray(w * h)
for y in range(h):
    row, base = px[y], y * w
    for x in range(w):
        if lum(row[x]) < args.threshold:
            mask[base + x] = 1

seen = bytearray(w * h)
best = None
for start in range(w * h):
    if not mask[start] or seen[start]:
        continue
    q = deque([start]); seen[start] = 1
    x0 = x1 = start % w; y0 = y1 = start // w; n = 0
    while q:
        i = q.popleft(); n += 1
        x, y = i % w, i // w
        x0, x1, y0, y1 = min(x0, x), max(x1, x), min(y0, y), max(y1, y)
        for j in ((i - 1 if x else -1), (i + 1 if x < w - 1 else -1),
                  (i - w if y else -1), (i + w if y < h - 1 else -1)):
            if j >= 0 and mask[j] and not seen[j]:
                seen[j] = 1; q.append(j)
    if best is None or n > best[0]:
        best = (n, x0, x1, y0, y1)

n, x0, x1, y0, y1 = best
bw, bh = x1 - x0 + 1, y1 - y0 + 1
out = {"image": str(args.image), "frame": [w, h],
       "bbox": {"x": x0, "y": y0, "width": bw, "height": bh},
       "aspect": round(bw / bh, 4), "pixels": n, "fill": round(n / (bw * bh), 4),
       "centreNorm": [round((x0 + x1) / 2 / w, 4), round((y0 + y1) / 2 / h, 4)],
       "widthNorm": round(bw / w, 4), "heightNorm": round(bh / h, 4)}
print(json.dumps(out, indent=2) if args.json else
      f"bbox {bw}x{bh} at ({x0},{y0}) aspect {out['aspect']} "
      f"widthNorm {out['widthNorm']} heightNorm {out['heightNorm']} centre {out['centreNorm']}")
