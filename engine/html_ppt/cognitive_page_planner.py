# -*- coding: utf-8 -*-
from __future__ import annotations

from engine.cognitive_model.schema import CognitiveModel
from engine.html_ppt_v12 import summarize_text
from engine.html_ppt_v13 import ReadingBlock, ReadingPage


def plan_cognitive_pages(model: CognitiveModel) -> list[ReadingPage]:
    pages: list[ReadingPage] = [_cover(model)]

    for optional in (_source_map, _experts, _library_lens):
        page = optional(model)
        if page:
            pages.append(page)

    if model.book_spine.core_question:
        pages.append(_core_question(model))
    if model.book_spine.delta_sentence or model.book_spine.consensus_baseline:
        pages.append(_baseline_delta(model))
    if model.source_understanding.key_terms or model.book_spine.signature_terms:
        page = _concept_anchor(model)
        if page:
            pages.append(page)
        definition = _definition(model)
        if definition:
            pages.append(definition)
    if model.root_rank.root_generators or model.root_rank.candidate_generators:
        pages.append(_rank_map(model))

    for round_data in model.roundtable.rounds:
        opening = _round_opening(round_data)
        if opening:
            pages.append(opening)
        response = _response_graph(round_data)
        if response:
            pages.append(response)
        case = _case_shock(round_data)
        if case:
            pages.append(case)
        clash = _clash(round_data)
        if clash:
            pages.append(clash)
        upgrade = _cognitive_upgrade(round_data)
        if upgrade:
            pages.append(upgrade)

    if model.distillation.qa_chain:
        pages.append(_qa(model))
    if model.distillation.insights:
        pages.append(_insight(model))
    if model.distillation.open_questions:
        pages.append(_open_questions(model))
    tension = _tension_map(model)
    if tension:
        pages.append(tension)
    future_bets = _future_bets(model)
    if future_bets:
        pages.append(future_bets)

    pages.append(_ending(model))
    return pages


def _cover(model: CognitiveModel) -> ReadingPage:
    return ReadingPage(
        page_type="cover",
        title=model.title,
        thesis="一场围绕问题、冲突、案例与认知升级展开的圆桌洞见",
        takeaway=model.book_spine.carryaway or "先找到这本书真正制造的张力，再讨论它能带走什么。",
        layout="reading_brief_4zone",
        blocks=[
            ReadingBlock("metric", "专家", str(len(model.roundtable.participants))),
            ReadingBlock("metric", "回合", str(len(model.roundtable.rounds))),
            ReadingBlock("metric", "洞见", str(len(model.distillation.insights))),
        ],
        meta={"cover_meta": model.source_understanding.author_problem or "Roundtable OS"},
    )


def _source_map(model: CognitiveModel) -> ReadingPage | None:
    blocks = [
        ReadingBlock("material", str(item.get("type") or "材料"), str(item.get("content") or ""))
        for item in model.source_understanding.material_map[:6]
        if str(item.get("content") or "").strip()
    ]
    if not blocks and model.source_understanding.author_problem:
        blocks.append(ReadingBlock("problem", "作者问题", model.source_understanding.author_problem))
    if not blocks:
        return None
    return ReadingPage(
        page_type="source_map",
        title="材料地图",
        thesis=model.source_understanding.author_problem or "先看材料由哪些问题、案例与冲突构成。",
        takeaway="材料地图的作用不是介绍背景，而是把后续讨论的证据源先摆上桌。",
        layout="reading_brief_4zone",
        blocks=blocks,
    )


def _experts(model: CognitiveModel) -> ReadingPage | None:
    blocks = []
    for participant in model.roundtable.participants[:6]:
        text = str(participant.get("function") or "")
        bias = str(participant.get("bias_warning") or "")
        if bias:
            text = f"{text}｜盲点：{bias}" if text else f"盲点：{bias}"
        name = str(participant.get("name") or "")
        if name:
            blocks.append(ReadingBlock("expert", name, text, label=str(participant.get("role") or "专家")))
    if not blocks:
        return None
    return ReadingPage(
        page_type="experts",
        title="专家阵容",
        thesis="每位专家都代表一种解释机器，也携带一种偏见。",
        takeaway="圆桌的价值不在专家多，而在他们的盲点能彼此照亮。",
        layout="reading_brief_4zone",
        blocks=blocks,
    )


