# 语义组件系统（V7.0）

将文本逻辑翻译为 UI 逻辑，禁止用纯文本/ASCII 表达逻辑。

## 核心组件清单

### 1. 人物卡片系统

#### 上升者卡片（card-rise）

```html
<div class="card-rise">
  <div class="card-bar"></div>
  <div class="card-content">
    <div class="card-name">芮小丹</div>
    <div class="card-role">天生自在的得道者</div>
    <div class="card-arc">↑ 上升弧</div>
  </div>
</div>
```

**CSS 变量**：
```css
.card-rise {
  --bar-color: var(--color-rise, #10b981);
  --bg-color: var(--color-rise-bg, rgba(16, 185, 129, 0.1));
}
```

#### 坠落者卡片（card-fall）

```html
<div class="card-fall">
  <div class="card-bar"></div>
  <div class="card-content">
    <div class="card-name">刘冰</div>
    <div class="card-role">弱势文化的终极样本</div>
    <div class="card-arc">↓ 坠落弧</div>
  </div>
</div>
```

**CSS 变量**：
```css
.card-fall {
  --bar-color: var(--color-fall, #ef4444);
  --bg-color: var(--color-fall-bg, rgba(239, 68, 68, 0.1));
}
```

---

### 2. 警示系统

#### 警告框（warning-box）

```html
<div class="warning-box">
  <div class="warning-icon">⚠️</div>
  <div class="warning-content">
    <div class="warning-title">致命误区</div>
    <div class="warning-text">以为做A就行 → 真相：必须先做B</div>
  </div>
</div>
```

#### 正解框（ok-box）

```html
<div class="ok-box">
  <div class="ok-icon">✓</div>
  <div class="ok-content">
    <div class="ok-title">正确理解</div>
    <div class="ok-text">文化属性决定命运，强势文化遵循客观规律</div>
  </div>
</div>
```

---

### 3. 数据系统

#### 统计卡片（stat-card）

```html
<div class="stat-card">
  <div class="stat-label">上升弧</div>
  <div class="stat-num">3</div>
  <div class="stat-note">芮小丹 · 肖亚文 · 欧阳雪</div>
</div>
```

#### 大数字展示（big-number）

```html
<div class="big-number">
  <div class="bn-label">总页数</div>
  <div class="bn-value">38</div>
  <div class="bn-unit">pages</div>
</div>
```

---

### 4. 时间线系统

#### 基础时间线

```html
<div class="timeline">
  <div class="tl-item">
    <div class="tl-dot"></div>
    <div class="tl-content">
      <div class="tl-time">第1-8章</div>
      <div class="tl-title">布局期</div>
      <div class="tl-desc">丁元英隐居古城，人物关系建制</div>
    </div>
  </div>
  <div class="tl-item">
    <div class="tl-dot"></div>
    <div class="tl-content">
      <div class="tl-time">第9-19章</div>
      <div class="tl-title">发展期</div>
      <div class="tl-desc">芮小丹引出王庙村，格律诗商业模式设计</div>
    </div>
  </div>
</div>
```

---

### 5. 矩阵表格

#### 对比矩阵

```html
<div class="matrix-table">
  <div class="matrix-header">
    <div class="matrix-cell">维度</div>
    <div class="matrix-cell">老版本</div>
    <div class="matrix-cell">新版本</div>
  </div>
  <div class="matrix-row">
    <div class="matrix-cell">体验</div>
    <div class="matrix-cell">阅读文档</div>
    <div class="matrix-cell">沉浸体验</div>
  </div>
  <div class="matrix-row">
    <div class="matrix-cell">排版</div>
    <div class="matrix-cell">字号模糊</div>
    <div class="matrix-cell">发布会级对比度</div>
  </div>
</div>
```

---

### 6. 金句系统

#### 大金句页（slide-quote）

```html
<section class="slide slide-quote dark">
  <div class="quote-content">
    <div class="quote-text">大爱不爱</div>
    <div class="quote-author">— 智玄大师</div>
    <div class="quote-context">第20章 · 五台山问道</div>
  </div>
</section>
```

**CSS 要求**：
```css
.quote-text {
  font-size: clamp(48px, 8vw, 120px);
  font-weight: 900;
  letter-spacing: 0.05em;
}
```

---

## 语义色系统

| 语义 | 变量名 | 默认值 | 用途 |
|:---|:---|:---|:---|
| 上升/正向 | `--color-rise` | `#10b981` | 成功、增长、正面 |
| 坠落/负向 | `--color-fall` | `#ef4444` | 失败、下降、负面 |
| 强调/主色 | `--color-accent` | `#f59e0b` | 金句、重点、标题 |
| 警告 | `--color-warning` | `#f97316` | 误区、红线 |
| 信息 | `--color-info` | `#3b82f6` | 备注、说明 |

---

## 组件使用原则

1. **禁止纯文本表达逻辑**：所有并列、递进、对比关系必须用组件
2. **语义优先**：选择组件时先问"这是什么逻辑关系"，再选对应组件
3. **一致性**：同一文档中相同语义使用相同组件
4. **留白**：组件之间必须有足够间距（至少 2rem）
5. **动画配合**：组件入场使用 `anim-1` 到 `anim-6` 分层延迟
