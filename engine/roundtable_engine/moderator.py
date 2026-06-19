# -*- coding: utf-8 -*-
"""主持人摘要提取器：确保每轮有完整的 moderator 字段。"""
from __future__ import annotations

from typing import Any


def extract_moderator_summary(rounds: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """为每轮圆桌提取或补全 moderator 字段。

    moderator 结构：{"core_crack": str, "structure_map": str, "next_question": str}

    规则：
    - 已有 moderator.core_crack 且非空 → 保留
    - 否则从 summary 提取
    - 如果 next_question 为空，从下一轮的 guiding_question 提取
    """
    result: list[dict[str, Any]] = []
    for i, rd in enumerate(rounds):
        r = dict(rd)
        mod = dict(r.get("moderator") or {})
        core_crack = str(mod.get("core_crack") or "").strip()
        if not core_crack:
            core_crack = str(
                r.get("summary")
                or r.get("tension_axis")
                or ""
            ).strip()
        mod["core_crack"] = core_crack
        mod.setdefault("structure_map", "")
        next_q = str(mod.get("next_question") or "").strip()
        if not next_q and i + 1 < len(rounds):
            next_q = str(
                rounds[i + 1].get("guiding_question")
                or rounds[i + 1].get("core_question")
                or ""
            ).strip()
        mod["next_question"] = next_q
        r["moderator"] = mod
        result.append(r)
    return result