def _library_lens(model: CognitiveModel) -> ReadingPage | None:
    if not (model.book_spine.core_question or model.book_spine.landing_sentence or model.book_spine.carryaway):
        return None
    blocks = []
    if model.book_spine.core_question:
        blocks.append(ReadingBlock("question", "问题轴", model.book_spine.core_question))
    if model.book_spine.landing_sentence:
        blocks.append(ReadingBlock("landing", "落点句", model.book_spine.landing_sentence))
    if model.book_spine.carryaway:
        blocks.append(ReadingBlock("carryaway", "行囊", model.book_spine.carryaway))
    return ReadingPage(
        page_type="library_lens",
        title="这本书的取景框",
        thesis="不是复述情节，而是确认：这本书让我们用什么方式重新看世界。",
        takeaway="取景框一旦清楚，后面的冲突就不再散。",
        layout="magazine_focus",
        blocks=blocks,
    )


def _core_question(model: CognitiveModel) -> ReadingPage:
    return ReadingPage(
        page_type="core_question",
        title="作者真正回答的问题",
        thesis=model.book_spine.core_question,
        takeaway="先固定问题轴，后面的圆桌才不会滑成观点堆叠。",
        layout="magazine_focus",
        blocks=[
            ReadingBlock("question", "核心问题", model.book_spine.core_question),
            ReadingBlock("baseline", "旧共识", model.book_spine.consensus_baseline),
            ReadingBlock("move", "作者转向", model.book_spine.author_move),
            ReadingBlock("landing", "落点", model.book_spine.landing_sentence),
        ],
    )


def _baseline_delta(model: CognitiveModel) -> ReadingPage:
    return ReadingPage(
        page_type="baseline_delta",
        title="旧共识与作者位移",
        thesis=model.book_spine.delta_sentence or model.book_spine.author_move,
        takeaway="洞见来自位移，不来自把原书换一种说法。",
        layout="evolution_ladder",
        blocks=[
            ReadingBlock("before", "旧思维", model.book_spine.consensus_baseline),
            ReadingBlock("turn", "转向", model.book_spine.author_move),
            ReadingBlock("after", "位移后", model.book_spine.delta_sentence),
        ],
    )


def _concept_anchor(model: CognitiveModel) -> ReadingPage | None:
    terms = []
    for term in [*model.source_understanding.key_terms, *model.book_spine.signature_terms]:
        if term and term not in terms:
            terms.append(term)
    blocks = [ReadingBlock("term", "核心术语", term) for term in terms[:8]]
    if not blocks:
        return None
    return ReadingPage(
        page_type="concept_anchor",
        title="概念锚点",
        thesis="先锁定关键词，否则讨论会漂移到熟悉但错误的解释框架。",
        takeaway="概念不是装饰，是整场讨论的坐标钉。",
        layout="reading_brief_4zone",
        blocks=blocks,
    )


def _definition(model: CognitiveModel) -> ReadingPage | None:
    terms = [*model.book_spine.signature_terms, *model.source_understanding.key_terms]
    core = next((term for term in terms if term), "")
    if not core:
        return None
    return ReadingPage(
        page_type="definition",
        title=f"概念定场｜{core}",
        thesis=f"先确定“{core}”在本次讨论中的含义和边界。",
        takeaway="定义页的作用是防止专家在同一个词上各说各话。",
        layout="reading_brief_4zone",
        blocks=[
            ReadingBlock("concept", "核心概念", core),
            ReadingBlock("definition", "概念定义", model.book_spine.author_move or model.book_spine.core_question),
            ReadingBlock("boundary", "概念边界", model.book_spine.consensus_baseline or model.book_spine.delta_sentence),
        ],
    )


def _rank_map(model: CognitiveModel) -> ReadingPage:
    blocks = [ReadingBlock("root", "根生成器", item) for item in model.root_rank.root_generators]
    blocks.extend(ReadingBlock("candidate", "候选生成器", item) for item in model.root_rank.candidate_generators[:5])
    blocks.extend(
        ReadingBlock("regeneration", str(item.get("phenomenon", "现象")), str(item.get("generator", "")))
        for item in model.root_rank.regeneration_matrix[:4]
    )
    return ReadingPage(
        page_type="rank_map",
        title="根秩图",
        thesis="找到少数能重新生成现象的底层机制。",
        takeaway="根秩页用来防止洞见停在关键词层。",
        layout="tension_bars",
        blocks=blocks,
    )


