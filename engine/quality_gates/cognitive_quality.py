# -*- coding: utf-8 -*-
from __future__ import annotations

from engine.cognitive_model.schema import CognitiveModel, QualityIssue


def validate_cognitive_quality(model: CognitiveModel) -> dict[str, object]:
    errors: list[QualityIssue] = []

    if not model.book_spine.core_question.strip():
        errors.append(QualityIssue("error", "missing_core_question", "缺少核心问题", "book_spine.core_question"))
    if not model.book_spine.consensus_baseline.strip():
        errors.append(QualityIssue("error", "missing_consensus_baseline", "缺少旧共识或常见回答", "book_spine.consensus_baseline"))
    if not model.book_spine.delta_sentence.strip():
        errors.append(QualityIssue("error", "missing_delta_sentence", "缺少作者位移 delta 句", "book_spine.delta_sentence"))
    elif "之前" not in model.book_spine.delta_sentence or "作者说" not in model.book_spine.delta_sentence:
        errors.append(QualityIssue("error", "invalid_delta_sentence", "delta 句必须表达旧回答与作者新回答", "book_spine.delta_sentence"))
    if not model.book_spine.signature_terms:
        errors.append(QualityIssue("error", "missing_signature_terms", "缺少作者指纹术语", "book_spine.signature_terms"))
    if len(model.root_rank.candidate_generators) < 2:
        errors.append(QualityIssue("error", "insufficient_candidate_generators", "候选生成器少于 2 个", "root_rank.candidate_generators"))
    if not model.root_rank.root_generators:
        errors.append(QualityIssue("error", "missing_root_generators", "缺少最终根生成器", "root_rank.root_generators"))
    if len(model.root_rank.regeneration_matrix) < 3:
        errors.append(QualityIssue("error", "insufficient_regeneration_matrix", "根生成器回测少于 3 个现象", "root_rank.regeneration_matrix"))
    if not model.distillation.qa_chain:
        errors.append(QualityIssue("error", "missing_qa_chain", "缺少问答链", "distillation.qa_chain"))

    return {
        "ok": not errors,
        "errors": [issue.to_dict() for issue in errors],
    }
