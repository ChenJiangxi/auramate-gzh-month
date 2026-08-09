#!/usr/bin/env python3
"""Blur private or mismatched sample data while preserving a real product UI."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


def parse_box(value: str) -> tuple[int, int, int, int]:
    parts = [int(item) for item in value.split(",")]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("box 格式应为 x1,y1,x2,y2")
    return tuple(parts)  # type: ignore[return-value]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("output")
    parser.add_argument("--box", action="append", type=parse_box, required=True)
    parser.add_argument("--radius", type=int, default=12)
    args = parser.parse_args()
    image = Image.open(args.input).convert("RGBA")
    for box in args.box:
        region = image.crop(box).filter(ImageFilter.GaussianBlur(args.radius))
        image.paste(region, box)
        veil = Image.new("RGBA", image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(veil)
        draw.rounded_rectangle(box, radius=12, fill=(255, 255, 255, 54), outline=(140, 170, 190, 110), width=2)
        image = Image.alpha_composite(image, veil)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(output, quality=92, optimize=True)
    print(f"已输出遮罩截图：{output}")


if __name__ == "__main__":
    main()
