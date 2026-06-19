# 风格预设参考（Style Presets）

精心策划的视觉风格，避免通用 AI 审美。**抽象形状优先 — 不使用插图。**

---

## 深色主题

### 1. 墨水经典（Ink Classic）

**调性**：自信、现代、高冲击力

**布局**：深色渐变背景上的彩色卡片。数字在左上，导航在右上，标题在左下。

**字体**：
- 标题：`Noto Serif SC` (900)
- 正文：`Noto Sans SC` (400/500)

**配色**：
```css
:root {
  --bg-primary: #0a0a0b;
  --bg-gradient: linear-gradient(135deg, #0a0a0b 0%, #1a1a1a 50%, #0a0a0b 100%);
  --card-bg: #c9a227;
  --text-primary: #f1efea;
  --text-on-card: #0a0a0b;
  --accent: #c9a227;
}
```

**签名元素**：
- 金色强调卡片作为焦点
- 大号章节编号（01, 02 等）
- 导航面包屑带活跃/非活跃状态

---

### 2. 靛蓝瓷（Indigo Porcelain）

**调性**：大胆、干净、专业、高对比

**布局**：分层面板 — 白色在上，蓝色在下。品牌标记在角落。

**字体**：
- 标题：`Noto Serif SC` (800)
- 正文：`Noto Sans SC` (400/500)

**配色**：
```css
:root {
  --bg-dark: #0a1f3d;
  --bg-white: #f1f3f5;
  --accent-blue: #3b82f6;
  --text-dark: #0a1f3d;
  --text-light: #f1f3f5;
}
```

**签名元素**：
- 双面板垂直分割
- 面板边缘强调条
- 引用排版作为主视觉

---

### 3. 创意电压（Creative Voltage）

**调性**：大胆、创意、活力、复古现代

**布局**：分层面板 — 电光蓝在左，深色在右。手写体点缀。

**字体**：
- 标题：`ZCOOL KuaiLe` (700/800)
- 等宽：`JetBrains Mono` (400/700)

**配色**：
```css
:root {
  --bg-primary: #0066ff;
  --bg-dark: #1a1a2e;
  --accent-neon: #d4ff00;
  --text-light: #ffffff;
}
```

**签名元素**：
- 电光蓝 + 霓虹黄对比
- 半色调纹理图案
- 霓虹徽章/标注

---

### 4. 森林墨（Forest Ink）

**调性**：优雅、精致、艺术、高级

**布局**：深色背景上的居中内容。角落有抽象柔和形状。

**字体**：
- 标题：`Noto Serif SC` (400/600)
- 正文：`Noto Sans SC` (300/400)

**配色**：
```css
:root {
  --bg-primary: #1a2e1f;
  --text-primary: #f5f1e8;
  --text-secondary: #9a9590;
  --accent-warm: #22c55e;
  --accent-pink: #e8b4b8;
  --accent-gold: #c9b896;
}
```

**签名元素**：
- 抽象柔和渐变圆（模糊、重叠）
- 暖色强调（粉、金、陶土色）
- 细垂直强调线

---

## 浅色主题

### 5. 笔记本标签（Notebook Tabs）

**调性**：编辑、有序、优雅、触感

**布局**：深色背景上的米色纸卡片。右侧边缘有彩色标签。

**字体**：
- 标题：`Noto Serif SC` (400/700)
- 正文：`Noto Sans SC` (400/500)

**配色**：
```css
:root {
  --bg-outer: #2d2d2d;
  --bg-page: #f8f6f1;
  --text-primary: #1a1a1a;
  --tab-1: #98d4bb;
  --tab-2: #c7b8ea;
  --tab-3: #f4b8c5;
  --tab-4: #a8d8ea;
  --tab-5: #ffe6a7;
}
```

**签名元素**：
- 纸张容器带微妙阴影
- 右侧边缘彩色章节标签（垂直文字）
- 左侧装订孔装饰

---

### 6. 柔和几何（Pastel Geometry）

**调性**：友好、有序、现代、亲切

**布局**：柔和背景上的白色卡片。右侧边缘有垂直药丸标签。

**字体**：
- 标题：`Noto Sans SC` (700/800)
- 正文：`Noto Sans SC` (400/500)

**配色**：
```css
:root {
  --bg-primary: #c8d9e6;
  --card-bg: #faf9f7;
  --pill-pink: #f0b4d4;
  --pill-mint: #a8d4c4;
  --pill-sage: #5a7c6a;
  --pill-lavender: #9b8dc4;
}
```

