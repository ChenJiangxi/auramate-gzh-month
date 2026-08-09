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

### 2. 先搭文章框架，再决定配图

按下列顺序写 3200–5000 个中文字符的 Markdown：

1. 开场：节气场景、日主与流月关系、核心矛盾。
2. 固定提示：`以下内容以日主与流月关系为主，适合作为月度节奏参考；具体吉凶仍需结合完整八字、大运与流年同看。`
3. 流月底层结构：月干十神、月支主气与藏干暗线。
4. 身强／身弱分型：两类承接策略，避免绝对吉凶。
5. 刑冲合害与成局：先说明“原局见某支才可能触发”，再落到现实行为。
6. 四大核心维度：工作、财富、关系、健康。必须放在关系拆解之后。
7. 六大日柱：每柱讲结构差异、风险和行动，不只给口号。
8. AuraMate 数字化觉察：财运分析、缘分测算两种使用场景，官网固定为 `auramate.com.cn`。
9. 收束：一句发人深省的判断、二维码与“扫码使用产品”。

图片只承担结构解释或视觉转场，不重复整段正文。通常使用：封面、流月能量结构图、刑冲合害关系图、必要的转场图、六大日柱速览、两张真实产品截图、二维码。关系简单时宁可少图。

### 3. 生成配图

先用图像生成能力制作无字背景，再由 `scripts/render_month_assets.py` 叠字和画关系图。不得让图像模型直接生成中文文字。

```bash
python3 scripts/render_month_assets.py \
  --context work/context.json \
  --background work/cover-background.png \
  --output-dir work/assets
```

封面固定 `1410×600`（2.35:1）。“日主××的××月”使用粗宋体并保持一行；脚本应动态缩小字号，不得换行、挤压或错位。各日主主题色按五行变化，具体色板和背景提示词见视觉规范。

产品截图必须来自 AuraMate 当前官网界面，直接使用真实、未打码截图，不在截图上叠加“产品截图示例”等说明。截图只证明产品功能与使用场景，不把样例命盘当作文章命盘。

### 4. 生成公众号 HTML

把完成的正文保存为 `work/article.md`，图片位置使用以下独占行占位符：

```text
[[ENERGY_MAP]]
[[RELATION_MAP]]
[[PILLARS_MAP]]
[[AURAMATE_FORTUNE]]
[[AURAMATE_MATCH]]
```

运行：

```bash
python3 scripts/check_article.py work/article.md
python3 scripts/render_wechat_html.py \
  --context work/context.json \
  --article work/article.md \
  --assets work/assets \
  --qr assets/brand/auramate-wechat-qrcode.png \
  --output work/article.html
python3 scripts/validate_gzh_html.py work/article.html
python3 scripts/wrap_preview.py work/article.html --title-file work/article.md
```

验证必须达到 0 ERROR、0 WARNING。重点复查移动端：外层主题色底框左右留白、所有图片宽度、标题单行、信息图文字是否溢出、正文是否过窄。不要通过扩大所有段落或图片来修一个局部边距。

### 5. 交付预览页

打开 `work/article_预览.html`，确认页面顶部完整显示公众号标题，并分别测试“复制标题”“复制正文”。正文复制区域不得混入预览页工具栏和标题区。

向用户交付预览页和干净正文 HTML。用户在预览页先复制标题到公众号标题框，再复制正文到正文编辑器。到此结束，不登录、不修改、不保存公众号后台。

## 交付标准

- 十神、藏干、关系图与正文完全一致。
- 封面 2.35:1，标题为粗宋体单行，无图注。
- 五行主题有明显变化，同时保留 AuraMate 的金色品牌点缀。
- 正文以洞察为主，配图为辅；六大日柱图与正文不机械重复。
- 二维码上方只写“扫码使用产品”，官网只写 `auramate.com.cn`。
- 预览页可分别复制标题与正文，公众号 HTML 校验 0 ERROR、0 WARNING。
- 交付停在预览页，不自动写入草稿或发表。
