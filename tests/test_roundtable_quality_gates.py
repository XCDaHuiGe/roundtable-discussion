from engine.cognitive_model.schema import CognitiveModel
from engine.quality_gates.roundtable_quality import validate_roundtable_quality


def test_roundtable_quality_requires_responses_after_first_speech():
    model = CognitiveModel(title="测试书")
    model.roundtable.participants = [{"name": "A", "function": "定义问题"}]
    model.roundtable.rounds = [
        {
            "round_index": 1,
            "guiding_question": "问题？",
            "tension_axis": "个人选择 / 结构约束",
            "speeches": [
                {"id": "r1s1", "expert": "A", "responds_to": None, "action_type": "definition"},
                {"id": "r1s2", "expert": "B", "responds_to": None, "action_type": "response"},
            ],
            "moderator": {"core_crack": "裂缝", "next_question": "下一问？"},
        }
    ]

    result = validate_roundtable_quality(model)
    codes = {issue["code"] for issue in result["errors"]}

    assert "missing_response_link" in codes


def test_roundtable_quality_passes_when_round_has_tension_responses_and_moderator():
    model = CognitiveModel(title="测试书")
    model.roundtable.participants = [{"name": "A", "function": "定义问题"}]
    model.roundtable.rounds = [
        {
            "round_index": 1,
            "guiding_question": "问题？",
            "tension_axis": "个人选择 / 结构约束",
            "speeches": [
                {"id": "r1s1", "expert": "A", "responds_to": None, "action_type": "definition"},
                {"id": "r1s2", "expert": "B", "responds_to": "r1s1", "action_type": "response"},
            ],
            "moderator": {"core_crack": "裂缝", "next_question": "下一问？"},
        }
    ]

    result = validate_roundtable_quality(model)

    assert result["ok"] is True


def test_roundtable_quality_warns_on_placeholder_tension_axis():
    """张力轴为占位符 → warning（不影响 ok）"""
    model = CognitiveModel(title="测试书")
    model.roundtable.participants = [{"name": "A", "function": "定义问题"}]
    model.roundtable.rounds = [
        {
            "round_index": 1,
            "guiding_question": "问题？",
            "tension_axis": "第1轮张力",  # 占位符
            "speeches": [
                {"id": "r1s1", "expert": "A", "responds_to": None, "action_type": "definition"},
            ],
            "moderator": {"core_crack": "裂缝", "next_question": "下一问？"},
        }
    ]

    result = validate_roundtable_quality(model)
    codes = {issue["code"] for issue in result["errors"]}
    levels = {issue["level"] for issue in result["errors"]}

    assert "placeholder_tension_axis" in codes
    assert "warning" in levels
    # warning 不影响 ok
    assert result["ok"] is True


def test_roundtable_quality_passes_on_real_tension_axis():
    """张力轴为真实内容 → 通过"""
    model = CognitiveModel(title="测试书")
    model.roundtable.participants = [{"name": "A", "function": "定义问题"}]
    model.roundtable.rounds = [
        {
            "round_index": 1,
            "guiding_question": "问题？",
            "tension_axis": "个人自由 vs 社会责任",  # 真实张力轴
            "speeches": [
                {"id": "r1s1", "expert": "A", "responds_to": None, "action_type": "definition"},
            ],
            "moderator": {"core_crack": "裂缝", "next_question": "下一问？"},
        }
    ]

    result = validate_roundtable_quality(model)

    assert result["ok"] is True
    codes = {issue["code"] for issue in result["errors"]}
    assert "placeholder_tension_axis" not in codes


def test_roundtable_quality_allows_empty_next_question_in_last_round():
    """最后一轮 next_question 为空 → 通过"""
    model = CognitiveModel(title="测试书")
    model.roundtable.participants = [{"name": "A", "function": "定义问题"}]
    model.roundtable.rounds = [
        {
            "round_index": 1,
            "tension_axis": "张力1",
            "speeches": [
                {"id": "r1s1", "expert": "A", "responds_to": None, "action_type": "definition"},
            ],
            "moderator": {"core_crack": "裂缝1", "next_question": "下一问？"},
        },
        {
            "round_index": 2,
            "tension_axis": "张力2",
            "speeches": [
                {"id": "r2s1", "expert": "A", "responds_to": None, "action_type": "definition"},
            ],
            "moderator": {"core_crack": "裂缝2", "next_question": ""},  # 最后一轮可以为空
        }
    ]

    result = validate_roundtable_quality(model)

    assert result["ok"] is True
    codes = {issue["code"] for issue in result["errors"]}
    assert "missing_next_question" not in codes


def test_roundtable_quality_errors_on_missing_next_question_in_non_last_round():
    """非最后一轮 next_question 为空 → error"""
    model = CognitiveModel(title="测试书")
    model.roundtable.participants = [{"name": "A", "function": "定义问题"}]
    model.roundtable.rounds = [
        {
            "round_index": 1,
            "tension_axis": "张力1",
            "speeches": [
                {"id": "r1s1", "expert": "A", "responds_to": None, "action_type": "definition"},
            ],
            "moderator": {"core_crack": "裂缝1", "next_question": ""},  # 第一轮不能为空
        },
        {
            "round_index": 2,
            "tension_axis": "张力2",
            "speeches": [
                {"id": "r2s1", "expert": "A", "responds_to": None, "action_type": "definition"},
            ],
            "moderator": {"core_crack": "裂缝2", "next_question": "下一问？"},
        }
    ]

    result = validate_roundtable_quality(model)
    codes = {issue["code"] for issue in result["errors"]}

    assert "missing_next_question" in codes
    assert result["ok"] is False
