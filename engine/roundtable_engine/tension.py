# -*- coding: utf-8 -*-
"""张力轴分配器：确保每轮圆桌都有 tension_axis 字段。"""
from __future__ import annotations

from typing import Any


def assign_tension_axes(rounds: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """为每轮圆桌分配 tension_axis。

    规则：
    - 已有 tension_axis 且非空 → 保留
    - 否则从 topic / core_question / guiding_question 提取
    - 都为空 → 生成 "第N轮张力" 占位
    """
    result: list[dict[str, Any]] = []
    for i, rd in enumerate(rounds, start=1):
        r = dict(rd)
        axis = str(r.get("tension_axis") or "").strip()
        if not axis:
            axis = str(
                r.get("topic")
                or r.get("core_question")
                or r.get("guiding_question")
                or ""
            ).strip()
        if not axis:
            axis = f"第{i}轮张力"
        r["tension_axis"] = axis
        result.append(r)
    return result
