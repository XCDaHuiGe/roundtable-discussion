from engine.cognitive_model.schema import CognitiveModel
from engine.html_ppt.cognitive_page_planner import plan_cognitive_pages


def sample_model():
    model = CognitiveModel(title="测试书")
    model.book_spine.core_question = "人为什么误把适应当命运？"
    model.book_spine.consensus_baseline = "旧共识把命运归因于意志。"
    model.book_spine.author_move = "作者把问题转向脑的适应机制。"
    model.book_spine.delta_sentence = "之前大家以为命运来自意志强弱，作者说命运来自脑的适应回路。"
    model.root_rank.root_generators = ["适应回路"]
    model.root_rank.candidate_generators = ["奖励回路", "注意力筛选"]
    model.root_rank.regeneration_matrix = [
        {"generator": "适应回路", "phenomenon": "习惯形成"},
        {"generator": "适应回路", "phenomenon": "情绪反应"},
        {"generator": "适应回路", "phenomenon": "学习迁移"},
    ]
    model.distillation.qa_chain = [
        {"question": "问题是什么？", "answer": {"conclusion": "适应被误读。", "boundary": "不解释全部人生。"}}
    ]
    model.distillation.insights = [{"title": "适应不是宿命", "content": "它是可被重新训练的回路。"}]
    model.roundtable.rounds = [
        {
            "round_index": 1,
            "guiding_question": "适应是否能改变？",
            "tension_axis": "神经机制 / 行动选择",
            "speeches": [
                {"id": "r1s1", "expert": "神经科学家", "claim": "脑会重塑。", "action_type": "definition"},
                {"id": "r1s2", "expert": "哲学家", "claim": "选择需要意识。", "responds_to": "r1s1", "action_type": "response"},
            ],
            "moderator": {"core_crack": "机制解释不能替代行动选择。", "next_question": "训练从哪里开始？"},
        }
    ]
    return model


def test_plan_cognitive_pages_includes_new_page_family():
    pages = plan_cognitive_pages(sample_model())
    types = [page.page_type for page in pages]

    assert types[0] == "cover"
    assert "core_question" in types
    assert "baseline_delta" in types
    assert "rank_map" in types
    assert "response_graph" in types
    assert "qa" in types
    assert types[-1] == "ending"


def test_planned_pages_use_v13_reading_page_contracts():
    pages = plan_cognitive_pages(sample_model())

    assert all(page.title for page in pages)
    assert all(page.takeaway for page in pages)
    assert all(page.layout in {"reading_brief_4zone", "stance_spectrum"} for page in pages)
