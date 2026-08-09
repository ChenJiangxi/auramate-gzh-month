---
name: auramate-gzh-month
description: 为 AuraMate（灵伴）生成微信公众号日主流月运势文章与一键粘贴预览页。用于用户提出“流月运势”“十天干日主月运”“公众号月运文章”“配图排盘”“公众号标题与正文预览”等任务；从日主与流月干支计算十神、藏干、刑冲合害和六大日柱，按日主五行切换主题色，生成 2.35:1 粗宋体单行封面、紧凑关系图、真实产品截图章节和公众号兼容 HTML，最终提供可分别复制标题与正文的预览页。
---

# 灵伴公众号流月运势

从零完成一篇 AuraMate 日主流月公众号文章。把命理计算交给脚本，把观点、解释与读者洞察交给 agent；任何图文关系都必须由同一份 `context.json` 驱动。最终交付停在“一键粘贴预览页”，不操作微信公众号后台。

## 必需输入

先确定：日主天干、流月干支、年份与公历起止日。用户未给齐且无法从可靠来源确定时，只追问缺失项。可选输入包括参考文章、封面背景和 AuraMate 产品账号。

不得把登录凭据写入 Git、日志或生成物。需要自动登录 `auramate.net` 时，从 `AURAMATE_EMAIL`、`AURAMATE_PASSWORD` 环境变量或用户已有浏览器会话读取；公开仓库只保留配置模板。

## 资源导航

- 写正文前完整读取 [references/editorial-standard.md](references/editorial-standard.md)。
- 解释十神、藏干或刑冲合害时读取 [references/bazi-reference.md](references/bazi-reference.md)。
- 生成封面、信息图和五行配色时读取 [references/visual-system.md](references/visual-system.md)。
- 获取 AuraMate 产品截图和生成预览页前读取 [references/publishing.md](references/publishing.md)。
- 需要对照成品密度和层级时查看 `assets/examples/guishui-bingshen/`，不要照抄具体命理结论。

## 工作流

### 1. 建立唯一命理上下文

运行：

```bash
python3 scripts/bazi_core.py \
  --day-master 癸 \
  --month-pillar 丙申 \
  --year 2026 \
  --date-range "2026.8.7 — 9.7" \
  --output work/context.json
```

正文、封面、能量结构图、刑冲合害图和六大日柱必须读取这一个文件。不要凭记忆另写十神。若正文出现月支藏干，首次出现时明确写“月支内部藏干”，不能让读者误以为它们是额外出现的天干。

### 2. 先搭内容骨架，再决定叙事与配图

写 3200–5000 个中文字符的 Markdown。下面规定的是内容模块及相对顺序，不是要求照抄的小标题模板：

一级标题固定为 `日主{十大日主之一}的{流月干支}月：{主题句}`。十大日主仅指 `甲木、乙木、丙火、丁火、戊土、己土、庚金、辛金、壬水、癸水`，不是让 agent 自由拼接“天干五行”。例如：`日主癸水的丙申月：财星透照与印星生身，让资源真正落地`。“日主”必须在最前，冒号使用全角 `：`。

1. 开场：交代节气场景、日主与流月关系、核心矛盾。可以从场景、问题、反差、现实困境或一句判断进入，不必每篇使用同一种开头。
2. 固定提示：`**提示：** 以下内容以日主与流月关系为主，适合作为月度节奏参考；具体吉凶仍需结合完整八字、大运与流年同看。`，“提示：”必须加粗。
3. 流月底层结构：月干十神、月支主气与藏干暗线。
4. 身强／身弱分型：两类承接策略，避免绝对吉凶。
5. 刑冲合害与成局：先说明“原局见某支才可能触发”，再落到现实行为。
6. 四大核心维度：工作、财富、关系、健康。必须放在关系拆解之后。
7. 六大日柱：每柱讲结构差异、风险和行动，不只给口号。
8. AuraMate 数字化觉察：从实时产品图库中按本月主题选择 3–4 类产品，不能固定只写财运分析与缘分测算；官网固定为 `auramate.com.cn`。
9. 收束：一句发人深省的引用式判断，随后使用深色品牌卡展示官网、小红书、小尺寸二维码与“扫码使用产品”。

保留以下创作自由：

- 二级、三级标题应根据当月真正的矛盾重新命名，不机械复用示例标题；检查器按语义识别模块，而不是要求固定关键词。
- 各模块篇幅可以围绕主题上下浮动约 20%–30%。某月关系触发更关键时可多写关系，某月事业与资源更关键时可加深现实维度。
- 可以合并相邻短段，也可以在四大维度前增加一个与当月高度相关的主题章节，但不得打乱“流月结构→强弱策略→关系触发→现实维度→六大日柱→产品觉察”的主顺序。
- 开场意象、金句语气、关键词、案例场景、转场方式、产品组合和辅助配图均应随日主、流月与主题变化。

