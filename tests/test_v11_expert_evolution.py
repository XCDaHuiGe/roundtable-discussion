from engine.v11_expert_evolution import ExpertUpdate, append_expert_updates, render_update_block


def test_render_update_block_contains_traceability():
    update = ExpertUpdate(
        expert_name="弗洛姆",
        layer="素材层",
        update_type="高分发言",
        topic="AI 情感陪伴是否会替代真实亲密关系",
        round_number=3,
        score_basis="洞见增量 9/10，人格一致性 8/10",
        content="亲密不是持续陪伴，而是共同承担自由带来的焦虑。",
    )

    block = render_update_block(update, run_id="2026-06-08-hot-topics")
    assert "V11 自动训练沉淀" in block
    assert "素材层" in block
    assert "2026-06-08-hot-topics" in block
    assert "亲密不是持续陪伴" in block


def test_append_expert_updates_adds_block(tmp_path):
    expert_path = tmp_path / "弗洛姆.md"
    expert_path.write_text("# 弗洛姆\n\n## 素材层\n", encoding="utf-8")

    update = ExpertUpdate(
        expert_name="弗洛姆",
        layer="素材层",
        update_type="高分发言",
        topic="AI 情感陪伴",
        round_number=2,
        score_basis="人格一致性 9/10",
        content="逃避孤独不等于获得爱。",
    )
    append_expert_updates(expert_path, [update], run_id="run-1")

    text = expert_path.read_text(encoding="utf-8")
    assert "逃避孤独不等于获得爱" in text
    assert "run-1" in text
