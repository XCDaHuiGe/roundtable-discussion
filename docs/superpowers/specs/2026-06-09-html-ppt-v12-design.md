# HTML-PPT V12 主链路稳定化设计

## 目标

把圆桌洞见的 HTML-PPT 产出从“多个生成器、多个模板、多个导航脚本叠加”的状态，收敛成一条稳定、可验证、可演进的主链路。

V12 第一阶段优先解决稳定性：

- 生成质量不稳定：页面结构随机、排版死板、内容截断粗糙。
- 版式稳定性不足：内容过多时靠隐藏、截断或内部滚动兜底。
- 功能稳定性不足：模板和 normalizer 同时注入导航，导致翻页脚本重复。
- 验收标准不足：当前验证脚本只检查“有没有组件”，不检查最终 HTML 是否真的可用。

第一阶段不做完整视觉升级。视觉设计放在第二阶段，但第一阶段会预留设计 token、页面类型和布局槽位，让后续视觉升级不再破坏主链路。

## 设计原则

### 拒绝屎上雕花

现有结构可以参考，但不作为新主链路的约束。

V12 允许废弃以下做法：

- 每个模板自带一套完整导航逻辑。
- 生成器直接拼大量 inline style。
- 通过 `truncate_text()` 把溢出问题伪装成内容精简。
- 通过 `overflow-y:auto` 解决页面容量问题。
- 多个入口同时声称自己是主入口。

### 单一职责

主链路拆成五层：

```text
输入内容
  ↓
Page Planner：决定页面结构
  ↓
Layout Engine：选择白名单布局
  ↓
Capacity Engine：容量估算与自动拆页
  ↓
Single Renderer：唯一 HTML/CSS/JS 出口
  ↓
Acceptance Validator：最终 HTML 验收
```

每一层只承担一个职责，避免模板、生成器、normalizer 互相抢职责。

### 稳定先于风格

第一阶段的成功标准是：

- 每页都能完整显示。
- 没有内部滚动。
- 翻页方式稳定。
- 页面数量、导航点、进度条一致。
- 内容超出时自动拆页，而不是隐藏或滚动。
- 生成结果可被脚本验证。

## 当前问题判断

### 1. 导航职责重复

现有 `engine/generate_v6.py` 使用 adapter 模板，把生成好的 slides 塞进 `{{slides}}`。

同时，`engine/page-fragment-normalizer.py` 也会包裹 slides 并注入完整导航逻辑。

多个 `template-*.html` 文件内部存在自己的 `go()`、`wheelTimer`、`navDots`、点击翻页逻辑。部分模板甚至存在两套相似导航脚本。

这会导致：

- wheel 事件被多个监听器处理。
- 导航点重复或状态不同步。
- 当前页状态在 `.visible`、`.active`、scroll position 之间混乱。
- 生成器无法确定最终页面由谁控制。

### 2. 容量模型缺失

现有生成器主要依赖：

- 固定每页放几个发言。
- 文本截断。
- 模板内部视觉容器。

但没有明确的页面容量规则，例如：

- 一个发言页最多多少字。
- 一个洞见页最多几个支撑点。
- 一个碰撞页是否允许长攻击和长防御同时存在。
- 中文长段落在 1366x768、1440x900、1920x1080 下是否溢出。

没有容量模型，就只能靠运气。

### 3. 模板既负责设计又负责行为

现在模板同时负责：

- CSS 视觉风格。
- 页面容器。
- 导航组件。
- 键盘/滚轮/点击行为。
- 进度条。
- 响应式。

这导致换一个模板就可能换一套行为。主链路需要把行为从模板里拿出来。

### 4. 验证不足

当前 `engine/validate_templates.py` 更像模板存在性检查。

它能检查：

- 是否有 `<!DOCTYPE html>`。
- 是否有 `{{slides}}`。
- 是否有某种导航标记。
- 是否有某种翻页逻辑。

但它不能检查最终 HTML：

- 是否重复注入导航。
- 是否存在 `overflow-y:auto` 或 `overflow-y:scroll`。
- 是否有多个 `wheelTimer`。
- 是否 nav dots 数量等于 slide 数量。
- 是否每页内容超出视口。
- 是否点击、键盘、滚轮都能翻页。

## V12 主链路

### 入口

新主入口建议为：

```text
engine/render_html_ppt_v12.py
```

它成为默认 HTML-PPT 出口。

旧入口保留但标记为 legacy：

- `engine/generate_v4.py`
- `engine/generate_v5.py`
- `engine/generate_v6.py`
- `engine/page-fragment-normalizer.py`
- `engine/page-fragment-normalizer-v3.py`

legacy 文件不作为 V12 主链路继续扩展。除非用户要求兼容旧产物，否则不在旧链路上修补新功能。

### 输入

第一阶段支持现有 JSON 内容输入。

输入对象至少包含：

