#!/usr/bin/env python3
"""Render cover and deterministic relationship diagrams from context.json."""

from __future__ import annotations

import argparse
import json
from math import atan2, cos, pi, sin
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont


SKILL_ROOT = Path(__file__).resolve().parent.parent
SERIF_CANDIDATES = [
    SKILL_ROOT / "assets/fonts/SourceHanSerifCN-Bold.otf",
    Path.home() / "Library/Fonts/SOURCEHANSERIFCN-BOLD-2.OTF",
    Path("/System/Library/Fonts/Supplemental/Songti.ttc"),
]


def font_path() -> Path:
    for path in SERIF_CANDIDATES:
        if path.exists():
            return path
    raise FileNotFoundError("未找到粗宋体；请把思源宋体 Bold 放入 assets/fonts/")


def fnt(size: int, index: int = 0) -> ImageFont.FreeTypeFont:
    path = font_path()
    if path.suffix.lower() == ".ttc":
        return ImageFont.truetype(str(path), size, index=1)
    return ImageFont.truetype(str(path), size)


def rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def rgba(value: str, alpha: int) -> tuple[int, int, int, int]:
    return (*rgb(value), alpha)


def crop_resize(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    image = image.convert("RGB")
    w, h = image.size
    tw, th = size
    scale = max(tw / w, th / h)
    nw, nh = round(w * scale), round(h * scale)
    image = image.resize((nw, nh), Image.Resampling.LANCZOS)
    return image.crop(((nw - tw) // 2, (nh - th) // 2, (nw + tw) // 2, (nh + th) // 2))


def fit_font(draw: ImageDraw.ImageDraw, text: str, max_width: int, start: int, minimum: int = 38) -> ImageFont.FreeTypeFont:
    for size in range(start, minimum - 1, -2):
        font = fnt(size)
        if draw.textbbox((0, 0), text, font=font)[2] <= max_width:
            return font
    return fnt(minimum)


def centered(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str, font: ImageFont.FreeTypeFont, fill: str) -> None:
    x1, y1, x2, y2 = box
    bb = draw.textbbox((0, 0), text, font=font)
    draw.text((x1 + (x2 - x1 - (bb[2] - bb[0])) / 2, y1 + (y2 - y1 - (bb[3] - bb[1])) / 2 - bb[1]), text, font=font, fill=fill)


def arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], fill: str, width: int = 4) -> None:
    draw.line((*start, *end), fill=fill, width=width)
    angle = atan2(end[1] - start[1], end[0] - start[0])
    size = 16
    points = [end, (end[0] - size * cos(angle - pi / 7), end[1] - size * sin(angle - pi / 7)), (end[0] - size * cos(angle + pi / 7), end[1] - size * sin(angle + pi / 7))]
    draw.polygon(points, fill=fill)


def fallback_background(size: tuple[int, int], palette: dict) -> Image.Image:
    w, h = size
    image = Image.new("RGB", size, palette["dark"])
    draw = ImageDraw.Draw(image, "RGBA")
    for i in range(16):
        y = int(h * 0.45 + i * 24)
        draw.arc((w * 0.36 - i * 28, y - 120, w * 1.08 + i * 30, y + 260), 190, 350, fill=rgba(palette["accent"], 45), width=3)
    draw.ellipse((w - 330, 55, w - 185, 200), fill=rgba(palette["gold"], 190))
    return image


def render_cover(context: dict, background: Path | None, output: Path) -> None:
    size = (1410, 600)
    palette = context["palette"]
    if background and background.exists():
        image = crop_resize(Image.open(background), size)
        image = ImageEnhance.Color(image).enhance(0.9)
    else:
        image = fallback_background(size, palette)
    image = image.convert("RGBA")
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay, "RGBA")
    draw.rectangle((0, 0, 790, 600), fill=rgba(palette["dark"], 232))
    draw.rectangle((0, 0, 920, 600), fill=(0, 0, 0, 40))
    draw.rectangle((18, 18, 1392, 582), outline=rgba(palette["gold"], 220), width=2)
    draw.rectangle((36, 36, 1374, 564), outline=rgba(palette["gold"], 100), width=1)
    image = Image.alpha_composite(image, overlay)
    draw = ImageDraw.Draw(image)
    gold, white, accent = palette["gold"], "#FFFDF8", palette["accent"]
    draw.text((72, 68), f"AuraMate  |  {context['month_pillar']}月", font=fnt(28), fill=gold)
    draw.line((72, 118, 238, 118), fill=gold, width=4)
    title = context["cover_title"]
    title_font = fit_font(draw, title, 720, 78, 48)
    draw.text((70, 190), title, font=title_font, fill=white)
    draw.text((74, 335), context["cover_subtitle"], font=fit_font(draw, context["cover_subtitle"], 650, 37, 28), fill=gold)
    draw.text((74, 393), context["cover_tagline"], font=fit_font(draw, context["cover_tagline"], 620, 35, 26), fill=accent)
    draw.line((72, 490, 215, 490), fill=gold, width=4)
    if context.get("date_range"):
        draw.text((72, 515), context["date_range"], font=fnt(27), fill=white)
    image.convert("RGB").save(output, quality=94, optimize=True)


