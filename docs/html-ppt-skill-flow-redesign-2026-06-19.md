# HTML-PPT Skill 流程重构设计

> 目标：让圆桌会议的 HTML-PPT 产出从“agent 临场写页面”升级为“内容合同 + 页面合同 + 风格锁 + Python 渲染 + 双重验收”的稳定生产线。

## 1. 这次学习得到的核心判断

最近新版本变差，不是 HTML-PPT 这个媒介本身的问题，而是生成权力放错了层。

旧问题可以归纳为三点：

1. 生成器锁死表达。模型一旦直接生成最终 HTML，就会把内容、布局、风格、动效和导航混在一起，后续只能修补，不能治理。
2. 没有 HTML-PPT 框架型 skill。页面类型、节奏、信息密度、翻页器、安全区、无内部滚动等规则没有形成强合同。
3. 没有风格排版 skill。视觉规范没有先行，导致 agent 靠临场审美写 CSS，越升级越像模板拼贴。

新的方向：

```text
书籍材料
  -> 内容蒸馏合同
  -> 圆桌讨论合同
  -> 页面规划合同
  -> 风格锁
  -> Python 确定性渲染
  -> 静态验证 + 浏览器验证 + 内容锐度验证
  -> HTML-PPT
```

核心原则：agent 负责理解、判断、提炼和设计决策；Python 负责结构化、渲染、容量控制和验收。agent 不再直接写最终 HTML。

## 2. 外部项目可迁移的精华

### visual-style-ppt-skill

可吸收点：

- Style Lock 先于生成。每套风格必须明确定义字体、色彩、语言密度、网格、组件、禁忌和封面/内页差异。
- 先生成 outline 和 prompts，再进入视觉生产。迁移到本项目就是先生成 `deck-plan` 和 `style-lock`，再渲染。
- 多页作品先看节奏板。不能一页一页孤立设计，要先检查整套 PPT 的主题节奏、布局节奏和信息密度。
- 一个作品只用一个风格源。不能同时混用多个外部项目的审美语言。

对圆桌项目的落点：

- 增加 `style_locks/roundtable-editorial.json` 或 `styles/roundtable-editorial.md`。
- 每次生成前明确：本书走“出版级阅读型 PPT”，还是“演讲型 PPT”，还是“图解型 PPT”。
- 默认推荐“出版级阅读型 PPT”：低装饰、高信息、强分隔线、少渐变、少炫技。

### guizang-ppt-skill

可吸收点：

- 模板 class 必须先预检。agent 不能发明不存在的 CSS class。
- 页面节奏表必须先于写 slide。不能连续三页同一视觉气质。
- 浏览器视觉 QA 必须做。只看代码不算完成。
- 不允许 emoji 冒充图标，不允许导航被内容遮挡，不允许每页变成同一种卡片。
- checklist 基于真实失败沉淀，应该成为生成流程的一部分。

对圆桌项目的落点：

- `cognitive_page_contracts.py` 中的 `page_type -> layout` 要升级为“布局注册表”。
- validator 要检查连续布局重复、暗/亮节奏、核心页面缺失、导航点数量、单页 overflow。
- 每次生成后必须跑浏览器审计：可见页数量、当前页唯一、无内部滚动、关键页面无遮挡。

### html-ppt-skill

可吸收点：

- 一套 theme 是一套视觉气质；一个 layout 是一种页面类型；runtime 只管播放和交互。
- 必须从模板和布局库开始，不从空白 HTML 开始。
- token 驱动颜色、字体、阴影、圆角，不在 slide 里写临时颜色。
- speaker notes 和观众可见内容分离。
- 单页逻辑必须清晰：一页就是一个 logical page。

对圆桌项目的落点：

- 形成自己的三层：
  - `style lock`：给 agent 和 renderer 读的风格规范。
  - `layout registry`：给 renderer 读的页面布局注册表。
  - `runtime`：键盘、滚轮、点击、导航点、进度条。