- `title`
- `subtitle`
- `experts`
- `rounds`
- `insights`
- `open_questions`
- `dynamic_consensus_state`

后续可以增加 Markdown 输入，但第一阶段不扩大范围。

### 输出

输出仍然是单 HTML 文件：

```text
output/<书名>_圆桌洞见.html
```

HTML 内部只允许一套导航系统。

## Page Planner

Page Planner 不写 HTML，只生成页面计划。

页面计划是结构化数据：

```json
{
  "page_type": "speech",
  "title": "第一轮：文化属性是否决定命运",
  "layout": "two_speeches",
  "items": [],
  "meta": {
    "round_index": 1,
    "page_index": 2
  }
}
```

### 页面类型白名单

第一阶段只允许以下页面类型：

| 类型 | 用途 |
|:---|:---|
| `cover` | 封面 |
| `insight_overview` | 核心洞见总览 |
| `hypothesis_evolution` | 假设演化 |
| `tension_map` | 张力地图 |
| `experts` | 专家阵容 |
| `round_overview` | 轮次概览 |
| `speech` | 专家发言 |
| `clash` | 碰撞攻防 |
| `cost_analysis` | 代价分析 |
| `human_nature` | 人性分析 |
| `consensus_state` | 共识状态 |
| `open_questions` | 开放问题 |
| `summary` | 总结 |

不在白名单内的页面类型直接报错，不默默降级。

## Layout Engine

Layout Engine 从白名单布局中选择布局，不接受任意 HTML 片段。

### 布局白名单

| 布局 | 适用页面 | 规则 |
|:---|:---|:---|
| `hero_split` | cover | 左标题，右摘要 |
| `card_grid_2x3` | experts | 6 专家卡片 |
| `list_compact` | insight_overview/open_questions | 3 到 6 个短项 |
| `two_column_compare` | hypothesis_evolution/tension_map | 左右对照 |
| `two_speeches` | speech | 每页最多 2 条长发言 |
| `single_clash` | clash | 一次攻击和一次回应 |
| `stacked_cards` | cost_analysis/human_nature/consensus_state | 纵向卡片组 |
| `final_statement` | summary | 中心结论 |

布局决定 DOM 结构，内容只填槽位。

### 禁止 inline style

主链路生成的内容节点默认不写 inline style。

允许的例外：

- CSS 变量赋值。
- 必要的进度条宽度由脚本控制。

视觉差异通过 class 和 design tokens 控制。

## Capacity Engine

Capacity Engine 的职责是防止溢出。

它不追求精确排版引擎，而是用保守规则保证稳定。

### 第一阶段容量规则

| 内容类型 | 单页上限 |
|:---|:---|
| 标题 | 28 个中文字符 |
| 副标题 | 60 个中文字符 |
| 专家卡片 | 6 张，每张简介 60 字以内 |
| 发言页 | 每页最多 2 人，每人正文 220 字以内 |
| 碰撞页 | 攻击 180 字以内，回应 180 字以内 |
| 洞见总览 | 最多 5 条，每条 90 字以内 |
| 开放问题 | 最多 5 条，每条 80 字以内 |
| 总结页 | 主结论 120 字以内 |

超过上限时优先拆页。

只有在单个字段本身过长且无法自然拆页时，才生成摘要字段，并在页面计划里保留原文引用。

### 拆页策略

发言页：

```text
6 位专家发言 -> 3 页，每页 2 位
```

长发言：

```text
单人发言超过 220 字 -> 拆成观点页 + 论据页
```

长洞见：

```text
洞见超过 90 字 -> 总览页放摘要，详情页单独展开
```

长碰撞：

```text
攻击或回应过长 -> 拆成 clash_intro + clash_detail
```

禁止用内部滚动承载长内容。

## Single Renderer

Single Renderer 是唯一 HTML/CSS/JS 出口。

它负责：

- 生成 `<!DOCTYPE html>`、`html`、`head`、`body`。
- 注入统一 CSS。
- 渲染所有 slides。
- 注入唯一导航组件。
- 注入唯一翻页脚本。

模板不再注入导航脚本。

### 页面容器标准

每页必须满足：

```css
.slide {
  height: 100vh;
  overflow: hidden;
}
```

正文容器也默认 `overflow: hidden`。

禁止出现：

```css
overflow-y: auto;
overflow-y: scroll;
overflow: auto;
overflow: scroll;
```

### 导航标准

导航必须符合 `AGENTS.md`：

- 键盘翻页。
- 滚轮翻页，`preventDefault()`，400ms 节流。
- 点击空白区域下一页，排除交互元素。
- 每页一个导航点。
- 标准 `go(n)` 边界检查、状态切换、进度条更新。

V12 内部统一使用：

- `.slide`
- `.slide.visible`
- `.nav-dot`
- `#navDots`
- `#progress`

不再混用 `.active`、`.visible`、`.dot`、`.dots`。

## Acceptance Validator

新增最终 HTML 验收脚本：