def frame(draw: ImageDraw.ImageDraw, width: int, height: int, palette: dict) -> None:
    draw.rectangle((28, 28, width - 28, height - 28), outline=palette["gold"], width=4)
    draw.rectangle((48, 48, width - 48, height - 48), outline=rgba(palette["gold"], 100), width=1)


def render_energy(context: dict, output: Path) -> None:
    w, h = 1080, 1450
    p = context["palette"]
    image = Image.new("RGBA", (w, h), p["dark"])
    draw = ImageDraw.Draw(image, "RGBA")
    frame(draw, w, h, p)
    draw.text((78, 82), f"{context['month_pillar']}月能量结构", font=fnt(52), fill=p["gold"])
    draw.text((82, 150), "月干在外，月支在内，藏干是支内暗线", font=fnt(27), fill=p["accent"])

    draw.rounded_rectangle((340, 235, 740, 385), radius=24, fill=rgba(p["primary"], 55), outline=p["gold"], width=3)
    centered(draw, (340, 250, 740, 315), f"{context['month_stem']} · {context['month_stem_ten_god']}", fnt(39), "#FFFFFF")
    centered(draw, (340, 315, 740, 370), "流月天干：外显主题", fnt(23), p["accent"])
    arrow(draw, (540, 390), (540, 468), p["gold"], 5)

    draw.rounded_rectangle((82, 485, 998, 910), radius=28, fill=rgba(p["primary"], 42), outline=p["accent"], width=3)
    draw.text((120, 520), f"月支：{context['month_branch']}", font=fnt(40), fill="#FFFFFF")
    draw.text((120, 578), "内部藏干（主气在前）", font=fnt(25), fill=p["accent"])
    hidden = context["hidden_stems"]
    box_width = 250
    gap = 34
    total = len(hidden) * box_width + (len(hidden) - 1) * gap
    x = (w - total) // 2
    for item in hidden:
        draw.rounded_rectangle((x, 660, x + box_width, 815), radius=20, fill=rgba(p["dark"], 235), outline=p["gold"], width=2)
        centered(draw, (x, 676, x + box_width, 739), item["stem"], fnt(38), "#FFFFFF")
        centered(draw, (x, 740, x + box_width, 795), f"{item['ten_god']} · {item['role']}", fnt(23), p["accent"])
        x += box_width + gap
    draw.text((120, 850), "读图：这些天干属于月支内部，不与流月天干并列。", font=fnt(23), fill="#FFFFFF")
    arrow(draw, (540, 925), (540, 1010), p["accent"], 5)

    draw.rounded_rectangle((330, 1025, 750, 1195), radius=26, fill=rgba(p["primary"], 75), outline=p["gold"], width=3)
    centered(draw, (330, 1040, 750, 1110), f"日主：{context['day_master']}{context['day_master_element']}", fnt(42), "#FFFFFF")
    centered(draw, (330, 1112, 750, 1175), context["cover_tagline"], fnt(26), p["accent"])

    draw.rounded_rectangle((82, 1270, 998, 1375), radius=18, fill=rgba(p["primary"], 45), outline=p["gold"], width=2)
    summary = f"{context['month_stem_ten_god']}在外显题，{hidden[0]['ten_god']}在内托底；其余藏干提示责任与消耗。"
    centered(draw, (105, 1283, 975, 1362), summary, fit_font(draw, summary, 820, 25, 19), "#FFFFFF")
    image.convert("RGB").save(output, quality=93, optimize=True)


