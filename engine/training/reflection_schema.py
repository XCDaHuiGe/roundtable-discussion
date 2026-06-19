# -*- coding: utf-8 -*-
"""
反思模板 — Agent 辩论后的结构化反思输出

Agent 辩论完成后，生成一个 reflection.json，Python 用它指导升级。
这实现了 SkillOpt 的 "Reflect" 步骤，但由 Agent（LLM）执行，不调用外部 API。

用法：
  Agent 辩论后，按以下格式输出 JSON，保存到 memory/reflection_round{N}.json
  Python 端调用 load_reflection() 加载，然后用 gate_upgrade() 做门控验证。
"""

import json
import os
from typing import Dict, List, Optional


# ═══════════════════════════════════════════════════════════════
#  反思 JSON Schema（Agent 需要填充的结构）
# ═══════════════════════════════════════════════════════════════

REFLECTION_SCHEMA = {
    "description": "Agent 辩论后的结构化反思",
    "fields": {
        "debate_quality": {
            "type": "float (0-100)",
            "description": "本轮辩论的整体质量评分",
        },
        "dimensions": {
            "type": "dict",
            "description": "6维度评分（与 scorer.py 对齐）",
            "fields": {
                "reality_grounding": "float 0-100, 现实依据",
                "contradiction_handling": "float 0-100, 矛盾处理",
                "strategic_depth": "float 0-100, 策略深度",
                "cross_domain_transfer": "float 0-100, 跨域迁移",
                "novelty": "float 0-100, 新颖性",
                "personality_consistency": "float 0-100, 人格一致性",
            },
        },
        "expert_upgrades": {
            "type": "list[dict]",
            "description": "具体升级提案（每条是一个 Edit Patch）",
            "fields": {
                "expert": "专家名",
                "target_layer": "'strategy' 或 'material'",
                "action": "'MERGE' / 'ENHANCE' / 'BRANCH' / 'FUSE'",
                "what_to_add": "要添加什么",
                "what_to_remove": "要删除什么（可为空）",
                "reason": "为什么这个升级有效",
                "priority": "'high' / 'medium' / 'low'",
                "confidence": "float 0-1, 对这个升级的信心",
            },
        },
        "meta_observations": {
            "type": "list[str]",
            "description": "跨专家的元观察（如：专家间缺乏真正交锋）",
        },
        "what_worked": {
            "type": "list[str]",
            "description": "本轮辩论中有效的策略/模式",
        },
        "what_failed": {
            "type": "list[str]",
            "description": "本轮辩论中失败的策略/模式",
        },
    },
}


# ═══════════════════════════════════════════════════════════════
#  Agent 反思指令模板
# ═══════════════════════════════════════════════════════════════

REFLECTION_PROMPT = """
## 反思指令

辩论结束后，你需要生成一个结构化反思 JSON。这不是给读者看的内容，而是给训练系统用的。

### 你需要回答的问题：

1. **辩论质量**：这场辩论的质量如何？（0-100）
2. **6维度评分**：每个维度的具体分数是多少？
3. **专家升级**：每位专家需要做什么具体改进？
4. **元观察**：有什么跨专家的问题？
5. **成败分析**：什么策略有效？什么策略失败了？

### 输出格式：

```json
{
  "debate_quality": 75,
  "dimensions": {
    "reality_grounding": 70,
    "contradiction_handling": 65,
    "strategic_depth": 80,
    "cross_domain_transfer": 60,
    "novelty": 75,
    "personality_consistency": 85
  },
  "expert_upgrades": [
    {
      "expert": "专家名",
      "target_layer": "strategy",
      "action": "MERGE",
      "what_to_add": "具体要添加的能力/模式",
      "what_to_remove": "具体要删除的弱项（可为空）",
      "reason": "为什么这个升级有效，引用辩论中的具体证据",
      "priority": "high",
      "confidence": 0.8
    }
  ],
  "meta_observations": [
    "观察1：...",
    "观察2：..."
  ],
  "what_worked": [
    "有效的策略1",
    "有效的策略2"
  ],
  "what_failed": [
    "失败的策略1",
    "失败的策略2"
  ]
}
```

### 重要规则：

1. **confidence 决定是否应用**：confidence < 0.5 的升级不会被应用
2. **priority 决定应用顺序**：high > medium > low
3. **reason 必须引用具体证据**：不能泛泛而谈
4. **每轮最多 3 条升级**（Edit Budget）：选择最有效的 3 条
5. **不要为了升级而升级**：如果辩论质量已经很高，可以没有升级提案
"""


# ═══════════════════════════════════════════════════════════════
#  Python 端：加载和验证反思
# ═══════════════════════════════════════════════════════════════

EDIT_BUDGET = 3  # 每轮最多应用 3 条升级
MIN_CONFIDENCE = 0.5  # 最低信心阈值


