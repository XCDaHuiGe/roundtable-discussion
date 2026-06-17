# Roundtable Research OS 项目升级设计规格

## 目标

本次升级的目标不是新增一个孤立功能，而是把当前“圆桌洞见 HTML 生成项目”升级为一套更稳定、更深、更可验证的认知蒸馏系统。

目标形态：

- 底层：从零散 JSON、提示词和页面片段，升级为统一的 `CognitiveModel` 中间层。
- 稳定性：从“能生成”升级为“结构、质量、HTML 行为都可验证”。
- 产出质量：从“专家发言集合”升级为“问题轴、作者位移、认知张力、根秩、问答链共同支撑的洞见产品”。
- HTML 层面：延续 V12/V13 的单页无内部滚动、统一翻页、阅读型高信息密度原则，并新增面向认知结构的页面族。

本规格吸收 `ljg-skills` 中可复用的方法论，但不复制技能实现。项目应该拥有自己的稳定数据结构、渲染链路和质量门。

## 当前边界

现有项目已经形成几个重要约束：

- `Agent = LLM`，负责搜索、阅读、判断、生成辩论与洞见。
- `Python = 机械操作`，负责文件、结构化转换、渲染、容量拆页和验证。
- V12 是 HTML-PPT 稳定底座。
- V13 是阅读型 HTML-PPT 设计系统。
- Legacy 渲染器和旧模板可以保留，但不应继续作为主链路扩展入口。
- 每个 slide 或 section 必须 `height: 100vh` 且 `overflow: hidden`，内容超出必须拆页。

本次升级沿用这些边界，不做推倒重写。

## 推荐路线

采用增量升级路线：

```text
V13 阅读型 HTML-PPT
  -> CognitiveModel.v1
  -> Research OS 认知蒸馏层
  -> Roundtable Engine 张力增强
  -> Quality Gates 质量门
  -> V14 HTML 输出计划器
```

不推荐路线：

- 不把 `ljg-skills` 的输出格式直接塞进项目。
- 不让 Agent 直接生成最终 HTML。
- 不一次性重写所有旧模板。
- 不用更多提示词掩盖结构缺失。

## 总体架构

```text
输入材料
  -> SourceUnderstandingLayer
  -> CognitiveModel
  -> DistillationEngine
  -> RoundtableEngine
  -> PagePlanningEngine
  -> HTMLRenderer
  -> PublishPipeline
```

### SourceUnderstandingLayer

负责把书、论文、文章、概念、网页材料统一理解成可操作结构。

吸收来源：

- `ljg-read`：材料结构、段落角色、重要性、作者追问。
- `ljg-paper`：命题故事线、旧路、转折、证据、局限。
- `ljg-paper-river`：问题谱系、前序批判、后续进展。
- `ljg-learn`：概念画像、误解、历史、形式化、存在感。
- `ljg-plain`：白话可复述检查。

输出不直接进入 HTML，而是进入 `CognitiveModel.source_understanding`。

### CognitiveModel

项目新的统一中间层。所有后续圆桌、洞见、卡片、HTML、README 摘要都从它派生。

第一版建议结构：

```json
{
  "meta": {
    "title": "",
    "source_type": "book",
    "version": "CognitiveModel.v1"
  },
  "source_understanding": {
    "material_map": [],
    "author_problem": "",
    "paragraph_roles": [],
    "key_terms": []
  },
  "book_spine": {
    "core_question": "",
    "baseline_positions": [],
    "consensus_baseline": "",
    "author_move": "",
    "delta_sentence": "",
    "delta_type": "",
    "signature_terms": [],
    "landing_sentence": "",
    "carryaway": ""
  },
  "root_rank": {
    "domain_assumptions": [],
    "phenomena": [],
    "candidate_generators": [],
    "root_generators": [],
    "regeneration_matrix": [],
    "prediction_tests": []
  },
  "roundtable": {
    "participants": [],
    "tension_axes": [],
    "rounds": []
  },
  "distillation": {
    "insights": [],
    "qa_chain": [],
    "open_questions": [],
    "future_bets": []
  },
  "publishing": {
    "slides": [],
    "cards": [],
    "index_summary": ""
  },
  "quality": {
    "checks": []
  }
}
```

