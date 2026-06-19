# HTML-PPT 开放设计改造方案

> 本方案回应一个核心问题：HTML-PPT 的功能底盘必须稳定，但视觉风格、展示逻辑、页面排版和内容呈现不能被固定模板锁死。

## 1. 改造目标

当前系统已经从“agent 直接写 HTML”进化到“Python 规划 + Python 渲染”，这是正确方向。但现在仍有一个硬伤：

```text
page_type -> layout 是一对一映射
```

例如：

```text
case_shock -> case_file
cognitive_upgrade -> evolution_ladder
clash -> clash_courtroom
insight -> reading_brief_4zone
```

这会导致每次升级后，demo 看起来仍然像同一个模板换字。

新的目标不是取消页面类型，而是把页面类型降级为工程标签，把真正的设计入口改成：

```text
内容信号 -> 展示逻辑 -> 构图策略 -> 布局变体 -> HTML 渲染
```

一句话：

```text
固定 PPT 底盘，开放设计表达。
```

## 2. 不变的固定层

这些能力必须固定，不参与风格发散：

### 2.1 播放底盘

- 键盘翻页：方向键、空格、PageUp/PageDown、Home、End。
- 滚轮翻页：阻止默认滚动，400ms 节流。
- 点击空白翻页。
- 导航点跳转。
- 当前页进度条。
- 只允许一页 `.visible`。

### 2.2 单页安全

- 每页 `height:100vh`。
- 每页 `overflow:hidden`。
- 禁止内部滚动。
- 内容超出必须拆页。
- 桌面和移动端都不能遮挡主要内容。

### 2.3 内容底线

- 每页必须有明确阅读动作。
- 每页必须有可带走判断。
- 不能用空泛词填充页面，例如“圆桌张力”“观点冲突”“深度洞见”单独当结论。
- 案例页必须出现事件、结果或代价中的至少两类。
- 认知升级页必须出现旧框架和新框架。

## 3. 需要开放的设计层

这些层必须开放，不再固定模板：

### 3.1 展示逻辑

展示逻辑回答：

```text
这段内容要让读者发生什么观看动作？
```

建议第一批展示逻辑：

| display_logic | 适用内容 | 观看动作 |
|---|---|---|
| `impact` | 强结论、残酷事实、反直觉判断 | 先被击中 |
| `evidence` | 案例链、人物关系、材料碎片 | 看见证据如何互相指认 |
| `cross_exam` | 观点需要被追问 | 像审讯一样暴露漏洞 |
| `diagnosis` | 表层事件背后有结构病灶 | 像 X 光片一样照出结构 |
| `cost` | 行动、关系、时间、认知代价 | 让代价可视化 |
| `delta` | 旧共识到新判断 | 看到坐标位移 |
| `spectrum` | 多专家、多立场、多解释框架 | 看见立场空间 |
| `mechanism` | 系统、反馈、生成器、因果链 | 拆开机器 |
| `manifesto` | 最终洞见、可带走判断 | 钉住一句可迁移结论 |
| `quiet_reading` | 高密度解释、收束、注释 | 降噪阅读 |

### 3.2 页面类型

页面类型继续保留，但它变成展示逻辑之后的工程归类。

例如 `case_shock` 不再等于 `case_file`，而是：

```text
case_shock + impact      -> shock_poster
case_shock + evidence    -> evidence_wall
case_shock + cross_exam  -> interrogation_room
case_shock + diagnosis   -> xray_diagnosis
case_shock + cost        -> cost_blast
```

`cognitive_upgrade` 也不再等于 `evolution_ladder`，而是：

```text
cognitive_upgrade + delta      -> delta_map
cognitive_upgrade + diagnosis  -> xray_diagnosis
cognitive_upgrade + mechanism  -> mechanism_cutaway
cognitive_upgrade + quiet_reading -> annotated_reading
```

### 3.3 布局变体

每个页面类型必须有多个布局变体。

第一批建议：