- renderer 不再拥有审美自由，只读取 style token 和 layout renderer。
- 如果要保留演讲者注释，放在隐藏 notes 数据中，不能污染可见页面。

### web-design-skill / beautiful-article

可吸收点：

- 生产流程分关卡：source -> plan -> first spread -> full build -> final review -> repair。
- 信息密度是设计变量。100% 信息保留和 40% 视觉传播不是同一种作品。
- theme profile 给 agent 读，runtime theme 给浏览器读。两者必须同时存在。
- 先做第一组代表页验收，再生成全量内容。
- 修复必须是最小切片，不因为一个问题重写整套。

对圆桌项目的落点：

- 生成全书 PPT 前先产出 3 页代表页计划：封面、核心问题页、冲突/案例页。
- 内容密度要写入计划：圆桌洞见默认不是演讲提词器，而是阅读型 PPT，信息保留建议 70%-85%。
- 主题不能只是 CSS，要有“写作和布局指导”。例如：标题多尖锐、每页多少字、何时用大数字、何时用案例文件。

### ppt-anything

可吸收点：

- 每一页都是故事 beat。先问这一页让读者看到什么、感到什么、记住什么。
- 相邻页必须有布局和姿态变化。这个原则可迁移为：相邻页不能同布局、同信息形态、同视觉重量。
- 内容优先。任何角色、装饰、动效抢走内容注意力，都是 bug。
- 生成前要给用户看 outline 或 design intent，不能直接烧成本生成。

对圆桌项目的落点：

- 每页增加 `beat` 字段：`role`、`reader_question`、`memory_hook`、`why_this_page_exists`。
- validator 检查空泛页面：如果页面没有独立 beat，就不能进入渲染。

## 3. 新的圆桌 HTML-PPT 生成架构

### 层 1：内容蒸馏合同

输入：书籍材料、已有笔记、网页资料、用户目标。

输出：`content-brief.json`。

必须包含：

- `core_question`：作者真正回答的问题。
- `consensus_baseline`：旧共识或常见理解。
- `author_delta`：作者带来的认知位移。
- `signature_terms`：关键术语。
- `reality_cases`：现实案例或文本中的冲击性事件。
- `tension_axes`：全书核心张力。
- `portable_insights`：可迁移洞见。
- `uncertainties`：不能确定的内容。

验收标准：

- 没有 `core_question`，不能生成 PPT。
- 有 `reality_cases`，后续必须至少生成一页 `case_shock`。
- 有 `author_delta`，后续必须至少生成一页 `baseline_delta` 或 `cognitive_upgrade`。
- 有 `tension_axes`，后续必须至少生成一页 `tension_map`。

### 层 2：圆桌讨论合同

输入：`content-brief.json`。

输出：`roundtable-model.json`。

必须包含：

- 专家阵容，每位专家的立场、盲点、攻击方式。
- 每一轮的追问、张力轴、发言、冲突、主持人裁决。
- 现实案例如何改变讨论。
- 每一轮留下的认知位移。

验收标准：

- 每轮必须有明确追问，不能只有主题。
- 每轮至少一个分歧点或成本讨论。
- 专家发言不能互相独立堆叠，必须有回应关系。

### 层 3：页面规划合同

输入：`roundtable-model.json`。

输出：`deck-plan.json`。

每页结构：

```json
{
  "index": 7,
  "page_type": "case_shock",
  "layout": "case_file",
  "beat": "用现实代价打断抽象争论",
  "reader_question": "这个观点碰到现实后会付出什么代价？",
  "takeaway": "真正让思想变硬的不是观点，而是观点撞到现实后的代价。",
  "required_blocks": ["case_source", "event", "outcome", "cost"],
  "tone": "dark",
  "density": "medium",
  "source_refs": ["rounds[1].reality_cases[0]"]
}
```

验收标准：

