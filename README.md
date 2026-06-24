# 圆桌洞见 · Roundtable Insight

> **32位跨领域专家 × 深度辩论 × 自我进化训练系统**
>
> 给一个话题，系统自动匹配专家、生成深度辩论、渲染为HTML-PPT。

---

## 快速开始

```bash
# 1. 克隆
git clone https://github.com/XCDaHuiGe/roundtable-discussion.git
cd roundtable-discussion

# 2. 安装依赖（核心功能零外部依赖）
pip install pydantic

# 3. 直接运行（用已有JSON渲染HTML）
python run.py "AI会取代人类工作吗" --skip-debate --json content/AI时代的意义危机_v8.json

# 4. 完整管线（需要OPENROUTER_API_KEY）
export OPENROUTER_API_KEY=your_key
python run.py "你的问题"
```

**没有API key也能用**：系统自带47个已生成的圆桌洞见，直接打开 `output/` 下的HTML文件即可阅读。

---

## 这是什么

一个AI圆桌讨论系统。输入一个问题，6位跨领域专家展开3轮深度交锋，每轮包含立场表达、碰撞反驳、现实案例、代价分析、人性剖析、认知升级6个层次。最终输出一个自包含的HTML幻灯片。

**专家不是随意说话的AI角色**——每位专家有知识边界（老子不会谈AI，芒格不会谈量子力学）、时代约束、性格一致性。

---

## 两种使用方式

### 方式一：直接看成品

`output/` 目录下有47个HTML文件，直接双击打开，键盘翻页。

### 方式二：生成新话题

```bash
python run.py "你的话题" --theme gold --rounds 3
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--experts` | 指定专家（逗号分隔） | 自动匹配 |
| `--rounds` | 辩论轮数 | 3 |
| `--theme` | 主题色（gold/acid/warm） | gold |
| `--skip-debate` | 跳过LLM，用已有JSON | 否 |
| `--json` | 已有V8 JSON路径 | 无 |
| `--explain` | 只显示专家匹配理由 | 否 |

---

## 项目结构

```
roundtable-discussion/
├── run.py                    # 唯一入口：端到端管线
├── engine/                   # 核心引擎
│   ├── topic_router.py       # 话题→专家自动匹配
│   ├── material_collector.py # 多源素材聚合
│   ├── debate_generator.py   # LLM辩论生成
│   ├── html_renderer.py      # V8 JSON→HTML-PPT
│   ├── v8_normalizer.py      # JSON格式标准化
│   ├── auto_scorer.py        # 6维度自动评分
│   ├── auto_train.py         # V11训练管线
│   ├── scorer.py             # 加权评分计算
│   ├── llm_generate.py       # OpenRouter API调用
│   ├── schema_v8.py          # V8数据模型
│   ├── knowledge_boundary_checker.py  # 知识边界检查
│   ├── attack_constraint.py  # 交锋约束
│   ├── content_injector.py   # 话题→书单映射
│   ├── prompts/              # Prompt模板
│   ├── training/             # 训练模块
│   │   ├── coach.py          # Coach Agent审阅
│   │   ├── fusion_engine.py  # 融合增强引擎
│   │   ├── debate_arena.py   # 对抗竞技场
│   │   ├── tracker.py        # 进化追踪
│   │   └── ...
│   ├── scoring/              # 评分模块
│   ├── quality_gates/        # 质量门
│   └── roundtable_engine/    # 圆桌引擎辅助
├── expert-library/           # 专家库（32位×5领域）
│   └── experts/
│       ├── philosophy/       # 哲学（老子、尼采、苏格拉底...）
│       ├── economics/        # 经济（芒格、巴菲特、塔勒布...）
│       ├── psychology/       # 心理（卡尼曼、弗洛伊德、弗洛姆...）
│       ├── sociology/        # 社会（项飙、赫拉利、阿伦特）
│       └── literature/       # 文学（李诞、冯唐、罗翔...）
├── content/                  # V8 JSON辩论数据
├── output/                   # HTML-PPT成品
├── index.html                # 项目首页（GitHub Pages）
├── VERSION.md                # 版本历史
└── AGENTS.md                 # 项目铁律
```

---

## 核心模块

