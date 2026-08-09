#!/usr/bin/env python3
"""Wrap validated WeChat HTML with separate title/body copy controls."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

from title_rules import extract_markdown_title, validate_title


def build_preview(content: str, title: str, template: str) -> str:
    return (
        template.replace("{{PAGE_TITLE}}", html.escape(title, quote=True))
        .replace("{{ARTICLE_TITLE}}", html.escape(title))
        .replace("<!--GZH_CONTENT-->", content)
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="已校验的公众号正文 HTML")
    parser.add_argument("output", nargs="?", help="预览页输出路径")
    parser.add_argument("--context", required=True, help="用于校验公众号标题固定前缀")
    title_group = parser.add_mutually_exclusive_group(required=True)
    title_group.add_argument("--title", help="公众号标题")
    title_group.add_argument("--title-file", help="从 Markdown 一级标题读取公众号标题")
    args = parser.parse_args()

    source = Path(args.file)
    if not source.is_file():
        raise SystemExit(f"找不到文件：{source}")
    title = args.title or extract_markdown_title(Path(args.title_file))
    context = json.loads(Path(args.context).read_text(encoding="utf-8"))
    try:
        validate_title(title, context)
    except ValueError as error:
        raise SystemExit(str(error)) from error
    template = (Path(__file__).resolve().parent.parent / "assets/preview-template.html").read_text(encoding="utf-8")
    preview = build_preview(source.read_text(encoding="utf-8").strip(), title, template)
    output = Path(args.output) if args.output else source.with_name(source.stem + "_预览.html")
    output.write_text(preview, encoding="utf-8")
    print(f"已生成一键粘贴预览页：{output}")
    print(f"公众号标题：{title}")


if __name__ == "__main__":
    main()
