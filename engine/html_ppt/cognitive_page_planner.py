# -*- coding: utf-8 -*-
from __future__ import annotations

from engine.cognitive_model.schema import CognitiveModel
from engine.html_ppt_v12 import summarize_text
from engine.html_ppt_v13 import ReadingBlock, ReadingPage


def plan_cognitive_pages(model: CognitiveModel) -> list[ReadingPage]:
    pages = [_cover(model)]
    if model.book_spine.core_question:
        pages.append(_core_question(model))
    if model.book_spine.delta_sentence or model.book_spine.consensus_baseline:
        pages.append(_baseline_delta(model))
    if model.root_rank.root_generators or model.root_rank.candidate_generators:
        pages.append(_rank_map(model))
    for round_data in model.roundtable.rounds:
        pages.append(_response_graph(round_data))
    if model.distillation.qa_chain:
        pages.append(_qa(model))
    if model.distillation.insights:
        pages.append(_insight(model))
    pages.append(_ending(model))
    return pages


def _cover(model: CognitiveModel) -> ReadingPage:
    return ReadingPage(
        page_type="cover",
        title=model.title,
        thesis="认知蒸馏型圆桌洞见",
        takeaway=model.book_spine.carryaway or "从问题、位移、根秩与圆桌张力进入这份材料。",
        layout="reading_brief_4zone",
        blocks=[
            ReadingBlock("metric", "专家", str(len(model.roundtable.participants))),
            ReadingBlock("metric", "轮次", str(len(model.roundtable.rounds))),
            ReadingBlock("metric", "洞见", str(len(model.distillation.insights))),
        ],
        meta={"cover_meta": model.source_understanding.author_problem or "CognitiveModel.v1"},
    )


def _core_question(model: CognitiveModel) -> ReadingPage:
    return ReadingPage(
        page_type="core_question",
        title="作者真正回答的问题",
        thesis=model.book_spine.core_question,
        takeaway="先固定问题轴，后面的圆桌才不会滑成观点堆叠。",
        layout="reading_brief_4zone",
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
        layout="reading_brief_4zone",
        blocks=[
            ReadingBlock("baseline", "之前大家以为", model.book_spine.consensus_baseline),
            ReadingBlock("move", "作者说", model.book_spine.author_move),
            ReadingBlock("delta", "位移句", model.book_spine.delta_sentence),
            ReadingBlock("signature", "作者指纹", " / ".join(model.book_spine.signature_terms)),
        ],
    )


def _rank_map(model: CognitiveModel) -> ReadingPage:
    blocks = [ReadingBlock("root", "根生成器", item) for item in model.root_rank.root_generators]
    blocks.extend(ReadingBlock("candidate", "候选生成器", item) for item in model.root_rank.candidate_generators[:4])
    blocks.extend(
        ReadingBlock("regeneration", str(item.get("phenomenon", "现象")), str(item.get("generator", "")))
        for item in model.root_rank.regeneration_matrix[:3]
    )
    return ReadingPage(
        page_type="rank_map",
        title="根秩图",
        thesis="找到少数能重新生成现象的底层机制。",
        takeaway="根秩页用来防止洞见停在关键词层。",
        layout="reading_brief_4zone",
        blocks=blocks,
    )


def _response_graph(round_data: dict) -> ReadingPage:
    blocks = []
    for speech in list(round_data.get("speeches") or [])[:6]:
        label = str(speech.get("action_type") or "response")
        blocks.append(ReadingBlock("stance", str(speech.get("expert") or "专家"), str(speech.get("claim") or speech.get("stance") or ""), label=label))
    return ReadingPage(
        page_type="response_graph",
        title=f"第{round_data.get('round_index', 1)}轮：回应关系",
        thesis=summarize_text(str(round_data.get("tension_axis") or round_data.get("guiding_question") or "圆桌张力"), 90),
        takeaway=str((round_data.get("moderator") or {}).get("core_crack") or "真正的圆桌发生在回应关系里。"),
        layout="stance_spectrum",
        blocks=blocks,
    )


def _qa(model: CognitiveModel) -> ReadingPage:
    blocks = []
    for item in model.distillation.qa_chain[:6]:
        answer = item.get("answer") or {}
        if isinstance(answer, dict):
            text = f"{answer.get('conclusion', '')} {answer.get('boundary', '')}".strip()
        else:
            text = str(answer)
        blocks.append(ReadingBlock("qa", str(item.get("question") or "问题"), text))
    return ReadingPage(
        page_type="qa",
        title="问答链",
        thesis="用问题链复现作者的推理路线。",
        takeaway="读者能顺着问题走，才说明洞见被蒸馏成了结构。",
        layout="reading_brief_4zone",
        blocks=blocks,
    )


def _insight(model: CognitiveModel) -> ReadingPage:
    blocks = [
        ReadingBlock("insight", str(item.get("title") or "洞见"), str(item.get("content") or ""))
        for item in model.distillation.insights[:5]
    ]
    if model.distillation.open_questions:
        blocks.append(ReadingBlock("question", "开放问题", " / ".join(model.distillation.open_questions[:3])))
    if len(blocks) < 2:
        blocks.append(ReadingBlock("model", "模型提示", "当前输入来自旧 V8 数据，深度字段缺失时保留为质量提示。"))
    return ReadingPage(
        page_type="insight",
        title="核心洞见",
        thesis="从模型中提取可带走的判断。",
        takeaway="洞见必须能脱离原材料继续使用。",
        layout="reading_brief_4zone",
        blocks=blocks,
    )


def _ending(model: CognitiveModel) -> ReadingPage:
    return ReadingPage(
        page_type="ending",
        title="最终带走什么",
        thesis=model.book_spine.landing_sentence or "把材料压缩成一个可复用的判断框架。",
        takeaway=model.book_spine.carryaway or "下一次面对类似问题时，先找问题轴、位移和根生成器。",
        layout="reading_brief_4zone",
        blocks=[
            ReadingBlock("carryaway", "行囊", model.book_spine.carryaway),
            ReadingBlock("future", "未来预测", " / ".join(model.distillation.future_bets[:3])),
            ReadingBlock("open", "开放问题", " / ".join(model.distillation.open_questions[:3])),
        ],
    )
