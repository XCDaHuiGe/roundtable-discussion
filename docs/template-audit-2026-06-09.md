# HTML-PPT 模板审计报告（2026-06-09）

## 结论

`engine/` 里的 16 个历史模板不能直接并入 V13 主链路。它们大多能通过 `engine/validate_templates.py`，但这个验证器只检查基础存在性，不能证明模板满足“阅读型 PPT 生成标准”。

当前应把旧模板分成三类：

| 分级 | 模板 | 处理建议 |
|:---|:---|:---|
| A 可改造成 V13 主题 | consulting-report, clean-review, rain-notes, sunrise, pixel-report, y2k-brand, story-field, studio-photo, shiny-tiles | 提取颜色、字体、边框、背景、动效为 V13 theme token，不直接复用整页 HTML |
| B 需先修规范 | editorial, geek-report, dot-matrix, dot-matrix-light, premium-dark | 先修页面高度/锁滚动/导航冲突，再决定是否提炼为主题 |
| C legacy 隔离 | v2-starry, v3-magazine | Handlebars 老链路，不能直接作为 V13 theme；只提取视觉语言 |

## P0/P1 问题

### P0：旧验证器过宽

`validate_templates.py` 报告 16/16 通过，但严格审计发现：

- 没有检查 `.section/.slide` 是否稳定占满单页视口。
- 没有检查是否存在多套翻页脚本。
- 没有检查模板是 Adapter 还是 Handlebars legacy。
- 没有检查渲染后页面是否有内容裁切。
- 没有检查攻击/回应、专家发言等语义结构是否在同页正确呈现。

### P1：部分模板不符合单页铁律的显式写法

以下模板没有显式 `.section` 或 `.slide` 的 `height:100vh`，虽然有些通过 `position:fixed; inset:0` 或父容器实现了类似效果，但不符合统一标准：

- `template-editorial.html`
- `template-geek-report.html`
- `template-dot-matrix.html`
- `template-dot-matrix-light.html`

### P1：`premium-dark` 没有锁住 body 垂直滚动

`template-premium-dark.html` 的 body 只有 `overflow-x:hidden`，不符合当前项目“禁止内部滚动/整页翻页器接管 wheel”的稳定要求。它的 `.section` 有 `height:100vh; overflow:hidden`，但 body 层仍有风险。

### P1：多套导航脚本并存风险

多个模板中既有原始 `.section`/`.slide` 导航脚本，又有后续注入的标准导航脚本片段。表现为同一模板内同时出现：

- `const sections = document.querySelectorAll('.section')`
- `const slides = document.querySelectorAll('.slide')`
- 多段 `wheel/keydown/click` 监听

这会带来：

- 翻页状态不同步。
- 导航点数量和实际页面不一致。
- wheel/click 被重复处理。
- V13 再封装时行为不稳定。

### P1：V2/V3 模板仍是 Handlebars legacy

- `template-v2-starry.html`
- `template-v3-magazine.html`

它们使用 `{{#each ...}}`，走 `render_v8.py` / legacy 渲染语义，不是 `{{slides}}` adapter 结构，也不是 V13 ReadingPage 结构。不能直接作为 V13 主题引入。

### P1：旧渲染器存在编码损坏迹象

`engine/render_v8.py` 中存在明显乱码字符串，例如中文标签被破坏。这说明 legacy 渲染链路不适合继续扩展，只应作为历史兼容入口。

## 可复用资产

旧模板仍然有价值，但应按“视觉资产”而不是“运行时模板”复用：

- 色彩：暗黑、高级金、点阵、Y2K、雨天、摄影棚、晨光等风格。
- 字体层级：标题、kicker、正文、数字指标。
- 背景纹理：点阵、噪声、网格、光晕。
- 组件气质：咨询报告、杂志编辑、极客报告、故事田野等。

## 不建议直接复用的部分

- 每个模板自己的 JS 翻页系统。
- 每个模板自己的内容容量策略。
- 每个模板自己的 HTML 页面结构。
- hover 展开答案、内部 max-height 展开等可能造成内容不可读的交互。
- Handlebars 老数据结构。

## 推荐改造路线

### 第 1 步：冻结旧模板

保留 `template-*.html` 作为 legacy 视觉参考，不再把它们作为主链路扩展目标。

### 第 2 步：建立 V13 theme token

把旧模板拆成主题 token：

- `editorial`
- `obsidian`
- `blueprint`
- `consulting`
- `matrix`
- `magazine`
- `warm-paper`
- `studio`

每套 theme 只提供：

- background
- surface
- text
- muted text
- accent
- border
- shadow
- typography mood
- optional texture

### 第 3 步：V13 只保留一套结构合同

所有主题共用：

- cover
- insight reading
- stance spectrum
- clash courtroom
- summary

主题只换视觉，不换语义结构。这样才能保证攻击/回应同页、无内部滚动、内容不裁切。

### 第 4 步：升级验证器

新增严格验证：

- 识别重复导航脚本。
- 检查 slide/section 视口锁定。
- 检查 body/html overflow。
- 检查禁用 `overflow-y:auto/scroll`。
- 用浏览器批量扫描渲染产物，检查每页主要内容块 `scrollHeight <= clientHeight`。
- 对 clash 页检查 attack/defense 同页且都有内容。

## 当前立即结论

不能直接把 `engine/template-*.html` 当作“多风格 V13 模板库”。正确做法是：

1. 把旧模板审计分级。
2. 抽取视觉语言。
3. 改造成 V13 theme token。
4. 保持 V13 的结构和验证器统一。

否则会重新回到“好看但不稳定 / 稳定但不好看”的老问题。
