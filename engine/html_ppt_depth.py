# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


GENERIC_TERMS = {
    "深度思考",
    "圆桌张力",
    "观点冲突",
    "认知升级",
    "值得反思",
    "要有深度思考",
    "think deeply",
}


@dataclass
class DepthScore:
    score: int
    can_render: bool
    missing: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _present(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return any(_present(item) for item in value)
    if isinstance(value, dict):
        return any(_present(item) for item in value.values())
    return value is not None


def _specific_text(value: Any, minimum: int = 12) -> bool:
    text = str(value or "").strip()
    return len(text) >= minimum and text.lower() not in GENERIC_TERMS


def score_deep_content(model: dict[str, Any]) -> DepthScore:
    score = 0
    missing: list[str] = []
    warnings: list[str] = []

    if _specific_text(model.get("author_problem")):
        score += 10
    else:
        missing.append("author_problem")

    if _specific_text(model.get("consensus_baseline")) and _specific_text(model.get("author_delta")):
        score += 15
    else:
        missing.append("baseline_delta")

    if _specific_text(model.get("root_mechanism")):
        score += 15
    else:
        missing.append("root_mechanism")

    if len(model.get("reality_cases") or []) >= 2:
        score += 10
    else:
        missing.append("reality_cases")

    if _present(model.get("counter_positions")):
        score += 10
    else:
        missing.append("counter_positions")

    if _present(model.get("costs")) and _present(model.get("boundaries")):
        score += 15
    else:
        missing.append("costs_boundaries")

    insights = model.get("transferable_insights") or []
    if insights and all(str(item).strip().lower() not in GENERIC_TERMS for item in insights):
        score += 15
    else:
        missing.append("transferable_insights")

    if _present(model.get("uncertainty_notes")):
        score += 10
    else:
        warnings.append("uncertainty_not_named")

    return DepthScore(score=score, can_render=score >= 70, missing=missing, warnings=warnings)