图片只承担结构解释或视觉转场，不重复整段正文。通常使用：封面、流月能量结构图、刑冲合害关系图、必要的转场图、六大日柱速览、3–4 张与主题相关的真实产品截图、二维码。关系简单时宁可少图。

### 3. 生成配图

先用图像生成能力制作无字背景，再由 `scripts/render_month_assets.py` 叠字和画关系图。不得让图像模型直接生成中文文字。

```bash
python3 scripts/render_month_assets.py \
  --context work/context.json \
  --background work/cover-background.png \
  --output-dir work/assets
```

封面固定 `1410×600`（2.35:1）。“日主××的××月”使用粗宋体并保持一行；脚本应动态缩小字号，不得换行、挤压或错位。各日主主题色按五行变化，具体色板和背景提示词见视觉规范。

产品截图必须在每次任务中运行 `python3 scripts/capture_auramate.py`，由登录后的 Chrome 实时建立产品图库，覆盖财运分析、人生 K 线、专业报告、天赋脑图、命理体检、缘分测算和 MBTI 命格解析。随后运行 `python3 scripts/check_capture.py --assets work/assets`；文章从图库中选择 3–4 张与主题最相关的图。仓库示例截图只用于版式参考，禁止直接复制到当次 `work/assets`。

### 4. 生成公众号 HTML

把完成的正文保存为 `work/article.md`，图片位置使用以下独占行占位符：

```text
[[ENERGY_MAP]]
[[RELATION_MAP]]
[[PILLARS_MAP]]
[[AURAMATE_FORTUNE]]
[[AURAMATE_KLINE]]
[[AURAMATE_REPORT]]
[[AURAMATE_TALENT]]
[[AURAMATE_HEALTH]]
[[AURAMATE_MATCH]]
[[AURAMATE_MBTI]]
```

七个产品占位符只选 3–4 个写入文章，每个最多出现一次；选择必须由当月主题和正文论点决定。

运行：

```bash
python3 scripts/check_article.py work/article.md --context work/context.json
python3 scripts/capture_auramate.py
python3 scripts/check_capture.py --assets work/assets
python3 scripts/render_wechat_html.py \
  --context work/context.json \
  --article work/article.md \
  --assets work/assets \
  --qr assets/brand/auramate-wechat-qrcode.png \
  --output work/article.html
python3 scripts/validate_gzh_html.py work/article.html
python3 scripts/wrap_preview.py work/article.html --context work/context.json --title-file work/article.md
```

验证必须达到 0 ERROR、0 WARNING。重点复查移动端：外层主题色底框左右留白、所有图片宽度、标题单行、信息图文字是否溢出、正文是否过窄。不要通过扩大所有段落或图片来修一个局部边距。

### 5. 交付预览页

打开 `work/article_预览.html`，确认页面顶部完整显示公众号标题，并分别测试“复制标题”“复制正文”。正文复制区域不得混入预览页工具栏和标题区。

向用户交付预览页和干净正文 HTML。用户在预览页先复制标题到公众号标题框，再复制正文到正文编辑器。到此结束，不登录、不修改、不保存公众号后台。

## 交付标准

- 十神、藏干、关系图与正文完全一致。
- 公众号标题严格从十大日主固定名称中取值，使用 `日主{十大日主之一}的{流月干支}月：{主题句}`，并通过 `context.json` 校验。
- AuraMate 实时图库至少覆盖 5 类产品；正文从中选择 3–4 类，禁止只放财运和缘分，也禁止沿用示例图或旧截图。
- 封面 2.35:1，标题为粗宋体单行，无图注。
- 五行主题有明显变化，同时保留 AuraMate 的金色品牌点缀。
- 正文以洞察为主，配图为辅；六大日柱图与正文不机械重复。
- 模块顺序稳定，但标题、开场、篇幅重心、案例和产品组合要体现当月差异，不能生成十篇只替换干支的文章。
- 尾部二维码卡使用日主主题的深色底与品牌金描边，依次写官网、小红书和“扫码使用产品”；二维码带白色衬底，手机端二维码本体视觉宽度约 `90px`，不得随容器放大。
- 预览页可分别复制标题与正文，公众号 HTML 校验 0 ERROR、0 WARNING。
- 交付停在预览页，不自动写入草稿或发表。