def load_reflection(reflection_path: str) -> Optional[Dict]:
    """加载 Agent 的反思 JSON"""
    if not os.path.exists(reflection_path):
        return None
    try:
        with open(reflection_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return validate_reflection(data)
    except (json.JSONDecodeError, IOError):
        return None


def validate_reflection(data: Dict) -> Dict:
    """验证反思 JSON 的完整性"""
    # 确保必要字段存在
    if "debate_quality" not in data:
        data["debate_quality"] = 50.0
    if "dimensions" not in data:
        from scorer import default_scores
        data["dimensions"] = default_scores()
    if "expert_upgrades" not in data:
        data["expert_upgrades"] = []
    if "meta_observations" not in data:
        data["meta_observations"] = []
    if "what_worked" not in data:
        data["what_worked"] = []
    if "what_failed" not in data:
        data["what_failed"] = []

    # 过滤低信心升级
    data["expert_upgrades"] = [
        u for u in data["expert_upgrades"]
        if u.get("confidence", 0) >= MIN_CONFIDENCE
    ]

    # 按 priority 排序
    priority_order = {"high": 0, "medium": 1, "low": 2}
    data["expert_upgrades"].sort(
        key=lambda u: priority_order.get(u.get("priority", "low"), 2)
    )

    # 应用 Edit Budget
    data["expert_upgrades"] = data["expert_upgrades"][:EDIT_BUDGET]

    return data


def gate_upgrade(
    reflection: Dict,
    history_path: str = None,
) -> Dict:
    """
    门控验证：只有分数提升才允许升级

    SkillOpt 的核心机制：Validation Gate
    - 对比本轮分数与历史平均分
    - 只有高于历史平均才允许升级
    - 否则回退

    Returns:
        {
            "passed": bool,
            "reason": str,
            "current_score": float,
            "historical_avg": float,
            "delta": float,
            "allowed_upgrades": list,
        }
    """
    current_score = reflection.get("debate_quality", 0)
    allowed_upgrades = reflection.get("expert_upgrades", [])

    # 加载历史分数
    historical_scores = _load_historical_scores(history_path)
    historical_avg = (
        sum(historical_scores) / len(historical_scores)
        if historical_scores else 0
    )

    # 门控逻辑
    if not historical_scores:
        # 第一次训练，无历史，直接通过
        return {
            "passed": True,
            "reason": "首次训练，无历史对比",
            "current_score": current_score,
            "historical_avg": 0,
            "delta": current_score,
            "allowed_upgrades": allowed_upgrades,
        }

    delta = current_score - historical_avg

    if delta > 0:
        return {
            "passed": True,
            "reason": f"分数提升 +{delta:.1f}，允许升级",
            "current_score": current_score,
            "historical_avg": historical_avg,
            "delta": delta,
            "allowed_upgrades": allowed_upgrades,
        }
    else:
        return {
            "passed": False,
            "reason": f"分数下降 {delta:.1f}，拒绝升级（保留当前策略）",
            "current_score": current_score,
            "historical_avg": historical_avg,
            "delta": delta,
            "allowed_upgrades": [],  # 清空，不允许任何升级
        }


def _load_historical_scores(history_path: str = None) -> List[float]:
    """加载历史训练分数"""
    if not history_path:
        # 默认路径
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        history_path = os.path.join(base_dir, "..", "memory", "training_history.json")

    if not os.path.exists(history_path):
        return []

    try:
        with open(history_path, "r", encoding="utf-8") as f:
            history = json.load(f)
        if isinstance(history, list):
            return [h.get("score", 0) for h in history if "score" in h]
        return []
    except (json.JSONDecodeError, IOError):
        return []


def save_to_history(score: float, reflection: Dict, history_path: str = None):
    """保存本轮分数到历史记录"""
    if not history_path:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        history_path = os.path.join(base_dir, "..", "memory", "training_history.json")

    os.makedirs(os.path.dirname(history_path), exist_ok=True)

    history = []
    if os.path.exists(history_path):
        try:
            with open(history_path, "r", encoding="utf-8") as f:
                history = json.load(f)
        except (json.JSONDecodeError, IOError):
            history = []

    from datetime import datetime
    history.append({
        "score": score,
        "dimensions": reflection.get("dimensions", {}),
        "upgrades_applied": len(reflection.get("expert_upgrades", [])),
        "meta_observations": reflection.get("meta_observations", []),
        "timestamp": datetime.now().isoformat(),
    })

    # 保留最近 50 条
    history = history[-50:]

    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════════
#  Snapshot / Rollback
# ═══════════════════════════════════════════════════════════════

def snapshot_expert(expert_md_path: str) -> str:
    """保存专家档案快照（升级前调用）"""
    if not os.path.exists(expert_md_path):
        return ""

    snapshot_dir = os.path.join(os.path.dirname(expert_md_path), ".snapshots")
    os.makedirs(snapshot_dir, exist_ok=True)

    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    expert_name = os.path.splitext(os.path.basename(expert_md_path))[0]
    snapshot_path = os.path.join(snapshot_dir, f"{expert_name}_{timestamp}.md")

    with open(expert_md_path, "r", encoding="utf-8") as f:
        content = f.read()
    with open(snapshot_path, "w", encoding="utf-8") as f:
        f.write(content)

    return snapshot_path


def rollback_expert(expert_md_path: str, snapshot_path: str) -> bool:
    """回退专家档案到快照版本"""
    if not os.path.exists(snapshot_path):
        return False

    with open(snapshot_path, "r", encoding="utf-8") as f:
        content = f.read()
    with open(expert_md_path, "w", encoding="utf-8") as f:
        f.write(content)

    return True


def cleanup_snapshots(expert_md_path: str, keep_latest: int = 3):
    """清理旧快照，保留最近 N 个"""
    snapshot_dir = os.path.join(os.path.dirname(expert_md_path), ".snapshots")
    if not os.path.exists(snapshot_dir):
        return

    expert_name = os.path.splitext(os.path.basename(expert_md_path))[0]
    snapshots = sorted([
        f for f in os.listdir(snapshot_dir)
        if f.startswith(expert_name) and f.endswith(".md")
    ])

    # 删除多余的
    for old_snapshot in snapshots[:-keep_latest]:
        os.remove(os.path.join(snapshot_dir, old_snapshot))
