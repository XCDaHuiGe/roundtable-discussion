from engine.html_ppt_depth import score_deep_content


def test_depth_score_rewards_complete_deep_model():
    model = {
        "author_problem": "Why does individual effort fail under structural constraint?",
        "consensus_baseline": "Common sense explains failure as weak will.",
        "author_delta": "The author moves the problem from willpower to conditions and loops.",
        "root_mechanism": "Resources, identity, and feedback loops shape the available action space.",
        "reality_cases": ["case A", "case B"],
        "counter_positions": ["Individual responsibility still matters."],
        "costs": ["This insight weakens simple blame."],
        "boundaries": ["It cannot explain every personal difference."],
        "transferable_insights": ["Look at structural conditions before judging choices."],
        "uncertainty_notes": ["The source cannot prove every long-term outcome."],
    }

    result = score_deep_content(model)

    assert result.score >= 85
    assert result.can_render is True


def test_depth_score_blocks_shallow_model():
    result = score_deep_content({
        "author_problem": "What is this book about?",
        "transferable_insights": ["深度思考"],
    })

    assert result.score < 70
    assert result.can_render is False
    assert "baseline_delta" in result.missing