def render_relations(context: dict, output: Path) -> None:
    rows = context["branch_relations"]
    w = 1080
    h = max(1060, 330 + len(rows) * 175 + 120)
    p = context["palette"]
    image = Image.new("RGBA", (w, h), p["light"])
    draw = ImageDraw.Draw(image, "RGBA")
    frame(draw, w, h, p)
    draw.text((76, 80), f"{context['month_branch']}月暗线：关系触发提示", font=fnt(49), fill=p["dark"])
    draw.text((80, 148), "先看原局是否具备条件，再看流月如何引动", font=fnt(26), fill=p["text"])
    draw.rounded_rectangle((360, 218, 720, 330), radius=24, fill=p["dark"], outline=p["gold"], width=3)
    centered(draw, (360, 218, 720, 330), f"流月：{context['month_pillar']}", fnt(39), "#FFFFFF")
    y = 385
    for row in rows:
        draw.rounded_rectangle((76, y, 1004, y + 145), radius=20, fill="#FFFFFF", outline=p["primary"], width=2)
        draw.rounded_rectangle((102, y + 30, 280, y + 88), radius=14, fill=p["primary"])
        centered(draw, (102, y + 30, 280, y + 88), row["condition"], fit_font(draw, row["condition"], 150, 23, 18), "#FFFFFF")
        draw.text((326, y + 24), row["relation"], font=fit_font(draw, row["relation"], 620, 31, 23), fill=p["dark"])
        draw.text((326, y + 77), row["meaning"], font=fit_font(draw, row["meaning"], 620, 22, 18), fill=p["text"])
        y += 165
    note = "关系图是触发提示，不替代完整八字、大运与流年判断"
    draw.rounded_rectangle((76, h - 100, 1004, h - 48), radius=16, fill=p["dark"], outline=p["gold"], width=2)
    centered(draw, (76, h - 100, 1004, h - 48), note, fnt(23), "#FFFFFF")
    image.convert("RGB").save(output, quality=93, optimize=True)


def render_pillars(context: dict, output: Path) -> None:
    w, h = 1080, 1560
    p = context["palette"]
    image = Image.new("RGBA", (w, h), p["dark"])
    draw = ImageDraw.Draw(image, "RGBA")
    frame(draw, w, h, p)
    draw.text((76, 82), f"六大{context['day_master']}{context['day_master_element']}日柱速览", font=fnt(50), fill=p["gold"])
    draw.text((80, 150), "图看差异，完整条件与行动建议见正文", font=fnt(26), fill=p["accent"])
    y = 228
    for item in context["day_pillars"]:
        relation = item["month_relation"]
        branch_hidden = "、".join(f"{entry['stem']}·{entry['ten_god']}" for entry in item["hidden_relations"])
        draw.rounded_rectangle((76, y, 1004, y + 185), radius=20, fill=rgba(p["primary"], 42), outline=p["gold"], width=2)
        draw.text((112, y + 30), item["pillar"] + "日", font=fnt(36), fill="#FFFFFF")
        draw.text((330, y + 34), f"与{context['month_branch']}：{relation}", font=fnt(27), fill=p["accent"])
        draw.line((112, y + 92, 968, y + 92), fill=rgba(p["gold"], 130), width=1)
        detail = f"日支藏干：{branch_hidden}｜先看结构，再落到行动。"
        draw.text((112, y + 118), detail, font=fit_font(draw, detail, 850, 24, 18), fill="#FFFFFF")
        y += 205
    image.convert("RGB").save(output, quality=93, optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--context", required=True)
    parser.add_argument("--background")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    context = json.loads(Path(args.context).read_text(encoding="utf-8"))
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    render_cover(context, Path(args.background) if args.background else None, output_dir / "cover.jpg")
    render_energy(context, output_dir / "energy-map.jpg")
    render_relations(context, output_dir / "relation-map.jpg")
    render_pillars(context, output_dir / "pillars-map.jpg")
    print(f"已生成封面和排盘关系图：{output_dir}")


if __name__ == "__main__":
    main()
