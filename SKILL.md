---
name: roundtable-conference-v2
description: "认知演化圆桌系统 V3.0。深度讨论导向，7轮全员交锋，锚定书中情节，每轮包含独立碰撞页，榨干每一滴认知增量。"
---

# 圆桌会议 V3.0

> **核心定位：榨干每一滴认知增量**
> **质量 = 情节锚定 x 论证深度 x 碰撞强度 x 洞见锐度**

---

## 系统架构

### 模板系统（统一规范）

**唯一模板**: ssets/roundtable-template-v3.html

- 字体: IBM Plex Mono + Noto Serif SC + Noto Sans SC
- 配色: #0a0a0b 背景 + #f1efea 文字
- 动画: [data-anim] 入场动画
- 导航: 键盘/鼠标/触摸/滚轮/TOC

**禁止使用其他模板**

---

### HTML生成流程

**必须使用PowerShell生成**，禁止Python脚本（编码问题）

`powershell
# Step 1: 读取模板
 = [System.IO.File]::ReadAllText("assetsoundtable-template-v3.html", [System.Text.Encoding]::UTF8)

# Step 2: 准备slides内容
 = "slides HTML content here"

# Step 3: 替换占位符
 = .Replace("<!-- SLIDES_HERE -->", )
 = .Replace("__BOOK_TITLE__", "书名")

# Step 4: 写入文件
[System.IO.File]::WriteAllText("output\书名_圆桌洞见.html", , [System.Text.Encoding]::UTF8)
`

---

### CSS Class 规范

必须使用以下class（模板已定义）：
- .slide - 幻灯片外壳
- .slide.hero.active - 封面页
- .slide.title-slide - 标题页
- .frame - 内容区容器
- .sp - 发言块
- .cb - 碰撞块
- .insight-c - 洞见卡
- .metric - 指标卡
- .tag - 标签

**禁止自定义class**

---

### 入场动画

所有内容元素必须添加 data-anim 属性

---

## 质量保证

### 生成后必须验证

`powershell
 = [System.IO.File]::ReadAllText("output\书名_圆桌洞见.html", [System.Text.Encoding]::UTF8)

# 检查项：
# 1. Slide结构 - slideCount, activeCount
# 2. JS完整性 - go(), go(0), querySelectorAll, classList, wheel, keyboard
# 3. CSS完整性 - display:none, display:flex, font system
# 4. 组件完整性 - sp, cb, insight-c, TOC, progress-bar
`

**所有检查必须PASS**

---

### 常见问题预防

- 只有一页 -> JS被截断 -> 用PowerShell生成
- 样式丢失 -> 用了错误模板 -> 只用v3模板
- 编码乱码 -> 编码不一致 -> 全程UTF8
- 动画不生效 -> 缺少data-anim -> 所有内容元素加data-anim

---

## 内容规范

### 专家库同步规则

每次开始前必须同步专家库

---

### 质量红线

**内容深度红线**：
- 发言字数 < 350字 -> 无效发言
- 无书中情节引用 -> 无效发言
- 无因果推理链 -> 无效洞见
- 无专家间直接反驳 -> 无效碰撞
- 总页数 < 30页 -> 深度不足

**排版红线**：
- 同一屏幕内超过4人发言 -> 内容过载
- 无颜色标记的碰撞类型 -> 视觉混乱

**框架红线**：
- 缺少三层架构 -> 结构性失败

---

### 页面结构

总页数: 35-45页

**第一层：洞见全景 30-40%**
- 封面、洞见全景、讨论仪表盘、张力图谱

**第二层：深度讨论 40-50%**
- 每轮：标题页 + 发言页(2-3人/页) + 碰撞页

**第三层：认知演化 20-30%**
- 假设演化、开放问题、结语

---

## 风格预设

- **严肃风格**：学术分析、正式场合
- **接地气风格**：大众传播、轻松阅读
- **人物原有风格**：还原专家真实说话方式

---

## 工作流程

1. 同步专家库
2. 分析书籍内容
3. 选择6位专家
4. 生成7轮讨论
5. 用PowerShell生成HTML
6. 运行验证脚本
7. 提交到GitHub
8. 更新README.md和index.html

### 禁止事项

- 不要用Python脚本生成HTML
- 不要使用旧模板
- 不要自定义CSS class
- 不要跳过验证步骤
- 不要引入外部资源

---

## PPTX 导出（可选）

使用 Presentations 技能，配置选择：
- 观点表达 -> strategy-leadership
- 数据分析 -> inance-ir
- 产品介绍 -> product-platform

---

## 版本历史

- V1.0: 整合蒸馏引擎 + 圆桌讨论 + 专家库
- V2.0: 范式转变：深度讨论导向
- V2.1: 全员发言、论证深度、碰撞强度
- V2.2: 情节锚定、独立碰撞页
- V2.4: 排版规范、CSS自包含
- V2.5: 专家库同步规则
- V2.6: 三层架构、质量红线
- V3.0: **统一模板、PowerShell生成、自动化验证、稳定性保障**

---

*版本：V3.0*
*更新时间：2026-05-26*
*稳定性：PowerShell生成 + 自动化验证 + 单一模板*
