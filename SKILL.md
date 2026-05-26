---
name: roundtable-conference-v2
description: "认知演化圆桌系统 V2.5。深度讨论导向，7轮全员交锋，锚定书中情节，每轮包含独立碰撞页，榨干每一滴认知增量。"
---

## 专家库同步规则 ★必读

```
【强制规则】每次开始圆桌讨论前必须执行：

1. 检查 GitHub 更新
   - 访问: https://github.com/XCDaHuiGe/expert-library
   - 查看最新提交时间和内容

2. 同步本地仓库（如有更新）
   cd D:\vibe_coding\zhengliu\expert-library
   git fetch origin
   git pull origin main
   git push origin master  # 如本地有领先提交

3. 使用最新专家档案
   - 必须从本地同步后的仓库读取专家信息
   - 禁止使用过期的专家数据

4. 同步检查清单
   □ GitHub 最新提交时间
   □ 本地仓库是否同步
   □ 专家档案是否最新
```

## 内部闭环能力 ★

本项目完全独立运行，不依赖外部服务。内置以下能力：

| 能力 | 来源 | 说明 |
|:---|:---|:---|
| **HTML PPT 生成** | 内置 | 零依赖单HTML，支持35+主题 |
| **动画效果** | 内置 | 20+ WebGL/CSS 动画效果 |
| **响应式布局** | 内置 | 三档自适应（桌面/平板/手机） |
| **导航系统** | 内置 | 键盘/鼠标/触摸/目录 TOC |

### ppt-assets 资源

```
ppt-assets/
├── base.css              → 基础样式框架
├── fonts.css             → 字体配置
├── semantic.css          → 语义组件
├── runtime.js            → 运行时引擎
├── animations/           → 动画效果（20+ fx）
│   ├── animations.css
│   ├── fx-runtime.js
│   └── fx/              → 20+ WebGL/CSS 动画
│       ├── starfield.js
│       ├── matrix-rain.js
│       ├── constellation.js
│       └── ...
└── themes/               → 主题样式（35+）
    ├── cyberpunk-neon.css
    ├── editorial-magazine.css
    ├── nord.css
    └── ...
```

---

# 圆桌会议 V2.5 — Deep Discussion Roundtable

> **核心定位：榨干每一滴认知增量**
> **质量 = 情节锚定 × 论证深度 × 碰撞强度 × 洞见锐度**

---

## 问题复盘（从 V2.0 到 V2.5 的失败教训）

| 版本 | 问题 | 根因 | V2.5 解法 |
|:---|:---|:---|:---|
| V2.0 | 每轮只有3-4人发言 | 没有强制规则 | **6人全员，无人缺席** |
| V2.1 | 发言只有150-250字 | 没有最低字数约束 | **每次发言最低400字，硬性下限** |
| V2.1 | 讨论脱离书中内容 | 没有情节锚定机制 | **每次发言必须引用书中至少1个具体情节/对话/细节** |
| V2.1 | 碰撞只是各说各话 | 没有反驳交锋机制 | **每轮必须有独立碰撞页，包含3-4轮来回反驳** |
| V2.1 | 洞见句太泛 | 没有质量检验 | **洞见句必须包含因果推理，不能是独立断言** |
| V2.5 | 页数只有19页 | 每轮分配页数太少 | **每轮3-5页（标题页+发言页+碰撞页），总35-45页** |

---

## V2.6 质量红线（绝对禁止）

```yaml
# 内容深度红线
❌ 发言字数 < 350字 → 判定为无效发言
❌ 无书中情节引用 → 判定为无效发言  
❌ 无因果推理链 → 判定为无效洞见
❌ 无专家间直接反驳 → 判定为无效碰撞
❌ 总页数 < 30页 → 判定为深度不足

# 排版红线
❌ 同一屏幕内超过4人发言 → 内容过载
❌ 无左右分栏的碰撞页 → 区分不清
❌ 无颜色标记的碰撞类型 → 视觉混乱
❌ 字体大小 < 0.8rem → 可读性差

# 框架红线
❌ 缺少三层架构（洞见30%+讨论50%+演化20%）→ 结构性失败
❌ 缺少讨论仪表盘 → 缺乏全局视角
❌ 缺少张立图谱 → 缺乏认知演化追踪
```