def _round_opening(round_data: dict) -> ReadingPage | None:
    question = str(round_data.get("guiding_question") or "")
    theme = str(round_data.get("theme") or question)
    if not (theme or question):
        return None
    blocks = [
        ReadingBlock("question", "本轮追问", question or theme),
        ReadingBlock("tension", "张力轴", str(round_data.get("tension_axis") or theme)),
    ]
    case = _first_case(round_data)
    if case:
        blocks.append(ReadingBlock("case", "现实切口", str(case.get("case_name") or case.get("case_content") or "")))
    return ReadingPage(
        page_type="round_opening",
        title=f"R{round_data.get('round_index', 1)}｜{theme}",
        thesis=question or theme,
        takeaway="每一轮必须有一个尖锐问题，而不是一个泛泛主题。",
        layout="magazine_focus",
        blocks=blocks,
        meta={"tone": "dark"},
    )


def _response_graph(round_data: dict) -> ReadingPage | None:
    blocks = []
    for speech in list(round_data.get("speeches") or [])[:6]:
        claim = str(speech.get("claim") or speech.get("stance") or "")
        expert = str(speech.get("expert") or "专家")
        if claim:
            blocks.append(ReadingBlock("stance", expert, claim, label=str(speech.get("action_type") or "response")))
    if not blocks:
        return None
    return ReadingPage(
        page_type="response_graph",
        title=f"R{round_data.get('round_index', 1)}｜立场光谱",
        thesis=summarize_text(str(round_data.get("tension_axis") or round_data.get("guiding_question") or "圆桌张力"), 120),
        takeaway=str((round_data.get("moderator") or {}).get("core_crack") or "真正的圆桌发生在回应关系里。"),
        layout="stance_spectrum",
        blocks=blocks,
    )


def _case_shock(round_data: dict) -> ReadingPage | None:
    case = _first_case(round_data)
    if not case:
        return None
    blocks = [
        ReadingBlock("source", "案例来源", str(case.get("case_source") or "原书事件")),
        ReadingBlock("event", str(case.get("case_name") or "冲击事件"), str(case.get("case_content") or "")),
        ReadingBlock("outcome", "结果", str(case.get("case_outcome") or "")),
    ]
    cost = (round_data.get("cost_discussion") or {}).get("cost_analysis") or []
    for item in list(cost)[:2]:
        blocks.append(ReadingBlock("cost", str(item.get("cost") or "代价"), str(item.get("analysis") or "")))
    return ReadingPage(
        page_type="case_shock",
        title=f"R{round_data.get('round_index', 1)} Shock｜{case.get('case_name') or '现实反噬'}",
        thesis=str(case.get("case_content") or case.get("case_name") or ""),
        takeaway="真正让思想变硬的不是观点，而是观点碰到现实后的代价。",
        layout="case_file",
        blocks=blocks,
        meta={"tone": "dark"},
    )


def _clash(round_data: dict) -> ReadingPage | None:
    clashes = list(round_data.get("clashes") or [])
    if not clashes:
        return None
    clash = clashes[0]
    blocks = [
        ReadingBlock("attack", str(clash.get("attacker") or "攻击方"), str(clash.get("attack_content") or ""), label=str(clash.get("attack_type") or "反驳")),
        ReadingBlock("defense", str(clash.get("target") or "回应方"), str(clash.get("defense_content") or ""), label="回应"),
        ReadingBlock("essence", "冲突本质", str(round_data.get("tension_axis") or round_data.get("guiding_question") or "观点冲突")),
    ]
    return ReadingPage(
        page_type="clash",
        title=f"R{round_data.get('round_index', 1)}｜关键冲突",
        thesis="冲突不是装饰，它负责逼出理论的边界。",
        takeaway="真正的洞见来自冲突，不是来自共识。",
        layout="clash_courtroom",
        blocks=blocks,
    )


def _cognitive_upgrade(round_data: dict) -> ReadingPage | None:
    upgrade = round_data.get("cognitive_upgrade") or {}
    if not isinstance(upgrade, dict) or not upgrade:
        return None
    blocks = []
    mapping = [
        ("old_thinking", "旧思维"),
        ("new_thinking", "新思维"),
        ("complexity", "复杂性"),
        ("actionable_insight", "行动洞见"),
    ]
    for key, title in mapping:
        if upgrade.get(key):
            blocks.append(ReadingBlock(key, title, str(upgrade.get(key))))
    if not blocks:
        return None
    return ReadingPage(
        page_type="cognitive_upgrade",
        title=f"R{round_data.get('round_index', 1)}｜认知升级",
        thesis=str(upgrade.get("new_thinking") or round_data.get("guiding_question") or ""),
        takeaway="一轮讨论要留下可见的认知位移，否则只是热闹。",
        layout="evolution_ladder",
        blocks=blocks,
    )


