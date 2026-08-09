#!/usr/bin/env python3
"""Build one deterministic context for an AuraMate day-master monthly article."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


STEMS = {
    "甲": ("木", "阳"), "乙": ("木", "阴"),
    "丙": ("火", "阳"), "丁": ("火", "阴"),
    "戊": ("土", "阳"), "己": ("土", "阴"),
    "庚": ("金", "阳"), "辛": ("金", "阴"),
    "壬": ("水", "阳"), "癸": ("水", "阴"),
}
DAY_MASTER_NAMES = {stem: stem + element for stem, (element, _) in STEMS.items()}
STEM_ORDER = "甲乙丙丁戊己庚辛壬癸"
BRANCH_ORDER = "子丑寅卯辰巳午未申酉戌亥"
HIDDEN_STEMS = {
    "子": "癸", "丑": "己癸辛", "寅": "甲丙戊", "卯": "乙",
    "辰": "戊乙癸", "巳": "丙戊庚", "午": "丁己", "未": "己丁乙",
    "申": "庚壬戊", "酉": "辛", "戌": "戊辛丁", "亥": "壬甲",
}

GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
CONTROLS = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

CLASHES = [("子", "午"), ("丑", "未"), ("寅", "申"), ("卯", "酉"), ("辰", "戌"), ("巳", "亥")]
COMBINES = [("子", "丑"), ("寅", "亥"), ("卯", "戌"), ("辰", "酉"), ("巳", "申"), ("午", "未")]
HARMS = [("子", "未"), ("丑", "午"), ("寅", "巳"), ("卯", "辰"), ("申", "亥"), ("酉", "戌")]
PUNISH_TRIOS = [("寅", "巳", "申"), ("丑", "戌", "未")]
PUNISH_PAIRS = [("子", "卯")]
SELF_PUNISH = set("辰午酉亥")
TRINES = {
    ("申", "子", "辰"): "水", ("亥", "卯", "未"): "木",
    ("寅", "午", "戌"): "火", ("巳", "酉", "丑"): "金",
}
MEETINGS = {
    ("亥", "子", "丑"): "水", ("寅", "卯", "辰"): "木",
    ("巳", "午", "未"): "火", ("申", "酉", "戌"): "金",
}

PALETTES = {
    "木": {"primary": "#167A5B", "dark": "#0B2E28", "light": "#EEF8F2", "accent": "#8CC9A8", "gold": "#D8AA52", "text": "#243B35"},
    "火": {"primary": "#B64035", "dark": "#35130F", "light": "#FFF2EE", "accent": "#F19A62", "gold": "#D8AA52", "text": "#422B28"},
    "土": {"primary": "#9A6A2E", "dark": "#332719", "light": "#FAF5E9", "accent": "#5B7C74", "gold": "#D8AA52", "text": "#443A2D"},
    "金": {"primary": "#8B762F", "dark": "#1D252C", "light": "#F4F6F7", "accent": "#AFC4D0", "gold": "#D8AA52", "text": "#303A42"},
    "水": {"primary": "#087EA8", "dark": "#061A33", "light": "#F1F9FE", "accent": "#8ED8FF", "gold": "#D8AA52", "text": "#25384D"},
}

ELEMENT_TAGLINES = {
    "木": "让生长拥有方向", "火": "让热望拥有节奏", "土": "让承载拥有边界",
    "金": "让判断拥有尺度", "水": "让流动拥有秩序",
}


def ten_god(day_master: str, target: str) -> str:
    day_element, day_polarity = STEMS[day_master]
    target_element, target_polarity = STEMS[target]
    same_polarity = day_polarity == target_polarity
    if day_element == target_element:
        return "比肩" if same_polarity else "劫财"
    if GENERATES[day_element] == target_element:
        return "食神" if same_polarity else "伤官"
    if CONTROLS[day_element] == target_element:
        return "偏财" if same_polarity else "正财"
    if CONTROLS[target_element] == day_element:
        return "七杀" if same_polarity else "正官"
    if GENERATES[target_element] == day_element:
        return "偏印" if same_polarity else "正印"
    raise ValueError(f"无法计算十神：{day_master} -> {target}")


def six_day_pillars(day_master: str) -> list[str]:
    cycle = [STEM_ORDER[i % 10] + BRANCH_ORDER[i % 12] for i in range(60)]
    pillars = [pillar for pillar in cycle if pillar[0] == day_master]
    return sorted(pillars, key=lambda pillar: BRANCH_ORDER.index(pillar[1]))


def paired_other(branch: str, pairs: list[tuple[str, str]]) -> str | None:
    for left, right in pairs:
        if branch == left:
            return right
        if branch == right:
            return left
    return None


def canonical_pair(branch: str, pairs: list[tuple[str, str]]) -> str | None:
    for left, right in pairs:
        if branch in (left, right):
            return left + right
    return None


def branch_relations(month_branch: str) -> list[dict]:
    rows: list[dict] = []
    for label, pairs, meaning in [
        ("冲", CLASHES, "变化与位移被推动，先确认方向与代价。"),
        ("合", COMBINES, "连接与合作增强，也要写清条件与分工。"),
        ("害", HARMS, "不对称信息与暗处消耗增多，重要沟通要留痕。"),
    ]:
        other = paired_other(month_branch, pairs)
        if other:
            rows.append({"trigger": other, "condition": f"原局见{other}", "relation": f"{canonical_pair(month_branch, pairs)}{label}", "kind": label, "meaning": meaning})

    for trio in PUNISH_TRIOS:
        if month_branch in trio:
            for other in trio:
                if other != month_branch:
                    rows.append({"trigger": other, "condition": f"原局见{other}", "relation": f"{other}{month_branch}见刑意", "kind": "刑", "meaning": "机会与摩擦可能并存，承诺、付款和责任先说清。"})
    other = paired_other(month_branch, PUNISH_PAIRS)
    if other:
        rows.append({"trigger": other, "condition": f"原局见{other}", "relation": f"{other}{month_branch}相刑", "kind": "刑", "meaning": "表达与边界容易顶住，先处理规则再处理情绪。"})
    if month_branch in SELF_PUNISH:
        rows.append({"trigger": month_branch, "condition": f"原局再见{month_branch}", "relation": f"{month_branch}{month_branch}自刑", "kind": "刑", "meaning": "反复与内耗感可能放大，重要决定增加复核。"})

    for branches, element in TRINES.items():
        if month_branch in branches:
            others = "".join(b for b in branches if b != month_branch)
            rows.append({"trigger": others, "condition": f"原局同时见{'、'.join(others)}", "relation": f"{''.join(branches)}三合{element}势", "kind": "成局", "meaning": "只有条件较完整时才讨论成势，不能仅凭一个流月断定合化。"})
    for branches, element in MEETINGS.items():
        if month_branch in branches:
            others = "".join(b for b in branches if b != month_branch)
            rows.append({"trigger": others, "condition": f"原局同时见{'、'.join(others)}", "relation": f"{''.join(branches)}三会{element}势", "kind": "成势", "meaning": "同类气势可能增强，仍需结合节令、透干与全局判断。"})

    unique = []
    seen = set()
    for row in rows:
        key = (row["condition"], row["relation"])
        if key not in seen:
            seen.add(key)
            unique.append(row)

    grouped: list[dict] = []
    consumed: set[int] = set()
    for i, row in enumerate(unique):
        if i in consumed:
            continue
        matches = [
            (j, candidate) for j, candidate in enumerate(unique)
            if j > i and candidate["condition"] == row["condition"] and candidate["kind"] == "刑"
        ]
        if row["kind"] in {"冲", "合"} and matches:
            j, _ = matches[0]
            consumed.add(j)
            base_meaning = "路径变化与摩擦可能并存" if row["kind"] == "冲" else "连接机会与合作摩擦可能并存"
            grouped.append({
                **row,
                "relation": f"{row['relation']}，兼见刑意",
                "kind": f"{row['kind']}／刑",
                "meaning": f"{base_meaning}，承诺、付款和责任先说清。",
            })
        else:
            grouped.append(row)
    return grouped


def pillar_relation(day_branch: str, month_branch: str) -> str:
    labels = []
    for label, pairs in [("冲", CLASHES), ("合", COMBINES), ("害", HARMS)]:
        if {day_branch, month_branch} in [set(p) for p in pairs]:
            labels.append(label)
    if any(day_branch in trio and month_branch in trio for trio in PUNISH_TRIOS):
        labels.append("刑")
    if {day_branch, month_branch} in [set(p) for p in PUNISH_PAIRS]:
        labels.append("刑")
    if day_branch == month_branch and day_branch in SELF_PUNISH:
        labels.append("自刑")
    return "、".join(dict.fromkeys(labels)) or "无直接冲合刑害"


def build_context(day_master: str, month_pillar: str, year: int | None, date_range: str) -> dict:
    if day_master not in STEMS:
        raise ValueError("日主必须是十天干之一")
    if len(month_pillar) != 2 or month_pillar[0] not in STEMS or month_pillar[1] not in HIDDEN_STEMS:
        raise ValueError("流月干支格式应类似“丙申”")
    month_stem, month_branch = month_pillar
    element, polarity = STEMS[day_master]
    roles = ["主气", "中气", "余气"]
    hidden = [
        {"stem": stem, "ten_god": ten_god(day_master, stem), "role": roles[i]}
        for i, stem in enumerate(HIDDEN_STEMS[month_branch])
    ]
    pillars = [
        {
            "pillar": pillar,
            "branch": pillar[1],
            "month_relation": pillar_relation(pillar[1], month_branch),
            "hidden_stems": list(HIDDEN_STEMS[pillar[1]]),
            "hidden_relations": [
                {"stem": stem, "ten_god": ten_god(day_master, stem)}
                for stem in HIDDEN_STEMS[pillar[1]]
            ],
        }
        for pillar in six_day_pillars(day_master)
    ]
    main_relation = hidden[0]["ten_god"]
    stem_relation = ten_god(day_master, month_stem)
    subtitle = f"{stem_relation}透出，{main_relation}当令"
    return {
        "day_master": day_master,
        "day_master_name": DAY_MASTER_NAMES[day_master],
        "day_master_element": element,
        "day_master_polarity": polarity,
        "month_pillar": month_pillar,
        "month_stem": month_stem,
        "month_branch": month_branch,
        "month_stem_ten_god": stem_relation,
        "hidden_stems": hidden,
        "branch_relations": branch_relations(month_branch),
        "day_pillars": pillars,
        "year": year,
        "date_range": date_range,
        "cover_title": f"日主{DAY_MASTER_NAMES[day_master]}的{month_pillar}月",
        "article_title_prefix": f"日主{DAY_MASTER_NAMES[day_master]}的{month_pillar}月：",
        "cover_subtitle": subtitle,
        "cover_tagline": ELEMENT_TAGLINES[element],
        "palette": PALETTES[element],
        "disclaimer": "以下内容以日主与流月关系为主，适合作为月度节奏参考；具体吉凶仍需结合完整八字、大运与流年同看。",
        "website": "auramate.com.cn",
        "xiaohongshu": "AuraMate灵伴",
        "qr_cta": "扫码使用产品",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--day-master", required=True)
    parser.add_argument("--month-pillar", required=True)
    parser.add_argument("--year", type=int)
    parser.add_argument("--date-range", default="")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    context = build_context(args.day_master, args.month_pillar, args.year, args.date_range)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(context, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"已生成命理上下文：{output}")


if __name__ == "__main__":
    main()
