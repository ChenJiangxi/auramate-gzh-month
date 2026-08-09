#!/usr/bin/env python3
"""Convert structured Markdown into a WeChat-safe inline-style HTML fragment."""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import re
from html import escape
from pathlib import Path


TOKEN_RE = re.compile(r"(\*\*.+?\*\*|==.+?==|\+\+.+?\+\+|`.+?`)")
PLACEHOLDERS = {
    "[[ENERGY_MAP]]": "energy-map.jpg",
    "[[RELATION_MAP]]": "relation-map.jpg",
    "[[PILLARS_MAP]]": "pillars-map.jpg",
    "[[AURAMATE_FORTUNE]]": "auramate-fortune.jpg",
    "[[AURAMATE_KLINE]]": "auramate-kline.jpg",
    "[[AURAMATE_REPORT]]": "auramate-report.jpg",
    "[[AURAMATE_TALENT]]": "auramate-talent.jpg",
    "[[AURAMATE_HEALTH]]": "auramate-health.jpg",
    "[[AURAMATE_MATCH]]": "auramate-match.jpg",
    "[[AURAMATE_MBTI]]": "auramate-mbti.jpg",
}
EN_LABELS = {
    "底层": "BASE LOGIC", "结构": "STRUCTURE", "身强": "STRATEGY",
    "刑冲": "HIDDEN LINES", "暗线": "HIDDEN LINES", "核心维度": "FOUR AREAS",
    "日柱": "SIX PILLARS", "AuraMate": "DIGITAL AWARENESS", "结语": "CLOSING",
}


def leaf(text: str) -> str:
    return f'<span leaf="">{escape(text)}</span>'


def data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def inline(text: str, palette: dict) -> str:
    parts = []
    for token in TOKEN_RE.split(text):
        if not token:
            continue
        if token.startswith("**") and token.endswith("**"):
            parts.append(f'<strong style="color:{palette["primary"]};font-weight:900;">{leaf(token[2:-2])}</strong>')
        elif token.startswith("==") and token.endswith("=="):
            parts.append(f'<span style="border-bottom:2px solid {palette["accent"]};font-weight:800;color:{palette["primary"]};">{leaf(token[2:-2])}</span>')
        elif token.startswith("++") and token.endswith("++"):
            parts.append(f'<span style="border-bottom:1px solid {palette["gold"]};">{leaf(token[2:-2])}</span>')
        elif token.startswith("`") and token.endswith("`"):
            parts.append(f'<span style="font-family:monospace;background:{palette["light"]};padding:1px 4px;border-radius:3px;">{leaf(token[1:-1])}</span>')
        else:
            parts.append(leaf(token))
    return "".join(parts)


def paragraph(text: str, palette: dict) -> str:
    return f'<p style="margin:0 0 18px;font-size:15px;line-height:1.95;text-align:justify;color:{palette["text"]};padding:0 18px;">{inline(text, palette)}</p>'


def image_block(path: Path, palette: dict) -> str:
    if not path.exists():
        raise FileNotFoundError(f"缺少图片：{path}")
    return f'<section style="margin:0 14px 26px;border:1px solid {palette["accent"]};background:#FFFFFF;border-radius:8px;padding:6px;box-shadow:0 4px 14px -8px rgba(0,0,0,0.28);"><section style="margin:0;border-radius:6px;overflow:hidden;"><span leaf=""><img src="{data_uri(path)}" style="max-width:100%;height:auto;display:block;margin:0 auto;"></span></section></section>'


def section_heading(number: int, title: str, palette: dict) -> str:
    en = next((value for key, value in EN_LABELS.items() if key in title), "MONTHLY INSIGHT")
    return f'''<section style="margin:42px 14px 20px;padding:18px 18px 16px;border-radius:8px;background:linear-gradient(135deg,{palette['dark']},{palette['primary']} 72%,{palette['accent']});border:1px solid {palette['gold']};">
<p style="margin:0 0 8px;font-size:11px;color:{palette['gold']};font-weight:900;letter-spacing:0;">{leaf(f'{number:02d} · {en}')}</p>
<h3 style="margin:0;font-size:22px;line-height:1.45;color:#FFFFFF;font-weight:900;letter-spacing:0;">{leaf(title)}</h3>
</section>'''


def mini_heading(title: str, palette: dict) -> str:
    return f'<p style="margin:26px 18px 12px;font-size:16px;font-weight:900;color:{palette["dark"]};line-height:1.5;border-left:5px solid {palette["primary"]};padding-left:12px;">{leaf(title)}</p>'


