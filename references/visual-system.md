# AuraMate 流月视觉系统

## 五行主题

所有主题保留品牌金 `#D8AA52`，但主色必须随日主五行变化。不要用同一套蓝金模板只换标题。

| 五行 | 主色 | 深色 | 浅底 | 辅色 | 视觉意象 |
|---|---|---|---|---|---|
| 木 | `#167A5B` | `#0B2E28` | `#EEF8F2` | `#8CC9A8` | 林木、藤蔓、晨雾、向上生长 |
| 火 | `#B64035` | `#35130F` | `#FFF2EE` | `#F19A62` | 日轮、余烬、灯火、流动热浪 |
| 土 | `#9A6A2E` | `#332719` | `#FAF5E9` | `#5B7C74` | 山脉、岩层、田垄、承载结构 |
| 金 | `#8B762F` | `#1D252C` | `#F4F6F7` | `#AFC4D0` | 金属、矿脉、镜面、清肃切面 |
| 水 | `#087EA8` | `#061A33` | `#F1F9FE` | `#8ED8FF` | 深水、雨雾、泉眼、流动波纹 |

阴阳只调整气质，不改五行主色：阳干更明亮、有方向和尺度；阴干更细腻、含蓄、有层次和渗透感。

## 封面硬性规范

- 尺寸 `1410×600`，比例 2.35:1。
- 左侧文字，右侧主视觉；两者衔接紧密，避免中间大块空白。
- 第一行品牌和流月：`AuraMate | ××月`。
- 主标题：`日主××的××月`，粗宋体／思源宋体 Heavy，一行排下。
- 主标题不得使用黑体，不得断成两行，不得让图像模型直接生成文字。
- 副标题不超过 16 个汉字；行动句不超过 12 个汉字。
- 不放“封面：……”图注。
- 不在图中加入非官方水印；品牌名写 `AuraMate`。

`scripts/render_month_assets.py` 优先使用 `assets/fonts/SourceHanSerifCN-Bold.otf`。若缺失，依次查找用户字体目录的思源宋体和 macOS `Songti.ttc`。

## 背景生成

用图像生成模型先生成无字背景。提示词包含日主元素、流月元素、横幅构图和明确留白，禁止文字、logo、水印、二维码。示例：

```text
Create a cinematic 2.35:1 editorial banner background for a Chinese metaphysics monthly forecast. Day-master element: water, represented by deep flowing water and fine mist. Monthly influences: fire as warm directional light, metal as precise reflective mountain strata. Keep the left 48% dark and visually calm for typography; place the main visual on the right, extending toward the center so there is no empty gap. Premium, restrained, realistic, high detail. No text, no letters, no logo, no watermark, no QR code.
```

按五行替换主意象。生成后必须交给 Python 叠字；字体、字号、日期与品牌不依赖图像模型。

## 信息图

- 流月能量结构图优先使用紧凑横向结构，约 `1080×900`，避免单张图占据过长篇幅；复杂关系图可用 `1080×1200` 至 `1080×1700`。
- 大面积背景使用浅灰、白或五行浅底，主色只用于线条、标签和关键节点；不要用高饱和主色铺满整块容器。
- 先测量文字宽度，再决定字号；不把长句塞进小节点。
- “月支藏干”在视觉上放进月支容器内部，避免被误读为并列天干。
- 关系图一行一个触发条件，使用“原局见×”而不是直接断言。
- 六大日柱图只放关键词和一句摘要，正文承担详细解释。
- 生成后用图像查看工具按原始分辨率检查，不只看缩略图。

## 公众号正文宽度

外层主题底框使用 `max-width:677px;margin:0 -28px`，内部正文保持 `padding:0 18px`，图片卡保持 `margin:0 14px`。需要调整手机预览左右空白时，只改外层负边距，每次 4–8px；不要同时扩大正文、卡片和图片，否则版式会整体错乱。

所有文字节点使用 `<span leaf="">`，样式全部内联。禁止 `class`、`id`、`<style>`、`<script>`、`<div>`、CSS 变量、网格布局和绝对定位。