---

## 页面结构（V2.6 三层架构）

```
总页数: 35-45页（弹性多页）

【第一层：洞见全景 30-40%】
Slide 0:  封面（1页）
Slide 1:  洞见全景（1页，6个洞见卡片）
Slide 2:  讨论仪表盘（1页）
Slide 3:  张力图谱/观点演化时间线（1页）

【第二层：深度讨论 40-50%】
Slide 4:  Round 1 标题页（留白）
Slide 5-6: Round 1 发言页（2-3人/页）
Slide 7:  Round 1 碰撞页
Slide 8:  Round 2 标题页
Slide 9-10: Round 2 发言页
Slide 11: Round 2 碰撞页
Slide 12: Round 3 标题页
Slide 13-14: Round 3 发言页
Slide 15: Round 3 碰撞页
Slide 16: Round 4 标题页
Slide 17-18: Round 4 发言页
Slide 19: Round 4 碰撞页
Slide 20: Round 5 标题页
Slide 21-22: Round 5 发言页
Slide 23: Round 5 碰撞页
Slide 24: Round 6 标题页
Slide 25-26: Round 6 发言页
Slide 27: Round 6 碰撞页
Slide 28: Round 7 标题页
Slide 29-30: Round 7 发言页
Slide 31: Round 7 碰撞页

【第三层：认知演化 20-30%】
Slide 32: 假设演化（推翻的假设）
Slide 33: 核心争议聚焦
Slide 34: 开放问题（5个）
Slide 35-36: 结语
```

---

## 发言规则（V2.6 强制）

```yaml
每次发言必须满足:
  1. 最低400字（硬性下限，低于400字的发言无效）
  2. 必须引用书中至少2个具体情节/对话/细节
  3. 必须包含以下至少3项:
     - 书中情节引用（如：书中第X章写道...）
     - 推理链条（因为A所以B所以C）
     - 反驳指涉（回应某位专家的具体观点）
     - 案例类比（用其他领域的案例来类比）
     - 颠覆性观点（挑战常识）
  4. 禁止无推理链的断言
  5. 禁止脱离书中内容的纯抽象讨论

情节锚定机制:
  - 每次发言必须以书中具体情节为起点
  - 不能先说观点再找例子，必须从情节出发推导观点
  - 情节引用必须具体（人物+事件+对话+页码），不能泛泛而谈
```

---

## 讨论风格预设 ★

用户可通过提示词指定风格，如：`/roundtable-conference-v2 接地气风格 {书籍}`

### 预设 A：严肃风格（默认）

```yaml
语气: 严谨、克制、有分寸
允许: 学术术语（但必须用括号解释）
禁止: 段子、网络用语、情绪化表达
发言顺序: 先论据后论点
示例: |
  "凯蒂坚持让孩子每天读一页圣经、一页莎士比亚——请注意，她自己不识字。
  这在心理学上叫做'代际期望投射'（就是父母把自己没实现的愿望压在孩子身上），
  但凯蒂的情况更复杂：她不是在投射，而是在执行她母亲玛丽的遗嘱。"
```

### 预设 B：接地气风格

```yaml
语气: 像朋友聊天，轻松但有深度
允许: 口语、比喻、生活化类比
禁止: 未经解释的学术术语、论文腔、"从XX理论看"
发言顺序: 先说人话再上理论，先举例子再下结论
示例: |
  "凯蒂这个妈挺有意思的——自己一个字不认得，偏偏逼着孩子每天读圣经和莎士比亚。
  换成今天的话说，就是一个初中都没毕业的保洁阿姨，非要让孩子背《论语》和莎士比亚。
  你可能觉得这不现实，但凯蒂根本不在乎现实不现实。
  她妈临死前跟她说了一句话：'你可以没吃没穿，但你必须让孩子读书。'
  凯蒂就把这句话当圣旨执行了。"
```

### 预设 C：人物原有风格

