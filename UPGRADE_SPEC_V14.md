# V14 升级规范

## 版本定位

V14 = 渲染引擎V14 + 训练系统V11

**核心升级**：从模板化渲染 → 手工设计HTML + AI生图

## V13 → V14 升级点

### 1. 渲染引擎升级

| 维度 | V13 | V14 |
|------|-----|-----|
| 渲染方式 | html_renderer.py 模板化渲染 | 手工设计HTML |
| 页面类型 | 11种页面类型 | 保留V13的页面类型认知 |
| 分辨率 | 100vw/100vh | 1920x1080 固定舞台 |
| 设计风格 | 模板化（gold/acid/warm） | 手工设计（每本书独立设计） |
| 图片生成 | 无 | SiliconFlow Kolors API |

### 2. 内容生成升级

| 维度 | V13 | V14 |
|------|-----|-----|
| 生成方式 | 单agent生成 | 多agent并行生成 |
| 内容深度 | 6个维度 | 保留V8的6个维度 |
| JSON格式 | V8 JSON | V8 JSON（兼容） |

### 3. AI生图集成

#### 3.1 API信息
- **端点**：https://api.siliconflow.cn/v1/images/generations
- **模型**：Kwai-Kolors/Kolors（中文水墨风格）
- **Key文件**：`.sf_key`

#### 3.2 生图流程
```python
# 1. 根据页面内容生成prompt
# 2. 调用SiliconFlow API生成图片
# 3. 保存到output/assets/目录
# 4. 转base64嵌入HTML（可选）
```

#### 3.3 页面配图策略

| 页面类型 | 配图内容 | Prompt示例 |
|----------|----------|------------|
| Cover | 抽象概念图 | "Abstract golden eye emerging from darkness" |
| Expert grid | 专家头像/概念图 | "Four wise men silhouettes around a table" |
| Question | 主题概念图 | "Abstract golden circle on dark background" |
| Stances | 观点可视化 | "Flowing water meeting stone" |
| Clash | 对抗概念图 | "Two forces clashing" |
| Reality case | 案例场景图 | "Business meeting scene" |
| Cost | 代价概念图 | "Weight and balance concept" |
| Human nature | 人性探索图 | "Human brain with neural connections" |
| Cognitive upgrade | 升级概念图 | "Light rays emerging from center" |
| Final insight | 洞见概念图 | "Golden flower blooming" |
| Open questions | 问题概念图 | "Question marks in golden light" |

#### 3.4 图片规格
- **尺寸**：1024x1024
- **格式**：PNG
- **存储**：output/assets/{page_name}.png
- **嵌入**：base64编码嵌入HTML（独立文件）

### 4. 页面类型系统

保留V13的11种页面类型：

1. **Cover** - 封面（标题、副标题、专家）
2. **Expert grid** - 专家网格（4-8位专家档案）
3. **Question** - 问题页（每轮核心问题）
4. **Stances** - 立场页（每3个专家一批）
5. **Clash** - 交锋页（专家互相反驳）
6. **Reality case** - 案例页（现实案例）
7. **Cost** - 成本讨论页（代价分析）
8. **Human nature** - 人性分析页（心理分析）
9. **Cognitive upgrade** - 认知升级页（思维升级）
10. **Final insight** - 最终洞见
11. **Open questions** - 开放问题

### 5. V8 JSON格式（兼容）

```json
{
  "title": "真需求",
  "subtitle": "商业世界的本质是什么？",
  "experts": [
    {
      "name": "芒格",
      "title": "多元思维模型家",
      "avatar_color": "#D4A04A",
      "stance": "support",
      "core_belief": "...",
      "interest": "...",
      "fear": "...",
      "bias": "...",
      "experience": "...",
      "speaking_style": "..."
    }
  ],
  "rounds": [
    {
      "round_number": 1,
      "topic": "价值的本质",
      "core_question": "...",
      "stances": [...],
      "clash_rounds": [...],
      "reality_cases": [...],
      "cost_discussion": {...},
      "human_nature": {...},
      "cognitive_upgrade": {...}
    }
  ],
  "final_insight": "...",
  "open_questions": [...]
}
```

### 6. 设计规范

#### 6.1 分辨率
- 固定舞台：1920x1080
- 缩放方式：transform: scale() 适配不同屏幕

#### 6.2 配色系统
- 保留V13的gold/acid/warm主题
- 新增：每本书独立设计风格

#### 6.3 字体
- 中文：Noto Serif SC
- 英文：Inter / JetBrains Mono
- 特殊：Ma Shan Zheng（毛笔字体）

#### 6.4 页面布局
- Cover：居中对齐
- Expert grid：2x4网格
- Stances：每页3个专家
- Clash：左右对比
- 其他：居中对齐

### 7. 执行流程

```
1. 生成V8 JSON内容（多agent并行）
   - 每轮6个维度：立场、交锋、案例、成本、人性、认知升级
   - 每个专家深度发言（不限字数，重质量）

2. 生成配图（SiliconFlow API）
   - 根据页面内容生成prompt
   - 调用API生成图片
   - 保存到output/assets/目录

3. 手工设计HTML（基于V13的页面类型）
   - 每本书独立设计风格
   - 基于1920x1080分辨率
   - 使用CSS变量管理配色
   - 嵌入base64图片

4. 整合JSON和HTML
   - 基于V8 JSON生成HTML
   - 手工设计样式（不是模板化）
   - 嵌入AI生成的图片
```

## 升级计划

### Phase 1：定义V14规范
- [x] 调研V13架构
- [x] 定义V14升级点
- [x] 写升级规范文档
- [x] 集成AI生图功能

### Phase 2：生成V8 JSON内容
- [ ] 用子代理并行生成《真需求》的V8 JSON
- [ ] 每轮6个维度
- [ ] 验证内容质量

### Phase 3：生成配图
- [ ] 根据V8 JSON内容生成prompt
- [ ] 调用SiliconFlow API生成图片
- [ ] 保存到output/assets/目录

### Phase 4：手工设计HTML
- [ ] 基于V13的页面类型
- [ ] 手工设计样式
- [ ] 基于1920x1080分辨率
- [ ] 嵌入base64图片

### Phase 5：整合和测试
- [ ] 整合JSON和HTML
- [ ] 测试不同分辨率
- [ ] 验收

## 成功标准

1. **内容深度**：每轮6个维度，每个专家深度发言
2. **HTML设计**：手工设计，非模板化
3. **分辨率**：1920x1080 固定舞台
4. **页面类型**：保留V13的11种页面类型
5. **AI生图**：每个页面有AI生成的配图
6. **兼容性**：V8 JSON格式兼容

---

*定义时间：2026-06-23*
*基于V13.11升级*
*集成SiliconFlow Kolors API*
