# 产品截图与预览页交付

## AuraMate 产品截图

官网入口使用 `https://auramate.com.cn`，登录和产品页可能跳转到 `https://auramate.net`。优先复用用户已登录的 Chrome 会话；需要脚本登录时运行：

```bash
export AURAMATE_EMAIL="用户账号"
read -s AURAMATE_PASSWORD
export AURAMATE_PASSWORD
python3 scripts/capture_auramate.py
unset AURAMATE_PASSWORD
```

也可以设置 `AURAMATE_CAPTURE_DIR` 指定截图输出目录。不要把真实密码写入仓库中的 `.env`、Markdown、脚本或提交记录。

需要两张未打码截图：

1. 财运分析：展示真实产品导航、干支关系、趋势或建议界面。
2. 缘分测算：展示真实产品导航、关系指数、合盘或建议界面。

截图直接使用官网真实界面，不模糊样例数据，不叠加“产品截图示例”等文字。文章必须说明截图用于展示产品功能，不能把截图中的样例命盘解释成本文日主的命盘。裁去浏览器地址栏和无关空白即可。

二维码上方文案固定为“扫码使用产品”，下方写 `auramate.com.cn`。

## 一键粘贴预览页

最终交付是 `article_预览.html`，不是微信公众号草稿。预览页顶部必须包含：

- 完整公众号标题。
- “复制标题”按钮，只复制纯文本标题。
- “复制正文”按钮，只复制渲染后的公众号正文富文本。

生成命令：

```bash
python3 scripts/wrap_preview.py work/article.html --title-file work/article.md
```

在 390px 移动视口检查 `scrollWidth` 等于视口宽度，确认没有横向溢出。标题区和按钮属于预览工具，不得被复制进公众号正文。

交付时同时提供：预览页、干净正文 HTML、公众号标题。到此停止，不打开、不修改微信公众号后台。
