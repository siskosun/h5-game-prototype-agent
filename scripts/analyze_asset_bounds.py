#!/usr/bin/env python3
from __future__ import annotations
import json
import sys
from pathlib import Path

try:
    from PIL import Image
except Exception:
    print("ERROR: Pillow is required: python -m pip install Pillow")
    raise SystemExit(2)


def main() -> int:
    args = sys.argv[1:]
    if not args or len(args) > 3:
        print("usage: analyze_asset_bounds.py <image.png> [alpha-threshold-0..255] [--require-visible]")
        return 2

    require_visible = "--require-visible" in args
    args = [a for a in args if a != "--require-visible"]
    if len(args) not in (1, 2):
        print("usage: analyze_asset_bounds.py <image.png> [alpha-threshold-0..255] [--require-visible]")
        return 2

    path = Path(args[0])
    threshold = int(args[1]) if len(args) == 2 else 1
    if not 0 <= threshold <= 255:
        print("ERROR: alpha threshold must be 0..255")
        return 2
    if not path.exists():
        print(f"ERROR: missing file: {path}")
        return 2

    with Image.open(path) as im:
        rgba = im.convert("RGBA")
        alpha = rgba.getchannel("A")
        hist = alpha.histogram()
        mask = alpha.point(lambda a: 255 if a >= threshold else 0)
        bbox = mask.getbbox()
        w, h = rgba.size
        total = w * h
        visible_pixels = sum(hist[threshold:]) if total else 0
        alpha_sum = sum(i * count for i, count in enumerate(hist))
        alpha_mean = (alpha_sum / (255 * total)) if total else 0.0
        result = {
            "fileBytes": path.stat().st_size,
            "canvasWidth": w,
            "canvasHeight": h,
            "alphaMean": round(alpha_mean, 6),
            "nonTransparentPixels": visible_pixels,
            "nonTransparentRatio": round(visible_pixels / total, 6) if total else 0.0,
        }
        if bbox is None:
            result.update({"visibleBounds": None, "coverage": 0.0})
        else:
            left, top, right, bottom = bbox
            vw, vh = right - left, bottom - top
            result.update({
                "visibleBounds": {"x": left, "y": top, "width": vw, "height": vh},
                "coverage": round((vw * vh) / total, 6) if total else 0.0,
                "visibleCenterNormalized": [
                    round((left + vw / 2) / w, 6),
                    round((top + vh / 2) / h, 6),
                ],
                "recommendedAnchorHint": [0.5, 0.0],
            })
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if require_visible and (bbox is None or visible_pixels == 0):
            print("ERROR: image has no visible pixels at the requested alpha threshold", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
