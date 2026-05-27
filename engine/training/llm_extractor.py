# -*- coding: utf-8 -*-
"""
AI驱动的策略提取器 V5.0

核心升级：
- 用LLM深度分析发言质量（替代启发式长度判断）
- 提取认知增量（观点改变观点的证据）
- 识别真正的修辞质量（而非关键词计数）
- 输出带置信度的策略数据
- 支持 async/await 异步调用

用法：
    from engine.training.llm_extractor import analyze_speech_quality, extract_strategies
    quality = await analyze_speech_quality(speech_content, expert_name)
    strategies = await extract_strategies(json_path, expert_name)
"""

import json
import os
import sys
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from llm_generate import call_llm_json


# ─── 数据模型 ──────────────────────────────────────────────

@dataclass
class SpeechQuality:
    """单条发言的质量评估结果"""
    depth_score: float = 0.0      # 认知深度 (0-10)
    logic_score: float = 0.0      # 逻辑严密性 (0-10)
    evidence_score: float = 0.0   # 证据质量 (0-10)
    style_score: float = 0.0      # 风格辨识度 (0-10)
    impact_score: float = 0.0     # 实际影响力 (0-10)
    overall: float = 0.0          # 综合得分 (0-10)
    confidence: float = 1.0       # AI评估置信度
    why: str = ""                 # 评分理由


@dataclass
class AttackStrategy:
    """攻击策略分析"""
    best_angle: str = ""          # 最佳攻击角度
    why_effective: str = ""       # 为什么有效
    applicable_when: str = ""     # 适用场景
    kill_rating: str = ""         # 杀伤力评级
    quality_score: float = 0.0    # 质量评分


@dataclass
class DefenseWeakness:
    """防御弱点分析"""
    broken_by: str = ""           # 被什么类型攻击打破
    why_vulnerable: str = ""      # 为什么脆弱
    fix_strategy: str = ""        # 修复策略
    success_rate: float = 0.0     # 当前成功率


@dataclass
class StyleFingerprint:
    """风格指纹分析"""
    most_authentic_line: str = "" # 最像本人的发言
    why_authentic: str = ""       # 为什么像
    weakest_line: str = ""        # 最不像的发言
    why_weak: str = ""            # 为什么不像


@dataclass
class EvidencePreference:
    """证据偏好分析"""
    most_effective_type: str = "" # 最有效的证据类型
    ranking: List[str] = field(default_factory=list)


@dataclass
class InteractionPattern:
    """交互模式分析"""
    best_opponent: str = ""       # 最擅长对抗的专家
    worst_opponent: str = ""      # 最不擅长对抗的专家


@dataclass
class ExpertStrategies:
    """一位专家的完整策略画像"""
    attack_strategy: AttackStrategy = field(default_factory=AttackStrategy)
    defense_weakness: DefenseWeakness = field(default_factory=DefenseWeakness)
    style_fingerprint: StyleFingerprint = field(default_factory=StyleFingerprint)
    evidence_preference: EvidencePreference = field(default_factory=EvidencePreference)
    interaction_pattern: InteractionPattern = field(default_factory=InteractionPattern)


# ─── 核心函数 ──────────────────────────────────────────────

