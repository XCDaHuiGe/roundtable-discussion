# -*- coding: utf-8 -*-
from engine.roundtable_engine.tension import assign_tension_axes
from engine.roundtable_engine.response_graph import build_response_graph
from engine.roundtable_engine.moderator import extract_moderator_summary


# ── 公共测试数据 ──────────────────────────────────────────────

def sample_rounds():
    """3 轮圆桌，部分字段缺失，用于测试补全逻辑。"""
    return [
        {
            "tension_axis": "自由意志 vs 决定论",
            "topic": "自由意志存在吗",
            "core_question": "人真的有选择吗？",
            "summary": "核心裂缝在于因果链与主观体验的不可调和",
            "speeches": [
                {"id": "r1s1", "expert": "萨特", "stance": "存在先于本质"},
                {"expert": "斯宾诺莎", "stance": "自由是无知的幻觉"},
            ],
        },
        {
            "topic": "制度如何塑造人性",
            "core_question": "制度与文化谁先谁后？",
            "summary": "制度与文化互为因果，打破线性归因",
            "guiding_question": "制度设计能改变文化吗？",
            "speeches": [
                {"expert": "韩非子", "stance": "人性趋利避害"},
                {"id": "r2s2", "expert": "孟子", "stance": "制度塑造而非改变本性", "responds_to": "r2s1"},
            ],
        },
        {
            "core_question": "认知升级的代价是什么？",
            "speeches": [
                {"expert": "王阳明", "stance": "知行合一需要实践痛苦"},
            ],
        },
    ]


# ── tension.py 测试 ──────────────────────────────────────────

def test_tension_axes_preserves_existing():
    """已有 tension_axis 的轮次应原样保留。"""
    rounds = sample_rounds()
    result = assign_tension_axes(rounds)
    assert result[0]["tension_axis"] == "自由意志 vs 决定论"


def test_tension_axes_fallback_to_topic():
    """没有 tension_axis 时，从 topic 提取。"""
    rounds = sample_rounds()
    result = assign_tension_axes(rounds)
    assert result[1]["tension_axis"] == "制度如何塑造人性"


def test_tension_axes_fallback_to_core_question():
    """没有 topic 时，从 core_question 提取。"""
    rounds = sample_rounds()
    result = assign_tension_axes(rounds)
    assert result[2]["tension_axis"] == "认知升级的代价是什么？"


def test_tension_axes_generates_placeholder():
    """所有来源都为空时，生成占位符。"""
    rounds = [{}]
    result = assign_tension_axes(rounds)
    assert result[0]["tension_axis"] == "第1轮张力"


# ── response_graph.py 测试 ───────────────────────────────────

def test_response_graph_first_speech_responds_to_none():
    """每轮首条发言的 responds_to 应为 None。"""
    rounds = sample_rounds()
    result = build_response_graph(rounds)
    assert result[0]["speeches"][0]["responds_to"] is None
    assert result[1]["speeches"][0]["responds_to"] is None
    assert result[2]["speeches"][0]["responds_to"] is None


def test_response_graph_subsequent_speeches_have_responds_to():
    """后续发言应有 responds_to 指向前一条。"""
    rounds = sample_rounds()
    result = build_response_graph(rounds)
    # 第1轮第2条：responds_to 应为 r1s1
    assert result[0]["speeches"][1]["responds_to"] == "r1s1"
    # 第2轮第2条：已有 responds_to="r2s1"，应保留
    assert result[1]["speeches"][1]["responds_to"] == "r2s1"


def test_response_graph_generates_ids():
    """没有 id 的发言应自动生成。"""
    rounds = sample_rounds()
    result = build_response_graph(rounds)
    # 第1轮第2条没有 id，应生成 r1s2
    assert result[0]["speeches"][1]["id"] == "r1s2"
    # 第2轮第1条没有 id，应生成 r2s1
    assert result[1]["speeches"][0]["id"] == "r2s1"


def test_response_graph_preserves_existing_ids():
    """已有 id 的发言应保留原 id。"""
    rounds = sample_rounds()
    result = build_response_graph(rounds)
    assert result[0]["speeches"][0]["id"] == "r1s1"
    assert result[1]["speeches"][1]["id"] == "r2s2"


# ── moderator.py 测试 ────────────────────────────────────────

def test_moderator_preserves_existing_core_crack():
    """已有 moderator.core_crack 且非空时应保留。"""
    rounds = [
        {
            "moderator": {"core_crack": "已有裂缝", "structure_map": "", "next_question": ""},
            "summary": "这个摘要不应被使用",
        }
    ]
    result = extract_moderator_summary(rounds)
    assert result[0]["moderator"]["core_crack"] == "已有裂缝"


def test_moderator_fallback_to_summary():
    """moderator.core_crack 为空时，从 summary 提取。"""
    rounds = sample_rounds()
    result = extract_moderator_summary(rounds)
    assert result[1]["moderator"]["core_crack"] == "制度与文化互为因果，打破线性归因"


def test_moderator_next_question_from_next_round():
    """当前轮 next_question 为空时，从下一轮 guiding_question 提取。"""
    rounds = sample_rounds()
    result = extract_moderator_summary(rounds)
    # 第1轮的 next_question 应来自第2轮的 guiding_question
    assert result[0]["moderator"]["next_question"] == "制度设计能改变文化吗？"


def test_moderator_last_round_next_question_empty():
    """最后一轮没有下一轮，next_question 应为空。"""
    rounds = sample_rounds()
    result = extract_moderator_summary(rounds)
    assert result[2]["moderator"]["next_question"] == ""


def test_moderator_ensures_structure_map():
    """moderator 应始终有 structure_map 字段。"""
    rounds = sample_rounds()
    result = extract_moderator_summary(rounds)
    for r in result:
        assert "structure_map" in r["moderator"]


# ── 完整流程测试 ──────────────────────────────────────────────

def test_full_pipeline_3_rounds():
    """完整流程：3 轮圆桌 → 每轮有 tension_axis、moderator、回应关系。"""
    rounds = sample_rounds()

    rounds = assign_tension_axes(rounds)
    rounds = build_response_graph(rounds)
    rounds = extract_moderator_summary(rounds)

    assert len(rounds) == 3

    for i, r in enumerate(rounds, start=1):
        # 每轮有 tension_axis 且非空
        assert r.get("tension_axis"), f"第{i}轮缺少 tension_axis"

        # 每轮有 moderator 且含三个子字段
        mod = r.get("moderator", {})
        assert "core_crack" in mod, f"第{i}轮 moderator 缺少 core_crack"
        assert "structure_map" in mod, f"第{i}轮 moderator 缺少 structure_map"
        assert "next_question" in mod, f"第{i}轮 moderator 缺少 next_question"

        # 每轮发言有 id 和 responds_to
        for s in r.get("speeches", []):
            assert s.get("id"), f"第{i}轮有发言缺少 id"
            assert "responds_to" in s, f"第{i}轮有发言缺少 responds_to"
