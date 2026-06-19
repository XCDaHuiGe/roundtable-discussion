from engine.cognitive_model.schema import CognitiveModel
from engine.quality_gates.cognitive_quality import validate_cognitive_quality


def complete_model():
    model = CognitiveModel(title="测试书")
    model.book_spine.core_question = "人为什么会把适应误认为命运？"
    model.book_spine.consensus_baseline = "常见回答把命运理解为个人努力不足。"
    model.book_spine.author_move = "作者把问题转向脑与环境的互动机制。"
    model.book_spine.delta_sentence = "之前大家以为命运来自意志强弱，作者说命运来自脑的适应回路。"
    model.book_spine.signature_terms = ["适应回路"]
    model.root_rank.candidate_generators = ["奖励回路", "注意力筛选"]
    model.root_rank.root_generators = ["适应回路"]
    model.root_rank.phenomena = ["习惯形成", "情绪反应", "学习迁移"]
    model.root_rank.regeneration_matrix = [
        {"generator": "适应回路", "phenomenon": "习惯形成"},
        {"generator": "适应回路", "phenomenon": "情绪反应"},
        {"generator": "适应回路", "phenomenon": "学习迁移"},
    ]
    model.distillation.qa_chain = [
        {"question": "问题是什么？", "answer": {"conclusion": "问题是适应被误读。", "boundary": "不解释全部人生。"}}
    ]
    return model


def test_validate_cognitive_quality_passes_complete_model():
    result = validate_cognitive_quality(complete_model())

    assert result["ok"] is True
    assert result["errors"] == []


def test_validate_cognitive_quality_reports_missing_delta_and_rank():
    model = CognitiveModel(title="测试书")
    model.book_spine.core_question = "测试问题？"

    result = validate_cognitive_quality(model)
    codes = {issue["code"] for issue in result["errors"]}

    assert "missing_consensus_baseline" in codes
    assert "missing_delta_sentence" in codes
    assert "insufficient_candidate_generators" in codes
    assert "missing_qa_chain" in codes


def test_qa_chain_dependency_correct():
    """qa_chain 依赖顺序正确 → 通过"""
    model = complete_model()
    model.distillation.qa_chain = [
        {"question": "问题1", "answer": {"conclusion": "答案1", "boundary": ""}, "depends_on": None},
        {"question": "问题2", "answer": {"conclusion": "答案2", "boundary": ""}, "depends_on": "问题1"},
        {"question": "问题3", "answer": {"conclusion": "答案3", "boundary": ""}, "depends_on": "问题2"},
    ]

    result = validate_cognitive_quality(model)

    # 没有关于依赖链的 warning
    warning_codes = {issue["code"] for issue in result["warnings"]}
    assert "missing_depends_on" not in warning_codes
    assert "broken_dependency_chain" not in warning_codes


def test_qa_chain_dependency_broken():
    """qa_chain 依赖链断裂 → warning"""
    model = complete_model()
    model.distillation.qa_chain = [
        {"question": "问题1", "answer": {"conclusion": "答案1", "boundary": ""}, "depends_on": None},
        {"question": "问题2", "answer": {"conclusion": "答案2", "boundary": ""}, "depends_on": "不存在的问题"},
    ]

    result = validate_cognitive_quality(model)

    # 应该有 broken_dependency_chain warning
    warning_codes = {issue["code"] for issue in result["warnings"]}
    assert "broken_dependency_chain" in warning_codes


def test_qa_chain_missing_depends_on():
    """qa_chain 缺少 depends_on → warning"""
    model = complete_model()
    model.distillation.qa_chain = [
        {"question": "问题1", "answer": {"conclusion": "答案1", "boundary": ""}, "depends_on": None},
        {"question": "问题2", "answer": {"conclusion": "答案2", "boundary": ""}},  # 缺少 depends_on
    ]

    result = validate_cognitive_quality(model)

    # 应该有 missing_depends_on warning
    warning_codes = {issue["code"] for issue in result["warnings"]}
    assert "missing_depends_on" in warning_codes


def test_root_rank_backtest_insufficient():
    """根秩回测不足 3 项 → error"""
    model = complete_model()
    model.root_rank.regeneration_matrix = [
        {"generator": "适应回路", "phenomenon": "习惯形成"},
        {"generator": "适应回路", "phenomenon": "情绪反应"},
    ]

    result = validate_cognitive_quality(model)

    # 应该有 insufficient_root_rank_backtest error
    error_codes = {issue["code"] for issue in result["errors"]}
    assert "insufficient_root_rank_backtest" in error_codes


def test_root_rank_backtest_with_non_root_generators():
    """regeneration_matrix 中包含非 root_generators 的项 → 只统计有效的"""
    model = complete_model()
    model.root_rank.root_generators = ["适应回路"]
    model.root_rank.regeneration_matrix = [
        {"generator": "适应回路", "phenomenon": "习惯形成"},
        {"generator": "适应回路", "phenomenon": "情绪反应"},
        {"generator": "非根生成器", "phenomenon": "其他现象"},  # 这个不应该被统计
    ]

    result = validate_cognitive_quality(model)

    # 应该有 insufficient_root_rank_backtest error（只有 2 个有效）
    error_codes = {issue["code"] for issue in result["errors"]}
    assert "insufficient_root_rank_backtest" in error_codes


def test_root_rank_backtest_sufficient():
    """根秩回测足够 → 通过"""
    model = complete_model()
    model.root_rank.regeneration_matrix = [
        {"generator": "适应回路", "phenomenon": "习惯形成"},
        {"generator": "适应回路", "phenomenon": "情绪反应"},
        {"generator": "适应回路", "phenomenon": "学习迁移"},
    ]

    result = validate_cognitive_quality(model)

    # 不应该有 insufficient_root_rank_backtest error
    error_codes = {issue["code"] for issue in result["errors"]}
    assert "insufficient_root_rank_backtest" not in error_codes
