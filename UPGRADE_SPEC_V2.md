# 圆桌会议系统升级 Spec v2.0

> **Karpathy Guidelines**: 先想再写，最小改动，目标驱动

---

## 一、项目现状

### 1.1 核心数据
- 专家总数：32位
- 训练次数：1,480+次
- 知识边界覆盖：4/32（12.5%）
- HTML-PPT版本：v12/v13/showoff 并存

### 1.2 已完成升级
- ✅ 知识边界检查器（`engine/knowledge_boundary_checker.py`）
- ✅ 集成模块（`engine/knowledge_boundary_integration.py`）
- ✅ 升级版Prompt（`engine/prompts/expert_speak_v2.py`）
- ✅ 4位核心专家知识边界（芒格、老子、孔子、尼采）

### 1.3 待解决问题
| 问题 | 根因 | 影响 |
|:---|:---|:---|
| 专家乱引用理论 | 知识边界未全覆盖 | 28/32专家无约束 |
| 内容深度不够 | Prompt未要求Bloom 5-6 | 发言停留在Level 2-3 |
| 金句密度低 | 无金句提取机制 | 传播力弱 |
| 反驳质量低 | 无交锋约束 | "为了反驳而反驳" |

---

## 二、设计原则

### 2.1 Karpathy Guidelines应用

**Think Before Coding:**
- 诊断根因，不是症状
- 明确假设：核心问题是"专家灵魂"，不是"功能数量"

**Simplicity First:**
- 知识边界用"禁用词列表"（简单），不用"语义分析"（复杂）
- Prompt升级用"约束注入"（简单），不用"重构架构"（复杂）

**Surgical Changes:**
- 只改专家系统，不改渲染引擎
- 新增文件，不修改现有文件

**Goal-Driven:**
- 每个Phase有明确的验证标准
- 可量化、可测试、可回滚

### 2.2 灵魂三要素

```
专家的灵魂 = 时代 × 知识 × 性格
```

| 要素 | 定义 | 约束 |
|:---|:---|:---|
| **时代** | 他活在什么时候 | 不说超出时代的话 |
| **知识** | 他知道什么 | 不说不懂的东西 |
| **性格** | 他怎么说话 | 保持一致的表达风格 |

---

## 三、升级方案

### Phase 1：知识边界全覆盖

**目标：** 32位专家全部有知识边界定义

**范围：**
| 领域 | 专家数 | 已完成 | 待完成 |
|:---|:---:|:---:|:---:|
| 经济 | 10 | 1 | 9 |
| 哲学 | 15 | 3 | 12 |
| 心理 | 5 | 0 | 5 |
| 科技 | 4 | 0 | 4 |
| 文学 | 8 | 0 | 8 |

**方法：**
1. 参考已有4位专家的模板
2. 每位专家定义：时代背景、知识图谱、禁用词、比喻来源
3. 生成 `_知识边界.md` 文件

**验证标准：**
- [ ] 32位专家全部有 `_知识边界.md`
- [ ] 每个文件包含：时代背景、知识图谱、禁用词、比喻来源
- [ ] 知识边界检查器能正确读取

**文件清单：**
```
expert-library/experts/
├── economics/
│   ├── 芒格_知识边界.md ✅
│   ├── 巴菲特_知识边界.md
│   ├── 塔勒布_知识边界.md
│   ├── 达利欧_知识边界.md
│   ├── 刘润_知识边界.md
│   ├── 吴军_知识边界.md
│   ├── 吴晓波_知识边界.md
│   ├── 柯林斯_知识边界.md
│   └── ...
├── philosophy/
│   ├── 老子_知识边界.md ✅
│   ├── 孔子_知识边界.md ✅
│   ├── 尼采_知识边界.md ✅
│   ├── 韩非子_知识边界.md
│   ├── 阿伦特_知识边界.md
│   ├── 波伏娃_知识边界.md
│   └── ...
├── psychology/
│   ├── 卡尼曼_知识边界.md
│   ├── 弗洛伊德_知识边界.md
│   ├── 弗洛姆_知识边界.md
│   └── ...
├── literature/
│   ├── 项飙_知识边界.md
│   ├── 李诞_知识边界.md
│   ├── 冯唐_知识边界.md
│   └── ...
└── technology/
    ├── 凯文凯利_知识边界.md
    ├── 赫拉利_知识边界.md
    └── ...
```

