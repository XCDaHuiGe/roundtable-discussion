---
name: roundtable-conference-v2
description: "圆桌会议工程化HTML生成系统 V3.0。AI只负责内容(JSON)，程序负责渲染(Engine)。"
---

# 圆桌会议 V3.0 — 工程化HTML生成系统

> **核心原则：AI只负责内容，程序负责工程**

---

## 系统架构

```
AI生成JSON内容
    ↓
Schema验证 (Pydantic)
    ↓
渲染引擎 (render.py)
    ↓
HTML模板渲染
    ↓
自动验证 (validator.py)
    ↓
最终HTML
```

---

## 目录结构

```
/engine          - 渲染引擎
  schema.py      - 内容Schema定义
  render.py      - HTML渲染器
  validator.py   - HTML验证器

/templates       - 模板系统
  base.html      - HTML模板
  css/style.css  - 样式文件
  js/app.js      - 交互逻辑

/content         - JSON内容（AI生成）
  *.json         - 圆桌讨论内容

/output          - 生成结果
  *.html         - 最终HTML文件
```

---

## AI工作流程

### Step 1: AI生成JSON内容

AI **只负责生成JSON**，不负责HTML：

```json
{
  "title": "书名",
  "subtitle": "副标题",
  "style": "严肃",
  "dashboard": {
    "total_experts": 6,
    "total_rounds": 7,
    "total_clashes": 24,
    "total_insights": 6,
    "experts": ["专家1", "专家2", ...]
  },
  "rounds": [
    {
      "round_number": 1,
      "topic": "讨论主题",
      "question": "核心问题",
      "speakers": [
        {
          "name": "专家名",
          "role": "角色",
          "avatar_color": "#c23b22",
          "content": "发言内容（至少10字）"
        }
      ],
      "clashes": [
        {
          "type": "情节反驳/细节挑战/逻辑追问/框架质疑/反例引入",
          "expert": "专家名",
          "content": "碰撞内容"
        }
      ],
      "insight": {
        "statement": "洞见句",
        "explanation": "洞见说明"
      }
    }
  ],
  "open_questions": [
    {"question": "开放问题"}
  ],
  "conclusion": "结语"
}
```

### Step 2: 渲染HTML

```powershell
cd engine
python render.py "..\content\书名.json" "..\output\书名.html" "..\templates"
```

### Step 3: 验证HTML

```powershell
python validator.py "..\output\书名.html"
```

**必须PASS**，否则不交付。

---

## Schema定义 (schema.py)

### 核心模型

- `RoundtablePPT` - 完整PPT结构
- `Round` - 讨论轮次
- `Speaker` - 发言者
- `Clash` - 碰撞交锋
- `Insight` - 核心洞见

### 验证规则

- 发言内容最少10字
- 碰撞内容最少10字
- 洞见说明最少10字
- 轮次编号必须连续

---

## 验证器检查项 (validator.py)

### HTML结构

- slide数量 > 0
- active slide数量 = 1

### JS完整性

- go() 函数
- go(0) 初始化
- querySelectorAll
- classList操作
- wheel/keyboard事件

### CSS完整性

- display:none
- display:flex
- 字体系统
- 配色系统

### 组件完整性

- 发言块 .sp
- 碰撞块 .cb
- 洞见卡 .insight-c
- TOC
- 进度条

---

## 禁止事项

- **禁止AI直接输出HTML**
- **禁止AI修改JS逻辑**
- **禁止新增template-v2/v3/v4**
- **禁止内联script超过50行**
- **禁止使用PowerShell here-string生成HTML**
- **禁止生成未校验JSON**
- **禁止使用旧class命名**

---

## 内容质量红线

### 内容深度

- 发言字数 < 350字 → 无效发言
- 无书中情节引用 → 无效发言
- 无因果推理链 → 无效洞见
- 无专家间直接反驳 → 无效碰撞

### 排版规范

- 每页最多2-3人发言
- 碰撞块颜色标记
- 标题页大留白

### 框架结构

- 三层架构：洞见全景30% + 深度讨论50% + 认知演化20%
- 讨论仪表盘
- 张力图谱

---

## 风格预设

- **严肃风格**：学术分析、正式场合
- **接地气风格**：大众传播、轻松阅读
- **人物原有风格**：还原专家真实说话方式

---

## 版本历史

- V1.0-V2.6: AI直接拼HTML（不稳定）
- V3.0: **工程化架构，AI只负责内容，程序负责渲染**

---

*版本：V3.0*
*更新时间：2026-05-26*
*核心原则：AI只负责内容，程序负责工程*