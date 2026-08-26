#!/usr/bin/env python3
"""Measure a render's silhouette bounding box and aspect, so a proportion claim in a review
is a number rather than an impression.

Reads the PNG with the same stdlib decoder path forge/ uses (zlib + manual unfilter) so it
needs no PIL. Background is taken from the image corners.
"""
from __future__ import annotations

import argparse
import json
import struct
import sys
import zlib
from pathlib import Path


def read_png(path: Path) -> tuple[int, int, list[list[tuple[int, int, int]]]]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    pos, idat, meta = 8, bytearray(), None
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        ctype = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + length]
        if ctype == b"IHDR":
            meta = struct.unpack(">IIBBBBB", body)
        elif ctype == b"IDAT":
            idat += body
        elif ctype == b"IEND":
            break
        pos += 12 + length
    if meta is None:
        raise ValueError("no IHDR")
    width, height, depth, colour, _, _, interlace = meta
    if depth != 8 or interlace != 0 or colour not in (2, 6):
        raise ValueError(f"unsupported PNG: depth={depth} colour={colour} interlace={interlace}")
    channels = 3 if colour == 2 else 4
    raw = zlib.decompress(bytes(idat))
    stride = width * channels
    out: list[list[tuple[int, int, int]]] = []
    prev = bytearray(stride)
    pos = 0
    for _ in range(height):
        filt = raw[pos]
        line = bytearray(raw[pos + 1:pos + 1 + stride])
        pos += 1 + stride
        for i in range(stride):
            a = line[i - channels] if i >= channels else 0
            b = prev[i]
            c = prev[i - channels] if i >= channels else 0
            if filt == 1:
                line[i] = (line[i] + a) & 0xFF
            elif filt == 2:
                line[i] = (line[i] + b) & 0xFF
            elif filt == 3:
                line[i] = (line[i] + ((a + b) >> 1)) & 0xFF
            elif filt == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pred = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pred) & 0xFF
        out.append([tuple(line[i:i + 3]) for i in range(0, stride, channels)])
        prev = line
    return width, height, out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("render", type=Path)
    ap.add_argument("--tolerance", type=int, default=14,
                    help="per-channel distance from the corner background colour")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    width, height, pixels = read_png(args.render)
    corners = [pixels[0][0], pixels[0][-1], pixels[-1][0], pixels[-1][-1]]
    bg = tuple(sum(c[i] for c in corners) // 4 for i in range(3))

    x0, y0, x1, y1, count = width, height, -1, -1, 0
    for y in range(height):
        row = pixels[y]
        for x in range(width):
            p = row[x]
            if max(abs(p[0] - bg[0]), abs(p[1] - bg[1]), abs(p[2] - bg[2])) <= args.tolerance:
                continue
            count += 1
            if x < x0: x0 = x
            if x > x1: x1 = x
            if y < y0: y0 = y
            if y > y1: y1 = y
    if count == 0:
        print("no foreground found", file=sys.stderr)
        return 2
    bw, bh = x1 - x0 + 1, y1 - y0 + 1
    result = {
        "render": str(args.render), "background": list(bg),
        "bbox": {"x": x0, "y": y0, "width": bw, "height": bh},
        "aspect": round(bw / bh, 4),
        "foregroundPixels": count,
        "fillRatio": round(count / (bw * bh), 4),
        "note": "The shadow is part of the foreground unless it is within tolerance of the "
                "backdrop; check fillRatio before trusting the box on a shadowed render.",
    }
    print(json.dumps(result, indent=2) if args.json else
          f"bbox {bw}x{bh} aspect {result['aspect']} fill {result['fillRatio']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