### DistillationEngine

负责从 `CognitiveModel` 中提取深度洞见，而不是复述材料。

吸收来源：

- `ljg-book`：问题轴、零点、作者位移、delta、落点、行囊。
- `ljg-rank`：找不可再降的生成器，并验证能否重新生成现象。
- `ljg-think`：沿为什么一路下钻到不可再分的根部。
- `ljg-qa`：把推理链铸成问题链。
- `ljg-word`：关键术语的核心语义、源头图像和顿悟句。

第一阶段必须产出：

- `core_question`
- `consensus_baseline`
- `author_move`
- `delta_sentence`
- `root_generators`
- `qa_chain`
- `insights`

### RoundtableEngine

圆桌不再是“6 位专家轮流说话”，而是围绕张力轴推进的结构化讨论。

吸收来源：

- `ljg-roundtable`：主持人、张力网络、回应关系、回合裂缝、下一问。
- `ljg-relationship`：交换、权力、边界、阶段、叙事五层关系诊断，可用于专家观点关系和议题关系。

每轮发言建议结构：

```json
{
  "round_index": 1,
  "guiding_question": "",
  "tension_axis": "",
  "speeches": [
    {
      "expert": "",
      "stance": "",
      "responds_to": null,
      "action_type": "definition",
      "claim": "",
      "evidence": "",
      "one_line": ""
    }
  ],
  "moderator": {
    "core_crack": "",
    "structure_map": "",
    "next_question": ""
  }
}
```

非首条发言必须有 `responds_to`，否则不算真正圆桌。

## HTML 页面族

V14 不新增随意模板，而是在 V13 页面族基础上扩展认知页面类型。

建议页面类型：

| 页面类型 | 用途 |
|:---|:---|
| `cover` | 封面，建立书或议题的第一印象 |
| `source_map` | 材料地图，说明输入材料如何被阅读 |
| `core_question` | 作者真正回答的问题 |
| `baseline_delta` | 旧共识 vs 作者位移 |
| `concept_anchor` | 核心概念锚点 |
| `rank_map` | 根秩图，展示不可再降的生成器 |
| `experts` | 专家阵容与各自功能 |
| `definition` | 概念定场，防止讨论漂移 |
| `round` | 圆桌回合 |
| `response_graph` | 发言回应图 |
| `clash` | 关键冲突 |
| `moderator_crack` | 主持人提炼裂缝与下一问 |
| `insight` | 洞见页 |
| `qa` | 问答链 |
| `library_lens` | 一本书的取景框 |
| `future_bets` | 如果作者是对的，未来会怎样 |
| `ending` | 最终落点和读者带走什么 |

每个页面类型必须有数据合同。字段缺失时只能降级到明确的替代页面，不能让页面空壳渲染。

## HTML 行为合同

所有最终 HTML 必须满足：

```css
.slide,
.section {
  height: 100vh;
  overflow: hidden;
}
```

禁止：

```css
overflow-y: auto;
overflow-y: scroll;
overflow: auto;
overflow: scroll;
```

必须保留四种翻页：

- 键盘翻页：方向键、空格、PageUp、PageDown、Home、End。
- 滚轮翻页：`preventDefault()`，400ms 节流。
- 点击空白区域翻页：排除导航点、按钮、卡片和交互元素。
- 导航点点击：每页一个点，当前页高亮。

最终 HTML 只能有一套导航逻辑和一个 `go()` 状态源。

## 质量门

### 认知质量门

