# 项目指令

> 详细规范见 `SKILL.md`，本文件仅保留操作规则。

## 自动更新规则

**每完成一本书的圆桌讨论后，必须执行：**

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