**签名元素**：
- 圆角卡片带柔和阴影
- 右侧边缘垂直药丸标签
- 一致的药丸宽度，不同高度

---

### 7. 牛皮纸（Kraft Paper）

**调性**：怀旧、人文、文学、独立杂志

**布局**：米色背景上的居中内容。抽象几何形状作为点缀。

**字体**：
- 标题：`Noto Serif SC` (700/900)
- 正文：`Noto Sans SC` (400/500)

**配色**：
```css
:root {
  --bg-cream: #eedfc7;
  --text-primary: #2a1e13;
  --text-secondary: #555;
  --accent-warm: #d97706;
}
```

**签名元素**：
- 抽象几何形状（圆轮廓 + 线 + 点）
- 粗边框 CTA 框
- 机智、对话式的文案风格

---

### 8. 沙丘（Dune）

**调性**：艺术、设计、创意、画廊手册

**布局**：沙色背景上的居中内容。炭灰文字。

**字体**：
- 标题：`Noto Serif SC` (400/600)
- 正文：`Noto Sans SC` (300/400)

**配色**：
```css
:root {
  --bg-primary: #f0e6d2;
  --text-primary: #1f1a14;
  --text-secondary: #6b5e52;
  --accent: #a78bfa;
}
```

**签名元素**：
- 炭灰 + 沙色对比
- 克制、高级、中性
- 紫色点缀

---

## 特殊主题

### 9. 霓虹赛博（Neon Cyber）

**调性**：未来、科技、自信

**字体**：`Orbitron` + `Rajdhani`

**配色**：深海军蓝 (#0a0f1c)、青色强调 (#00ffcc)、品红 (#ff00aa)

**签名**：粒子背景、霓虹发光、网格图案

---

### 10. 终端绿（Terminal Green）

**调性**：开发者聚焦、黑客美学

**字体**：`JetBrains Mono`（仅等宽）

**配色**：GitHub 深色 (#0d1117)、终端绿 (#39d353)

**签名**：扫描线、闪烁光标、代码语法样式

---

### 11. 瑞士现代（Swiss Modern）

**调性**：干净、精确、包豪斯风格

**字体**：`Archivo` (800) + `Nunito` (400)

**配色**：纯白、纯黑、红色强调 (#ff3300)

**签名**：可见网格、不对称布局、几何形状

---

### 12. 纸与墨（Paper & Ink）

**调性**：编辑、文学、深思熟虑

**字体**：`Noto Serif SC` + `Source Serif 4`

**配色**：暖米色 (#faf9f7)、炭灰 (#1a1a1a)、深红强调 (#c41e3a)

**签名**：首字下沉、引用块、优雅水平线

---

## 字体配对速查表

| 预设 | 标题字体 | 正文字体 | 来源 |
|:---|:---|:---|:---|
| 墨水经典 | Noto Serif SC | Noto Sans SC | Google |
| 靛蓝瓷 | Noto Serif SC | Noto Sans SC | Google |
| 创意电压 | ZCOOL KuaiLe | JetBrains Mono | Google |
| 森林墨 | Noto Serif SC | Noto Sans SC | Google |
| 笔记本标签 | Noto Serif SC | Noto Sans SC | Google |
| 柔和几何 | Noto Sans SC | Noto Sans SC | Google |
| 牛皮纸 | Noto Serif SC | Noto Sans SC | Google |
| 沙丘 | Noto Serif SC | Noto Sans SC | Google |
| 霓虹赛博 | Orbitron | Rajdhani | Google |
| 终端绿 | JetBrains Mono | JetBrains Mono | JetBrains |
| 瑞士现代 | Archivo | Nunito | Google |
| 纸与墨 | Noto Serif SC | Source Serif 4 | Google |

---

## 禁止使用（通用 AI 模式）

**字体**：Inter、Roboto、Arial、系统字体作为标题

**配色**：`#6366f1`（通用靛蓝）、白色背景上的紫色渐变

**布局**：所有内容居中、通用 hero 区域、相同的卡片网格

**装饰**：写实插图、无目的的毛玻璃效果、无意义的阴影

---

## CSS 注意事项

### 否定 CSS 函数

**错误 — 浏览器静默忽略**：
```css
right: -clamp(28px, 3.5vw, 44px);   /* 浏览器忽略 */
margin-left: -min(10vw, 100px);      /* 浏览器忽略 */
```

**正确 — 使用 calc() 包装**：
```css
right: calc(-1 * clamp(28px, 3.5vw, 44px));
margin-left: calc(-1 * min(10vw, 100px));
```

CSS 不允许函数名前有前导 `-`。浏览器会静默丢弃整个声明。
