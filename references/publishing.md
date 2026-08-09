# 产品截图与预览页交付

## AuraMate 产品截图

官网入口使用 `https://auramate.com.cn`，登录和产品页可能跳转到 `https://auramate.net`。每次生成文章都必须运行截图脚本，让 Chrome 登录后实时访问产品页：

```bash
export AURAMATE_EMAIL="用户账号"
read -s AURAMATE_PASSWORD
export AURAMATE_PASSWORD
python3 scripts/capture_auramate.py
unset AURAMATE_PASSWORD
```

本机也可将账号写入被 Git 忽略的 `scripts/auramate_credentials.local.json`，结构参考 `assets/templates/auramate_credentials.local.example.json`。脚本优先读取环境变量，其次读取本机凭据文件；不要把真实密码提交到公开仓库。

截图后必须运行：

```bash
python3 scripts/check_capture.py --assets work/assets
```

检查器要求 `work/assets/auramate-capture.json` 标记来源为 `live-chrome`，实时图库至少包含 5 类在线产品页 URL，且采集时间不超过 12 小时。示例目录中的产品图只用于版式参考，不得代替实时截图。

也可以设置 `AURAMATE_CAPTURE_DIR` 指定截图输出目录。

脚本默认实时采集以下未打码产品截图：

1. 财运分析、人生 K 线、专业报告。
2. 天赋脑图、命理体检。
3. 缘分测算、MBTI 命格解析。

每篇文章根据主题选择 3–4 张：财富主题可用财运＋K 线＋专业报告；关系主题可用缘分＋MBTI＋专业报告；身心主题可用命理体检＋天赋脑图＋K 线。不要为了凑数把七张图全部塞进正文。

截图直接使用官网真实界面，不模糊样例数据，不叠加“产品截图示例”等文字。文章必须说明截图用于展示产品功能，不能把截图中的样例命盘解释成本文日主的命盘。裁去浏览器地址栏和无关空白即可。

文章尾部先放一段浅色结尾引语块，再放深色品牌二维码卡。卡片依次写 `官网： auramate.com.cn`、`小红书： AuraMate灵伴` 和金色 CTA“扫码使用产品”。二维码使用白色衬底，手机端二维码本体显示宽度约 `90px`，不得跟随正文宽度放大。

## 一键粘贴预览页

最终交付是 `article_预览.html`，不是微信公众号草稿。预览页顶部必须包含：

- 完整公众号标题。
- “复制标题”按钮，只复制纯文本标题。
- “复制正文”按钮，只复制渲染后的公众号正文富文本。

生成命令：

```bash
python3 scripts/wrap_preview.py work/article.html --context work/context.json --title-file work/article.md
```

在 390px 移动视口检查 `scrollWidth` 等于视口宽度，确认没有横向溢出。标题区和按钮属于预览工具，不得被复制进公众号正文。

交付时同时提供：预览页、干净正文 HTML、公众号标题。到此停止，不打开、不修改微信公众号后台。
