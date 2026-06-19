from engine.v11_roundtable_training import (
    RoundScore,
    TrainingRound,
    TrainingTopic,
    render_full_markdown,
    render_report_markdown,
)


def test_lowest_dimension_is_selected_from_scores():
    score = RoundScore(
        factual_robustness=8,
        insight_delta=7,
        conflict_strength=3,
        persona_consistency=8,
        structure=7,
        practical_usefulness=6,
        empty_talk_rate=2,
    )
    assert score.lowest_dimension() == "conflict_strength"


def test_render_full_markdown_keeps_original_and_rewrite():
    topic = TrainingTopic(
        title="AI 情感陪伴是否会替代真实亲密关系",
        definition="围绕 AI 伴侣、亲密关系和商业化的争议。",
        controversy_map="支持方认为它降低孤独，反对方认为它削弱真实关系。",
        experts=["弗洛姆", "尼采", "芒格", "项飙", "韩非子", "刘润"],
        rounds=[
            TrainingRound(
                round_number=1,
                purpose="立场建模",
                original="原稿内容",
                score=RoundScore(8, 6, 4, 8, 7, 6, 3),
                lowest_dimension="conflict_strength",
                rewrite_instruction="增强直接攻击。",
                rewritten="重写内容",
            )
        ],
        final_insights=["亲密关系的核心不是陪伴时长，而是互相承担现实后果。"],
    )

    full_md = render_full_markdown(topic)
    report_md = render_report_markdown(topic)

    assert "原稿内容" in full_md
    assert "重写内容" in full_md
    assert "增强直接攻击" in full_md
    assert "原稿内容" not in report_md
    assert "重写内容" in report_md
