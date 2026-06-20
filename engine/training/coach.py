# -*- coding: utf-8 -*-
"""
Coach Agent — 训练闭环中的监督审阅模块（V1.0）

在 Step4（评分+提取）和 Step5（融合升级）之间插入审阅环节。
Coach Agent 审阅辩论质量，给出结构化反馈，决定哪些升级值得执行。

设计原则（Karpathy Guidelines）：
  - Agent=LLM 负责审阅和判断
  - Python=机械操作 负责验证、过滤、预算控制
  - 不依赖外部LLM API

数据流：
  debate_json + extraction + expert_profiles
       ↓
  Coach Agent 审阅 → CoachReview (结构化JSON)
       ↓
  validate_coach_review() → 过滤低信心 + 预算控制
       ↓
  gate_upgrade() → 门控验证
       ↓
  FusionEngine.upgrade_expert() → 实际升级
"""

import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict


# ═══════════════════════════════════════════════════════════════
#  Coach Review Schema
# ═══════════════════════════════════════════════════════════════

COACH_REVIEW_SCHEMA = {
    "description": "Coach Agent 对辩论的结构化审阅",
    "fields": {
        "debate_quality": "float 0-100, 整体质量评分",
        "dimensions": {
            "depth": "float 0-100, 认知深度（是否触及本质）",
            "collision": "float 0-100, 碰撞质量（是否有真正的思想交锋）",
            "evidence": "float 0-100, 证据密度（引用、案例、数据）",
            "personality": "float 0-100, 人格一致性（是否像这个人会说的话）",
            "novelty": "float 0-100, 新颖性（是否有让人意外的洞见）",
        },
        "expert_critiques": {
            "type": "list[dict]",
            "fields": {
                "expert": "专家名",
                "stayed_in_character": "bool, 是否保持人设",
                "used_own_knowledge": "bool, 是否用了自己的知识体系",
                "depth_adequate": "bool, 论证是否足够深入",
                "strongest_moment": "str, 本场最精彩的一句话或论点",
                "weakest_moment": "str, 本场最薄弱的一句话或论点",
                "specific_improvements": "list[str], 具体改进建议（最多3条）",
            },
        },
        "upgrade_recommendations": {
            "type": "list[dict]",
            "description": "具体升级提案，将传递给 FusionEngine",
            "fields": {
                "expert": "专家名",
                "action": "MERGE / ENHANCE / BRANCH / FUSE",
                "target": "str, 具体要升级什么（如 '攻击模式:逻辑漏洞'）",
                "what_to_add": "str, 要添加什么",
                "what_to_remove": "str, 要删除/替换什么（可为空）",
                "reason": "str, 为什么这个升级有效（必须引用辩论中的具体证据）",
                "confidence": "float 0-1, 对这个升级的信心",
                "priority": "high / medium / low",
            },
        },
        "meta_observations": "list[str], 跨专家的元观察",
        "what_worked": "list[str], 本轮有效的策略/模式",
        "what_failed": "list[str], 本轮失败的策略/模式",
        "coach_notes": "str, Coach的总体评语（1-2句话）",
    },
}

COACH_REVIEW_PROMPT = """
## Coach 审阅指令

你是一个训练教练，审阅两位专家的辩论，给出结构化反馈。

### 审阅维度：

1. **认知深度**（depth）：是否触及问题本质，还是停留在表面？
2. **碰撞质量**（collision）：是否有真正的思想交锋，还是各说各话？
3. **证据密度**（evidence）：是否有具体的引用、案例、数据支撑？
4. **人格一致性**（personality）：专家是否像他本人会说的话？
5. **新颖性**（novelty）：是否有让人意外的洞见或角度？

### 对每位专家的审阅：

- 是否保持了人设？（时代、知识体系、说话风格）
- 是否用了自己的知识体系？（没借用其他专家的核心概念）
- 论证是否足够深入？（有没有浅尝辄止）
- 最强时刻：本场最精彩的一句话或论点
- 最弱时刻：本场最薄弱的一句话或论点
- 具体改进建议（最多3条，必须可执行）

### 升级建议：

基于辩论中的具体证据，提出升级建议。每条建议必须：
- 引用辩论中的具体段落或论点
- 说明为什么这个升级会让专家更强
- 给出信心分数（0-1）和优先级

### 输出格式：

```json
{
  "debate_quality": 72,
  "dimensions": {
    "depth": 75,
    "collision": 68,
    "evidence": 70,
    "personality": 80,
    "novelty": 65
  },
  "expert_critiques": [
    {
      "expert": "专家名",
      "stayed_in_character": true,
      "used_own_knowledge": true,
      "depth_adequate": false,
      "strongest_moment": "具体引用辩论中的一句话",
      "weakest_moment": "具体引用辩论中薄弱的一句",
      "specific_improvements": [
        "改进建议1（可执行）",
        "改进建议2（可执行）"
      ]
    }
  ],
  "upgrade_recommendations": [
    {
      "expert": "专家名",
      "action": "ENHANCE",
      "target": "防御模式:数据质疑",
      "what_to_add": "用XX案例增强数据质疑的说服力",
      "what_to_remove": "",
      "reason": "辩论中第2轮被对手用数据击穿，需要增强数据反驳能力",
      "confidence": 0.8,
      "priority": "high"
    }
  ],
  "meta_observations": ["观察1", "观察2"],
  "what_worked": ["有效策略1"],
  "what_failed": ["失败策略1"],
  "coach_notes": "总体评语"
}
```
"""

