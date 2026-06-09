import pytest

from engine.html_ppt_v12 import Page, ensure_page_type, split_text
from engine.html_ppt_v12_planner import plan_pages


def test_split_text_keeps_short_text_as_one_chunk():
    assert split_text("短文本", 20) == ["短文本"]


def test_split_text_prefers_chinese_sentence_boundaries():
    text = "第一句很重要。第二句也重要。第三句继续推进。"
    assert split_text(text, 12) == [
        "第一句很重要。",
        "第二句也重要。",
        "第三句继续推进。",
    ]


def test_ensure_page_type_rejects_unknown_type():
    with pytest.raises(ValueError, match="unknown page_type"):
        ensure_page_type("random_html")


def test_page_rejects_unknown_type():
    with pytest.raises(ValueError, match="unknown page_type"):
        Page(page_type="bad", title="Bad")


def sample_roundtable():
    return {
        "title": "《测试书》圆桌洞见",
        "subtitle": "六位专家讨论一个复杂问题",
        "experts": [
            {"name": f"专家{i}", "title": "思想家", "belief": "核心信念" * 20}
            for i in range(1, 7)
        ],
        "rounds": [
            {
                "topic": "第一轮主题",
                "core_question": "真正的问题是什么？",
                "stances": [
                    {"expert": f"专家{i}", "stance": "这是一个很长的观点。" * 20}
                    for i in range(1, 7)
                ],
                "clash_rounds": [
                    {
                        "attacker": "专家1",
                        "target": "专家2",
                        "attack_type": "逻辑攻击",
                        "attack_content": "攻击内容。" * 30,
                        "defense": "回应内容。" * 30,
                    }
                ],
            }
        ],
        "insights": [
            {"insight_title": "洞见一", "insight_content": "洞见内容。" * 30}
        ],
        "open_questions": ["开放问题。" * 20],
    }


def test_plan_pages_creates_core_page_sequence():
    pages = plan_pages(sample_roundtable())
    page_types = [p.page_type for p in pages]
    assert page_types[0] == "cover"
    assert "experts" in page_types
    assert "round_overview" in page_types
    assert "speech" in page_types
    assert "clash" in page_types
    assert page_types[-1] == "summary"


def test_plan_pages_splits_six_speeches_into_three_pages():
    pages = plan_pages(sample_roundtable())
    speech_pages = [p for p in pages if p.page_type == "speech"]
    assert len(speech_pages) == 3
    assert all(len(p.items) <= 2 for p in speech_pages)
    assert all(len(item["text"]) <= 220 for p in speech_pages for item in p.items)


def test_plan_pages_splits_long_clash_fields():
    pages = plan_pages(sample_roundtable())
    clash_pages = [p for p in pages if p.page_type == "clash"]
    assert len(clash_pages) >= 1
    assert all(len(item["attack"]) <= 180 for p in clash_pages for item in p.items)
    assert all(len(item["defense"]) <= 180 for p in clash_pages for item in p.items)
