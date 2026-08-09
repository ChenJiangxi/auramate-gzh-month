#!/usr/bin/env python3
"""Lint article structure before rendering expensive visual assets."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from title_rules import extract_markdown_title, validate_title


DISCLAIMER = "以下内容以日主与流月关系为主，适合作为月度节奏参考；具体吉凶仍需结合完整八字、大运与流年同看。"
ORDERED_HEADING_MODULES = [
    ("流月结构", ("底层", "结构", "月令", "财印", "五行")),
    ("强弱策略", ("身强", "身弱", "强弱", "承接", "借势", "分型")),
    (
        "关系触发",
        (
            "暗线", "刑冲", "冲合", "合害", "刑与合", "冲与合",
            "六合", "六冲", "三刑", "六害", "关系", "触发", "成局",
        ),
    ),
    ("现实维度", ("核心维度", "四大维度", "现实", "工作", "事业", "财富")),
    ("六大日柱", ("日柱", "六柱", "同是")),
    ("AuraMate 产品", ("AuraMate", "数字化觉察", "产品")),
]
CORE_PLACEHOLDERS = ["[[ENERGY_MAP]]", "[[RELATION_MAP]]", "[[PILLARS_MAP]]"]
PRODUCT_PLACEHOLDERS = [
    "[[AURAMATE_FORTUNE]]", "[[AURAMATE_KLINE]]", "[[AURAMATE_REPORT]]", "[[AURAMATE_TALENT]]",
    "[[AURAMATE_HEALTH]]", "[[AURAMATE_MATCH]]", "[[AURAMATE_MBTI]]",
]


def validate_heading_modules(headings: list[str]) -> list[str]:
    """Check the editorial spine without prescribing visible section titles."""
    errors = []
    cursor = -1
    for module, aliases in ORDERED_HEADING_MODULES:
        position = next(
            (
                index
                for index, heading in enumerate(headings)
                if index > cursor and any(alias in heading for alias in aliases)
            ),
            -1,
        )
        if position < 0:
            errors.append(f"缺少或顺序错误的内容模块：{module}")
            continue
        cursor = position
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("article")
    parser.add_argument("--context", required=True)
    parser.add_argument("--minimum-chars", type=int, default=3200)
    args = parser.parse_args()
    article = Path(args.article)
    text = article.read_text(encoding="utf-8")
    context = json.loads(Path(args.context).read_text(encoding="utf-8"))
    errors = []
    try:
        validate_title(extract_markdown_title(article), context)
    except ValueError as error:
        errors.append(str(error))
    chinese_chars = len(re.findall(r"[\u3400-\u9fff]", text))
    if chinese_chars < args.minimum_chars:
        errors.append(f"中文字符仅 {chinese_chars}，低于 {args.minimum_chars}")
    if f"**提示：** {DISCLAIMER}" not in text:
        errors.append("固定提示语前必须有加粗的“提示：”")
    headings = [line[3:].strip() for line in text.splitlines() if line.startswith("## ")]
    errors.extend(validate_heading_modules(headings))
    for placeholder in CORE_PLACEHOLDERS:
        if text.count(placeholder) != 1:
            errors.append(f"占位符应出现一次：{placeholder}")
    selected_products = [placeholder for placeholder in PRODUCT_PLACEHOLDERS if text.count(placeholder) == 1]
    duplicated_products = [placeholder for placeholder in PRODUCT_PLACEHOLDERS if text.count(placeholder) > 1]
    if len(selected_products) < 3 or len(selected_products) > 4:
        errors.append("AuraMate 产品截图应从实时图库中选择 3–4 类，不能只放财运和缘分")
    for placeholder in duplicated_products:
        errors.append(f"产品占位符最多出现一次：{placeholder}")
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