```text
engine/validate_html_ppt_v12.py
```

它验证最终输出，而不是只验证模板。

### 静态检查

必须检查：

- 只有一个 `function go(` 或一个 `const go =`。
- 只有一个 `wheelTimer`。
- 只有一个 `#navDots`。
- 禁止 `overflow-y:auto`、`overflow-y:scroll`、`overflow:auto`、`overflow:scroll`。
- 每个 `.slide` 有 `height:100vh` 与 `overflow:hidden` 的规则覆盖。
- slide 数量大于 0。
- nav dot 由脚本按 slide 数生成，不手写多个静态点。
- 不存在 `<script>` 重复导航块。

### 浏览器检查

如环境可用，使用 Playwright 或浏览器工具打开最终 HTML，检查：

- 初始页可见。
- `ArrowRight` 后页码变化。
- `ArrowLeft` 后页码变化。
- wheel 后页码变化。
- 点击空白区域后页码变化。
- 每个 slide 的 `scrollHeight <= clientHeight + 容忍值`。
- 移动视口下没有横向溢出。

如果浏览器检查不可用，静态检查必须通过，并在结果中说明缺少浏览器验收。

## 设计系统位置

视觉设计放在第二阶段。

第一阶段只建立最小设计系统：

- `theme-default`
- 基础颜色 token
- 字体 token
- 间距 token
- 页面类型 class
- 布局 class

第二阶段再做：

- 多主题风格。
- 专家页视觉升级。
- 冲突页戏剧化设计。
- 洞见页更强信息层级。
- 与 guizang-ppt-skill 的风格能力融合。

这样做的原因是：如果第一阶段就追求风格多样，稳定性问题会继续被视觉复杂度掩盖。

## 旧模板处理

第一阶段不删除旧模板。

处理策略：

1. 旧模板继续保留，避免破坏已有产物。
2. `templates.json` 可以保留旧模板列表，但 V12 默认不从旧模板选择。
3. V12 有自己的 renderer 和 CSS。
4. 后续第二阶段再决定是否把旧模板改造成 theme。

## Skill 更新

V12 完成后，需要更新：

- `SKILL.md`
- `.trae/skills/roundtable-html-ppt/SKILL.md`

更新重点：

- HTML-PPT 主链路入口改为 V12。
- Agent 不再生成任意 HTML 片段。
- Agent 只生成结构化页面计划或内容字段。
- Python 负责布局、容量、渲染、验收。
- 内部滚动是硬错误。
- 最终 HTML 必须通过 V12 验收。

## 测试策略

### 单元测试

覆盖：

- Page Planner 页面顺序。
- Layout Engine 页面类型到布局映射。
- Capacity Engine 自动拆页。
- Renderer 只注入一套导航。
- Validator 能发现重复导航和内部滚动。

### 集成测试

使用现有 `content/遥远的救世主_V8.json` 生成 HTML。

必须验证：

- 能生成输出文件。
- 输出包含所有核心页面。
- slide 数和 nav 逻辑一致。
- 不含内部滚动。
- 不含重复导航脚本。

### 可选浏览器测试

如果 Playwright 可用：

- 打开生成 HTML。
- 截图检查首屏非空。
- 模拟键盘、滚轮、点击翻页。
- 检查每页没有垂直溢出。

## 成功标准

第一阶段完成时，认为成功的条件：

- 默认 HTML-PPT 主链路走 V12。
- 旧链路不再作为默认生成方式。
- 最终 HTML 只有一套导航系统。
- 验收脚本能阻止内部滚动、重复导航、页面溢出。
- 用现有示例书籍生成的 HTML 通过静态验收。
- 如果浏览器工具可用，生成 HTML 通过交互验收。
- 项目文档明确说明 V12 主链路和 legacy 边界。

## 非目标

第一阶段不做：

- 完整多主题系统。
- 大规模重写所有旧模板。
- 接入新的联网资料流程。
- 改造 V11 热点训练链路。
- 重新设计专家库训练算法。
- 生成 PPTX。

## 风险与应对

### 风险：容量估算不够精确

应对：

- 第一阶段使用保守上限。
- 对中文长段落优先拆页。
- 通过浏览器检查发现真实溢出。

### 风险：旧文件太多，入口混乱

应对：

- 新入口命名清晰。
- `SKILL.md` 标明 V12 是默认。
- legacy 文件保留但不推荐。

### 风险：视觉第一版不够惊艳

应对：

- 第一阶段目标是稳定，不是最终审美。
- 保留 design tokens 和 layout slots。
- 第二阶段单独做视觉质量升级。

## 实施顺序建议

1. 新建 V12 页面计划、容量、渲染、验收模块。
2. 用现有 JSON 跑通最小 HTML。
3. 增加静态验收。
4. 增加测试。
5. 切换默认入口和 skill 文档。
6. 用示例书籍验证输出。
7. 再进入第二阶段视觉设计升级。

