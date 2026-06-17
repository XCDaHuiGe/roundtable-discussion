from engine.cognitive_model.adapters import from_v8


def sample_v8():
    return {
        "title": "《测试书》圆桌洞见",
        "subtitle": "文化属性与命运",
        "experts": [
            {"name": "丁元英", "title": "思想者", "core_belief": "如实观照"},
            {"name": "韩非子", "title": "法家", "core_belief": "制度约束"},
        ],
        "rounds": [
            {
                "topic": "文化属性真的决定命运吗",
                "core_question": "文化是原因还是结果？",
                "stances": [
                    {"expert": "丁元英", "stance": "文化属性决定行动方式。"},
                    {"expert": "韩非子", "stance": "制度才决定路径。"},
                ],
                "clash_rounds": [
                    {
                        "attacker": "韩非子",
                        "target": "丁元英",
                        "attack_type": "制度优先",
                        "attack_content": "文化解释掩盖规则缺失。",
                        "defense": "规则也来自长期文化选择。",
                    }
                ],
            }
        ],
        "insights": [
            {"insight_title": "文化不是宿命", "insight_content": "文化更像行动系统。"}
        ],
        "open_questions": ["弱势文化是原因还是结果？"],
    }


def test_from_v8_preserves_title_experts_rounds_and_insights():
    model = from_v8(sample_v8())

    assert model.title == "《测试书》圆桌洞见"
    assert model.source_type == "book"
    assert model.book_spine.core_question == "文化是原因还是结果？"
    assert model.roundtable.participants[0]["name"] == "丁元英"
    assert model.roundtable.rounds[0]["guiding_question"] == "文化是原因还是结果？"
    assert model.distillation.insights[0]["title"] == "文化不是宿命"
    assert model.distillation.open_questions == ["弱势文化是原因还是结果？"]


def test_from_v8_marks_missing_deep_fields_as_warnings():
    model = from_v8(sample_v8())
    codes = {issue.code for issue in model.quality.checks}

    assert "partial_model" in codes
    assert "missing_delta_sentence" in codes
    assert "missing_root_rank" in codes
    assert "missing_qa_chain" in codes
