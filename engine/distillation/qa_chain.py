# -*- coding: utf-8 -*-
"""从材料字典中提取或构建问答链（qa_chain）。"""
from __future__ import annotations

from typing import Any


def build_qa_chain(data: dict[str, Any]) -> list[dict[str, Any]]:
    """从材料字典构建问答链。

    优先级：
    1. data 已有 qa_chain 且格式正确 → 直接返回
    2. 从 insights 构建
    3. 从 rounds 的 core_question 构建补充问答

    返回列表，每项包含 question / answer / depends_on。
    """
    # 1. 已有 qa_chain 且格式正确 → 直接返回
    existing = data.get("qa_chain")
    if _is_valid_chain(existing):
        return existing

    # 收集所有候选问题
    items: list[dict[str, Any]] = []

    # 2. 从 insights 构建
    for insight in data.get("insights") or []:
        title = str(insight.get("title") or insight.get("insight_title") or "").strip()
        if not title:
            continue
        content = str(insight.get("content") or insight.get("insight_content") or "")
        evidence = str(insight.get("evidence") or "")
        items.append(_make_qa(
            question=title,
            conclusion=content,
            boundary=evidence,
        ))

    # 3. 从 rounds 构建补充问答（去重：与已有 question 不重复）
    seen_questions = {item["question"] for item in items}
    for round_data in data.get("rounds") or []:
        q_text = str(
            round_data.get("core_question")
            or round_data.get("topic")
            or ""
        ).strip()
        if not q_text or q_text in seen_questions:
            continue
        summary = str(round_data.get("summary") or "")
        items.append(_make_qa(
            question=q_text,
            conclusion=summary,
            boundary="",
        ))
        seen_questions.add(q_text)

    # 4. 构建链式 depends_on
    _link_chain(items)

    return items


def _make_qa(question: str, conclusion: str, boundary: str) -> dict[str, Any]:
    return {
        "question": question,
        "answer": {
            "conclusion": conclusion,
            "formalization": "",
            "steps": [],
            "boundary": boundary,
        },
        "depends_on": None,
    }


def _link_chain(items: list[dict[str, Any]]) -> None:
    """为 items 设置链式 depends_on：第一个为 None，后续指向前一个 question。"""
    for i, item in enumerate(items):
        if i == 0:
            item["depends_on"] = None
        else:
            item["depends_on"] = items[i - 1]["question"]


def _is_valid_chain(chain: Any) -> bool:
    """判断已有的 qa_chain 是否格式正确（非空列表，每项含 question 和 answer）。"""
    if not isinstance(chain, list) or not chain:
        return False
    for item in chain:
        if not isinstance(item, dict):
            return False
        if "question" not in item or "answer" not in item:
            return False
        answer = item["answer"]
        if not isinstance(answer, dict) or "conclusion" not in answer:
            return False
    return True
