# -*- coding: utf-8 -*-
"""回应关系图构建器：确保每条发言有 id 和 responds_to 字段。"""
from __future__ import annotations

from typing import Any


def build_response_graph(rounds: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """为每轮圆桌的发言建立回应关系图。

    规则：
    - 每轮首条发言 responds_to 为 None
    - 后续发言 responds_to 指向前一条发言的 id
    - 如果发言没有 id，生成 "r{round_index}s{speech_index}" 格式
    - 如果发言已有 responds_to 且非空，保留
    """
    result: list[dict[str, Any]] = []
    for round_idx, rd in enumerate(rounds, start=1):
        r = dict(rd)
        speeches = list(r.get("speeches") or [])
        previous_id: str | None = None
        for speech_idx, speech in enumerate(speeches, start=1):
            s = dict(speech)
            if not str(s.get("id") or "").strip():
                s["id"] = f"r{round_idx}s{speech_idx}"
            if speech_idx == 1:
                s.setdefault("responds_to", None)
            else:
                existing = s.get("responds_to")
                if not existing:
                    s["responds_to"] = previous_id
            previous_id = s["id"]
            speeches[speech_idx - 1] = s
        r["speeches"] = speeches
        result.append(r)
    return result