| 检查项 | 通过条件 |
|:---|:---|
| 问题轴 | 必须有 `core_question`，且不是书名或主题复述 |
| 零点 | 必须说明旧共识或常见回答 |
| 作者位移 | 必须有 `delta_sentence`，形如“之前大家以为 X，作者说 Y” |
| 作者指纹 | 必须有至少 1 个独特术语、公式、模型或概念 |
| 根秩 | 至少给出 2 个候选生成器和 1 个最终根生成器 |
| 生成回测 | 根生成器必须能解释至少 3 个现象 |
| 纵向下钻 | 至少 3 层 `why` 链，或明确说明材料不足 |
| 问答链 | 问题必须有依赖顺序，答案必须有结论和边界 |

### 圆桌质量门

| 检查项 | 通过条件 |
|:---|:---|
| 专家功能 | 每位专家必须有参与理由和观点功能 |
| 张力轴 | 每轮必须有 `tension_axis` |
| 回应关系 | 非首条发言必须有 `responds_to` |
| 行动类型 | 发言需标记定义、质疑、补充、反驳、修正或综合 |
| 主持人裂缝 | 每轮主持人必须提炼 `core_crack` |
| 下一问 | 每轮必须产生推动下一轮的问题 |

### HTML 质量门

| 检查项 | 通过条件 |
|:---|:---|
| 单页高度 | 每个 slide/section 固定 100vh |
| 内部滚动 | 不允许任何内部滚动 |
| 导航唯一 | 只有一套 `go()`、`wheelTimer`、nav dots |
| 内容容量 | 文本超出视口时必须拆页 |
| 移动端 | 无横向溢出，按钮和文字不重叠 |
| 页面完整 | slide 数、nav dot 数、进度条状态一致 |

## 文件与模块建议

第一阶段新增模块建议：

```text
engine/cognitive_model/
  schema.py
  validate.py
  adapters.py

engine/distillation/
  book_spine.py
  rank.py
  qa_chain.py
  quality.py

engine/roundtable_engine/
  response_graph.py
  tension.py
  moderator.py

engine/html_ppt/
  cognitive_page_planner.py
  cognitive_page_contracts.py

engine/quality_gates/
  validate_cognitive_model.py
  validate_roundtable_quality.py
  validate_html_output.py
```

如果现有 V13 已有相近模块，应优先复用或小范围扩展，不重复造一套同名能力。

## 兼容策略

现有 `content/*_V8.json` 不废弃。

第一阶段应新增适配器，把旧数据转成部分 `CognitiveModel`：

```text
V8 JSON
  -> cognitive_model.adapters.from_v8()
  -> CognitiveModel.v1 partial
  -> V14 page planner
  -> V13/V14 renderer
```

旧数据缺少 `delta_sentence`、`root_rank`、`qa_chain` 时，质量门应给出 warning，而不是静默伪造。

## 产出链路

### 标准链路

```text
材料收集
  -> Agent 生成 CognitiveModel
  -> Python 校验 CognitiveModel
  -> Python 生成 slide plan
  -> Python 渲染 HTML
  -> Python 静态质量检查
  -> 浏览器交互与溢出检查
  -> README / index 更新
  -> git commit / push
```

### 无 GPT 保底链路

```text
已有 V8 JSON
  -> 适配为 partial CognitiveModel
  -> 只生成可证明字段对应页面
  -> 缺失深度字段显示为质量 warning
  -> HTML 仍必须稳定可用
```

无 GPT 模式可以降低洞见深度，但不能降低 HTML 稳定性。

## 测试策略

### 单元测试

覆盖：

- `CognitiveModel` 必填字段校验。
- V8 到 `CognitiveModel` 的适配。
- `delta_sentence` 格式检查。
- roundtable `responds_to` 检查。
- QA 链依赖检查。
- 根秩回测检查。
- 页面类型到页面合同的映射。

### 集成测试

至少使用一本已有书：

```text
content/<书名>_V8.json
  -> CognitiveModel
  -> slide plan
  -> output/<书名>_圆桌洞见.html
  -> validators
```

通过标准：