# ═══════════════════════════════════════════════════════════════
#  Python 端：验证和过滤 Coach Review
# ═══════════════════════════════════════════════════════════════

COACH_EDIT_BUDGET = 3       # 每轮最多应用 3 条升级
COACH_MIN_CONFIDENCE = 0.5  # 最低信心阈值


@dataclass
class ExpertCritique:
    """对单个专家的审阅"""
    expert: str
    stayed_in_character: bool = True
    used_own_knowledge: bool = True
    depth_adequate: bool = True
    strongest_moment: str = ""
    weakest_moment: str = ""
    specific_improvements: List[str] = field(default_factory=list)


@dataclass
class UpgradeRecommendation:
    """一条升级建议"""
    expert: str
    action: str = "ENHANCE"  # MERGE / ENHANCE / BRANCH / FUSE
    target: str = ""
    what_to_add: str = ""
    what_to_remove: str = ""
    reason: str = ""
    confidence: float = 0.5
    priority: str = "medium"


@dataclass
class CoachReview:
    """Coach 的完整审阅结果"""
    debate_quality: float = 50.0
    dimensions: Dict[str, float] = field(default_factory=lambda: {
        "depth": 50, "collision": 50, "evidence": 50,
        "personality": 50, "novelty": 50,
    })
    expert_critiques: List[ExpertCritique] = field(default_factory=list)
    upgrade_recommendations: List[UpgradeRecommendation] = field(default_factory=list)
    meta_observations: List[str] = field(default_factory=list)
    what_worked: List[str] = field(default_factory=list)
    what_failed: List[str] = field(default_factory=list)
    coach_notes: str = ""


def validate_coach_review(data: Dict) -> CoachReview:
    """验证 Coach Review JSON，过滤低信心升级，应用预算控制

    这是 Python 端的机械操作，不涉及 LLM 调用。
    """
    # 1. 基础字段校验
    debate_quality = float(data.get("debate_quality", 50))
    debate_quality = max(0, min(100, debate_quality))

    dimensions = data.get("dimensions", {})
    for key in ["depth", "collision", "evidence", "personality", "novelty"]:
        if key in dimensions:
            dimensions[key] = max(0, min(100, float(dimensions[key])))
        else:
            dimensions[key] = 50

    # 2. 解析 expert_critiques
    critiques = []
    for c in data.get("expert_critiques", []):
        critiques.append(ExpertCritique(
            expert=c.get("expert", "未知"),
            stayed_in_character=c.get("stayed_in_character", True),
            used_own_knowledge=c.get("used_own_knowledge", True),
            depth_adequate=c.get("depth_adequate", True),
            strongest_moment=c.get("strongest_moment", ""),
            weakest_moment=c.get("weakest_moment", ""),
            specific_improvements=c.get("specific_improvements", [])[:3],
        ))

    # 3. 解析 upgrade_recommendations + 过滤
    upgrades = []
    for u in data.get("upgrade_recommendations", []):
        conf = float(u.get("confidence", 0))
        if conf < COACH_MIN_CONFIDENCE:
            continue  # 过滤低信心
        upgrades.append(UpgradeRecommendation(
            expert=u.get("expert", "未知"),
            action=u.get("action", "ENHANCE"),
            target=u.get("target", ""),
            what_to_add=u.get("what_to_add", ""),
            what_to_remove=u.get("what_to_remove", ""),
            reason=u.get("reason", ""),
            confidence=conf,
            priority=u.get("priority", "medium"),
        ))

    # 4. 按 priority 排序
    priority_order = {"high": 0, "medium": 1, "low": 2}
    upgrades.sort(key=lambda u: priority_order.get(u.priority, 2))

    # 5. 应用 Edit Budget
    upgrades = upgrades[:COACH_EDIT_BUDGET]

    return CoachReview(
        debate_quality=debate_quality,
        dimensions=dimensions,
        expert_critiques=critiques,
        upgrade_recommendations=upgrades,
        meta_observations=data.get("meta_observations", []),
        what_worked=data.get("what_worked", []),
        what_failed=data.get("what_failed", []),
        coach_notes=data.get("coach_notes", ""),
    )


def load_coach_review(path: str) -> Optional[CoachReview]:
    """从 JSON 文件加载 Coach Review"""
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return validate_coach_review(data)
    except (json.JSONDecodeError, IOError):
        return None