| 模块 | 职责 | 依赖 |
|------|------|------|
| `run.py` | 端到端管线编排 | 标准库 |
| `topic_router.py` | 话题→专家匹配 | 标准库 |
| `html_renderer.py` | JSON→HTML渲染 | 标准库 |
| `auto_scorer.py` | 6维度自动评分 | 标准库 |
| `debate_generator.py` | LLM辩论生成 | urllib + OpenRouter |
| `coach.py` | Coach审阅 | 标准库 |
| `knowledge_boundary_checker.py` | 知识边界检查 | 标准库 |

**零外部框架**：核心功能全部基于Python标准库。LLM调用通过OpenRouter HTTP API（`urllib.request`），不依赖任何AI框架。

---

## 专家系统

32位专家，5大领域，每位专家有三层档案：

| 层 | 内容 | 可变性 |
|----|------|--------|
| **灵魂层** | 核心信念、价值排序、思维底色 | 永不改变 |
| **策略层** | 攻击模式、防御模式、分析框架 | Coach升级 |
| **素材层** | 精选发言、核心案例、金句库 | 融合替换 |

37个知识边界文件（`_知识边界.md`）自动加载，确保专家不乱引用理论、不时空错乱。

---

## 版本

当前版本：**v13.11**（渲染引擎v13 + 训练系统v11）

详见 [VERSION.md](VERSION.md)

---

## 文档

- [VERSION.md](VERSION.md) — 版本历史与命名规范
- [AGENTS.md](AGENTS.md) — 项目铁律与工作流程
- [EXPERT_SOUL_SPEC.md](EXPERT_SOUL_SPEC.md) — 专家灵魂升级规范

---

*更新时间：2026-06-21 · v13.11*

---

## V14 图片压缩经验（2026-06-24）

### 问题
1. PNG图片太大（1024x1024，每张约2.5MB）
2. 10张图片导致HTML文件87MB
3. GitHub推送警告文件过大

### 解决方案
1. **压缩PNG图片**：1024x1024 → 512x512，每张从2.5MB → 400KB
2. **使用PIL优化**：`img.save(output_path, 'PNG', optimize=True)`
3. **保持PNG格式**：不转JPEG，保留RGBA透明通道

### 压缩效果
- 单张图片：2.5MB → 400KB（减少84%）
- HTML文件：87MB → 21MB（减少75%）
- GitHub推送：正常通过

### 关键代码
```python
from PIL import Image
img = Image.open(input_path)
img_resized = img.resize((512, 512), Image.LANCZOS)
img_resized.save(output_path, 'PNG', optimize=True)
```

### 注意事项
1. **不要转JPEG**：PNG有alpha通道，JPEG没有
2. **不要用quantize**：会丢失颜色，浏览器不显示
3. **保持RGBA格式**：确保浏览器兼容性

---

## V14 流程升级（2026-06-24）

### 升级后的流程
```
1. 理解书籍（深度阅读）
2. 设计HTML-PPT（结构+布局+组件）
3. 审核设计（用户确认）
4. 渲染HTML（实现设计）
5. 验证功能（翻页/动画等）
6. 提交GitHub
```

### 核心改进
- ✅ 新增"理解书籍"步骤（深度阅读，理解精髓）
- ✅ 新增"设计HTML-PPT"步骤（结构+布局+组件）
- ✅ 新增"审核设计"步骤（用户确认）
- ✅ 新增"验证功能"步骤（翻页/动画等）
- ✅ 保留"多agent并行生成"和"JSON汇总"
- ✅ 保留"提交GitHub"

---

## 《围城》V14 项目

### 项目信息
- **标题**：围城 · 深度拆解
- **作者**：钱锺书
- **页数**：73页
- **文件**：`output/weicheng_v14.html`（21MB）

### 设计特点
- **主题**：水墨风 + 琥珀色
- **背景**：每页独立背景图（512x512 PNG）
- **动画**：data-anim淡入效果
- **翻页**：scroll-snap + 键盘/滚轮/触摸

### 语义组件
- expert-speech（不同专家不同颜色左边框）
- speaker-label（专家名字+角色标签）
- stance-evo（立场演化标记）
- shock-flash（认知突破）
- warning-box（警告框）
- mutation-box（观点变异）
- tension-card（张力图谱）
- hypo-card（假设演化）

### 浏览方式
- 本地：打开 `output/weicheng_v14.html`
- GitHub Pages：`https://XCDaHuiGe.github.io/roundtable-discussion/output/weicheng_v14.html`