def _qa(model: CognitiveModel) -> ReadingPage:
    blocks = []
    for item in model.distillation.qa_chain[:6]:
        answer = item.get("answer") or {}
        text = f"{answer.get('conclusion', '')} {answer.get('boundary', '')}".strip() if isinstance(answer, dict) else str(answer)
        blocks.append(ReadingBlock("qa", str(item.get("question") or "问题"), text))
    return ReadingPage(
        page_type="qa",
        title="问答链",
        thesis="用问题链复现作者的推理路线。",
        takeaway="读者能顺着问题走，才说明洞见被蒸馏成了结构。",
        layout="question_wall",
        blocks=blocks,
    )


def _insight(model: CognitiveModel) -> ReadingPage:
    blocks = [
        ReadingBlock("insight", str(item.get("title") or "洞见"), str(item.get("content") or ""), label=str(item.get("contributors") or ""))
        for item in model.distillation.insights[:5]
    ]
    return ReadingPage(
        page_type="insight",
        title="五个可以带走的洞见",
        thesis="从圆桌冲突中提取可迁移的判断。",
        takeaway="洞见必须能脱离原材料继续使用。",
        layout="reading_brief_4zone",
        blocks=blocks,
    )


def _open_questions(model: CognitiveModel) -> ReadingPage:
    blocks = [
        ReadingBlock("question", f"Q{index}", question)
        for index, question in enumerate(model.distillation.open_questions[:7], start=1)
    ]
    return ReadingPage(
        page_type="open_questions",
        title="未解决的开放问题",
        thesis="好书不是终止问题，而是把问题推到更锋利的位置。",
        takeaway="开放问题是下一轮思考的入口，不是未完成的尾巴。",
        layout="question_wall",
        blocks=blocks,
    )


def _tension_map(model: CognitiveModel) -> ReadingPage | None:
    blocks = []
    for round_data in model.roundtable.rounds:
        question = str(round_data.get("guiding_question") or round_data.get("theme") or "")
        if question:
            blocks.append(ReadingBlock("tension", f"R{round_data.get('round_index', len(blocks)+1)}", question))
        cost = (round_data.get("cost_discussion") or {}).get("cost_analysis") or []
        for item in list(cost)[:1]:
            blocks.append(ReadingBlock("cost", str(item.get("cost") or "代价"), str(item.get("analysis") or "")))
    if not blocks:
        return None
    return ReadingPage(
        page_type="tension_map",
        title="全书核心张力图谱",
        thesis="这些张力无法被一次性解决，它们构成了这本书持续有效的原因。",
        takeaway="张力不是缺陷，是这本书真正的发动机。",
        layout="tension_bars",
        blocks=blocks[:8],
    )


def _future_bets(model: CognitiveModel) -> ReadingPage | None:
    blocks = [ReadingBlock("bet", "预测", str(bet)) for bet in model.distillation.future_bets[:6] if bet]
    if not blocks:
        return None
    return ReadingPage(
        page_type="future_bets",
        title="未来预测",
        thesis="从当前洞见延伸出的可验证判断。",
        takeaway="好的洞见应该能生成未来检验。",
        layout="question_wall",
        blocks=blocks,
    )


def _ending(model: CognitiveModel) -> ReadingPage:
    return ReadingPage(
        page_type="ending",
        title="深度不等于页数",
        thesis=model.book_spine.landing_sentence or "把材料压缩成一个可复用的判断框架。",
        takeaway=model.book_spine.carryaway or "下一次面对类似问题时，先找问题轴、位移和核心张力。",
        layout="magazine_focus",
        blocks=[
            ReadingBlock("carryaway", "带走", model.book_spine.carryaway),
            ReadingBlock("landing", "落点", model.book_spine.landing_sentence),
            ReadingBlock("open", "继续追问", " / ".join(model.distillation.open_questions[:3])),
        ],
    )


def _first_case(round_data: dict) -> dict | None:
    cases = list(round_data.get("reality_cases") or [])
    return cases[0] if cases else None
