# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from engine.cognitive_model.schema import CognitiveModel, QualityIssue


def from_v8(data: dict[str, Any]) -> CognitiveModel:
    model = CognitiveModel(title=str(data.get("title") or "圆桌洞见"), source_type="book")
    model.source_understanding.author_problem = str(data.get("subtitle") or "")
    model.source_understanding.material_map = _material_map(data)
    model.source_understanding.key_terms = _key_terms(data)
    model.roundtable.participants = _participants(data.get("experts") or [])
    model.roundtable.rounds = [
        _round(round_data, index, data.get("rounds") or [])
        for index, round_data in enumerate(data.get("rounds") or [], start=1)
    ]
    model.roundtable.tension_axes = [
        str(round_data.get("theme") or round_data.get("key_question") or round_data.get("topic") or "")
        for round_data in data.get("rounds") or []
    ]
    model.distillation.insights = _insights(data.get("insights") or [], data.get("final_insight"))
    model.distillation.open_questions = [str(item) for item in (data.get("open_questions") or [])]

    _fill_book_spine(model, data)
    _mark_partial(model)
    return model


def _participants(experts: list[dict[str, Any]]) -> list[dict[str, str]]:
    participants: list[dict[str, str]] = []
    for expert in experts:
        name = str(expert.get("name") or expert.get("expert") or "")
        if not name:
            continue
        traits = expert.get("core_traits") or []
        participants.append({
            "name": name,
            "role": str(expert.get("title") or expert.get("category") or "专家"),
            "function": str(expert.get("core_belief") or expert.get("stance") or " / ".join(map(str, traits[:3])) or "提供解释框架"),
            "bias_warning": str(expert.get("bias_warning") or ""),
            "color": str(expert.get("color") or ""),
        })
    return participants


def _round(round_data: dict[str, Any], index: int, all_rounds: list[dict[str, Any]]) -> dict[str, Any]:
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
            "one_line": content[:80],
        })
        previous_id = speech_id

    next_question = ""
    if index < len(all_rounds):
        next_question = str(all_rounds[index].get("key_question") or all_rounds[index].get("core_question") or "")

    key_question = str(round_data.get("key_question") or round_data.get("core_question") or round_data.get("topic") or "")
    theme = str(round_data.get("theme") or round_data.get("topic") or key_question)
    cognitive_upgrade = round_data.get("cognitive_upgrade") or {}

    return {
        "round_index": int(round_data.get("round_number") or round_data.get("round_index") or index),
        "theme": theme,
        "guiding_question": key_question,
        "tension_axis": _tension_axis(round_data, theme, key_question),
        "speeches": speeches,
        "clashes": _clashes(round_data),
        "reality_cases": list(round_data.get("reality_cases") or []),
        "cost_discussion": round_data.get("cost_discussion") or {},
        "human_nature": round_data.get("human_nature") or {},
        "cognitive_upgrade": cognitive_upgrade,
        "moderator": {
            "core_crack": str(
                (cognitive_upgrade or {}).get("complexity")
                or round_data.get("summary")
                or key_question
                or theme
            ),
            "structure_map": str((cognitive_upgrade or {}).get("new_thinking") or ""),
            "next_question": next_question,
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

    return []


def _clashes(round_data: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for clash in list(round_data.get("clash_rounds") or []):
        result.append({
            "attacker": str(clash.get("attacker") or ""),
            "target": str(clash.get("target") or ""),
            "attack_type": str(clash.get("attack_type") or "关键反驳"),
            "attack_content": str(clash.get("attack_content") or clash.get("counter_attack") or ""),
            "defense_content": str(clash.get("defense_content") or clash.get("defense") or ""),
        })
    return result


def _insights(insights: list[dict[str, Any]], final_insight: Any = None) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for insight in insights:
        result.append({
            "title": str(insight.get("insight_title") or insight.get("title") or "洞见"),
            "content": str(insight.get("insight_content") or insight.get("content") or insight.get("attack_content") or ""),
            "evidence": str(insight.get("evidence") or ""),
            "contributors": " / ".join(map(str, insight.get("contributors") or [])),
        })
    if final_insight and not result:
        result.append({"title": "最终洞见", "content": str(final_insight), "evidence": ""})
    return result


def _material_map(data: dict[str, Any]) -> list[dict[str, str]]:
    rounds = list(data.get("rounds") or [])
    items = []
    for round_data in rounds[:3]:
        if round_data.get("theme"):
            items.append({"type": "讨论回合", "content": str(round_data.get("theme"))})
        for case in list(round_data.get("reality_cases") or [])[:1]:
            items.append({"type": "现实案例", "content": str(case.get("case_name") or case.get("case_content") or "")})
    return items[:6]


def _key_terms(data: dict[str, Any]) -> list[str]:
    terms: list[str] = []
    for round_data in list(data.get("rounds") or []):
        for field in ("theme", "key_question"):
            value = str(round_data.get(field) or "")
            for token in ("文化属性", "神即道", "道法自然", "如来", "杀富济贫", "天道", "人道", "选择", "规律"):
                if token in value and token not in terms:
                    terms.append(token)
    return terms[:8]


def _fill_book_spine(model: CognitiveModel, data: dict[str, Any]) -> None:
    rounds = list(data.get("rounds") or [])
    insights = model.distillation.insights
    if rounds:
        first = rounds[0]
        model.book_spine.core_question = str(first.get("key_question") or first.get("core_question") or first.get("theme") or "")
        model.book_spine.author_move = str((first.get("cognitive_upgrade") or {}).get("new_thinking") or "")
        model.book_spine.consensus_baseline = str((first.get("cognitive_upgrade") or {}).get("old_thinking") or "")
        model.book_spine.delta_sentence = str((first.get("cognitive_upgrade") or {}).get("complexity") or "")
    if insights:
        model.book_spine.landing_sentence = str(insights[0].get("content") or "")
        model.book_spine.carryaway = str(insights[0].get("title") or "")
    model.book_spine.signature_terms = model.source_understanding.key_terms[:5]


def _tension_axis(round_data: dict[str, Any], theme: str, key_question: str) -> str:
    if key_question:
        return key_question
    if "：" in theme:
        return theme.split("：", 1)[-1]
    return theme


def _mark_partial(model: CognitiveModel) -> None:
    model.quality.checks.append(QualityIssue("warning", "partial_model", "V8 输入已转换为 CognitiveModel，仍需人工审校深度字段", "meta"))
    if not model.root_rank.root_generators:
        model.quality.checks.append(QualityIssue("warning", "missing_root_rank", "缺少根秩生成器", "root_rank.root_generators"))
    if not model.distillation.qa_chain:
        model.quality.checks.append(QualityIssue("warning", "missing_qa_chain", "缺少问答链", "distillation.qa_chain"))