---

### Phase 2：Prompt升级（深度提升）

**目标：** 发言达到Bloom Level 5-6

**当前Prompt问题：**
```python
# 当前（Level 2-3）
prompt = f"请以{expert}的身份，就{topic}发表看法"
```

**升级Prompt：**
```python
# 升级后（Level 5-6）
prompt = f"""
你是{expert}，{era}的{identity}。

知识体系：{core_knowledge}
禁用词：{forbidden_words}

话题：{topic}

要求（Bloom Level 5-6）：
1. 用一个"反直觉"的观察开场（不要用"我认为"、"我觉得"）
2. 用你最擅长的思维模型分析（只用你知识体系内的概念）
3. 给出一个"可截图传播"的金句（不超过30字）
4. 最后抛出一个"让对手难以回答"的问题

禁止：
- 不说禁用词：{forbidden_words}
- 不引用其他专家的核心概念
- 不为了反驳而反驳
- 不说"以上就是我的观点"
"""
```

**验证标准：**
- [ ] 每个发言有"反直觉"开场
- [ ] 每个发言有"判断性结论"
- [ ] 每个发言有"可截图金句"
- [ ] 知识边界检查通过率 > 95%

---

### Phase 3：金句页视觉升级

**目标：** 金句有专门的视觉设计

**新增CSS模板：**
```css
/* 金句页：一页只展示一句话 */
.quote-page {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  min-height: 100vh;
  padding: 48px;
}

.quote-text {
  font-size: clamp(36px, 5vw, 72px);
  font-weight: 900;
  line-height: 1.2;
  max-width: 80%;
  font-family: var(--serif);
  position: relative;
}

.quote-text::before {
  content: """;
  font-size: 120px;
  color: var(--accent);
  opacity: 0.3;
  position: absolute;
  left: -40px;
  top: -20px;
}

.quote-author {
  font-size: 18px;
  color: var(--muted);
  margin-top: 24px;
  font-family: var(--mono);
  letter-spacing: 0.1em;
}

.quote-context {
  font-size: 14px;
  color: var(--muted);
  margin-top: 8px;
  max-width: 600px;
}
```

**验证标准：**
- [ ] 金句页有专门的视觉设计
- [ ] 金句字体 > 36px
- [ ] 有引用符号装饰
- [ ] 有作者署名

---

### Phase 4：交锋约束机制

**目标：** 反驳基于自己的知识体系

**当前问题：**
```
❌ 老子反驳芒格："你的多元思维模型就像量子力学..."
   → 老子不知道量子力学，也不知道多元思维模型
```

**解决方案：**
```python
def validate_attack(attacker, target, attack_content):
    """
    验证攻击是否合理
    """
    # 1. 检查攻击者是否使用了自己的知识体系
    attacker_boundary = get_boundary(attacker)
    if not attacker_boundary:
        return True, "无边界定义"
    
    # 2. 检查是否使用了禁用词
    forbidden = check_forbidden_words(attack_content, attacker)
    if forbidden:
        return False, f"使用了禁用词: {forbidden}"
    
    # 3. 检查是否引用了其他专家的核心概念
    other_concepts = check_other_expert_concepts(attack_content, attacker)
    if other_concepts:
        return False, f"引用了其他专家概念: {other_concepts}"
    
    return True, "攻击合理"
```

**验证标准：**
- [ ] 攻击不使用禁用词
- [ ] 攻击不引用其他专家核心概念
- [ ] 攻击基于自己的知识体系
- [ ] 交锋约束检查通过率 > 90%

---

