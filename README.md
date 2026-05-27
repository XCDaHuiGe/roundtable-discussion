# 圆桌会议系统

> **书籍蒸馏 × 专家辩论 × 认知洞见**

## 核心功能

- 🎯 **圆桌洞见生成** - 6位专家深度辩论，提炼书籍核心洞见
- 🧠 **专家库训练** - 32位专家档案，持续学习升级
- 📊 **深度训练引擎** - WebSearch + 知乎MCP + LLM辩论驱动升级
- 🎨 **16种PPT模板** - 自动匹配话题风格

## 快速开始

```bash
# 一键训练（推荐）
python train.py 100

# 深度训练
说："深度训练10轮"

# 生成圆桌洞见
python engine/generate_roundtable.py --book "遥远的救世主"
```

## 目录结构

```
圆桌会议/
├── train.py              # 一键训练入口
├── engine/               # 核心引擎
│   ├── training/         # 训练模块
│   │   ├── orchestrator.py    # 训练编排器
│   │   ├── scorer_v2.py       # 严格评分器
│   │   ├── fusion_engine.py   # 融合增强引擎
│   │   ├── llm_extractor.py   # AI策略提取器
│   │   └── zhihu_miner.py     # 知乎MCP采集
│   ├── generate_roundtable.py # 讨论生成
│   └── render_v8.py           # HTML渲染
├── expert-library/       # 专家库（32位）
│   └── experts/
│       ├── philosophy/   # 哲学家
│       ├── economics/    # 经济学家
│       ├── psychology/   # 心理学家
│       └── ...
├── content/              # 讨论JSON
├── output/               # 圆桌洞见HTML
├── memory/               # 训练日志
├── docs/                 # 文档
│   ├── USAGE_GUIDE.md    # 使用指南
│   └── ...               # 其他文档
└── .trae/skills/         # Skills
    ├── roundtable-training-engine/  # 训练引擎Skill
    ├── deep-training/               # 深度训练Skill
    └ expert-training/               # 专家训练Skill
```

## 训练方式对比

| 方式 | 命令 | 内容来源 | 速度 |
|:---|:---|:---|:---|
| **快速训练** | `python train.py 100` | 本地JSON | 2.7秒/100轮 |
| **深度训练** | 说"深度训练10轮" | WebSearch+知乎MCP | 较慢 |

## 专家库（32位）

| 类别 | 专家 |
|:---|:---|
| **哲学** | 孔子、老子、韩非子、尼采、萨特、叔本华 |
| **经济** | 巴菲特、芒格、达利欧、塔勒布、席勒 |
| **心理** | 卡尼曼、津巴多、弗洛伊德、弗洛姆 |
| **科技** | 凯文·凯利、吴军、赫拉利、博斯特罗姆 |
| **文学** | 李诞、冯唐、许知远、刘润 |
| **社会** | 项飙、阿伦特、波伏娃 |

## Skills触发

```
"训练5轮"           → 快速训练
"深度训练10轮"      → WebSearch + 知乎MCP + LLM辩论
"训练专家 孔子"     → 单专家档案训练
"生成10个话题并训练" → 批量生成训练
```

## PPT模板（16种）

| 类型 | 模板 |
|:---|:---|
| 投资 | consulting-report, clean-review |
| 科技 | geek-report, pixel-report |
| 文学 | editorial, sunrise |
| 情感 | rain-notes, story-field |

## 知乎MCP服务

```bash
cd D:\vibe_coding\zhengliu\zhihu-mcp
python main.py --port 18061
# 服务地址: http://127.0.0.1:18061/mcp
```

## 文档

- [使用指南](docs/USAGE_GUIDE.md)
- [SKILL.md](SKILL.md) - Skills详细说明
- [AGENTS.md](AGENTS.md) - 项目指令

## 版本

| 版本 | 核心升级 |
|:---|:---|
| V5.0 | 深度训练引擎 + WebSearch + 知乎MCP |
| V4.0 | 融合增强式升级 + AI策略提取 |
| V3.0 | 进化式升级 + 对抗自训练 |
| V1.0 | 基础训练系统 |

---

*更新时间：2026-05-27*