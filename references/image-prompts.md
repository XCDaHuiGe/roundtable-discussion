# 配图生成指南（Image Prompts）

本文档定义配图生成流程，用于为 HTML PPT 生成高质量的插图。

---

## 图片类型

### 1. 人文纪实照片

**适合**：封面、左文右图、图片网格

**风格**：富士/徕卡感的真实场景，增加人文表现力

**提示词模板**：
```
A documentary photograph of [主题], 
shot on Fujifilm, natural lighting, 
shallow depth of field, editorial style,
16:9 aspect ratio, no text, no watermark
```

**示例**：
```
A documentary photograph of a business meeting in a modern office,
shot on Fujifilm, natural lighting from large windows,
shallow depth of field, editorial magazine style,
16:9 aspect ratio, no text, no watermark
```

---

### 2. 概念信息图

**适合**：概念解释、流程展示、数据可视化

**风格**：简洁的矢量风格，配色与主题色协调

**提示词模板**：
```
An infographic illustration of [概念],
minimalist vector style, [主题色] accent color,
clean lines, white background,
16:10 aspect ratio, no text labels
```

**示例**：
```
An infographic illustration of communication flow between two people,
minimalist vector style, golden accent color,
clean lines, white background,
16:10 aspect ratio, no text labels
```

---

### 3. 流程图/系统图

**适合**：Pipeline 布局、方法论展示

**风格**：简洁的流程图风格，节点清晰

**提示词模板**：
```
A flowchart diagram showing [流程],
minimalist style, connected nodes,
[主题色] accent, white background,
16:9 aspect ratio, clean design
```

---

### 4. 对比图

**适合**：Before/After 布局

**风格**：左右对比或上下对比

**提示词模板**：
```
A split comparison image showing [对比内容],
left side shows [A], right side shows [B],
editorial style, clean composition,
16:9 aspect ratio, no text
```

---

### 5. 场景插图

**适合**：案例分析、故事叙述

**风格**：杂志风插图，有叙事感

**提示词模板**：
```
An editorial illustration of [场景],
magazine style, [主题色] color palette,
detailed but not cluttered,
16:10 aspect ratio, no text
```

---

## 图片比例规范

| 布局类型 | 推荐比例 | CSS 类 |
|:---|:---|:---|
| Layout 1 封面 | 16:9 | `.r-16x9` |
| Layout 4 左文右图 | 16:10 或 4:3 | `.r-16x10` / `.r-4x3` |
| Layout 5 图片网格 | 固定高度 | `.h-22` / `.h-26` |
| Layout 10 图文混排 | 4:3 或 3:2 | `.r-4x3` / `.r-3x2` |

---

## 配色协调

生成的图片配色应与主题色协调：

| 主题 | 图片配色建议 |
|:---|:---|
| 🖋 墨水经典 | 金色/暖棕强调，黑白灰主体 |
| 🌊 靛蓝瓷 | 蓝色系，冷色调 |
| 🌿 森林墨 | 绿色/棕色，自然色调 |
| 🍂 牛皮纸 | 暖棕/米色，复古色调 |
| 🌙 沙丘 | 灰紫/沙色，中性色调 |

---

## 图片命名规范

```
{页号}-{语义}.{ext}
```

**示例**：
- `01-cover.jpg` — 封面图
- `03-concept.png` — 概念图
- `05-workflow.png` — 流程图
- `08-quote.jpg` — 引用配图

---

## 生成后检查

1. **比例正确**：与布局槽位匹配
2. **无文字**：图片内不应有文字标签
3. **无水印**：确保无水印
4. **配色协调**：与主题色协调
5. **分辨率足够**：宽度 ≥ 1600px

---

## 图片存储

所有图片存放在 `images/` 目录，与 `index.html` 同级：

```
项目/
├── index.html
└── images/
    ├── 01-cover.jpg
    ├── 03-concept.png
    └── ...
```
