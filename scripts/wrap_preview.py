#!/usr/bin/env python3
"""Wrap validated WeChat HTML with separate title/body copy controls."""

from __future__ import annotations

import argparse
import html
from pathlib import Path


def title_from_markdown(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    raise ValueError(f"未在 Markdown 中找到一级标题：{path}")


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
    title_group = parser.add_mutually_exclusive_group(required=True)
    title_group.add_argument("--title", help="公众号标题")
    title_group.add_argument("--title-file", help="从 Markdown 一级标题读取公众号标题")
    args = parser.parse_args()

    source = Path(args.file)
    if not source.is_file():
        raise SystemExit(f"找不到文件：{source}")
    title = args.title or title_from_markdown(Path(args.title_file))
    template = (Path(__file__).resolve().parent.parent / "assets/preview-template.html").read_text(encoding="utf-8")
    preview = build_preview(source.read_text(encoding="utf-8").strip(), title, template)
    output = Path(args.output) if args.output else source.with_name(source.stem + "_预览.html")
    output.write_text(preview, encoding="utf-8")
    print(f"已生成一键粘贴预览页：{output}")
    print(f"公众号标题：{title}")


if __name__ == "__main__":
    main()