- 每页必须有 `beat`，不能只给 `title`。
- 相邻两页不能使用同一 `layout`。
- 8 页以上必须有至少一页暗色强冲击页和一页安静解释页。
- `case_shock`、`cognitive_upgrade`、`tension_map` 等关键页面必须由内容触发，不由审美偏好触发。
- 页面总数不是目标，阅读节奏才是目标。内容多就拆页，绝不内部滚动。

### 层 4：风格锁

输入：用户目标、书籍气质、输出场景。

输出：`style-lock.json` 或 `style-lock.md`。

默认风格建议：

```text
roundtable-editorial
- 适用：书籍深度讨论、思想类圆桌、阅读型 PPT
- 气质：出版物、研究简报、高级编辑部
- 背景：温白或近黑
- 字体：中文宋体/黑体组合，标题用衬线，正文用无衬线
- 布局：硬网格、细线、分栏、案例文件、对照表
- 禁止：大面积紫蓝渐变、圆角堆卡片、emoji 图标、装饰性光斑、无意义动效
- 内容密度：每页一个判断，一个问题，一个可带走句
```

验收标准：

- 一个 deck 只能绑定一个 style lock。
- renderer 只能使用 style lock 中定义的 token。
- 新增主题必须同时有 agent 读的 profile 和浏览器读的 CSS token。

### 层 5：确定性渲染

输入：`deck-plan.json`、`style-lock`、页面数据。

输出：HTML。

renderer 职责：

- 根据 `page_type` 选择布局。
- 根据 style token 渲染颜色、字体、线条、间距。
- 根据容量规则裁剪或拆页。
- 注入统一 runtime：键盘、滚轮、点击、导航点、进度条。
- 禁止内部滚动。

renderer 不做的事：

- 不发明新观点。
- 不临场改写核心结论。
- 不发明新布局 class。
- 不因为空间不足删除必保留内容。

## 4. 页面类型升级建议

现有页面类型已经有雏形，建议升级为强合同。

| page_type | 内容角色 | 触发条件 | 失败表现 |
|---|---|---|---|
| `cover` | 建立书名、问题、阅读承诺 | 必有 | 像普通封面，没有问题意识 |
| `source_map` | 交代材料证据来自哪里 | 有多源材料或作者问题 | 背景介绍堆砌 |
| `experts` | 展示解释机器与盲点 | 有圆桌专家 | 只是头像名片 |
| `core_question` | 锁定作者问题 | 有核心问题 | 主题泛泛 |
| `baseline_delta` | 旧共识到作者位移 | 有旧共识或位移 | 只有观点复述 |
| `concept_anchor` | 锁定关键概念 | 有术语 | 术语墙 |
| `rank_map` | 找底层生成器 | 有根因/秩分析 | 把结论当列表 |
| `round_opening` | 开启一轮追问 | 每轮必有 | 只写“第几轮” |
| `response_graph` | 展示回应关系 | 有多专家发言 | 发言并列堆叠 |
| `case_shock` | 现实案例打断抽象 | 有 reality_cases | 案例被压成一句话 |
| `clash` | 暴露真正分歧 | 有攻击与防守 | 假冲突、无代价 |
| `cognitive_upgrade` | 留下认知位移 | 有新旧思维对照 | 热闹但无升级 |
| `qa` | 用问答链复现推理 | 有 QA chain | 问答像百科 |
| `insight` | 提炼可迁移洞见 | 有洞见 | 金句堆砌 |
| `open_questions` | 留下继续追问 | 有未解问题 | 像未完成清单 |
| `tension_map` | 汇总全书核心张力 | 有多轮张力 | 总结页空泛 |
| `ending` | 收束为可带走判断 | 必有 | 客套收尾 |

## 5. 新流程的实际执行顺序

1. 读取材料，产出 `content-brief.json`。
2. 做内容自检：问题、旧共识、位移、案例、张力是否齐。
3. 生成 `roundtable-model.json`。
4. 生成 `deck-plan.json`，先不渲染。
5. 生成 `style-lock`，并绑定唯一主题。
6. 做“节奏板”检查：
   - 页面顺序是否像一场阅读旅程。
   - 是否连续重复同布局。
   - 是否有强弱、明暗、案例、解释、总结的节奏。
