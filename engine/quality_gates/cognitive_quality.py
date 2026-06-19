# -*- coding: utf-8 -*-
from __future__ import annotations

from engine.cognitive_model.schema import CognitiveModel, QualityIssue


def validate_cognitive_quality(model: CognitiveModel) -> dict[str, object]:
    errors: list[QualityIssue] = []
    warnings: list[QualityIssue] = []

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

    # 新增检查：qa_chain 依赖顺序
    qa_warnings = _check_qa_chain_dependency(model)
    warnings.extend(qa_warnings)

    # 新增检查：根秩回测
    rank_errors = _check_root_rank_backtest(model)
    errors.extend(rank_errors)

    return {
        "ok": not errors,
        "errors": [issue.to_dict() for issue in errors],
        "warnings": [issue.to_dict() for issue in warnings],
    }


def _check_qa_chain_dependency(model: CognitiveModel) -> list[QualityIssue]:
    """检查 qa_chain 依赖顺序。

    规则：
    1. 每个 qa_chain 项（除首项）必须有 depends_on 字段且非空
    2. depends_on 必须指向前面某个问题的 question 字段
    3. 如果依赖链断裂（指向不存在的问题），报 warning
    """
    warnings: list[QualityIssue] = []

    if not model.distillation.qa_chain:
        return warnings

    # 收集所有问题
    all_questions = set()
    for item in model.distillation.qa_chain:
        question = item.get("question", "")
        if question:
            all_questions.add(question)

    # 检查每一项的依赖
    for i, item in enumerate(model.distillation.qa_chain):
        # 首项可以没有 depends_on
        if i == 0:
            continue

        depends_on = item.get("depends_on")

        # 检查 depends_on 是否存在且非空
        if not depends_on:
            warnings.append(QualityIssue(
                "warning",
                "missing_depends_on",
                f"qa_chain 第 {i+1} 项缺少 depends_on 字段",
                f"distillation.qa_chain[{i}]"
            ))
            continue

        # 检查 depends_on 是否指向前面某个问题
        if depends_on not in all_questions:
            warnings.append(QualityIssue(
                "warning",
                "broken_dependency_chain",
                f"qa_chain 第 {i+1} 项的 depends_on 指向不存在的问题: {depends_on}",
                f"distillation.qa_chain[{i}]"
            ))

    return warnings


def _check_root_rank_backtest(model: CognitiveModel) -> list[QualityIssue]:
    """检查根秩回测。

    规则：
    1. root_generators 必须能解释至少 3 个现象
    2. 检查方式：regeneration_matrix 中至少有 3 项，且每项的 generator 在 root_generators 中
    """
    errors: list[QualityIssue] = []

    if not model.root_rank.root_generators:
        # 已经在主函数中检查过了
        return errors

    root_set = set(model.root_rank.root_generators)

    # 统计 regeneration_matrix 中 generator 在 root_generators 中的项数
    valid_count = 0
    for item in model.root_rank.regeneration_matrix:
        generator = item.get("generator", "")
        if generator in root_set:
            valid_count += 1

    if valid_count < 3:
        errors.append(QualityIssue(
            "error",
            "insufficient_root_rank_backtest",
            f"根生成器回测不足 3 个现象（当前 {valid_count} 个），root_generators 必须能解释至少 3 个现象",
            "root_rank.regeneration_matrix"
        ))

    return errors
