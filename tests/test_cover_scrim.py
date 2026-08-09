from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import bazi_core  # noqa: E402
import render_month_assets  # noqa: E402


class CoverScrimTests(unittest.TestCase):
    def setUp(self) -> None:
        self.context = bazi_core.build_context("乙", "丙申", 2026, "2026.8.7 — 9.7")

    def test_scrim_fades_monotonically_without_alpha_steps(self) -> None:
        scrim = render_month_assets.cover_text_scrim((1410, 600), self.context["palette"])
        alpha_row = scrim.getchannel("A").crop((0, 300, 1410, 301))
        alpha = [alpha_row.getpixel((x, 0)) for x in range(alpha_row.width)]

        self.assertGreaterEqual(alpha[0], 220)
        self.assertEqual(alpha[-1], 0)
        self.assertTrue(all(left >= right for left, right in zip(alpha, alpha[1:])))
        self.assertLessEqual(max(abs(left - right) for left, right in zip(alpha, alpha[1:])), 2)

    def test_rendered_cover_has_no_full_height_vertical_scrim_seam(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            background = temp / "flat-background.png"
            output = temp / "cover.png"
            Image.new("RGB", (1410, 600), "#809080").save(background)

            render_month_assets.render_cover(self.context, background, output)

            with Image.open(output) as cover:
                row = [sum(cover.getpixel((x, 150))) for x in range(60, 1300)]
            adjacent_steps = [abs(left - right) for left, right in zip(row, row[1:])]
            self.assertLessEqual(max(adjacent_steps), 4)


if __name__ == "__main__":
    unittest.main()