def quote(text: str, palette: dict) -> str:
    return f'<section style="margin:20px 18px 28px;background:{palette["light"]};border-left:5px solid {palette["primary"]};border-radius:0 8px 8px 0;padding:16px 18px;"><p style="margin:0;font-size:16px;font-weight:900;color:{palette["dark"]};line-height:1.85;">{inline(text, palette)}</p></section>'


def list_item(text: str, palette: dict) -> str:
    return f'<p style="margin:0 18px 12px;padding-left:14px;border-left:2px solid {palette["accent"]};font-size:14px;line-height:1.85;color:{palette["text"]};">{inline(text, palette)}</p>'


def qr_block(qr: Path, context: dict) -> str:
    p = context["palette"]
    return f'''<section style="margin:28px 14px 10px;padding:14px 18px 16px;background:{p['dark']};border:1px solid {p['gold']};border-radius:8px;text-align:center;">
<p style="margin:0 0 2px;font-size:11px;line-height:1.6;color:#FFFFFF;">{leaf(f'官网： {context["website"]}')}</p>
<p style="margin:0 0 4px;font-size:11px;line-height:1.6;color:#FFFFFF;">{leaf(f'小红书： {context["xiaohongshu"]}')}</p>
<p style="margin:0 0 8px;font-size:11px;line-height:1.6;font-weight:900;color:{p['gold']};">{leaf(context['qr_cta'])}</p>
<section style="width:96px;max-width:34%;margin:0 auto;padding:6px;background:#FFFFFF;border-radius:5px;">
<span leaf=""><img src="{data_uri(qr)}" width="90" style="width:90px;max-width:100%;height:auto;display:block;margin:0 auto;"></span>
</section>
</section>'''


def flush_paragraph(buffer: list[str], blocks: list[str], palette: dict) -> None:
    if buffer:
        blocks.append(paragraph("".join(part.strip() for part in buffer), palette))
        buffer.clear()


def render(markdown: str, context: dict, assets: Path, qr: Path) -> str:
    palette = context["palette"]
    if f'**提示：** {context["disclaimer"]}' not in markdown:
        raise ValueError("正文缺少加粗的固定提示语")
    blocks = [image_block(assets / "cover.jpg", palette)]
    buffer: list[str] = []
    chapter = 0
    for raw in markdown.splitlines():
        line = raw.strip()
        if not line:
            flush_paragraph(buffer, blocks, palette)
            continue
        if line.startswith("# "):
            flush_paragraph(buffer, blocks, palette)
            continue
        if line.startswith("## "):
            flush_paragraph(buffer, blocks, palette)
            chapter += 1
            blocks.append(section_heading(chapter, line[3:].strip(), palette))
            continue
        if line.startswith("### "):
            flush_paragraph(buffer, blocks, palette)
            blocks.append(mini_heading(line[4:].strip(), palette))
            continue
        if line.startswith("> "):
            flush_paragraph(buffer, blocks, palette)
            blocks.append(quote(line[2:].strip(), palette))
            continue
        if line in PLACEHOLDERS:
            flush_paragraph(buffer, blocks, palette)
            blocks.append(image_block(assets / PLACEHOLDERS[line], palette))
            continue
        if re.match(r"^(?:[-*]|\d+[.、])\s+", line):
            flush_paragraph(buffer, blocks, palette)
            text = re.sub(r"^(?:[-*]|\d+[.、])\s+", "", line)
            blocks.append(list_item(text, palette))
            continue
        buffer.append(line)
    flush_paragraph(buffer, blocks, palette)
    blocks.append(qr_block(qr, context))
    return f'''<section style="max-width:677px;margin:0 -28px;background:{palette['light']};font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Hiragino Sans GB','Microsoft YaHei',sans-serif;color:{palette['text']};line-height:1.9;letter-spacing:0;overflow-x:hidden;">
{''.join(blocks)}
</section>'''


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--context", required=True)
    parser.add_argument("--article", required=True)
    parser.add_argument("--assets", required=True)
    parser.add_argument("--qr", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    context = json.loads(Path(args.context).read_text(encoding="utf-8"))
    markdown = Path(args.article).read_text(encoding="utf-8")
    html = render(markdown, context, Path(args.assets), Path(args.qr))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html + "\n", encoding="utf-8")
    print(f"已生成公众号 HTML：{output}")


if __name__ == "__main__":
    main()