7. 先渲染代表页：
   - 封面。
   - 核心问题/位移页。
   - 案例冲击或冲突页。
8. 代表页通过后渲染全 deck。
9. 静态 validator：
   - HTML 声明。
   - 导航组件。
   - 四种翻页方式。
   - 无内部滚动。
   - 每页有标题和最终洞见。
   - 关键页面齐全。
   - 相邻布局不重复。
10. 浏览器 validator：
    - 只有一页 visible。
    - 导航点数量等于页数。
    - 所有页面无 overflow。
    - 当前页切换正常。
    - 桌面和移动视口无内容遮挡。
11. 内容锐度 validator：
    - 每页有一个刺点句或位移句。
    - 禁止“圆桌张力”“观点冲突”“深度洞见”这类无源泛词单独充当结论。
    - 案例页必须有事件、结果、代价。
    - 升级页必须有旧思维和新思维。
12. 只做最小修复，不重写整套。

## 6. 建议新增或改造的文件

短期不需要推翻现有 V13，只补合同和验收。

建议新增：

```text
docs/html-ppt-skill-flow-redesign-2026-06-19.md
engine/html_ppt/style_locks/
  roundtable_editorial.json
engine/html_ppt/deck_plan.py
engine/html_ppt/rhythm_validator.py
engine/html_ppt/content_sharpness_validator.py
engine/html_ppt/browser_audit.py
```

建议增强：

```text
engine/html_ppt/cognitive_page_contracts.py
  - 从 page_type -> layout 映射升级为 page_type 合同
  - 增加 required_blocks、trigger、minimum_density、forbidden_generic_words

engine/html_ppt/cognitive_page_planner.py
  - 输出 deck-plan artifact
  - 每页增加 beat、reader_question、source_refs

engine/html_ppt_v13_renderer.py
  - 读取 style lock
  - 禁止写死主题 token
  - 布局 renderer 只接受注册 layout

engine/validate_html_ppt_v13.py
  - 增加 rhythm、required page、content sharpness 检查
```

## 7. 第一阶段落地优先级

优先级 1：先补合同，不动大渲染器。

- 在 `cognitive_page_contracts.py` 增加页面合同表。
- 在 `cognitive_page_planner.py` 给每页补 `beat` 和 `source_refs`。
- 在 validator 增加关键页面缺失检查。

优先级 2：补风格锁。

- 把 `html_ppt_v13_renderer.py` 中写死的主题变量抽出为 style lock。
- 先只保留一个默认主题：`roundtable-editorial`。
- 不急着做多主题，避免继续版本膨胀。

优先级 3：补节奏 validator。

- 检查相邻布局重复。
- 检查全 deck 明暗页比例。
- 检查强冲击页是否存在。
- 检查结尾是否回扣核心问题。

优先级 4：补浏览器自动审计。

- 使用本地浏览器打开输出。
- 检查每页 bounding box、overflow、导航状态。
- 生成简短 audit markdown。

优先级 5：再谈视觉升级。

- 在合同稳定前不要再随意换视觉生成器。
- 视觉升级要通过 style lock 和 layout registry 进入，而不是让 agent 写新 CSS。

## 8. 成功标准

一套新的圆桌 HTML-PPT 算成功，必须同时满足：

- 内容上：能说清作者问题、旧共识、作者位移、现实案例、专家冲突、最终洞见。
- 结构上：每页只有一个 beat，页面顺序形成阅读旅程。
- 视觉上：同一风格锁贯穿全 deck，相邻页有节奏变化。
- 技术上：无内部滚动，四种翻页方式齐全，浏览器验收通过。
- 工程上：agent 不直接生成最终 HTML，renderer 不发明内容，validator 能拦住平庸输出。

一句话：以后我们不是“生成一个好看的 HTML”，而是“先生成一套可审计的思想演示结构，再把它渲染成 HTML-PPT”。