async def analyze_speech_quality(
    speech_content: str,
    expert_name: str,
    context: str = ""
) -> SpeechQuality:
    """
    使用LLM分析单条发言的质量

    Args:
        speech_content: 发言内容
        expert_name: 专家名称（用于风格辨识度评估）
        context: 可选的上下文信息（话题、轮次等）

    Returns:
        SpeechQuality: 五维度质量评分
    """
    prompt = f"""你是一位资深的辩论质量评估专家。请对「{expert_name}」的以下发言进行严格的质量评分。

## 评分维度（每项0-10分）

1. **认知深度** (depth): 是否触及问题本质？是否有洞察？是否超越表面观点？
2. **逻辑严密性** (logic): 论证是否有逻辑链？前提→推理→结论是否完整？是否有逻辑谬误？
3. **证据质量** (evidence): 证据是否具体（有情节/数据/引用）？证据是否支撑论点？
4. **风格辨识度** (style): 是否像「{expert_name}」说的话？是否有个人化的表达？是否模板化？
5. **实际影响力** (impact): 这条发言是否推动了讨论？是否引发了他人的回应或改变？

## 发言内容

{context}

{speech_content[:800]}

## 输出格式（严格JSON）

```json
{{
  "depth_score": 7.5,
  "logic_score": 8.0,
  "evidence_score": 6.5,
  "style_score": 9.0,
  "impact_score": 7.0,
  "overall": 7.6,
  "confidence": 0.85,
  "why": "评分理由，100字以内"
}}
```

要求：
1. 评分必须基于内容质量，不是长度
2. 6分=普通水平，8分=优秀，9分+=卓越
3. 模板化、空洞的发言给低分（3-5分）
4. 有具体情节引用+独特视角的发言给高分（8-10分）
5. confidence表示你对评分的确信程度
"""

    result = call_llm_json(
        prompt,
        system=f"你是一位严格、客观的辩论质量评估专家。你只根据内容质量评分，不受发言长度影响。",
        max_tokens=1500,
        temperature=0.3,
    )

    if result.get("success") and result.get("data"):
        data = result["data"]
        return SpeechQuality(
            depth_score=float(data.get("depth_score", 5.0)),
            logic_score=float(data.get("logic_score", 5.0)),
            evidence_score=float(data.get("evidence_score", 5.0)),
            style_score=float(data.get("style_score", 5.0)),
            impact_score=float(data.get("impact_score", 5.0)),
            overall=float(data.get("overall", 5.0)),
            confidence=float(data.get("confidence", 0.5)),
            why=data.get("why", ""),
        )

    return _fallback_quality_score(speech_content)


def _fallback_quality_score(content: str) -> SpeechQuality:
    """LLM失败时的启发式评分"""
    import re

    depth = 5.0
    if re.search(r'本质上|核心|根本|关键在于|深层', content):
        depth += 2
    if len(content) > 200:
        depth += 1

    logic = 5.0
    logic_chain = content.count('因为') + content.count('所以') + content.count('如果')
    if logic_chain >= 2:
        logic += 2
    if re.search(r'但是|然而|问题是|矛盾', content):
        logic += 1

    evidence = 5.0
    if re.search(r'第.{1,3}章|情节|原文|书中|案例|数据', content):
        evidence += 2
    if re.search(r'\d+%|\d+万|\d+亿', content):
        evidence += 1

    style = 5.0
    if re.search(r'说白了|坦白说|老实说|你想想', content):
        style += 2
    if re.search(r'就像|好比|类似于', content):
        style += 1

    impact = 5.0
    if len(content) > 150:
        impact += 2

    overall = (depth + logic + evidence + style + impact) / 5

    return SpeechQuality(
        depth_score=round(depth, 1),
        logic_score=round(logic, 1),
        evidence_score=round(evidence, 1),
        style_score=round(style, 1),
        impact_score=round(impact, 1),
        overall=round(overall, 1),
        confidence=0.3,
        why='启发式评分（LLM调用失败）',
    )