| layout_variant | 视觉形态 | 适合逻辑 |
|---|---|---|
| `shock_poster` | 黑场大字报 | impact |
| `evidence_wall` | 证据墙、红线、便签 | evidence |
| `interrogation_room` | 审讯室、证物、问答对抗 | cross_exam |
| `xray_diagnosis` | X 光片、扫描线、病灶标签 | diagnosis |
| `cost_blast` | 大字爆破、成本栈 | cost |
| `delta_map` | 坐标位移、前后世界观 | delta |
| `stance_radar` | 立场雷达、解释空间 | spectrum |
| `mechanism_cutaway` | 机器剖面、反馈回路 | mechanism |
| `editorial_spread` | 杂志跨页、主次洞见 | quiet_reading |
| `manifesto_poster` | 宣言海报、可带走句 | manifesto |

## 4. 推荐架构

我建议采用方案 B：最小重构，但增加展示逻辑层。

### 方案 A：继续一对一模板

```text
page_type -> layout -> render
```

优点：改动最小。

缺点：继续死板，不解决根因。

结论：不推荐。

### 方案 B：展示逻辑层改造

```text
content signal -> display_logic -> layout_variant -> render
```

优点：

- 保留现有 Python 主链。
- 不推翻当前页面类型。
- 能明显打破模板感。
- 容易加 validator。

缺点：

- 需要新增几个字段和 renderer 分发逻辑。

结论：推荐。

### 方案 C：完全设计生成器

```text
agent/image model -> concept -> code -> browser QA
```

优点：设计自由度最高。

缺点：

- 不稳定。
- 难批量生产书籍。
- 容易再次变成 agent 临场写 HTML。

结论：只适合单次精品，不适合主链。

## 5. 新数据结构

### 5.1 ReadingPage 增强

当前：

```python
ReadingPage(
    page_type="case_shock",
    title="...",
    thesis="...",
    takeaway="...",
    layout="case_file",
    blocks=[...],
    meta={...},
)
```

建议升级：

```python
ReadingPage(
    page_type="case_shock",
    display_logic="evidence",
    layout_variant="evidence_wall",
    beat="让读者看到观点如何被现实证据包围",
    reader_question="这个案例到底推翻了哪个抽象判断？",
    title="证据墙",
    thesis="...",
    takeaway="...",
    layout="case_shock_dynamic",
    blocks=[...],
    source_refs=["rounds[1].reality_cases[0]", "rounds[1].cost_discussion"],
    meta={"tone": "dark", "intensity": "high"},
)
```

字段说明：

| 字段 | 作用 |
|---|---|
| `display_logic` | 展示逻辑，决定观看动作 |
| `layout_variant` | 具体构图变体 |
| `beat` | 这一页为什么存在 |
| `reader_question` | 读者看到这页时要追问什么 |
| `source_refs` | 页面内容来自模型的哪个位置 |
| `intensity` | 视觉强度，用于节奏调度 |

### 5.2 PageContract 增强

新增 `PageContract`：

```python
@dataclass
class PageContract:
    page_type: str
    allowed_display_logic: list[str]
    required_blocks: list[str]
    allowed_variants: list[str]
    default_logic: str
    default_variant: str
    min_blocks: int
    max_blocks: int
    can_split: bool
    forbidden_generic_terms: list[str]
```

示例：

```python
PageContract(
    page_type="case_shock",
    allowed_display_logic=["impact", "evidence", "cross_exam", "diagnosis", "cost"],
    required_blocks=["event", "outcome", "cost"],
    allowed_variants=["shock_poster", "evidence_wall", "interrogation_room", "xray_diagnosis", "cost_blast"],
    default_logic="impact",
    default_variant="shock_poster",
    min_blocks=3,
    max_blocks=6,
    can_split=True,
    forbidden_generic_terms=["观点冲突", "深度案例", "现实反噬"],
)
```

### 5.3 LayoutVariant 增强

新增 `LayoutVariant`：

```python
@dataclass
class LayoutVariant:
    name: str
    display_logic: str
    visual_temperature: str
    density: str
    renderer: str
    max_text_chars: int
    required_block_kinds: list[str]
    rhythm_weight: int
```

示例：

```python
LayoutVariant(
    name="evidence_wall",
    display_logic="evidence",
    visual_temperature="dark_forensic",
    density="medium",
    renderer="render_evidence_wall",
    max_text_chars=620,
    required_block_kinds=["event", "outcome", "cost"],
    rhythm_weight=4,
)
```

## 6. 内容到展示逻辑的选择规则

新增 `display_logic_selector.py`。

输入：

