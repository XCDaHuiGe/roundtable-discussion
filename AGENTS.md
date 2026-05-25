# 项目指令

## 自动更新规则

**每次完成一本书的圆桌讨论后，必须执行以下操作：**

1. **更新 README.md**
   - 在"已讨论书目"表格中添加新书目（书名、作者、版本、页数、专家数、轮次、核心洞见）
   - 更新版本历史（如有版本变更）

2. **更新 index.html**
   - 在"已讨论书目"区域 `<div class="books">` 开头添加新的 book-card 卡片
   - 卡片结构：
     ```html
     <div class="book-card">
     <div class="book-tag">V2.x · N页</div>
     <h3>书名</h3>
     <div class="book-author">作者 · 原著书名</div>
     <div class="book-stats"><span>6专家</span><span>N轮</span><span>42发言</span><span>5洞见</span></div>
     <div class="book-desc">简短描述，突出核心议题和参与专家</div>
     <a class="book-link" href="output/书名_圆桌洞见.html">查看洞见</a>
     </div>
     ```
   - 更新页脚版本号（如 V2.4 → V2.5）
   - 新卡片应添加在现有卡片之前（最新优先）

3. **提交并推送到 GitHub**
   ```
   git add -A
   git commit -m "feat: 添加《书名》圆桌洞见 (V2.x · N页)"
   git push origin main
   ```

## 输出规范

- HTML PPT 文件放在 `output/` 目录
- 文件名格式：`{书名}_圆桌洞见.html`
- CSS 必须自包含（不引用外部资源）
- 总页数 35-45 页（弹性多页布局）
