#!/usr/bin/env python3
"""Reject stale or non-live AuraMate product screenshots."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path


def validate_capture(assets: Path, max_age_hours: float) -> list[str]:
    manifest_path = assets / "auramate-capture.json"
    if not manifest_path.is_file():
        return ["缺少实时截图清单 auramate-capture.json，请先运行 capture_auramate.py"]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        captured_at = datetime.fromisoformat(manifest["captured_at"])
    except (KeyError, ValueError, json.JSONDecodeError) as error:
        return [f"实时截图清单无法读取：{error}"]
    if captured_at.tzinfo is None:
        captured_at = captured_at.replace(tzinfo=timezone.utc)
    age_hours = (datetime.now(timezone.utc) - captured_at.astimezone(timezone.utc)).total_seconds() / 3600
    errors = []
    if manifest.get("source") != "live-chrome":
        errors.append("产品截图不是来自实时 Chrome 采集")
    if age_hours < 0 or age_hours > max_age_hours:
        errors.append(f"产品截图已超过 {max_age_hours:g} 小时，请重新实时截取")
    products = manifest.get("products") or {}
    if len(products) < 5:
        errors.append("实时产品图库少于 5 类，不能只使用财运与缘分截图")
    for key, row in products.items():
        if not str(row.get("url", "")).startswith(("https://auramate.net", "https://auramate.com.cn")):
            errors.append(f"{key} 缺少 AuraMate 在线页面 URL")
        image = assets / row.get("file", "")
        if not image.is_file() or image.stat().st_size < 10_000:
            errors.append(f"{key} 实时截图缺失或文件异常")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assets", default="work/assets")
    parser.add_argument("--max-age-hours", type=float, default=12)
    args = parser.parse_args()
    errors = validate_capture(Path(args.assets), args.max_age_hours)
    if errors:
        print("产品截图检查失败：")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)
    print("产品截图检查通过：实时产品图库来源与时效均合格")


if __name__ == "__main__":
    main()