- `page_type`
- `blocks`
- `round_data`
- `book_spine`
- `distillation`

输出：

- `display_logic`
- `layout_variant`
- `reason`

第一批规则：

```text
如果有 reality_case 且 cost_analysis >= 2
  -> display_logic = cost
  -> layout_variant = cost_blast

如果有 reality_case 且 case_content 很强但 cost 较少
  -> display_logic = impact
  -> layout_variant = shock_poster

如果有 case_source/event/outcome 多碎片
  -> display_logic = evidence
  -> layout_variant = evidence_wall

如果有 attack/defense/question
  -> display_logic = cross_exam
  -> layout_variant = interrogation_room

如果有 old_thinking/new_thinking
  -> display_logic = delta
  -> layout_variant = delta_map

如果有 root_generators/regeneration_matrix
  -> display_logic = mechanism
  -> layout_variant = mechanism_cutaway

如果是 ending 或 carryaway
  -> display_logic = manifesto
  -> layout_variant = manifesto_poster
```

## 7. 节奏调度器

新增 `rhythm_planner.py`。

它不决定内容，只调整全 deck 的视觉节奏。

检查项：

- 不允许连续 3 页同一 `display_logic`。
- 不允许连续 2 页同一 `layout_variant`。
- 8 页以上必须至少包含：
  - 1 页 `impact` 或 `cost`
  - 1 页 `quiet_reading`
  - 1 页 `delta`
  - 1 页 `spectrum` 或 `mechanism`
- 高强度页面之间必须插入解释页或安静页。
- 结尾前不能连续堆冲击页，必须降噪收束。

## 8. Renderer 改造

当前 renderer 主要按 `layout` 分发。

建议改成：

```python
renderer_key = page.layout_variant or page.layout
renderer = VARIANT_RENDERERS[renderer_key]
```

新增 renderer：

```text
render_shock_poster()
render_evidence_wall()
render_interrogation_room()
render_xray_diagnosis()
render_cost_blast()
render_delta_map()
render_stance_radar()
render_mechanism_cutaway()
render_editorial_spread()
render_manifesto_poster()
```

保留旧 renderer 作为 fallback：

```text
reading_brief_4zone
magazine_focus
stance_spectrum
case_file
clash_courtroom
evolution_ladder
tension_bars
question_wall
```

关键原则：

```text
旧 layout 负责稳定兜底
新 variant 负责设计表达
```

## 9. Validator 改造

新增三类验收。

### 9.1 底盘验收

继续检查：

- `<!DOCTYPE html>`
- 导航点。
- 键盘翻页。
- 滚轮翻页。
- 点击翻页。
- `height:100vh`
- 禁止 `overflow-y:auto/scroll`

### 9.2 反模板化验收

新增：

- `layout_variant` 不得全 deck 单一。
- 相邻页不得重复同一 `layout_variant`。
- 全 deck 至少出现 4 种 `display_logic`。
- `case_shock` 不得永远使用同一个变体。
- 如果页数超过 12，至少出现 6 种以上 layout variant。

### 9.3 内容匹配验收

新增：

- `display_logic=cost` 必须有 cost block。
- `display_logic=evidence` 必须有至少 3 个证据型 block。
- `display_logic=delta` 必须有 old/new 或 before/after。
- `display_logic=cross_exam` 必须有 question/attack/defense。
- `display_logic=mechanism` 必须有 generator/cause/effect。

## 10. 文件改造清单

### 第一批新增

```text
engine/html_ppt/display_logic.py
engine/html_ppt/layout_variants.py
engine/html_ppt/display_logic_selector.py
engine/html_ppt/rhythm_planner.py
engine/html_ppt/open_design_validators.py
```

### 第一批修改

```text
engine/html_ppt_v13.py
  - ReadingPage 增加 display_logic/layout_variant/beat/reader_question/source_refs

engine/html_ppt/cognitive_page_contracts.py
  - 从 PAGE_LAYOUTS 升级为 PAGE_CONTRACTS + LAYOUT_VARIANTS

engine/html_ppt/cognitive_page_planner.py
  - 页面生成后调用 display_logic_selector
  - 增加 beat 和 source_refs
  - 生成后调用 rhythm_planner

engine/html_ppt_v13_renderer.py
  - 增加 VARIANT_RENDERERS
  - 新增第一批激进布局 renderer

engine/validate_html_ppt_v13.py
  - 接入 open_design_validators
```

