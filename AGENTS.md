# 项目指令

> 详细规范见 `SKILL.md`，本文件仅保留操作规则。

## 自动更新规则

**每完成一本书的圆桌洞见后，必须执行：**

1. **更新 README.md**
   - 在"已讨论书目"表格中添加新书目

2. **更新 index.html**
   - 在 `<div class="books">` 开头添加新的 book-card 卡片
   - 卡片结构：
     ```html
     <div class="book-card">
     <div class="book-tag">V4.0 · N页</div>
     <h3>书名</h3>
     <div class="book-author">作者 · 原著书名</div>
     <div class="book-stats"><span>6专家</span><span>N轮</span><span>42发言</span><span>5洞见</span></div>
     <div class="book-desc">简短描述，突出核心议题和参与专家</div>
     <a class="book-link" href="output/书名_圆桌洞见.html">查看洞见</a>
     </div>
     ```
   - 新卡片应添加在现有卡片之前（最新优先）

3. **提交并推送到 GitHub**
   ```
   git add -A
   git commit -m "feat: 添加《书名》圆桌洞见 (V2.x · N页)"
   git push origin main
   ```

---

## 单页禁止内部滚动铁律 ★最重要

**所有模板的每个页面（section/slide）绝对不能出现内部滚动！**

### 原因
- 滚轮翻页器会拦截 wheel 事件并调用 e.preventDefault()
- 如果页面有内部滚动，用户无法滚动查看完整内容
- 内容与翻页器冲突

### 规则
```css
/* ✅ 正确：固定高度，禁止滚动 */
.section, .slide {
  height: 100vh;
  overflow: hidden;  /* 禁止内部滚动 */
}

/* ❌ 错误：允许内部滚动 */
.section {
  overflow-y: auto;  /* 绝对禁止 */
  overflow-y: scroll; /* 绝对禁止 */
}
```

### 内容处理
- **内容可以跨页** — 如果内容太多，拆分到下一页
- **每页内容控制在视口内** — 高度不超过 100vh
- **使用分页** — 而不是单页内滚动

---

## 模板翻页功能铁律

**所有模板必须实现以下 4 种翻页方式：**

### 1. 键盘翻页（必须）

```javascript
document.addEventListener('keydown',e=>{
  if(e.key==='ArrowDown'||e.key==='ArrowRight'||e.key===' '||e.key==='PageDown'){
    e.preventDefault();go(cur+1);
  }else if(e.key==='ArrowUp'||e.key==='ArrowLeft'||e.key==='PageUp'){
    e.preventDefault();go(cur-1);
  }else if(e.key==='Home'){
    e.preventDefault();go(0);
  }else if(e.key==='End'){
    e.preventDefault();go(total-1);
  }
});
```

| 按键 | 功能 |
|:---|:---|
| `↓` / `→` / `Space` / `PageDown` | 下一页 |
| `↑` / `←` / `PageUp` | 上一页 |
| `Home` | 第一页 |
| `End` | 最后一页 |

### 2. 滚轮翻页（必须）

```javascript
let wheelTimer=null;
document.addEventListener('wheel',e=>{
  e.preventDefault();
  if(wheelTimer)return;
  wheelTimer=setTimeout(()=>wheelTimer=null,400);
  if(e.deltaY>0)go(cur+1);
  else if(e.deltaY<0)go(cur-1);
},{passive:false});
```

**要点**：
- 必须使用 `e.preventDefault()` 阻止默认滚动
- 必须使用节流（`wheelTimer`）防止连续触发
- 节流间隔 400ms

### 3. 点击翻页（必须）

```javascript
document.body.addEventListener('click',e=>{
  if(e.target.closest('.nav-dot,.nav-dots,.expert-card,.speech-block,.clash-block,.insight-block,.question-card,.conclusion-card'))return;
  go(cur+1);
});
```

**要点**：
- 点击空白区域自动下一页
- 必须排除交互元素（导航点、卡片、按钮等）
- 使用 `e.target.closest()` 检查排除列表

### 4. 导航点点击（必须）

```javascript
sections.forEach((s,i)=>{
  const dot=document.createElement('button');
  dot.className='nav-dot'+(i===0?' active':'');
  dot.onclick=()=>go(i);
  dotsContainer.appendChild(dot);
});
```

**要点**：
- 每个页面对应一个导航点
- 当前页导航点高亮（`.active`）
- 点击导航点直接跳转对应页

---

## go() 函数标准实现

```javascript
function go(n){
  if(n<0||n>=total)return;           // 边界检查
  sections[cur].classList.remove('visible');  // 隐藏当前页
  dotsContainer.children[cur]?.classList.remove('active');  // 取消高亮
  cur=n;                             // 更新索引
  sections[cur].scrollIntoView({behavior:'smooth',block:'start'});  // 滚动到目标页
  sections[cur].classList.add('visible');      // 显示目标页
  dotsContainer.children[cur]?.classList.add('active');  // 高亮导航点
  const pct=Math.min(100,((cur+1)/total)*100);  // 更新进度条
  progress.style.width=pct+'%';
}
```

---

## 模板验证标准

验证脚本 `engine/validate_templates.py` 检查：

| 检查项 | 要求 |
|:---|:---|
| HTML声明 | `<!DOCTYPE html>` |
| 内容占位符 | `{{slides}}` 或 `{{#each` |
| 导航组件 | `id="nav"` 或 `id="navDots"` 或 `class="nav-dots"` |
| 翻页逻辑 | `prevBtn` 或 `btnPrev` 或滚动式设计 |

---

## 模板类型分类

| 类型 | 渲染方式 | 标识 |
|:---|:---|:---|
| Handlebars | `render_v8.py` | 包含 `{{#each` 或 `{{add` |
| Adapter | `render_adapter.py` | 包含 `{{slides}}` |
| Scroll | 滚动式单页 | 包含 `.section{` + `scrollIntoView` |

---

*版本：V5.1*
*更新时间：2026-05-26*