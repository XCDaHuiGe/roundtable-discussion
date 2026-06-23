# V14 升级规范

## 版本定位

V14 = 渲染引擎V14 + 训练系统V11

**核心升级**：从模板化渲染 → 手工设计HTML

## V13 → V14 升级点

### 1. 渲染引擎升级

| 维度 | V13 | V14 |
|------|-----|-----|
| 渲染方式 | html_renderer.py 模板化渲染 | 手工设计HTML |
| 页面类型 | 11种页面类型 | 保留V13的页面类型认知 |
| 分辨率 | 100vw/100vh | 1920x1080 固定舞台 |
| 设计风格 | 模板化（gold/acid/warm） | 手工设计（每本书独立设计） |

### 2. 内容生成升级

| 维度 | V13 | V14 |
|------|-----|-----|
| 生成方式 | 单agent生成 | 多agent并行生成 |
| 内容深度 | 6个维度 | 保留V8的6个维度 |
| JSON格式 | V8 JSON | V8 JSON（兼容） |

### 3. 页面类型系统

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

### 4. V8 JSON格式（兼容）

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

### 5. 设计规范

#### 5.1 分辨率
- 固定舞台：1920x1080
- 缩放方式：transform: scale() 适配不同屏幕

#### 5.2 配色系统
- 保留V13的gold/acid/warm主题
- 新增：每本书独立设计风格

#### 5.3 字体
- 中文：Noto Serif SC
- 英文：Inter / JetBrains Mono
- 特殊：Ma Shan Zheng（毛笔字体）

#### 5.4 页面布局
- Cover：居中对齐
- Expert grid：2x4网格
- Stances：每页3个专家
- Clash：左右对比
- 其他：居中对齐

### 6. 执行流程

```
1. 生成V8 JSON内容（多agent并行）
   - 每轮6个维度：立场、交锋、案例、成本、人性、认知升级
   - 每个专家深度发言（不限字数，重质量）

2. 手工设计HTML（基于V13的页面类型）
   - 每本书独立设计风格
   - 基于1920x1080分辨率
   - 使用CSS变量管理配色

3. 整合JSON和HTML
   - 基于V8 JSON生成HTML
   - 手工设计样式（不是模板化）
```

## 升级计划

### Phase 1：定义V14规范
- [x] 调研V13架构
- [x] 定义V14升级点
- [x] 写升级规范文档

### Phase 2：生成V8 JSON内容
- [ ] 用子代理并行生成《真需求》的V8 JSON
- [ ] 每轮6个维度
- [ ] 验证内容质量

### Phase 3：手工设计HTML
- [ ] 基于V13的页面类型
- [ ] 手工设计样式
- [ ] 基于1920x1080分辨率

### Phase 4：整合和测试
- [ ] 整合JSON和HTML
- [ ] 测试不同分辨率
- [ ] 验收

## 成功标准

1. **内容深度**：每轮6个维度，每个专家深度发言
2. **HTML设计**：手工设计，非模板化
3. **分辨率**：1920x1080 固定舞台
4. **页面类型**：保留V13的11种页面类型
5. **兼容性**：V8 JSON格式兼容

---

*定义时间：2026-06-23*
*基于V13.11升级*
