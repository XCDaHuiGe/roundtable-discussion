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