```yaml
语气: 还原每位专家的真实说话方式
核心: 每位专家用自己著作中的语言风格发言
规则:
  - 马斯洛: 用"需求""自我实现""高峰体验"等自己的术语，语气温和人本主义
  - 加缪: 用"荒谬""反抗""西西弗斯"等意象，语言简洁有力带哲学诗意
  - 芒格: 用"多元思维模型""反过来想""能力圈"等自己的概念，直接毒舌
  - 孔子: 用"仁""礼""中庸"等儒家概念，温润而坚定
  - 塞利格曼: 用"习得性无助""习得性乐观""PERMA"等术语，实证导向
  - 格拉德威尔: 用"引爆点""异类""10000小时"等自己的框架，讲故事风格
示例: |
  加缪: "弗兰西坐在太平梯上觉得自己住在树上。这就是西西弗斯。
  她每天推石头上山——捡破烂、挨饿、被人嘲笑——然后第二天重新开始。
  但她找到了一个山顶：那棵天堂树。石头不再重要了。"
```

### 风格切换规则

```yaml
选择方式:
  - 用户提示词包含"严肃" → 预设A
  - 用户提示词包含"接地气"/"通俗"/"大白话" → 预设B
  - 用户提示词包含"原味"/"人物风格"/"还原" → 预设C
  - 未指定 → 默认预设A

混搭规则:
  - 同一轮讨论内风格必须统一
  - 不同轮次可以切换风格（需用户明确指定）
  - 洞见句始终使用简洁直白风格（不随预设变化）

## 碰撞机制（V2.6 强制）

```yaml
每轮必须有独立碰撞页:
  碰撞页结构:
    - 碰撞回合1: 专家A→专家B（250-350字，引用书中情节）
    - 碰撞回合2: 专家B→专家A（250-350字，引用书中情节）
    - 碰撞回合3: 专家C→专家A/B（250-350字，引用书中情节）
    - 碰撞回合4: 专家D加入新维度（250-350字）
    - 洞见句: 碰撞产生的新认知（80字以内）

  碰撞类型（每轮至少使用3种）:
    1. 情节反驳: "你引用的情节恰恰证明了相反的观点..."
    2. 细节挑战: "但你忽略了书中另一处..."
    3. 逻辑追问: "如果A成立，那么书中X情节如何解释？"
    4. 框架质疑: "你用的这个框架本身就是..."
    5. 反例引入: "但书中有一个反例..."

  碰撞质量标准:
    - 不追求和谐共识
    - 追求有价值的分歧
    - 碰撞必须基于书中具体情节
    - 禁止脱离文本的抽象争论
    - 禁止"礼貌性附和"，鼓励"认知冲突"
```

---

## 洞见提炼机制（V2.4 强制）

```yaml
每轮必须产出:
  - 洞见句: 1句（50字以内，必须包含因果推理）
  - 格式: "因为A，所以B，这意味着C"
  - 禁止: 独立断言（如"贫穷是环境暴力"）

全场必须产出:
  - 核心洞见: 5个（每个150-250字，含情节+推理+结论）
  - 颠覆性观点: 至少1个（挑战常识的认知）
  - 开放问题: 5个（留给读者思考）

洞见质量检验:
  - ✓ 合格: "因为凯蒂坚持让弗兰西每天读圣经和莎士比亚，而凯蒂自己不识字，所以教育不是知识传递，而是一种代际意义建构"
  - ✗ 不合格: "教育是贫穷的解药"（无推理链，无情节锚定）
```

---

## 专家选择规则

```yaml
每场讨论选择6位专家:
  - 主辩手: 1位（核心论点持有者，贯穿全场）
  - 挑战者: 3位（负责质疑和反驳，轮换发力）
  - 调和者: 1位（寻找共识、总结分歧、发现盲点）
  - 观察者: 1位（元视角，点评讨论过程，发现遗漏维度）

选择标准:
  - 必须从专家库中选择真实专家
  - 专家之间必须有明显的立场差异
  - 禁止选择立场相似的专家
  - 至少有1位与书的主题直接相关的领域专家
```

---

## HTML PPT 生成（V2.7 模板化）

**模板文件**: `assets/roundtable-template.html`

### 生成流程（必须严格遵守）

```
Step 1: 读取模板
  template = read("assets/roundtable-template.html")