def coach_review_to_dict(review: CoachReview) -> Dict:
    """CoachReview → Dict（用于序列化和传递给 FusionEngine）"""
    return {
        "debate_quality": review.debate_quality,
        "dimensions": review.dimensions,
        "expert_critiques": [
            {
                "expert": c.expert,
                "stayed_in_character": c.stayed_in_character,
                "used_own_knowledge": c.used_own_knowledge,
                "depth_adequate": c.depth_adequate,
                "strongest_moment": c.strongest_moment,
                "weakest_moment": c.weakest_moment,
                "specific_improvements": c.specific_improvements,
            }
            for c in review.expert_critiques
        ],
        "upgrade_recommendations": [
            {
                "expert": u.expert,
                "action": u.action,
                "target": u.target,
                "what_to_add": u.what_to_add,
                "what_to_remove": u.what_to_remove,
                "reason": u.reason,
                "confidence": u.confidence,
                "priority": u.priority,
            }
            for u in review.upgrade_recommendations
        ],
        "meta_observations": review.meta_observations,
        "what_worked": review.what_worked,
        "what_failed": review.what_failed,
        "coach_notes": review.coach_notes,
    }


def extract_strategies_from_coach_review(review: CoachReview) -> Dict[str, Dict]:
    """从 Coach Review 中提取每位专家的升级策略

    将 Coach 的 upgrade_recommendations 转换为 FusionEngine 能理解的格式。
    """
    expert_strategies = {}

    for rec in review.upgrade_recommendations:
        name = rec.expert
        if name not in expert_strategies:
            expert_strategies[name] = {
                "attack_strategy": {},
                "defense_weakness": {},
                "style_fingerprint": {},
                "evidence_preference": {},
                "interaction_pattern": {},
            }

        # 根据 action 类型分发到不同策略字段
        if rec.action in ("MERGE", "BRANCH"):
            # 攻击策略升级
            expert_strategies[name]["attack_strategy"][rec.target] = {
                "type": rec.action,
                "description": rec.what_to_add,
                "source": "coach_review",
                "confidence": rec.confidence,
            }
        elif rec.action == "ENHANCE":
            # 防御策略增强
            expert_strategies[name]["defense_weakness"][rec.target] = {
                "type": "ENHANCE",
                "description": rec.what_to_add,
                "source": "coach_review",
                "confidence": rec.confidence,
            }
        elif rec.action == "FUSE":
            # 风格/素材融合
            expert_strategies[name]["style_fingerprint"][rec.target] = {
                "type": "FUSE",
                "description": rec.what_to_add,
                "remove": rec.what_to_remove,
                "source": "coach_review",
                "confidence": rec.confidence,
            }

    return expert_strategies


# ═══════════════════════════════════════════════════════════════
#  CLI 测试
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # 测试：验证一个 Coach Review
    test_review = {
        "debate_quality": 72,
        "dimensions": {
            "depth": 75, "collision": 68, "evidence": 70,
            "personality": 80, "novelty": 65,
        },
        "expert_critiques": [
            {
                "expert": "老子",
                "stayed_in_character": True,
                "used_own_knowledge": True,
                "depth_adequate": False,
                "strongest_moment": "上善若水，水善利万物而不争",
                "weakest_moment": "对算法的论述超出了时代知识",
                "specific_improvements": ["用'术'替代'算法'", "增加更多自然比喻"],
            }
        ],
        "upgrade_recommendations": [
            {
                "expert": "老子",
                "action": "ENHANCE",
                "target": "防御模式:数据质疑",
                "what_to_add": "用'水无常形'来回应数据质疑",
                "what_to_remove": "",
                "reason": "辩论中被对手用数据击穿，需要用道家概念回应",
                "confidence": 0.8,
                "priority": "high",
            },
            {
                "expert": "老子",
                "action": "BRANCH",
                "target": "攻击模式:反者道之动",
                "what_to_add": "用'反者道之动'来攻击线性增长论",
                "what_to_remove": "",
                "reason": "辩论中展示了这个攻击角度的威力",
                "confidence": 0.7,
                "priority": "medium",
            },
        ],
        "meta_observations": ["两位专家的知识体系差异很大，碰撞有火花"],
        "what_worked": ["老子的水之比喻很有说服力"],
        "what_failed": ["数据论证环节薄弱"],
        "coach_notes": "整体不错，但老子在数据环节需要加强",
    }

    review = validate_coach_review(test_review)
    print(f"debate_quality: {review.debate_quality}")
    print(f"dimensions: {review.dimensions}")
    print(f"expert_critiques: {len(review.expert_critiques)}")
    print(f"upgrade_recommendations (after filter+ budget): {len(review.upgrade_recommendations)}")
    for u in review.upgrade_recommendations:
        print(f"  [{u.priority}] {u.expert}: {u.action} {u.target} (conf={u.confidence})")

    strategies = extract_strategies_from_coach_review(review)
    print(f"\nextracted strategies: {json.dumps(strategies, ensure_ascii=False, indent=2)}")
