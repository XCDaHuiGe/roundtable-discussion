# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from engine.cognitive_model.schema import CognitiveModel, QualityIssue


def from_v8(data: dict[str, Any]) -> CognitiveModel:
    model = CognitiveModel(title=str(data.get("title") or "圆桌洞见"), source_type="book")
    model.source_understanding.author_problem = str(data.get("subtitle") or "")
    model.roundtable.participants = _participants(data.get("experts") or [])
    model.roundtable.rounds = [
        _round(round_data, index)
        for index, round_data in enumerate(data.get("rounds") or [], start=1)
    ]
    model.roundtable.tension_axes = [
        str(round_data.get("topic") or round_data.get("core_question") or f"第{index}轮张力")
        for index, round_data in enumerate(data.get("rounds") or [], start=1)
    ]
    model.distillation.insights = _insights(data.get("insights") or [], data.get("final_insight"))
    model.distillation.open_questions = [str(item) for item in (data.get("open_questions") or [])]

    if model.roundtable.rounds:
        first_round = model.roundtable.rounds[0]
        model.book_spine.core_question = str(first_round.get("guiding_question") or "")
    if model.distillation.insights:
        model.book_spine.landing_sentence = str(model.distillation.insights[0].get("content") or "")
        model.book_spine.carryaway = str(model.distillation.insights[0].get("title") or "")

    _mark_partial(model)
    return model


def _participants(experts: list[dict[str, Any]]) -> list[dict[str, str]]:
    participants: list[dict[str, str]] = []
    for expert in experts:
        name = str(expert.get("name") or expert.get("expert") or "")
        if not name:
            continue
        participants.append({
            "name": name,
            "role": str(expert.get("title") or expert.get("category") or "专家"),
            "function": str(expert.get("core_belief") or expert.get("stance") or "提供解释框架"),
        })
    return participants


def _round(round_data: dict[str, Any], index: int) -> dict[str, Any]:
    speeches = []
    previous_id: str | None = None
    source_speeches = _speech_source(round_data)
    for speech_index, stance in enumerate(source_speeches, start=1):
        speech_id = f"r{index}s{speech_index}"
        content = str(stance.get("stance") or stance.get("content") or stance.get("speech") or "")
        speeches.append({
            "id": speech_id,
            "expert": str(stance.get("expert") or stance.get("expert_name") or "专家"),
            "stance": content,
            "responds_to": previous_id,
            "action_type": "definition" if previous_id is None else "response",
            "claim": content,
            "evidence": "",
            "one_line": content[:60],
        })
        previous_id = speech_id
    return {
        "round_index": index,
        "guiding_question": str(round_data.get("core_question") or round_data.get("topic") or ""),
        "tension_axis": str(round_data.get("topic") or round_data.get("core_question") or ""),
        "speeches": speeches,
        "clashes": list(round_data.get("clash_rounds") or []),
        "moderator": {
            "core_crack": str(round_data.get("summary") or round_data.get("topic") or ""),
            "structure_map": "",
            "next_question": "",
        },
    }


def _speech_source(round_data: dict[str, Any]) -> list[dict[str, Any]]:
    stances = list(round_data.get("stances") or [])
    if stances:
        return stances

    speeches = list(round_data.get("speeches") or [])
    if speeches:
        return speeches

    clash_speeches: list[dict[str, Any]] = []
    for clash in list(round_data.get("clash_rounds") or []):
        attacker = str(clash.get("attacker") or "")
        attack = str(clash.get("attack_content") or clash.get("counter_attack") or "")
        if attacker and attack:
            clash_speeches.append({"expert": attacker, "stance": attack})
        target = str(clash.get("target") or "")
        defense = str(clash.get("defense") or clash.get("defense_content") or "")
        if target and defense:
            clash_speeches.append({"expert": target, "stance": defense})
    if clash_speeches:
        return clash_speeches

    case_speeches: list[dict[str, Any]] = []
    for case in list(round_data.get("reality_cases") or []):
        case_name = str(case.get("case_name") or "现实案例")
        case_text = str(case.get("case_content") or case.get("case_lesson") or case.get("case_outcome") or "")
        if case_text:
            case_speeches.append({"expert": case_name, "stance": case_text})

    cognitive_upgrade = round_data.get("cognitive_upgrade") or {}
    if isinstance(cognitive_upgrade, dict):
        for title, value in (
            ("旧思维", cognitive_upgrade.get("old_thinking")),
            ("新思维", cognitive_upgrade.get("new_thinking")),
            ("复杂性", cognitive_upgrade.get("complexity")),
            ("行动洞见", cognitive_upgrade.get("actionable_insight")),
        ):
            if value:
                case_speeches.append({"expert": title, "stance": str(value)})
    if case_speeches:
        return case_speeches

    return clash_speeches


def _insights(insights: list[dict[str, Any]], final_insight: Any = None) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for insight in insights:
        result.append({
            "title": str(insight.get("insight_title") or insight.get("title") or "洞见"),
            "content": str(insight.get("insight_content") or insight.get("content") or insight.get("attack_content") or ""),
            "evidence": str(insight.get("evidence") or ""),
        })
    if final_insight and not result:
        result.append({
            "title": "最终洞见",
            "content": str(final_insight),
            "evidence": "",
        })
    return result


def _mark_partial(model: CognitiveModel) -> None:
    model.quality.checks.append(QualityIssue("warning", "partial_model", "V8 输入只能形成部分 CognitiveModel", "meta"))
    if not model.book_spine.delta_sentence:
        model.quality.checks.append(QualityIssue("warning", "missing_delta_sentence", "缺少作者位移 delta 句", "book_spine.delta_sentence"))
    if not model.root_rank.root_generators:
        model.quality.checks.append(QualityIssue("warning", "missing_root_rank", "缺少根秩生成器", "root_rank.root_generators"))
    if not model.distillation.qa_chain:
        model.quality.checks.append(QualityIssue("warning", "missing_qa_chain", "缺少问答链", "distillation.qa_chain"))
