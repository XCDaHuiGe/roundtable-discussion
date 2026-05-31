# -*- coding: utf-8 -*-
"""
策略提取器 V9.0 — 纯机械操作

Agent传入分析结果，Python只做格式化输出。
零LLM依赖。

用法：
    from engine.training.llm_extractor import LLMStrategyExtractor
    extractor = LLMStrategyExtractor()
    result = extractor.extract(json_path, agent_analysis=...)
"""

import json
import os
import re
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class ExpertStrategies:
    """一位专家的完整策略画像"""
    attack_strategy: Dict = field(default_factory=dict)
    defense_weakness: Dict = field(default_factory=dict)
    style_fingerprint: Dict = field(default_factory=dict)
    evidence_preference: Dict = field(default_factory=dict)
    interaction_pattern: Dict = field(default_factory=dict)


class LLMStrategyExtractor:
    """纯机械策略提取器"""

    def __init__(self, api_key: str = None, model: str = None):
        pass

    def extract(self, json_path: str, agent_analysis: Dict = None) -> Dict:
        """
        提取策略数据（纯机械操作）

        Args:
            json_path: 辩论JSON文件路径
            agent_analysis: Agent传入的分析结果（可选）
                {
                    "experts": {
                        "孔子": {
                            "attack_strategy": {...},
                            "defense_weakness": {...},
                            ...
                        }
                    }
                }

        Returns:
            {
                "book_title": str,
                "source_file": str,
                "experts": {...}
            }
        """
        data = self._load_discussion(json_path)
        book_title = data.get("title", "未知")
        expert_names = self._extract_all_expert_names(data)

        result = {
            "book_title": book_title,
            "source_file": json_path,
            "experts": {},
        }

        if agent_analysis and agent_analysis.get("experts"):
            result["experts"] = agent_analysis["experts"]
        else:
            for name in expert_names:
                result["experts"][name] = self._build_default_strategy(name, data)

        return result

    def _load_discussion(self, json_path: str) -> Dict:
        """加载讨论JSON"""
        with open(json_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        if isinstance(data, dict) and "title" in data:
            data["title"] = data["title"].lstrip("\ufeff")
        return data

    def _extract_all_expert_names(self, data: Dict) -> List[str]:
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

    def _build_default_strategy(self, expert_name: str, data: Dict) -> Dict:
        """构建默认策略（启发式提取）"""
        speeches = self._extract_speeches(data, expert_name)

        best_attack = max(
            [s for s in speeches if s.get("type") == "attack"],
            key=lambda s: len(s.get("content", "")),
            default={}
        )
        best_stance = max(
            [s for s in speeches if s.get("type") == "stance"],
            key=lambda s: len(s.get("content", "")),
            default={}
        )
        worst_defense = min(
            [s for s in speeches if s.get("type") == "defense"],
            key=lambda s: len(s.get("content", "")),
            default={}
        )

        return {
            "attack_strategy": {
                "best_angle": best_attack.get("attack_type", "逻辑攻击"),
                "why_effective": f"在{best_attack.get('topic', '讨论')}中有效",
                "applicable_when": "对手立场偏激时",
                "kill_rating": "中",
                "quality_score": 5.0,
            },
            "defense_weakness": {
                "broken_by": worst_defense.get("attacker", "逻辑攻击"),
                "why_vulnerable": "回应简短",
                "fix_strategy": "增加证据支撑",
                "success_rate": 30.0,
            },
            "style_fingerprint": {
                "most_authentic_line": best_stance.get("content", "")[:200] if best_stance else "",
                "why_authentic": "风格鲜明",
                "weakest_line": "",
                "why_weak": "",
            },
            "evidence_preference": {
                "most_effective_type": "逻辑推演",
                "ranking": ["逻辑推演", "案例归纳", "数据实证"],
            },
            "interaction_pattern": {
                "best_opponent": best_attack.get("target", ""),
                "worst_opponent": worst_defense.get("attacker", ""),
            },
        }

    def _extract_speeches(self, data: Dict, expert_name: str) -> List[Dict]:
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
                        "attack_type": c.get("attack_type", ""),
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