from engine.html_ppt_v13_planner import plan_reading_pages


def sample_data():
    return {
        "title": "《测试书》圆桌洞见",
        "subtitle": "文化属性与命运",
        "experts": [{"name": f"专家{i}", "title": "思想家", "core_belief": "核心信念"} for i in range(1, 7)],
        "rounds": [
            {
                "topic": "文化属性真的决定命运吗",
                "core_question": "文化是原因还是结果？",
                "stances": [
                    {"expert": "丁元英", "stance": "文化属性决定行动方式。"},
                    {"expert": "韩非子", "stance": "制度和法律才决定路径。"},
                    {"expert": "马克思", "stance": "资本和生产关系放大结果。"},
                    {"expert": "老子", "stance": "道法自然，规律不可违。"},
                    {"expert": "芒格", "stance": "复杂问题需要多元模型。"},
                    {"expert": "尼采", "stance": "选择来自强力意志。"},
                ],
                "clash_rounds": [
                    {
                        "attacker": "马克思",
                        "target": "丁元英",
                        "attack_type": "因果倒置",
                        "attack_content": "文化解释掩盖了资本结构。",
                        "defense": "规律不是资本发明的。",
                    }
                ],
            }
        ],
        "insights": [
            {"insight_title": "文化属性不是宿命", "insight_content": "文化属性更像情境应对系统。"},
            {"insight_title": "合法不等于合情", "insight_content": "杀富济贫暴露法律和人性的裂缝。"},
            {"insight_title": "理性也有井底", "insight_content": "如实观照也有认知边界。"},
        ],
        "open_questions": ["弱势文化是原因还是结果？"],
    }


def test_plan_reading_pages_creates_reading_page_family():
    pages = plan_reading_pages(sample_data())
    page_types = [page.page_type for page in pages]
    assert page_types[0] == "cover"
    assert "insight_reading" in page_types
    assert "roundtable_reading" in page_types
    assert "clash_reading" in page_types
    assert page_types[-1] == "summary_reading"


def test_roundtable_reading_page_has_six_stance_blocks_and_takeaway():
    pages = plan_reading_pages(sample_data())
    page = next(p for p in pages if p.page_type == "roundtable_reading")
    stance_blocks = [block for block in page.blocks if block.kind == "stance"]
    assert len(stance_blocks) == 6
    assert page.layout == "stance_spectrum"
    assert page.takeaway
    assert {block.label for block in stance_blocks} >= {"文化解释", "制度解释", "资本解释", "规律解释"}


def test_clash_reading_page_has_attack_defense_essence_and_takeaway():
    pages = plan_reading_pages(sample_data())
    page = next(p for p in pages if p.page_type == "clash_reading")
    kinds = {block.kind for block in page.blocks}
    assert {"attack", "defense", "essence"} <= kinds
    assert page.takeaway
