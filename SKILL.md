# 圆桌会议 Skills 集合

> **一键触发，自动执行复杂任务**

## 当前版本：V9.0

**核心设计**：Agent=LLM，Python=机械操作

| 角色 | 职责 |
|:---|:---|
| Agent（你） | 搜索、阅读、生成辩论、评分 |
| Python模块 | 机械计算、文件保存、HTML渲染 |

**零LLM依赖**：不依赖任何外部LLM API Key

---

## 可用 Skills

| Skill | 触发指令 | 功能 |
|:---|:---|:---|
| **deep-training** | "深度训练N轮" | Agent生成辩论 → Python评分升级 |
| **expert-training** | "训练专家 {名}" | 单专家档案训练 |
| **v11-auto-training** | "热点训练" / "自动训练" / "从互联网找争议话题训练" | 实时联网找中文热点 → 3轮圆桌训练 → Markdown产物 → 标准更新专家库 |

---

## V11 自动训练入口

当用户要求"热点训练"、"自动训练"、"从互联网找争议话题训练"时，使用 V11 流程：

1. 按 `docs/V11_AGENT_RESEARCH_PROTOCOL.md` 实时联网采集。
2. 生成 prepared JSON。
3. 运行 `python engine/v11_cli.py --input <prepared.json> --base-dir .`。
4. 检查 `training_runs/` 下的 `full.md` 和 `report.md`。
5. 根据训练结果用标准更新模式更新专家库。

训练日志不提交 GitHub；专家库更新可以提交。

---

## deep-training

**描述**：深度训练引擎 V9.0

**触发指令**：
```
"深度训练10轮"
"专家辩论训练"
```

**核心流程**：
```
Agent生成话题 → Agent生成辩论 → Python评分 → Python提取策略 → Python升级专家
```

**Python模块**：
| 模块 | 功能 |
|:---|:---|
| `auto_train.py` | 训练入口（step1-step5） |
| `scorer.py` | 6维度加权评分 |
| `llm_extractor.py` | 策略提取（纯机械） |
| `fusion_engine.py` | 融合增强升级 |

**评分维度**：
| 维度 | 权重 |
|:---|:---|
| reality_grounding | 25% |
| contradiction_handling | 20% |
| strategic_depth | 20% |
| cross_domain_transfer | 15% |
| novelty | 10% |
| personality_consistency | 10% |

---

## expert-training

**描述**：专家档案训练系统 V3.0

**触发指令**：
```
"训练专家 孔子"
"继续训练"
```

**核心流程**：
```
WebSearch搜索 → 知乎MCP采集 → 档案生成 → L1/L2/L3评估
```

---

## 进化闭环

**核心逻辑**：Agent读取策略层 → 生成更好辩论 → Python升级策略层 → 下次Agent读取已进化的策略

```
┌─────────────────────────────────────────────────────────┐
│  1. Agent调用 get_expert_profile()                       │
│     → 读取攻击模式、防御弱点、风格指纹                     │
│                                                          │
│  2. Agent根据策略层生成辩论                               │
│     → 选择最佳攻击角度                                    │
│     → 针对对手弱点攻击                                    │
│     → 模仿专家风格                                        │
│                                                          │
│  3. Python评分 + 提取新策略                               │
│     → step4_score_and_extract()                          │
│                                                          │
│  4. Python融合升级策略层                                  │
│     → FusionEngine: MERGE/ENHANCE/BRANCH                 │
│                                                          │
│  5. 下次训练，Agent读取已进化的策略                        │
│     → 进化闭环完成                                        │
└─────────────────────────────────────────────────────────┘
```

**进化效果**：
| 训练前 | 训练后 |
|:---|:---|
| 攻击模式: 1个 | 攻击模式: 2个（MERGE） |
| 防御成功率: 0% | 防御成功率: 15%（ENHANCE） |
| 弱点: 哲学思辨型 | 弱点: 已修补 |

---

## 专家库

**路径**：`expert-library/experts/{category}/{name}.md`

**三层架构**：
| 层级 | 内容 | 对应Persona要素 | 更新频率 |
|:---|:---|:---|:---|
| 灵魂层 | 核心信念、价值观、**禁忌话题** | Role + Objectives + **Constraints** | 永不改变 |
| 策略层 | 攻击模式、防御弱点、风格指纹 | Domain Scope + Interaction Style | 训练升级 |
| 素材层 | 精选发言、核心案例、金句、**失败案例** | Examples + **Uncertainty Handling** | 每次积累 |

**Persona 7要素完整覆盖**：
```
1. Role（角色） → 灵魂层：代表身份
2. Domain Scope（范围） → 策略层：分析框架
3. Objectives（目标） → 灵魂层：价值排序
4. Constraints（约束） → 灵魂层：禁忌话题 ✅ 新增
5. Interaction Style（风格） → 策略层：交互策略
6. Examples（示例） → 素材层：精选发言、金句
7. Uncertainty Handling → 素材层：失败案例 ✅ 新增
```

---

## 评估体系

### 内容质量验证

**函数**：`validate_content(debate_json)`

**检查项**：
| 指标 | 标准 |
|:---|:---|
| 引用数量 | ≥ 2 |
| 发言长度 | ≥ 100字 |
| 碰撞轮次 | ≥ 1 |

**返回**：`{"passed": True, "quote_count": 3, "issues": []}`

---

### 训练效果对比

**函数**：`compare_performance(expert_name, topic, old_score, new_score)`

**流程**：
```
1. 同一话题，旧版本专家辩论 → 评分
2. 同一话题，新版本专家辩论 → 评分
3. 对比分数差异 → 提升证据
```

**返回**：`{"improved": True, "delta": 15.5, "analysis": ["评分提升: 65 → 80 (+15)"]}`

---

## 渲染器

**路径**：`engine/render_roundtable.py`

**用法**：
```bash
python render_roundtable.py content/书名_v8.json --output output/书名_圆桌洞见.html
```

---

*版本：V9.0 · 更新时间：2026-05-31*