Step 2: 生成 slide 内容（纯 HTML，不含 <head>/<body>/<style>/<script>）
  slides_html = ""
  slides_html += cover_slide(book_title, author, experts)
  slides_html += toc_slide(rounds)
  slides_html += insight_slide(insights)
  slides_html += dashboard_slide(metrics)
  for round in rounds:
      slides_html += title_slide(round.theme, round.question)
      slides_html += speech_slide(round.speeches[:3])   # 上半场 3人
      slides_html += speech_slide(round.speeches[3:])   # 下半场 3人
      slides_html += collision_slide(round.collisions, round.insight)
  slides_html += evolution_slide(hypotheses)
  slides_html += questions_slide(open_questions)
  slides_html += conclusion_slide(quote, summary)

Step 3: 注入模板
  html = template.replace("<!-- SLIDES_HERE -->", slides_html)
  html = html.replace("__BOOK_TITLE__", book_title)

Step 4: 写入文件
  write("output/{书名}_圆桌洞见.html", html)
```

### ⚠️ 绝对禁止

- ❌ 不要手写 <style> 标签（模板已包含）
- ❌ 不要手写 <script> 标签（模板已包含）
- ❌ 不要修改模板中的 CSS class 名（.slide, .active, .frame 等）
- ❌ 不要在 slide 内容中使用内联 style 超过 3 行
- ❌ 不要引入任何外部资源

### Slide HTML 规则

```yaml
每个 slide:
  外壳: <div class="slide" data-title="标题">
  首页: <div class="slide hero active" data-title="封面">
  标题页: <div class="slide title-slide" data-title="标题">
  内容区: <div class="frame">...</div>
  关闭: </div>

发言块:
  <div class="sp">
    <div class="sh"><span class="sn">专家名</span><span class="sr">角色</span></div>
    <div class="st">发言内容...</div>
  </div>

碰撞块:
  <div class="cb [blue|purple|orange|green]">
    <div class="cl [blue|purple|orange|green]">碰撞类型</div>
    <div class="sh"><span class="sn">专家名</span></div>
    <div class="st">发言内容...</div>
  </div>

洞见句:
  <div class="insight-c">
    <div class="insight-q">洞见句</div>
    <div class="insight-a">内容...</div>
  </div>

标签:
  <span class="tag [tag-gold|tag-red|tag-blue|tag-purple|tag-green|tag-brown]">文字</span>

指标:
  <div class="metrics">
    <div class="metric"><div class="metric-val">7</div><div class="metric-label">轮次</div></div>
  </div>
```

每页内容密度：
  - 标题页: 轮次主题 + 核心问题（100字以内，大留白）
  - 发言页: 2-3人发言，每人400-500字
  - 碰撞页: 3-4轮来回反驳 + 洞见句
  - 每页总字数: 800-1200字（控制在一屏可读范围内）

Slide HTML 规则：
  - 每个 slide 用 `<div class="slide" data-title="标题">` 包裹
  - 第一个 slide 加 `active` class: `<div class="slide hero active" data-title="封面">`
  - 内容区用 `<div class="frame">` 包裹
  - 发言块用 `.sp` > `.sh`(头部) + `.st`(正文)
  - 碰撞块用 `.cb` + 颜色 class（.blue/.purple/.orange/.green）
  - 洞见卡用 `.insight-c` > `.insight-q` + `.insight-a`

---

## 质量评分卡（V2.4）

```yaml
核心指标（必须高分）:
  情节锚定: X/5       ★★★ 每次发言是否引用书中具体情节
  发言覆盖: X/5       ★★★ 6人是否每轮都发言
  碰撞强度: X/5       ★★★ 是否有真正的来回反驳
  论证深度: X/5       ★★★ 是否有推理链+情节+反驳

过程指标:
  专家真实性: X/5     ★★ 必须使用真实专家名
  发言字数: X/5       ★★ 每次发言是否达到300字
  洞见句质量: X/5     ★★ 是否包含因果推理

产出指标:
  颠覆性观点: X/5     ★★ 是否挑战了常识
  可引用性: X/5       ★★ 洞见句是否可以直接引用
  开放问题: X/5       ★ 是否留给读者有价值的思考

总分: XX/50
  45-50: 洞见级讨论
  35-44: 深度讨论
  25-34: 有效讨论
  <25: 需重做
