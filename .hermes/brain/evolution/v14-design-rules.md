# V14 设计规则总结

> 基于圆桌洞见项目V14版本的开发经验，总结HTML-PPT设计规则

## 一、核心设计哲学

```
内容决定形式，形式服务内容
专家灵魂 > 功能，深度 > 广度
```

### 1.1 设计优先级

1. **内容深度**：每个专家发言200-500字，深度分析
2. **文字可读性**：背景图上的文字必须清晰可辨
3. **页面节奏**：根据内容密度决定页面布局

### 1.2 反面教材（V13的教训）

- ❌ 模板化渲染（html_renderer.py）
- ❌ 每个专家只有1-2句浅层观点
- ❌ 文字在背景图上看不清

## 二、设计系统

### 2.1 分辨率

- **固定舞台**：1920x1080
- **适配方式**：transform: scale() 适配不同屏幕
- **内容区域**：屏幕宽度70%（左右各15%留白）

```css
.page {
  padding: 3rem 15vw;  /* 左右各15%留白 */
}
```

### 2.2 配色系统

| 角色 | 颜色 | 用途 |
|------|------|------|
| 背景 | #0A0A0A | 全屏深色背景 |
| 文字 | #F5F0E8 | 正文颜色 |
| 强调色 | #C9A96E | 标题、高亮、边框 |
| 强调色浅 | #E8D5A8 | 渐变、悬停 |
| 强调色深 | #8B7355 | 次要文字、辅助信息 |

### 2.3 字体

| 用途 | 字体 | 说明 |
|------|------|------|
| 标题 | Noto Serif SC | 宋体，中文优雅 |
| 正文 | Noto Serif SC | 宋体，易读 |
| 英文/数字 | Inter | 无衬线，干净 |
| 特殊 | Ma Shan Zheng | 毛笔字体（可选） |

```css
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600;700;900&family=Inter:wght@400;500;600;700&display=swap');
```

## 三、页面类型系统（11种）

### 3.1 页面类型概览

| # | 类型 | CSS类 | 用途 | 内容密度 |
|---|------|-------|------|----------|
| 1 | Cover | `.cover` | 封面（标题+副标题） | 低 |
| 2 | Expert Grid | `.grid` | 专家列表（3列网格） | 中 |
| 3 | Chapter | `.chapter` | 章节标题页 | 低 |
| 4 | Dialogue | `.dialogue` | 立场发言（每页3个专家） | 高 |
| 5 | Case | `.case` | 案例分析 | 中 |
| 6 | Clash | `.dialogue` | 交锋页面（与dialogue共用） | 高 |
| 7 | Cost | `.insight` | 成本分析（与insight共用） | 中 |
| 8 | Human Nature | `.insight` | 人性分析（与insight共用） | 中 |
| 9 | Cognitive Upgrade | `.insight` | 认知升级 | 低 |
| 10 | Quote | `.qi` | 金句页 | 低 |
| 11 | Ending | `.end` | 结尾页 | 低 |

### 3.2 页面布局规则

```
信息密度高（对话/案例） → 多内容堆叠在一页
信息密度低（金句/章节标题） → 留白，单条展示
```

### 3.3 对话页布局

```
每页3个专家发言，超过3个分页
每个发言包含：
- 专家名（金色，加粗）
- 发言内容（白字，opacity 0.98）
- 左侧金色边框（3px）
- 深色卡片背景（rgba(10,10,10,0.88)）
```

## 四、背景图规则

### 4.1 图片来源

- **AI生成**：SiliconFlow Kolors API（1024x1024）
- **嵌入方式**：base64编码嵌入HTML
- **存储目录**：output/assets/{page_name}.png

### 4.2 背景图分层

```html
<div class="page chapter">
  <div class="bg" style="background:url('data:image/png;base64,...') center/cover"></div>
  <!-- 内容 -->
</div>
```

```css
/* 背景图 - 最低层，低透明度 */
.page > .bg {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background-size: cover;
  background-position: center;
  opacity: 0.3;       /* 降低透明度，不干扰文字 */
  z-index: -1;
}

/* 深色遮罩 - 中间层 */
.page::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(10, 10, 10, 0.75);  /* 深色遮罩 */
  z-index: 0;
}

/* 内容 - 最上层 */
.page > * { position: relative; z-index: 2; }
```

### 4.3 文字可读性保障

```css
/* 卡片背景 */
.sp {
  background: rgba(10, 10, 10, 0.88);  /* 深色卡片 */
  border-left: 3px solid #C9A96E;       /* 金色边框 */
}

/* 文字 */
.st {
  color: #F5F0E8;
  opacity: 0.98;   /* 几乎不透明 */
}
```

