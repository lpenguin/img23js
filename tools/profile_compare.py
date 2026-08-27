#!/usr/bin/env python3
"""Compare two silhouettes as normalized outline profiles.

Both images are reduced to their largest connected foreground component, then each is sampled
on its OWN bounding box in relative coordinates. That removes framing, scale and position from
the comparison and leaves shape: a difference here is a shape difference, not a camera one.
"""
import argparse, sys
from collections import deque
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from silhouette_metrics import read_png  # noqa: E402


def object_mask(path: Path, threshold: float):
    w, h, px = read_png(path)
    lum = lambda p: 0.2126 * p[0] + 0.7152 * p[1] + 0.0722 * p[2]
    mask = bytearray(w * h)
    for y in range(h):
        row, base = px[y], y * w
        for x in range(w):
            if lum(row[x]) < threshold:
                mask[base + x] = 1
    seen = bytearray(w * h)
    best = None
    for start in range(w * h):
        if not mask[start] or seen[start]:
            continue
        q = deque([start]); seen[start] = 1; comp = [start]
        while q:
            i = q.popleft(); x, y = i % w, i // w
            for j in ((i - 1 if x else -1), (i + 1 if x < w - 1 else -1),
                      (i - w if y else -1), (i + w if y < h - 1 else -1)):
                if j >= 0 and mask[j] and not seen[j]:
                    seen[j] = 1; q.append(j); comp.append(j)
        if best is None or len(comp) > len(best):
            best = comp
    obj = bytearray(w * h)
    for i in best:
        obj[i] = 1
    xs = [i % w for i in best]; ys = [i // w for i in best]
    return obj, w, h, min(xs), max(xs), min(ys), max(ys)


def row_edges(obj, w, box, v):
    x0, x1, y0, y1 = box
    y = int(round(y0 + v * (y1 - y0)))
    base = y * w
    left = right = None
    for x in range(x0, x1 + 1):
        if obj[base + x]:
            if left is None:
                left = x
            right = x
    if left is None:
        return None
    span = (x1 - x0) or 1
    return (left - x0) / span, (right - x0) / span


def col_edges(obj, w, box, u):
    x0, x1, y0, y1 = box
    x = int(round(x0 + u * (x1 - x0)))
    top = bottom = None
    for y in range(y0, y1 + 1):
        if obj[y * w + x]:
            if top is None:
                top = y
            bottom = y
    if top is None:
        return None
    span = (y1 - y0) or 1
    return (top - y0) / span, (bottom - y0) / span


ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("reference", type=Path)
ap.add_argument("render", type=Path)
ap.add_argument("--threshold", type=float, default=200.0)
ap.add_argument("--steps", type=int, default=16)
args = ap.parse_args()

a = object_mask(args.reference, args.threshold)
b = object_mask(args.render, args.threshold)
for name, m in (("reference", a), ("render", b)):
    _, _, _, x0, x1, y0, y1 = m
    print(f"{name:9s} bbox {x1-x0+1}x{y1-y0+1} aspect {(x1-x0+1)/(y1-y0+1):.4f}")

print("\nrow  v      ref[left,right]     render[left,right]   d_left  d_right")
for i in range(args.steps + 1):
    v = i / args.steps
    ra = row_edges(a[0], a[1], a[3:], v)
    rb = row_edges(b[0], b[1], b[3:], v)
    if not ra or not rb:
        continue
    print(f"    {v:4.2f}  [{ra[0]:.3f},{ra[1]:.3f}]      [{rb[0]:.3f},{rb[1]:.3f}]"
          f"      {rb[0]-ra[0]:+.3f}  {rb[1]-ra[1]:+.3f}")

print("\ncol  u      ref[top,bottom]     render[top,bottom]   d_top   d_bottom")
for i in range(args.steps + 1):
    u = i / args.steps
    ca = col_edges(a[0], a[1], a[3:], u)
    cb = col_edges(b[0], b[1], b[3:], u)
    if not ca or not cb:
        continue
    print(f"    {u:4.2f}  [{ca[0]:.3f},{ca[1]:.3f}]      [{cb[0]:.3f},{cb[1]:.3f}]"
          f"      {cb[0]-ca[0]:+.3f}  {cb[1]-ca[1]:+.3f}")
