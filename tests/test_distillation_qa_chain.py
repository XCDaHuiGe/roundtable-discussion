# -*- coding: utf-8 -*-
from engine.distillation.qa_chain import build_qa_chain


def test_existing_qa_chain_returned_directly():
    """已有 qa_chain 且格式正确时，直接返回原对象。"""
    existing = [
        {
            "question": "什么是关键问题？",
            "answer": {"conclusion": "结论A", "formalization": "", "steps": [], "boundary": "边界A"},
            "depends_on": None,
        },
        {
            "question": "第二问？",
            "answer": {"conclusion": "结论B", "formalization": "", "steps": [], "boundary": "边界B"},
            "depends_on": "什么是关键问题？",
        },
    ]
    result = build_qa_chain({"qa_chain": existing, "insights": [{"title": "不应使用", "content": "x"}]})
    assert result is existing
    assert len(result) == 2


def test_build_from_insights_chain_order_and_depends_on():
    """从 insights 构建时，顺序与输入一致，depends_on 链式。"""
    data = {
        "insights": [
            {"title": "洞见一", "content": "内容一", "evidence": "证据一"},
            {"title": "洞见二", "content": "内容二", "evidence": "证据二"},
            {"title": "洞见三", "content": "内容三", "evidence": "证据三"},
        ],
    }
    result = build_qa_chain(data)

    assert len(result) == 3
    assert result[0]["question"] == "洞见一"
    assert result[0]["depends_on"] is None
    assert result[1]["question"] == "洞见二"
    assert result[1]["depends_on"] == "洞见一"
    assert result[2]["question"] == "洞见三"
    assert result[2]["depends_on"] == "洞见二"


def test_build_from_insights_and_rounds_merged():
    """insights 先，rounds 补充，去重。"""
    data = {
        "insights": [
            {"title": "已有的问题", "content": "答", "evidence": ""},
        ],
        "rounds": [
            {"core_question": "已有的问题", "summary": "重复的"},
            {"core_question": "新问题", "summary": "补充回答"},
        ],
    }
    result = build_qa_chain(data)

    assert len(result) == 2
    assert result[0]["question"] == "已有的问题"
    assert result[1]["question"] == "新问题"
    assert result[1]["depends_on"] == "已有的问题"


def test_empty_input_returns_empty_list():
    """空输入返回空列表。"""
    assert build_qa_chain({}) == []
    assert build_qa_chain({"insights": [], "rounds": []}) == []


def test_each_answer_has_conclusion_and_boundary():
    """每个 answer 必须有 conclusion 和 boundary 字段。"""
    data = {
        "insights": [
            {"title": "Q1", "content": "C1", "evidence": "E1"},
        ],
        "rounds": [
            {"core_question": "Q2", "summary": "S2"},
        ],
    }
    result = build_qa_chain(data)

    for item in result:
        answer = item["answer"]
        assert "conclusion" in answer
        assert "boundary" in answer


def test_invalid_existing_chain_falls_through():
    """已有的 qa_chain 格式不正确时，走正常构建流程。"""
    data = {
        "qa_chain": [{"bad": "format"}],
        "insights": [{"title": "正常问题", "content": "正常回答", "evidence": ""}],
    }
    result = build_qa_chain(data)

    assert len(result) == 1
    assert result[0]["question"] == "正常问题"


def test_rounds_uses_topic_fallback():
    """rounds 没有 core_question 时回退到 topic。"""
    data = {
        "rounds": [
            {"topic": "主题问题", "summary": "主题回答"},
        ],
    }
    result = build_qa_chain(data)

    assert len(result) == 1
    assert result[0]["question"] == "主题问题"
    assert result[0]["answer"]["conclusion"] == "主题回答"


def test_insights_uses_insight_title_fallback():
    """insights 使用 insight_title 作为兼容字段名。"""
    data = {
        "insights": [
            {"insight_title": "兼容标题", "insight_content": "兼容内容", "evidence": ""},
        ],
    }
    result = build_qa_chain(data)

    assert len(result) == 1
    assert result[0]["question"] == "兼容标题"
    assert result[0]["answer"]["conclusion"] == "兼容内容"


def test_empty_title_insight_skipped():
    """title 为空的 insight 被跳过。"""
    data = {
        "insights": [
            {"title": "", "content": "内容"},
            {"title": "有效", "content": "有效内容"},
        ],
    }
    result = build_qa_chain(data)

    assert len(result) == 1
    assert result[0]["question"] == "有效"
