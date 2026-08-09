from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import bazi_core  # noqa: E402
import render_month_assets  # noqa: E402
import render_wechat_html  # noqa: E402
import title_rules  # noqa: E402
import validate_gzh_html  # noqa: E402
import wrap_preview  # noqa: E402


class BaziCoreTests(unittest.TestCase):
    def test_guishui_bingshen_ten_gods(self) -> None:
        self.assertEqual(bazi_core.ten_god("癸", "丙"), "正财")
        self.assertEqual(bazi_core.ten_god("癸", "庚"), "正印")
        self.assertEqual(bazi_core.ten_god("癸", "壬"), "劫财")
        self.assertEqual(bazi_core.ten_god("癸", "戊"), "正官")

    def test_each_day_master_has_six_pillars(self) -> None:
        for stem in bazi_core.STEMS:
            self.assertEqual(len(bazi_core.six_day_pillars(stem)), 6)
        self.assertEqual(
            bazi_core.six_day_pillars("癸"),
            ["癸丑", "癸卯", "癸巳", "癸未", "癸酉", "癸亥"],
        )

    def test_shen_relations_are_canonical_and_deduplicated(self) -> None:
        rows = bazi_core.branch_relations("申")
        relations = {row["relation"] for row in rows}
        self.assertIn("寅申冲，兼见刑意", relations)
        self.assertIn("巳申合，兼见刑意", relations)
        self.assertIn("申亥害", relations)
        self.assertIn("申子辰三合水势", relations)
        self.assertEqual(len([row for row in rows if row["condition"] == "原局见寅"]), 1)

    def test_five_elements_use_five_palettes(self) -> None:
        colors = {bazi_core.PALETTES[element]["primary"] for element in "木火土金水"}
        self.assertEqual(len(colors), 5)

    def test_article_title_prefix_is_fixed_for_every_day_master(self) -> None:
        for stem in bazi_core.STEMS:
            context = bazi_core.build_context(stem, "丙申", 2026, "2026.8.7 — 9.7")
            expected = f'日主{stem}{context["day_master_element"]}的丙申月：'
            self.assertEqual(context["article_title_prefix"], expected)
            self.assertEqual(title_rules.validate_title(expected + "主题句", context), expected + "主题句")
            with self.assertRaises(ValueError):
                title_rules.validate_title(f'{stem}{context["day_master_element"]}日主的丙申月：主题句', context)

    def test_article_title_requires_text_after_prefix(self) -> None:
        context = bazi_core.build_context("甲", "丙申", 2026, "2026.8.7 — 9.7")
        with self.assertRaises(ValueError):
            title_rules.validate_title("日主甲木的丙申月：", context)


class PipelineTests(unittest.TestCase):
    def test_all_cover_titles_fit_one_line(self) -> None:
        canvas = Image.new("RGB", (1410, 600), "#000000")
        draw = render_month_assets.ImageDraw.Draw(canvas)
        for stem in bazi_core.STEMS:
            context = bazi_core.build_context(stem, "丙申", 2026, "2026.8.7 — 9.7")
            title = context["cover_title"]
            self.assertNotIn("\n", title)
            font = render_month_assets.fit_font(draw, title, 720, 78, 48)
            self.assertLessEqual(draw.textbbox((0, 0), title, font=font)[2], 720)

    def test_guishui_example_renders_and_validates(self) -> None:
        context = bazi_core.build_context("癸", "丙申", 2026, "2026.8.7 — 9.7")
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            assets = temp / "assets"
            assets.mkdir()
            render_month_assets.render_cover(
                context,
                ROOT / "assets/examples/guishui-bingshen/cover-background.png",
                assets / "cover.jpg",
            )
            render_month_assets.render_energy(context, assets / "energy-map.jpg")
            render_month_assets.render_relations(context, assets / "relation-map.jpg")
            render_month_assets.render_pillars(context, assets / "pillars-map.jpg")
            shutil.copy2(ROOT / "assets/examples/guishui-bingshen/auramate-fortune.jpg", assets / "auramate-fortune.jpg")
            shutil.copy2(ROOT / "assets/examples/guishui-bingshen/auramate-match.jpg", assets / "auramate-match.jpg")
            markdown = (ROOT / "assets/examples/guishui-bingshen/article.md").read_text(encoding="utf-8")
            html = render_wechat_html.render(markdown, context, assets, ROOT / "assets/brand/auramate-wechat-qrcode.png")
            errors, warnings, leaf_count = validate_gzh_html.validate(html)
            self.assertEqual(errors, [])
            self.assertEqual(warnings, [])
            self.assertGreater(leaf_count, 50)
            self.assertIn("扫码使用产品", html)
            self.assertIn("小红书： AuraMate灵伴", html)
            self.assertNotIn("扫码关注我们", html)
            self.assertIn(f"background:{context['palette']['dark']}", html)
            self.assertIn("width:96px;max-width:34%", html)
            self.assertIn('width="90"', html)
            self.assertIn("margin:0 -28px", html)
            with Image.open(assets / "cover.jpg") as cover:
                self.assertEqual(cover.size, (1410, 600))
            with Image.open(assets / "energy-map.jpg") as energy:
                self.assertEqual(energy.size, (1080, 920))

    def test_preview_separates_title_and_body_copy_targets(self) -> None:
        template = (ROOT / "assets/preview-template.html").read_text(encoding="utf-8")
        title = "日主癸水的丙申月：财星透照与印星生身"
        preview = wrap_preview.build_preview("<section>正文</section>", title, template)
        self.assertIn(f'id="articleTitle">{title}</h1>', preview)
        self.assertIn("copyTitle()", preview)
        self.assertIn("copyBody()", preview)
        self.assertIn('<section id="gzh-content">', preview)
        body_start = preview.index('<section id="gzh-content">')
        self.assertNotIn(title, preview[body_start:])


if __name__ == "__main__":
    unittest.main()