async def extract_strategies(
    json_path: str,
    expert_name: str
) -> Dict:
    """
    从讨论JSON中提取某位专家的策略数据

    Args:
        json_path: 讨论JSON文件路径
        expert_name: 专家名称

    Returns:
        {
            "attack_strategy": {
                "best_angle": str,      # 最佳攻击角度
                "why_effective": str,   # 为什么有效
                "applicable_when": str, # 适用场景
                "kill_rating": str,     # 杀伤力评级
                "quality_score": float, # 质量评分
            },
            "defense_weakness": {
                "broken_by": str,       # 被什么类型攻击打破
                "why_vulnerable": str,  # 为什么脆弱
                "fix_strategy": str,    # 修复策略
                "success_rate": float,  # 当前成功率
            },
            "style_fingerprint": {
                "most_authentic_line": str,  # 最像本人的发言
                "why_authentic": str,
                "weakest_line": str,
                "why_weak": str,
            },
            "evidence_preference": {
                "most_effective_type": str,  # 最有效的证据类型
                "ranking": List[str],
            },
            "interaction_pattern": {
                "best_opponent": str,   # 最擅长对抗的专家
                "worst_opponent": str,  # 最不擅长对抗的专家
            },
        }
    """
    data = _load_discussion(json_path)
    book_title = data.get("title", "未知")

    speeches = _extract_speeches(data, expert_name)
    interactions = _extract_interactions(data, expert_name)

    if not speeches:
        return _empty_strategies()

    # Step 1: AI质量评分
    quality_speeches = await _batch_score_speeches(speeches, expert_name, book_title)

    # Step 2: 基于质量提取策略
    strategies = await _ai_extract_strategy(
        expert_name, quality_speeches, interactions, book_title
    )

    return strategies