## 四、实施计划

### 4.1 Phase 1：知识边界全覆盖（3天）

**Day 1：经济+哲学领域**
- 经济：巴菲特、塔勒布、达利欧、刘润、吴军、吴晓波、柯林斯
- 哲学：韩非子、阿伦特、波伏娃、苏格拉底、柏拉图

**Day 2：心理+科技领域**
- 心理：卡尼曼、弗洛伊德、弗洛姆、津巴多、戈尔曼
- 科技：凯文凯利、赫拉利、博斯特罗姆、阿西莫夫

**Day 3：文学+验证**
- 文学：项飙、李诞、冯唐、吴晓波、万维钢、许知远、罗翔、丁元英
- 验证：运行测试，确保32位专家全覆盖

**产出：**
- 28个 `_知识边界.md` 文件
- 更新 `knowledge_boundary_checker.py` 添加新专家

### 4.2 Phase 2：Prompt升级（2天）

**Day 1：升级Prompt模板**
- 修改 `engine/prompts/expert_speak_v2.py`
- 添加Bloom Level 5-6要求
- 添加金句提取要求

**Day 2：集成到训练流程**
- 修改 `engine/auto_train.py`
- 添加知识边界验证
- 测试验证

**产出：**
- 升级版Prompt模板
- 集成代码
- 测试用例

### 4.3 Phase 3：金句页视觉（1天）

**任务：**
- 添加金句页CSS模板
- 修改 `engine/html_ppt_v13_renderer.py`
- 测试渲染效果

**产出：**
- 金句页CSS模板
- 渲染代码更新
- 示例HTML

### 4.4 Phase 4：交锋约束（2天）

**Day 1：实现交锋验证**
- 添加 `validate_attack()` 函数
- 集成到辩论流程

**Day 2：测试验证**
- 编写测试用例
- 验证交锋质量

**产出：**
- 交锋验证代码
- 测试用例

---

## 五、成功标准

### 5.1 量化指标

| 指标 | 当前 | 目标 | 验证方法 |
|:---|:---:|:---:|:---|
| 知识边界覆盖 | 4/32 | 32/32 | 文件计数 |
| 禁用词检查通过率 | 未知 | >95% | 自动化测试 |
| 金句密度 | 低 | 每200字1句 | 人工审核 |
| Bloom Level | 2-3 | 5-6 | 人工审核 |
| 交锋约束通过率 | 未知 | >90% | 自动化测试 |

### 5.2 质量指标

| 指标 | 验证方法 |
|:---|:---|
| 专家不乱引用 | 知识边界检查通过 |
| 金句可截图 | 人工审核 |
| 反驳有深度 | 人工审核 |
| 视觉有吸引力 | 人工审核 |

---

## 六、风险与缓解

| 风险 | 影响 | 缓解措施 |
|:---|:---|:---|
| 知识边界定义太严 | 专家发言受限 | 允许"类比扩展" |
| 工作量太大 | 进度延迟 | 优先处理核心专家 |
| Prompt升级效果不明显 | 深度未提升 | 迭代优化Prompt |
| 交锋约束太严 | 辩论不精彩 | 调整约束参数 |

---

## 七、Karpathy Guidelines检查清单

- [x] **Think Before Coding**: 诊断了4个根因
- [x] **Simplicity First**: 用禁用词列表，不用语义分析
- [x] **Surgical Changes**: 只改专家系统，不改渲染引擎
- [x] **Goal-Driven**: 每个Phase有明确验证标准

---

## 八、下一步行动

1. **立即开始 Phase 1**：批量生成28位专家知识边界
2. **并行准备 Phase 2**：设计升级版Prompt模板
3. **Phase 1完成后**：运行测试验证
4. **Phase 2完成后**：集成到训练流程
5. **全部完成后**：提交GitHub

---

*文档版本: v2.0*
*创建时间: 2026-06-20*
*遵循原则: Karpathy Guidelines*
*上次更新: 知识边界系统集成完成*
