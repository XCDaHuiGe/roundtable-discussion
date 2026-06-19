# -*- coding: utf-8 -*-
from engine.distillation.book_spine import extract_book_spine


# ── 完整输入 ──────────────────────────────────────────────────────────────

def test_full_input_extracts_all_fields():
    """完整输入 → 所有字段正确提取。"""
    data = {
        "title": "天道",
        "subtitle": "文化属性与命运",
        "core_question": "文化属性真的决定命运吗？",
        "consensus_baseline": "强势文化造就强者，弱势文化造就弱者",
        "author_move": "文化属性是结果而非原因",
        "delta_sentence": "之前大家以为文化属性决定命运，作者说文化属性只是行动系统的表征",
        "signature_terms": ["文化属性", "强势文化", "弱势文化"],
        "landing_sentence": "命运不是文化决定的，而是认知模式决定的",
        "carryaway": "跳出文化属性看认知",
        "baseline_positions": ["文化决定论", "基因决定论"],
    }

    result = extract_book_spine(data)

    assert result["core_question"] == "文化属性真的决定命运吗？"
    assert result["consensus_baseline"] == "强势文化造就强者，弱势文化造就弱者"
    assert result["author_move"] == "文化属性是结果而非原因"
    assert result["delta_sentence"] == "之前大家以为文化属性决定命运，作者说文化属性只是行动系统的表征"
    assert result["delta_type"] == "consensus_shift"
    assert result["signature_terms"] == ["文化属性", "强势文化", "弱势文化"]
    assert result["landing_sentence"] == "命运不是文化决定的，而是认知模式决定的"
    assert result["carryaway"] == "跳出文化属性看认知"
    assert result["baseline_positions"] == ["文化决定论", "基因决定论"]


def test_delta_type_with_variant_markers():
    """delta_sentence 使用变体标记也能正确分类。"""
    data = {
        "delta_sentence": "以前普遍认为天赋决定成就，作者认为刻意练习才是关键",
    }
    result = extract_book_spine(data)
    assert result["delta_type"] == "consensus_shift"


def test_delta_type_empty_when_format_invalid():
    """delta_sentence 缺少"之前"或"作者说"变体时，delta_type 为空。"""
    data = {
        "delta_sentence": "文化属性很重要",
    }
    result = extract_book_spine(data)
    assert result["delta_sentence"] == "文化属性很重要"
    assert result["delta_type"] == ""


# ── 缺失字段 → 返回空字符串/空列表，不报错 ────────────────────────────────

def test_empty_input_returns_defaults():
    """空字典 → 所有字段为空字符串或空列表。"""
    result = extract_book_spine({})

    assert result["core_question"] == ""
    assert result["baseline_positions"] == []
    assert result["consensus_baseline"] == ""
    assert result["author_move"] == ""
    assert result["delta_sentence"] == ""
    assert result["delta_type"] == ""
    assert result["signature_terms"] == []
    assert result["landing_sentence"] == ""
    assert result["carryaway"] == ""


def test_missing_optional_fields_no_error():
    """只提供部分字段，不报错。"""
    data = {
        "title": "某本书",
        "author_move": "翻转了 X 假设",
    }
    result = extract_book_spine(data)

    assert result["author_move"] == "翻转了 X 假设"
    assert result["core_question"] == ""
    assert result["signature_terms"] == []


# ── 从 rounds 和 insights 中提取 core_question、landing_sentence ─────────

def test_core_question_from_rounds_fallback():
    """顶层无 core_question/topic 时，从 rounds 第一轮提取。"""
    data = {
        "rounds": [
            {"core_question": "制度与文化哪个优先？"},
            {"core_question": "第二轮问题"},
        ],
    }
    result = extract_book_spine(data)
    assert result["core_question"] == "制度与文化哪个优先？"


def test_core_question_from_rounds_topic_key():
    """rounds 第一轮只有 topic 时也能提取。"""
    data = {
        "rounds": [
            {"topic": "自由意志是否存在"},
        ],
    }
    result = extract_book_spine(data)
    assert result["core_question"] == "自由意志是否存在"


def test_landing_sentence_from_insights_fallback():
    """顶层无 landing_sentence 时，从 insights 第一条提取。"""
    data = {
        "insights": [
            {"insight_content": "认知模式才是关键变量", "insight_title": "认知升级"},
        ],
    }
    result = extract_book_spine(data)
    assert result["landing_sentence"] == "认知模式才是关键变量"


def test_carryaway_from_insights_fallback():
    """顶层无 carryaway 时，从 insights 第一条的 title 提取。"""
    data = {
        "insights": [
            {"insight_title": "重构认知框架", "insight_content": "详细内容"},
        ],
    }
    result = extract_book_spine(data)
    assert result["carryaway"] == "重构认知框架"


def test_top_level_fields_take_priority_over_rounds_and_insights():
    """顶层字段优先于 rounds/insights 的回退值。"""
    data = {
        "core_question": "顶层问题",
        "landing_sentence": "顶层落点",
        "carryaway": "顶层行囊",
        "rounds": [
            {"core_question": "轮次问题"},
        ],
        "insights": [
            {"insight_content": "洞见内容", "insight_title": "洞见标题"},
        ],
    }
    result = extract_book_spine(data)

    assert result["core_question"] == "顶层问题"
    assert result["landing_sentence"] == "顶层落点"
    assert result["carryaway"] == "顶层行囊"


def test_empty_rounds_and_insights_returns_defaults():
    """rounds 和 insights 为空列表时，回退字段仍为空字符串。"""
    data = {
        "rounds": [],
        "insights": [],
    }
    result = extract_book_spine(data)

    assert result["core_question"] == ""
    assert result["landing_sentence"] == ""
    assert result["carryaway"] == ""


def test_insights_with_content_and_title_keys():
    """insights 使用 content/title 键（非 insight_content/insight_title）。"""
    data = {
        "insights": [
            {"content": "用 content 键的内容", "title": "用 title 键的标题"},
        ],
    }
    result = extract_book_spine(data)
    assert result["landing_sentence"] == "用 content 键的内容"
    assert result["carryaway"] == "用 title 键的标题"
