"""Deterministic title rules for monthly WeChat articles."""

from __future__ import annotations

from pathlib import Path


def expected_prefix(context: dict) -> str:
    prefix = context.get("article_title_prefix") or f'{context["cover_title"]}：'
    return prefix if prefix.endswith("：") else prefix + "："


def extract_markdown_title(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    raise ValueError(f"未在 Markdown 中找到一级标题：{path}")


def validate_title(title: str, context: dict) -> str:
    prefix = expected_prefix(context)
    if not title.startswith(prefix):
        raise ValueError(f"公众号标题格式错误，应以“{prefix}”开头")
    if not title[len(prefix):].strip():
        raise ValueError(f"公众号标题缺少主题句，应使用“{prefix}xxx”格式")
    return title