- 输出 HTML 文件存在。
- 页面数大于 0。
- nav dots 与页面数一致。
- 不包含内部滚动。
- 键盘、滚轮、点击翻页可用。
- 每页无明显垂直溢出。

### 浏览器验证

如果本地浏览器工具可用，必须检查：

- 桌面视口首屏非空。
- 移动视口无横向溢出。
- `ArrowRight` 翻页成功。
- `ArrowLeft` 返回成功。
- wheel 翻页成功。
- 点击空白区域翻页成功。
- 所有 slide 的 `scrollHeight <= clientHeight + tolerance`。

## 分阶段实施

### Phase 1：规格与模型

- 写入本设计规格。
- 定义 `CognitiveModel.v1` schema。
- 实现 V8 适配器。
- 实现模型质量校验器。

成功标准：

- 旧 V8 JSON 可以生成 partial `CognitiveModel`。
- 缺失深度字段会产生明确 warning。
- 校验器有单元测试。

### Phase 2：认知蒸馏增强

- 增加 book spine 字段生成约束。
- 增加 root rank 结构。
- 增加 QA chain 结构。
- 增加 roundtable response graph。

成功标准：

- 新书内容可以产出完整 `CognitiveModel`。
- 至少一份旧书可以补齐关键认知字段。
- 圆桌发言有可追踪回应关系。

### Phase 3：HTML 页面计划器

- 新增认知页面族。
- 把 `CognitiveModel` 转换为 slide plan。
- 复用 V13 renderer 或做最小扩展。

成功标准：

- 至少生成 `core_question`、`baseline_delta`、`rank_map`、`response_graph`、`qa` 五类新增页面。
- 所有新增页面无内部滚动。

### Phase 4：质量门与浏览器验证

- 增强 HTML 静态检查。
- 增加浏览器交互检查。
- 增加移动端溢出检查。

成功标准：

- 生成 HTML 能通过静态检查。
- 浏览器验证覆盖翻页和溢出。
- 检查失败时给出具体页面和原因。

### Phase 5：出版链路

- 统一 README 和 index 更新字段来源。
- 增加发布前检查命令。
- 保持项目自动更新规则。

成功标准：

- 新书完成后，README 和 index 信息来自同一份模型或派生摘要。
- commit 前能看到模型质量、HTML 质量、发布清单三个结果。

## 风险与处理

### 风险：范围过大

处理：

- 先做模型和适配器，不先改所有模板。
- 每个阶段必须能独立验证。
- 旧链路保留，直到新链路生成结果稳定。

### 风险：深度字段被伪造

处理：

- 缺失字段标 warning，不自动编造。
- Agent 负责补齐认知字段，Python 负责检查格式和完整性。
- 质量门区分 error 与 warning。

### 风险：HTML 好看但不可用

处理：

- HTML 行为合同优先于视觉尝试。
- 所有新页面必须通过无内部滚动检查。
- 浏览器验证作为发布前必跑项。

### 风险：新模型破坏旧内容

处理：

- V8 适配器先支持 partial model。
- 旧渲染链路保留。
- 新链路从一本试点书开始。

## 非目标

本阶段不做：

- 全量重写所有模板。
- 删除 legacy 渲染器。
- 自动下载盗版书籍全文。
- 接入外部 LLM API。
- 生成 PPTX。
- 一次性把所有历史输出重制。
- 把所有 `ljg-skills` 原样迁移进项目。

## 成功标准

项目升级完成时应满足：

- 有统一的 `CognitiveModel.v1`。
- 旧 V8 内容可适配进入新模型。
- 新书产出必须经过认知质量门、圆桌质量门和 HTML 质量门。
- HTML 仍满足项目铁律：无内部滚动，四种翻页完整。
- 至少一本书使用新链路生成并通过验证。
- README 和 index 更新链路有明确数据来源。
- 旧链路仍可保留为兼容入口，但新链路是默认推荐路径。

