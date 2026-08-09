#!/usr/bin/env python3
"""Lint article structure before rendering expensive visual assets."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


DISCLAIMER = "以下内容以日主与流月关系为主，适合作为月度节奏参考；具体吉凶仍需结合完整八字、大运与流年同看。"
ORDERED_HEADINGS = ["底层", "身强", "暗线", "核心维度", "日柱", "AuraMate"]
PLACEHOLDERS = ["[[ENERGY_MAP]]", "[[RELATION_MAP]]", "[[PILLARS_MAP]]", "[[AURAMATE_FORTUNE]]", "[[AURAMATE_MATCH]]"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("article")
    parser.add_argument("--minimum-chars", type=int, default=3200)
    args = parser.parse_args()
    text = Path(args.article).read_text(encoding="utf-8")
    errors = []
    chinese_chars = len(re.findall(r"[\u3400-\u9fff]", text))
    if chinese_chars < args.minimum_chars:
        errors.append(f"中文字符仅 {chinese_chars}，低于 {args.minimum_chars}")
    if DISCLAIMER not in text:
        errors.append("缺少固定提示语")
    headings = [line[3:].strip() for line in text.splitlines() if line.startswith("## ")]
    heading_text = "\n".join(headings)
    positions = []
    for keyword in ORDERED_HEADINGS:
        position = heading_text.find(keyword)
        if position < 0:
            errors.append(f"缺少章节关键词：{keyword}")
        positions.append(position)
    valid_positions = [position for position in positions if position >= 0]
    if valid_positions != sorted(valid_positions):
        errors.append("章节顺序不符合：底层结构→身强身弱→关系暗线→四大维度→六大日柱→AuraMate")
    for placeholder in PLACEHOLDERS:
        if text.count(placeholder) != 1:
            errors.append(f"占位符应出现一次：{placeholder}")
    if "扫码关注我们" in text:
        errors.append("二维码文案错误，应为“扫码使用产品”")
    if errors:
        print("文章检查失败：")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)
    print(f"文章检查通过：{chinese_chars} 个中文字符，结构与占位符完整")


if __name__ == "__main__":
    main()
