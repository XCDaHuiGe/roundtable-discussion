# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from engine.html_ppt_v12 import CAPACITY, Page, summarize_text, split_text


def plan_pages(data: dict[str, Any]) -> list[Page]:
    pages: list[Page] = []
    title = data.get("title", "圆桌洞见")
    pages.append(Page("cover", title=title, subtitle=data.get("subtitle", "")))

    insights = data.get("insights") or []
    if insights:
        pages.append(_plan_insight_overview(insights))

    experts = data.get("experts") or []
    if experts:
        pages.append(_plan_experts(experts))

    for round_index, round_data in enumerate(data.get("rounds") or [], start=1):
        pages.append(_plan_round_overview(round_data, round_index))
        pages.extend(_plan_speeches(round_data, round_index))
        pages.extend(_plan_clashes(round_data, round_index))

    questions = data.get("open_questions") or []
    if questions:
        pages.append(_plan_open_questions(questions))

    pages.append(Page("summary", title="最终结论", body="深度不等于页数，深度等于认知增量。"))
    return pages


def _plan_insight_overview(insights: list[dict[str, Any]]) -> Page:
    items = []
    for insight in insights[:5]:
        items.append({
            "title": summarize_text(insight.get("insight_title", "洞见"), CAPACITY["title"]),
            "text": summarize_text(
                insight.get("insight_content", insight.get("attack_content", "")),
                CAPACITY["insight_overview"],
            ),
        })
    return Page("insight_overview", title="五大核心洞见", items=items)


def _plan_experts(experts: list[dict[str, Any]]) -> Page:
    items = []
    for expert in experts[:6]:
        items.append({
            "name": summarize_text(expert.get("name", ""), 12),
            "title": summarize_text(expert.get("title", expert.get("role", "")), 18),
            "belief": summarize_text(
                expert.get("belief", expert.get("core_belief", expert.get("description", ""))),
                CAPACITY["expert_belief"],
            ),
        })
    return Page("experts", title="专家阵容", items=items)


def _plan_round_overview(round_data: dict[str, Any], round_index: int) -> Page:
    return Page(
        "round_overview",
        title=f"第{round_index}轮：{round_data.get('topic', '讨论')}",
        body=summarize_text(round_data.get("core_question", ""), 160),
        meta={"round_index": round_index},
    )


def _plan_speeches(round_data: dict[str, Any], round_index: int) -> list[Page]:
    speech_items = []
    for stance in round_data.get("stances") or []:
        expert = stance.get("expert", stance.get("expert_name", "专家"))
        text = stance.get("stance", stance.get("content", stance.get("speech", "")))
        chunks = split_text(text, CAPACITY["speech"]) or [""]
        for part_index, chunk in enumerate(chunks, start=1):
            suffix = f"（{part_index}）" if part_index > 1 else ""
            speech_items.append({"expert": expert, "text": chunk, "part": suffix})

    pages = []
    for index in range(0, len(speech_items), 2):
        page_items = speech_items[index:index + 2]
        pages.append(Page(
            "speech",
            title=f"第{round_index}轮发言 {index // 2 + 1}",
            items=page_items,
            meta={"round_index": round_index},
        ))
    return pages


def _plan_clashes(round_data: dict[str, Any], round_index: int) -> list[Page]:
    pages = []
    for clash_index, clash in enumerate(round_data.get("clash_rounds") or [], start=1):
        attack_parts = split_text(clash.get("attack_content", ""), CAPACITY["clash_attack"]) or [""]
        defense_parts = split_text(
            clash.get("defense", clash.get("defense_content", "")),
            CAPACITY["clash_defense"],
        ) or [""]
        count = max(len(attack_parts), len(defense_parts))
        for part_index in range(count):
            pages.append(Page(
                "clash",
                title=f"{clash.get('attacker', '攻击方')} → {clash.get('target', '回应方')}",
                items=[{
                    "attacker": clash.get("attacker", "攻击方"),
                    "target": clash.get("target", "回应方"),
                    "attack_type": clash.get("attack_type", "观点碰撞"),
                    "attack": attack_parts[part_index] if part_index < len(attack_parts) else "",
                    "defense": defense_parts[part_index] if part_index < len(defense_parts) else "",
                }],
                meta={
                    "round_index": round_index,
                    "clash_index": clash_index,
                    "part_index": part_index + 1,
                },
            ))
    return pages


def _plan_open_questions(questions: list[Any]) -> Page:
    items = [{"text": summarize_text(q, CAPACITY["open_question"])} for q in questions[:5]]
    return Page("open_questions", title="开放问题", items=items)