def _load_discussion(json_path: str) -> Dict:
    """加载讨论JSON"""
    with open(json_path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    if isinstance(data, dict) and "title" in data:
        data["title"] = data["title"].lstrip("\ufeff")
    return data


def _extract_speeches(data: Dict, expert_name: str) -> List[Dict]:
    """提取某位专家的所有发言"""
    speeches = []
    for r in data.get("rounds", []):
        for s in r.get("stances", []):
            if s.get("expert") == expert_name:
                speeches.append({
                    "type": "stance",
                    "round": r.get("round_number", 0),
                    "topic": r.get("topic", ""),
                    "content": s.get("stance", ""),
                })
        for c in r.get("clash_rounds", []):
            if c.get("attacker") == expert_name:
                speeches.append({
                    "type": "attack",
                    "round": r.get("round_number", 0),
                    "topic": r.get("topic", ""),
                    "target": c.get("target", ""),
                    "content": c.get("attack_content", ""),
                })
            if c.get("target") == expert_name and c.get("counter_attack"):
                speeches.append({
                    "type": "defense",
                    "round": r.get("round_number", 0),
                    "topic": r.get("topic", ""),
                    "attacker": c.get("attacker", ""),
                    "content": c.get("counter_attack", ""),
                })
    return speeches


def _extract_interactions(data: Dict, expert_name: str) -> List[Dict]:
    """提取某位专家的所有交互"""
    interactions = []
    for r in data.get("rounds", []):
        for c in r.get("clash_rounds", []):
            if c.get("attacker") == expert_name or c.get("target") == expert_name:
                interactions.append({
                    "round": r.get("round_number", 0),
                    "topic": r.get("topic", ""),
                    "attacker": c.get("attacker", ""),
                    "target": c.get("target", ""),
                    "attack_type": c.get("attack_type", ""),
                    "attack_content": c.get("attack_content", ""),
                    "counter_attack": c.get("counter_attack", ""),
                    "has_counter": bool(c.get("counter_attack")),
                })
    return interactions


async def _batch_score_speeches(
    speeches: List[Dict],
    expert_name: str,
    book_title: str
) -> List[Dict]:
    """批量评分发言"""
    results = []
    for speech in speeches:
        context = f"话题: {speech.get('topic', '')} | 类型: {speech.get('type', '')}"
        quality = await analyze_speech_quality(
            speech["content"], expert_name, context
        )
        results.append({
            "speech": speech,
            "quality": quality,
        })
    return results


async def _ai_extract_strategy(
    expert_name: str,
    quality_speeches: List[Dict],
    interactions: List[Dict],
    book_title: str
) -> Dict:
    """基于质量评分提取策略"""
    speeches = [qs["speech"] for qs in quality_speeches]
    qualities = [qs["quality"] for qs in quality_speeches]

    # 按overall排序
    sorted_items = sorted(
        zip(speeches, qualities),
        key=lambda x: x[1].overall,
        reverse=True
    )

    best_attack = next(
        ((s, q) for s, q in sorted_items if s["type"] == "attack"), (None, None)
    )
    best_defense = next(
        ((s, q) for s, q in sorted_items if s["type"] == "defense"), (None, None)
    )
    best_stance = next(
        ((s, q) for s, q in sorted_items if s["type"] == "stance"), (None, None)
    )
    worst = min(sorted_items, key=lambda x: x[1].overall) if sorted_items else (None, None)

    prompt = f"""基于以下质量评分数据，提取「{expert_name}」在《{book_title}》讨论中的战斗策略。

## 高质量发言示例（AI评分认证）

"""
    if best_attack[0]:
        prompt += f"""
### 最佳攻击（综合{best_attack[1].overall}/10）
- 深度: {best_attack[1].depth_score} | 逻辑: {best_attack[1].logic_score} | 证据: {best_attack[1].evidence_score}
- 内容: {best_attack[0]['content'][:400]}
- 质量理由: {best_attack[1].why}
"""

    if best_stance[0]:
        prompt += f"""
### 最佳立场（综合{best_stance[1].overall}/10）
- 风格: {best_stance[1].style_score} | 影响力: {best_stance[1].impact_score}
- 内容: {best_stance[0]['content'][:400]}
"""

    if worst[0]:
        prompt += f"""
### 最弱发言（综合{worst[1].overall}/10）
- 深度: {worst[1].depth_score} | 逻辑: {worst[1].logic_score}
- 内容: {worst[0]['content'][:300]}
- 弱点: {worst[1].why}
"""

    prompt += f"""
## 交互记录
"""
    for i in interactions[:5]:
        role = "攻击方" if i["attacker"] == expert_name else "防守方"
        prompt += f"- {i['attacker']} → {i['target']} [{i['attack_type']}] ({role})\n"

    prompt += """
## 输出格式（严格JSON）

```json
{
  "attack_strategy": {
    "best_angle": "最有效的攻击角度（一句话）",
    "why_effective": "为什么这个角度有效（基于质量分析）",
    "applicable_when": "什么场景下使用",
    "kill_rating": "高/中/低",
    "quality_score": 8.5
  },
  "defense_weakness": {
    "broken_by": "被什么角度击穿",
    "why_vulnerable": "为什么在这个角度上脆弱（基于低分分析）",
    "fix_strategy": "具体修复方案（不是泛泛而谈）",
    "success_rate": 35.0
  },
  "style_fingerprint": {
    "most_authentic_line": "最像这个人说的话（原文引用）",
    "why_authentic": "为什么这句最像他",
    "weakest_line": "最不像这个人说的话",
    "why_weak": "为什么这句不像他"
  },
  "evidence_preference": {
    "most_effective_type": "最有效的证据类型",
    "ranking": ["类型1", "类型2", "类型3"]
  },
  "interaction_pattern": {
    "best_opponent": "最擅长对抗的专家",
    "worst_opponent": "最不擅长对抗的专家"
  }
}
```

要求：
1. 所有结论必须基于上面的质量评分数据
2. 修复方案必须具体（"增加数据支撑"→"引用书中第X章的Y情节"）
3. 风格指纹要足够具体，能区分这个人和其他人
4. quality_score 和 success_rate 必须是数字
"""

    result = call_llm_json(
        prompt,
        system="你是一位辩论策略分析师。你基于质量数据提取策略，不编造。",
        max_tokens=2500,
        temperature=0.4,
    )

    if result.get("success") and result.get("data"):
        data = result["data"]
        return {
            "attack_strategy": data.get("attack_strategy", {}),
            "defense_weakness": data.get("defense_weakness", {}),
            "style_fingerprint": data.get("style_fingerprint", {}),
            "evidence_preference": data.get("evidence_preference", {}),
            "interaction_pattern": data.get("interaction_pattern", {}),
        }

    return _build_fallback_strategy(best_attack, best_defense, best_stance, worst)


def _build_fallback_strategy(
    best_attack: Tuple[Optional[Dict], Optional[SpeechQuality]],
    best_defense: Tuple[Optional[Dict], Optional[SpeechQuality]],
    best_stance: Tuple[Optional[Dict], Optional[SpeechQuality]],
    worst: Tuple[Optional[Dict], Optional[SpeechQuality]],
) -> Dict:
    """基于质量评分的启发式策略构建"""
    return {
        "attack_strategy": {
            "best_angle": best_attack[0]["content"][:80] if best_attack[0] else "逻辑攻击",
            "why_effective": f"AI评分: 深度{best_attack[1].depth_score}/10" if best_attack[1] else "默认策略",
            "applicable_when": "对手立场偏激时",
            "kill_rating": "高" if best_attack[1] and best_attack[1].overall >= 8 else "中",
            "quality_score": best_attack[1].overall if best_attack[1] else 5.0,
        },
        "defense_weakness": {
            "broken_by": worst[0]["type"] if worst[0] else "未知",
            "why_vulnerable": worst[1].why if worst[1] else "数据不足",
            "fix_strategy": "增加证据支撑和逻辑链",
            "success_rate": worst[1].overall * 10 if worst[1] else 30.0,
        },
        "style_fingerprint": {
            "most_authentic_line": best_stance[0]["content"][:200] if best_stance[0] else "",
            "why_authentic": f"风格评分: {best_stance[1].style_score}/10" if best_stance[1] else "",
            "weakest_line": worst[0]["content"][:200] if worst[0] else "",
            "why_weak": worst[1].why if worst[1] else "",
        },
        "evidence_preference": {
            "most_effective_type": "经典引用",
            "ranking": ["经典引用", "历史案例", "逻辑推演"],
        },
        "interaction_pattern": {
            "best_opponent": "未知",
            "worst_opponent": "未知",
        },
    }


def _empty_strategies() -> Dict:
    """返回空的策略结构"""
    return {
        "attack_strategy": {
            "best_angle": "",
            "why_effective": "",
            "applicable_when": "",
            "kill_rating": "",
            "quality_score": 0.0,
        },
        "defense_weakness": {
            "broken_by": "",
            "why_vulnerable": "",
            "fix_strategy": "",
            "success_rate": 0.0,
        },
        "style_fingerprint": {
            "most_authentic_line": "",
            "why_authentic": "",
            "weakest_line": "",
            "why_weak": "",
        },
        "evidence_preference": {
            "most_effective_type": "",
            "ranking": [],
        },
        "interaction_pattern": {
            "best_opponent": "",
            "worst_opponent": "",
        },
    }


# ─── 兼容旧接口的同步包装 ──────────────────────────────────

class LLMStrategyExtractor:
    """兼容旧接口的策略提取器"""

    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
        self.model = model or "deepseek/deepseek-chat-v3-0324:free"

    def extract(self, json_path: str, output_path: str = None) -> Dict:
        """同步提取所有专家的策略"""
        data = _load_discussion(json_path)
        book_title = data.get("title", "未知")
        experts_names = _extract_all_expert_names(data)

        print(f"\n{'='*60}")
        print(f"AI策略提取: 《{book_title}》")
        print(f"专家数: {len(experts_names)}")
        print(f"{'='*60}\n")

        result = {
            "book_title": book_title,
            "source_file": json_path,
            "experts": {},
            "quality_matrix": {},
        }

        for name in experts_names:
            strategies = asyncio.run(extract_strategies(json_path, name))
            result["experts"][name] = strategies

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\n策略数据保存: {output_path}")

        return result


def _extract_all_expert_names(data: Dict) -> List[str]:
    """提取所有专家名"""
    names = set()
    for r in data.get("rounds", []):
        for s in r.get("stances", []):
            if s.get("expert"):
                names.add(s["expert"])
        for c in r.get("clash_rounds", []):
            if c.get("attacker"):
                names.add(c["attacker"])
            if c.get("target"):
                names.add(c["target"])
    return sorted(list(names))


# ─── 测试代码 ──────────────────────────────────────────────

if __name__ == "__main__":
    import tempfile

    # 创建测试用的讨论JSON
    test_discussion = {
        "title": "测试书籍",
        "rounds": [
            {
                "round_number": 1,
                "topic": "人性本善还是本恶？",
                "stances": [
                    {
                        "expert": "孔子",
                        "stance": "人性本善。'人之初，性本善'，每个人生来都有恻隐之心。我看到一个孩子要掉进井里，任何人都会本能地产生惊骇恻隐之情，这不是为了讨好孩子父母，也不是为了博取名声，而是发自内心的善。",
                    },
                    {
                        "expert": "韩非子",
                        "stance": "人性本恶。人天生趋利避害，好逸恶劳。父母对子女的爱也是出于'计算之心'——养儿防老。如果没有法律和刑罚的约束，人人都会成为盗贼。",
                    },
                ],
                "clash_rounds": [
                    {
                        "attacker": "韩非子",
                        "target": "孔子",
                        "attack_type": "证据质疑",
                        "attack_content": "你说人有恻隐之心，但现实中父母遗弃婴儿、兄弟争夺遗产的案例比比皆是。如果人性本善，为什么需要礼教来约束？",
                        "counter_attack": "礼教不是约束本性，而是引导本性。就像园丁修剪树木，不是树木本身不好，而是需要引导才能长成栋梁。",
                    },
                ],
            },
        ],
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(test_discussion, f, ensure_ascii=False, indent=2)
        test_json_path = f.name

    print("=" * 60)
    print("测试 llm_extractor.py")
    print("=" * 60)

    # 测试1: analyze_speech_quality
    print("\n[测试1] analyze_speech_quality")
    test_speech = "人性本善。'人之初，性本善'，每个人生来都有恻隐之心。"
    quality = asyncio.run(analyze_speech_quality(test_speech, "孔子"))
    print(f"  认知深度: {quality.depth_score}")
    print(f"  逻辑严密性: {quality.logic_score}")
    print(f"  证据质量: {quality.evidence_score}")
    print(f"  风格辨识度: {quality.style_score}")
    print(f"  实际影响力: {quality.impact_score}")
    print(f"  综合得分: {quality.overall}")
    print(f"  置信度: {quality.confidence}")
    print(f"  理由: {quality.why}")

    # 测试2: extract_strategies
    print("\n[测试2] extract_strategies")
    strategies = asyncio.run(extract_strategies(test_json_path, "孔子"))
    print(f"  攻击策略: {strategies.get('attack_strategy', {})}")
    print(f"  防御弱点: {strategies.get('defense_weakness', {})}")
    print(f"  风格指纹: {strategies.get('style_fingerprint', {})}")
    print(f"  证据偏好: {strategies.get('evidence_preference', {})}")
    print(f"  交互模式: {strategies.get('interaction_pattern', {})}")

    # 测试3: LLMStrategyExtractor.extract (兼容接口)
    print("\n[测试3] LLMStrategyExtractor (兼容接口)")
    extractor = LLMStrategyExtractor()
    result = extractor.extract(test_json_path)
    print(f"  书名: {result['book_title']}")
    print(f"  专家数: {len(result['experts'])}")
    for name, data in result["experts"].items():
        attack = data.get("attack_strategy", {})
        print(f"  {name}: 最佳攻击角度='{attack.get('best_angle', 'N/A')}'")

    # 清理
    os.unlink(test_json_path)

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
