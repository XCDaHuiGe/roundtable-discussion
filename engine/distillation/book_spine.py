# -*- coding: utf-8 -*-
"""从材料字典中提取 book_spine 字段。

最简实现：直接从 data 中提取已有字段，缺失字段填空字符串/空列表。
不做任何 LLM 调用。
"""
from __future__ import annotations

from typing import Any

# ── delta_sentence 格式验证 ──────────────────────────────────────────────
_BEFORE_MARKERS = ("之前", "以前", "过去", "传统上", "大家以为", "人们以为", "普遍认为")
_AUTHOR_MARKERS = ("作者说", "作者认为", "作者指出", "作者提出", "本书认为", "实际上", "真相是")


def _validate_delta(text: str) -> bool:
    """验证 delta_sentence 是否包含"之前"和"作者说"的变体。"""
    has_before = any(m in text for m in _BEFORE_MARKERS)
    has_author = any(m in text for m in _AUTHOR_MARKERS)
    return has_before and has_author


def _classify_delta(text: str) -> str:
    """对已验证的 delta_sentence 给出类型标签。

    简单关键词分类，不依赖 LLM。
    """
    if not _validate_delta(text):
        return ""
    return "consensus_shift"


# ── 从 rounds 第一轮提取 core_question ───────────────────────────────────
def _core_question_from_rounds(rounds: list[dict[str, Any]]) -> str:
    """从轮次列表的第一轮提取 core_question。"""
    if not rounds:
        return ""
    first = rounds[0]
    return str(first.get("core_question") or first.get("topic") or "")


# ── 从 insights 提取 landing_sentence / carryaway ────────────────────────
def _landing_from_insights(insights: list[dict[str, Any]]) -> str:
    if not insights:
        return ""
    first = insights[0]
    return str(first.get("landing_sentence") or first.get("insight_content")
               or first.get("content") or "")


def _carryaway_from_insights(insights: list[dict[str, Any]]) -> str:
    if not insights:
        return ""
    first = insights[0]
    return str(first.get("carryaway") or first.get("insight_title")
               or first.get("title") or "")


# ── 主函数 ───────────────────────────────────────────────────────────────
def extract_book_spine(data: dict[str, Any]) -> dict[str, Any]:
    """从材料字典中提取 book_spine 各字段。

    参数:
        data: 材料字典，可能来自 V8 JSON 或 Agent 生成的材料。

    返回:
        包含 book_spine 全部字段的字典。
    """
    # ── core_question：优先顶层，回退 rounds ──
    core_question = str(data.get("core_question") or data.get("topic") or "")
    if not core_question:
        core_question = _core_question_from_rounds(data.get("rounds") or [])

    # ── 直接提取的字段 ──
    consensus_baseline = str(data.get("consensus_baseline") or "")
    author_move = str(data.get("author_move") or "")
    signature_terms = list(data.get("signature_terms") or [])

    # ── baseline_positions ──
    baseline_positions = [str(p) for p in (data.get("baseline_positions") or [])]

    # ── delta_sentence + delta_type ──
    delta_sentence = str(data.get("delta_sentence") or "")
    delta_type = _classify_delta(delta_sentence) if delta_sentence else ""

    # ── landing_sentence：优先顶层，回退 insights ──
    landing_sentence = str(data.get("landing_sentence") or "")
    if not landing_sentence:
        landing_sentence = _landing_from_insights(data.get("insights") or [])

    # ── carryaway：优先顶层，回退 insights ──
    carryaway = str(data.get("carryaway") or "")
    if not carryaway:
        carryaway = _carryaway_from_insights(data.get("insights") or [])

    return {
        "core_question": core_question,
        "baseline_positions": baseline_positions,
        "consensus_baseline": consensus_baseline,
        "author_move": author_move,
        "delta_sentence": delta_sentence,
        "delta_type": delta_type,
        "signature_terms": signature_terms,
        "landing_sentence": landing_sentence,
        "carryaway": carryaway,
    }
