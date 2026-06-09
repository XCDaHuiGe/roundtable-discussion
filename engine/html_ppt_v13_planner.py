# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from engine.html_ppt_v12 import summarize_text
from engine.html_ppt_v13 import ReadingBlock, ReadingPage, classify_position_label


def plan_reading_pages(data: dict[str, Any]) -> list[ReadingPage]:
    pages: list[ReadingPage] = []
    pages.append(_cover_page(data))

    insights = data.get("insights") or []
    if insights:
        pages.append(_insight_page(insights))

    for round_index, round_data in enumerate(data.get("rounds") or [], start=1):
        pages.append(_roundtable_page(round_data, round_index))
        for clash_index, clash in enumerate(_paired_clashes(round_data.get("clash_rounds") or []), start=1):
            pages.append(_clash_page(clash, round_index, clash_index))

    pages.append(_summary_page(data))
    return pages


def _cover_page(data: dict[str, Any]) -> ReadingPage:
    return ReadingPage(
        page_type="cover",
        title=data.get("title", "圆桌洞见"),
        thesis=data.get("subtitle", "阅读型圆桌洞见"),
        takeaway="本 deck 以阅读型结构呈现核心争议、专家立场和最终洞见。",
        layout="reading_brief_4zone",
        blocks=[
            ReadingBlock("metric", "专家", str(len(data.get("experts") or []))),
            ReadingBlock("metric", "轮次", str(len(data.get("rounds") or []))),
            ReadingBlock("metric", "洞见", str(len(data.get("insights") or []))),
        ],
    )


def _insight_page(insights: list[dict[str, Any]]) -> ReadingPage:
    blocks = []
    for insight in insights[:5]:
        blocks.append(ReadingBlock(
            kind="insight",
            title=insight.get("insight_title", "洞见"),
            text=insight.get("insight_content", insight.get("attack_content", "")),
        ))
    return ReadingPage(
        page_type="insight_reading",
        title="核心洞见",
        thesis="先看结论，再进入圆桌讨论。",
        takeaway="这些洞见是后续专家冲突的阅读索引。",
        layout="reading_brief_4zone",
        blocks=blocks,
    )


def _roundtable_page(round_data: dict[str, Any], round_index: int) -> ReadingPage:
    blocks = [
        ReadingBlock(
            kind="stance",
            title=stance.get("expert", stance.get("expert_name", "专家")),
            text=stance.get("stance", stance.get("content", stance.get("speech", ""))),
            label=classify_position_label(stance.get("stance", stance.get("content", ""))),
        )
        for stance in (round_data.get("stances") or [])[:6]
    ]
    return ReadingPage(
        page_type="roundtable_reading",
        title=f"第{round_index}轮：{round_data.get('topic', '圆桌讨论')}",
        thesis=summarize_text(round_data.get("core_question", "这一轮讨论的核心争议是什么？"), 90),
        takeaway="阅读重点：看清专家不是在重复观点，而是在不同解释框架之间竞争。",
        layout="stance_spectrum",
        blocks=blocks,
        meta={"round_index": round_index},
    )


def _clash_page(clash: dict[str, Any], round_index: int, clash_index: int) -> ReadingPage:
    attacker = clash.get("attacker", "攻击方")
    target = clash.get("target", "回应方")
    attack = clash.get("attack_content", "")
    defense = clash.get("defense", clash.get("defense_content", clash.get("counter_attack", "")))
    essence = clash.get("attack_type", "观点冲突")
    return ReadingPage(
        page_type="clash_reading",
        title=f"{attacker} 对 {target}：{essence}",
        thesis="真正值得读的不是谁赢了，而是冲突背后的解释框架。",
        takeaway=f"本页冲突本质：{summarize_text(essence, 40)}。",
        layout="clash_courtroom",
        blocks=[
            ReadingBlock("attack", attacker, attack, label="攻击"),
            ReadingBlock("defense", target, defense, label="回应"),
            ReadingBlock("essence", "冲突本质", essence, label="判读"),
        ],
        meta={"round_index": round_index, "clash_index": clash_index},
    )


def _paired_clashes(clashes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    paired: list[dict[str, Any]] = []
    index = 0
    while index < len(clashes):
        clash = clashes[index]
        if "attack_content" not in clash and "counter_attack" in clash:
            index += 1
            continue

        merged = dict(clash)
        next_clash = clashes[index + 1] if index + 1 < len(clashes) else {}
        if "counter_attack" in next_clash and not next_clash.get("attack_content"):
            merged["counter_attack"] = next_clash.get("counter_attack", "")
            index += 2
        else:
            index += 1

        paired.append(merged)
    return paired


def _summary_page(data: dict[str, Any]) -> ReadingPage:
    questions = data.get("open_questions") or []
    blocks = [
        ReadingBlock("takeaway", "结论一", "文化、制度、资本和行动共同塑造命运。"),
        ReadingBlock("takeaway", "结论二", "强势文化不是口号，而是识别规律并承担代价。"),
        ReadingBlock("question", "开放问题", questions[0] if questions else "读者如何把洞见放回自己的处境？"),
    ]
    return ReadingPage(
        page_type="summary_reading",
        title="读者最终带走什么",
        thesis="不要寻找救世主，要识别自己的解释框架。",
        takeaway="阅读完成后，至少应带走一个可复用的判断框架。",
        layout="reading_brief_4zone",
        blocks=blocks,
    )