## 五、翻页系统

### 5.1 固定功能

| 功能 | 实现 | 优先级 |
|------|------|--------|
| 进度条 | 顶部渐变条 | 必须 |
| 页码 | 右下角显示 | 必须 |
| scroll-snap | 横向滚动 | 必须 |
| 键盘翻页 | ← → 方向键 | 必须 |
| 滚轮翻页 | 防抖处理 | 必须 |

### 5.2 翻页容器

```css
.deck {
  display: flex;
  width: 100vw;
  height: 100vh;
  overflow-x: auto;
  scroll-snap-type: x mandatory;
  scrollbar-width: none;
}
```

### 5.3 翻页JS

```javascript
// 键盘翻页
document.addEventListener('keydown', e => {
  if (e.key === 'ArrowRight' || e.key === ' ') scrollToPage(currentIdx + 1);
  if (e.key === 'ArrowLeft') scrollToPage(currentIdx - 1);
});

// 滚轮翻页（防抖）
let wheelTimer;
deck.addEventListener('wheel', e => {
  e.preventDefault();
  clearTimeout(wheelTimer);
  wheelTimer = setTimeout(() => {
    if (e.deltaY > 0) scrollToPage(currentIdx + 1);
    else scrollToPage(currentIdx - 1);
  }, 80);
}, { passive: false });
```

## 六、内容生成规则

### 6.1 V8 JSON结构

```json
{
  "title": "真需求",
  "experts": [{ "name": "芒格", "title": "多元思维模型家", ... }],
  "rounds": [
    {
      "round_number": 1,
      "topic": "价值的本质",
      "core_question": "...",
      "stances": [{ "expert": "刘润", "text": "200-500字深度发言" }],
      "clash_rounds": [...],
      "reality_cases": [{ "case_name": "...", "case_content": "...", "case_lesson": "..." }],
      "cost_discussion": { "scenario": "...", "cost_analysis": [...] },
      "human_nature": { "question": "...", "psychological_analysis": "...", "conclusion": "..." },
      "cognitive_upgrade": { "old_thinking": "...", "new_thinking": "..." }
    }
  ]
}
```

### 6.2 生成方式

```
多agent并行生成 → 汇总V8 JSON → 渲染HTML
- 每轮6个维度
- 每个专家深度发言（不限字数，重质量）
```

## 七、AI配图规则

### 7.1 API配置

- **端点**：`https://api.siliconflow.cn/v1/images/generations`
- **模型**：`Kwai-Kolors/Kolors`（中文水墨风格）
- **尺寸**：1024x1024
- **格式**：PNG
- **Key文件**：`.sf_key`

### 7.2 配图策略

| 页面类型 | Prompt方向 | 示例 |
|----------|-----------|------|
| Cover | 抽象概念 | 金色眼睛从黑暗中浮现 |
| Expert Grid | 人物群像 | 四位智者围桌而坐 |
| Question | 主题概念 | 金色圆圈在暗色背景上 |
| Stances | 观点可视化 | 流水碰石，金色涟漪 |
| Case | 案例场景 | 商业会议场景 |
| Insight | 升级概念 | 光芒从中心射出的光 |

### 7.3 嵌入方式

```python
img_b64 = base64.b64encode(img.content).decode()
bg = "url('data:image/png;base64," + img_b64 + "') center/cover"
```

## 八、常见反模式

### 8.1 设计反模式

- ❌ 模板化渲染（固定模板只换颜色）
- ❌ 背景图直接显示，不加遮罩
- ❌ 文字在背景图上透明度太低
- ❌ 页面边距太小（文字贴边）
- ❌ 所有页面等宽等距（不分密度）

### 8.2 内容反模式

- ❌ 每个专家只有1-2句浅层观点
- ❌ 缺乏书籍原文引用
- ❌ 缺乏深度分析和碰撞
- ❌ 案例不够具体

## 九、质量检查清单

### 9.1 功能检查

- [ ] 翻页器工作正常（键盘+滚轮）
- [ ] 进度条实时更新
- [ ] 页码显示正确
- [ ] scroll-snap流畅

### 9.2 设计检查

- [ ] 文字可读性（背景遮罩≥0.7）
- [ ] 左右留白（15vw）
- [ ] 配色一致（金色+深色）
- [ ] 字体一致（Noto Serif SC）

### 9.3 内容检查

- [ ] 每个专家发言200-500字
- [ ] 每轮6个维度完整
- [ ] 案例具体（名称+内容+启示）
- [ ] 认知升级明确（旧思维→新思维）

---

*文档版本：v1.0*
*对应项目版本：v14.11*
*更新时间：2026-06-23*
