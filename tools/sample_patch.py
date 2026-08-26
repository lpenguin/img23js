#!/usr/bin/env python3
"""Mean sRGB of a rectangular patch of a render, so a tone claim is a number.

Usage: sample_patch.py render.png x,y,w,h [more patches...]
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from silhouette_metrics import read_png  # noqa: E402

path = Path(sys.argv[1])
_, _, px = read_png(path)
for spec in sys.argv[2:]:
    x, y, w, h = (int(v) for v in spec.split(","))
    total = [0, 0, 0]
    n = 0
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            p = px[yy][xx]
            for i in range(3):
                total[i] += p[i]
            n += 1
    print(f"{spec}: rgb({total[0] // n}, {total[1] // n}, {total[2] // n})")