### 第一批测试

```text
tests/test_display_logic_selector.py
tests/test_layout_variants.py
tests/test_rhythm_planner.py
tests/test_open_design_validators.py
tests/test_html_ppt_v13_renderer_variants.py
```

## 11. 落地阶段

### Phase 1：数据结构和选择器

目标：不改变现有输出，只让 page 携带新信息。

改动：

- 增加字段：`display_logic`、`layout_variant`、`beat`、`reader_question`、`source_refs`。
- 增加 `display_logic_selector.py`。
- 增加基础测试。

验收：

- 现有测试继续通过。
- 每个页面都有 `display_logic`。
- 旧 renderer 还能照常输出。

### Phase 2：布局变体池

目标：让 `case_shock`、`cognitive_upgrade`、`insight` 先活起来。

优先做三个页面类型：

```text
case_shock:
  shock_poster
  evidence_wall
  interrogation_room
  xray_diagnosis
  cost_blast

cognitive_upgrade:
  delta_map
  xray_diagnosis
  mechanism_cutaway

insight:
  editorial_spread
  manifesto_poster
  quiet_reading
```

验收：

- 同一本书输出中，同类页面不再都长一样。
- 现有底盘规则不破。

### Phase 3：节奏调度器

目标：避免全 deck 视觉同质化。

改动：

- 接入 `rhythm_planner.py`。
- 检查连续页面展示逻辑。
- 自动替换重复变体。

验收：

- 大于 8 页的 deck 至少有 4 种展示逻辑。
- 相邻页不重复同一布局变体。

### Phase 4：开放设计 validator

目标：让“死板”成为可测试失败。

新增失败条件：

- variant 数量太少。
- 同一 page_type 永远同一 variant。
- 页面缺少 beat。
- 展示逻辑与内容 block 不匹配。

验收：

- 老式固定模板输出会被 warning 或 fail。
- 新式开放设计输出通过。

### Phase 5：风格锁池

目标：让不同书有不同气质，但不失控。

第一批风格锁：

```text
roundtable_editorial      出版物 / 深度阅读
forensic_black            证据墙 / 案例冲击
swiss_delta               瑞士网格 / 认知位移
quiet_academic            学术注释 / 高密度解释
manifesto_poster          宣言海报 / 收束洞见
```

验收：

- 每个 deck 一个主风格锁。
- 每页可有局部视觉温度，但不脱离主风格。

## 12. 最终生成链路

目标链路：

```text
content json
  -> cognitive_page_planner
  -> page contracts
  -> display_logic_selector
  -> layout_variant selector
  -> rhythm_planner
  -> html_ppt_v13_renderer
  -> fixed runtime injection
  -> validate_html_ppt_v13
  -> browser audit
  -> final html
```

核心变化：

```text
现在：page_type -> layout -> HTML
以后：content signal -> display_logic -> layout_variant -> HTML
```

## 13. 改造成功标准

一套输出算成功，必须满足：

- 固定底盘不坏：翻页、导航、无滚动、无溢出。
- 设计不死板：同类页面有多个合法变体。
- 内容匹配设计：不是随机炫技，而是内容信号决定展示逻辑。
- 页面有节奏：强冲击、解释、位移、证据、收束交替出现。
- 代码可维护：新增变体是注册表扩展，不是到处写 if/else。
- validator 能拦住旧问题：一对一固定模板、空泛洞见、连续重复布局都会被发现。

## 14. 推荐立即执行的第一步

先做 Phase 1 + Phase 2 的最小闭环：

1. 给 `ReadingPage` 加新字段。
2. 新增 `display_logic.py` 和 `layout_variants.py`。
3. 改造 `case_shock`：
   - 让它根据内容自动选择 `shock_poster`、`evidence_wall`、`interrogation_room`、`xray_diagnosis`、`cost_blast`。
4. renderer 只新增这 5 个 case shock 变体。
5. validator 增加：
   - 每页必须有 `display_logic`。
   - `case_shock` 不能始终只有 `case_file`。

这样最小，但能直接击中你指出的问题：固定模板、demo 同质化、没有美化、内容与设计不匹配。
