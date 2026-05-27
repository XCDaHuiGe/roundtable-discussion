# 圆桌会议系统使用指南

## 快速开始

### 一键训练（推荐）

```bash
# 快速训练（本地文件）
python train.py 100

# 深度训练（WebSearch + 知乎MCP + LLM辩论）
说："深度训练10轮"
```

### 生成圆桌洞见

```bash
# 从书籍生成
python engine/generate_roundtable.py --book "遥远的救世主"

# 从话题生成
python engine/generate_roundtable.py --topic "AI时代的职业危机"

# 批量生成
python engine/generate_roundtable.py --batch content/topics.json
```

---

## 核心功能

### 1. 训练引擎

| 功能 | 命令 | 说明 |
|:---|:---|:---|
| **快速训练** | `python train.py 100` | 使用本地JSON文件训练专家 |
| **深度训练** | 说"深度训练10轮" | WebSearch + 知乎MCP + LLM辩论 |
| **V4引擎** | `python engine/training/orchestrator.py --engine v4` | 融合增强式升级 |
| **V3引擎** | `python engine/training/orchestrator.py --engine v3` | 进化式升级（默认） |

### 2. 专家库管理

| 功能 | 命令 | 说明 |
|:---|:---|:---|
| **查看专家** | `expert-library/experts/{类别}/{专家名}.md` | 32位专家档案 |
| **训练专家** | 说"训练专家 孔子" | WebSearch + 知乎MCP采集 |
| **查看冲突** | `python engine/training/debate_arena.py --show-conflicts` | 专家信念冲突点 |

### 3. 内容生成

| 功能 | 命令 | 说明 |
|:---|:---|:---|
| **生成讨论JSON** | `python engine/generate_roundtable.py` | 生成V8格式讨论 |
| **渲染HTML** | `python engine/render_v8.py content/某书_v8.json` | 生成圆桌洞见HTML |
| **选择模板** | `python engine/template_selector.py --list` | 16个PPT模板 |

### 4. 知乎MCP服务

```bash
# 启动知乎MCP
cd D:\vibe_coding\zhengliu\zhihu-mcp
python main.py --port 18061

# 服务地址
http://127.0.0.1:18061/mcp
```

---

## 训练流程对比

### 快速训练（train.py）

```
本地JSON → 评分 → 提取策略 → 更新专家档案
          ↓
      2.7秒/100轮
```

**优点**：速度快，无需网络
**缺点**：内容来源单一

### 深度训练（deep-training Skill）

```
专家信念冲突 → LLM生成话题 → WebSearch搜索 → 知乎MCP采集 → LLM辩论 → 更新档案
```

**优点**：内容丰富，真正提升
**缺点**：需要网络，耗时较长

---

## 专家档案结构

```markdown
# 专家名

## 元信息
- 版本: V2
- 训练次数: 5
- 当前评分: 75

## 核心立场
> 一句话概括

## 攻击模式
| 类型 | 适用场景 | 杀伤力 | 来源 |
| 现实矛盾 | 对手观点与现实冲突时 | 高 | 深度训练#1 |

## 防御模式
| 被攻击类型 | 化解策略 | 成功率 |
| 现实矛盾 | 德法共治回应 | 65% |

## 精选发言
> "高质量发言..." — 深度训练#1
```

---

## PPT模板选择

### 话题匹配规则

| 话题类型 | 推荐模板 |
|:---|:---|
| 投资 | consulting-report, clean-review |
| 科技/AI | geek-report, pixel-report |
| 文学/哲学 | editorial, rain-notes |
| 情感 | sunrise, story-field |

### 强制指定模板

```bash
python engine/template_selector.py --topic "AI" --force v3-magazine
```

---

## 输出目录

| 目录 | 内容 |
|:---|:---|
| `content/` | 讨论JSON文件 |
| `output/` | 圆桌洞见HTML |
| `memory/` | 训练日志 |
| `expert-library/` | 专家档案 |

---

## 常见问题

### Q: 训练后专家没有提升？
A: 检查评分是否达到阈值（60分）。低于60分跳过进化。

### Q: 知乎MCP连接失败？
A: 确认服务已启动：`python main.py --port 18061`

### Q: 如何查看训练进度？
A: 查看 `memory/training_*.json` 日志文件

### Q: 如何添加新专家？
A: 说"训练专家 新专家名"，系统会自动采集内容生成档案

---

## 版本说明

| 版本 | 说明 |
|:---|:---|
| V1.0 | 基础训练系统 |
| V3.0 | 进化式升级 + 对抗自训练 |
| V4.0 | 融合增强式 + AI策略提取 + 严格评分 |
| V5.0 | 深度训练引擎 + WebSearch + 知乎MCP |

---

*更新时间：2026-05-27*