```

---

## 排版规范（V2.7）

CSS/JS/导航/响应式全部由模板 `assets/roundtable-template.html` 提供，无需手写。

内容排版规则：
  - 发言页最多 2-3 人/页，6 人发言拆成 2-3 页
  - 长发言（>400字）独占一页
  - 标题页大留白，只放轮次编号 + 主题 + 核心问题
  - 碰撞页颜色标记：情节反驳(红)、细节挑战(蓝)、逻辑追问(紫)、框架质疑(橙)、反例引入(绿)

禁止事项：
  - 禁止 inline style 超过 3 行
  - 禁止引入任何外部资源（字体、图标、CDN）


## HTML 模板说明（V2.6+）

### 模板文件
- **主模板**: `assets/roundtable-template-v2.html`（推荐）
- **旧模板**: `assets/roundtable-template.html`（兼容）

### V2.6 模板设计特点

**视觉风格**
- 深色主题：`#0a0a0f` 背景 + `#e8e0d4` 文字
- 衬线字体：Noto Serif SC，更有质感
- 渐变色标题：金色渐变效果
- 毛玻璃效果：backdrop-filter

**配色系统**
```css
--accent: #c23b22  /* 主强调色（红） */
--gold: #d4a843    /* 次强调色（金） */
--blue: #4a6a9a    /* 蓝色 */
--purple: #8a4aaa  /* 紫色 */
--green: #3a8a5c   /* 绿色 */
```

**组件样式**
- 发言块 `.sp`：卡片式设计，左侧彩色边条
- 碰撞块 `.cb`：虚线边框，颜色区分类型
- 洞见卡 `.insight-c`：渐变背景，顶部金色装饰线
- 指标卡 `.metric`：简洁卡片，大号数字

**动画效果**
- 入场动画 `.anim-up`：向上淡入，逐个延迟
- 进度条 `.progress-bar`：顶部渐变进度
- 平滑过渡：所有交互都有缓动效果

**响应式设计**
- 桌面：>1024px，80px 侧边距
- 平板：768-1024px，40px 侧边距
- 手机：<768px，20px 侧边距，隐藏导航点

### Slide HTML 规则（V2.6）

```yaml
每个 slide:
  外壳: <div class="slide" data-title="标题">
  首页: <div class="slide hero active" data-title="封面">
  标题页: <div class="slide title-slide" data-title="标题">
  内容区: <div class="frame">...</div>
  动画: 内容元素加 class="anim-up"
  关闭: </div>

封面:
  <div class="cover-badge">圆桌洞见 V2.6</div>
  <h1 class="cover-title">书名</h1>
  <p class="cover-sub">描述</p>
  <div class="cover-stats">
    <div class="cover-stat"><div class="cover-stat-num">6</div><div class="cover-stat-label">专家</div></div>
  </div>

发言块:
  <div class="sp anim-up">
    <div class="sh">
      <div class="speaker-avatar" style="background:#c23b22">孔</div>
      <span class="sn">孔子</span>
      <span class="sr">主辩手</span>
    </div>
    <div class="st">发言内容...</div>
  </div>

碰撞块:
  <div class="cb [blue|purple|orange|green] anim-up">
    <div class="cl [blue|purple|orange|green]">碰撞类型</div>
    <div class="sh"><span class="sn">专家名</span></div>
    <div class="st">发言内容...</div>
  </div>

洞见卡:
  <div class="insight-c anim-up">
    <div class="insight-q">洞见句</div>
    <div class="insight-a">内容...</div>
  </div>

指标:
  <div class="metrics anim-up">
    <div class="metric"><div class="metric-val">7</div><div class="metric-label">轮次</div></div>
  </div>
```
## 版本历史

| 版本 | 核心升级 |
|:---|:---|
| V1.0 | 整合蒸馏引擎 + 圆桌讨论 + 专家库 |
| V2.0 | 范式转变：从蒸馏导向到深度讨论导向 |
| V2.1 | 全员发言、论证深度、碰撞强度 |
| V2.2 | 情节锚定、独立碰撞页、300字硬性下限、因果推理洞见句 |
| V2.4 | 排版规范、CSS自包含、响应式三档、滚动处理、碰撞页颜色标记 |
| V2.5 | 新增专家库同步规则（每次工作前必须检查GitHub） |
| V2.6 | 三层架构、400字下限、4轮碰撞、张力图谱、质量红线 |

---

*版本：V2.6*
*更新时间：2026-05-25*
*核心定位：锚定书中情节，榨干每一滴认知增量*
