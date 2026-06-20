from engine.html_ppt_open_design_planner import plan_open_design_pages


def test_showoff_planner_emits_display_logic_and_extreme_variants():
    data = {
        "title": "Test Book",
        "subtitle": "show-off deck",
        "insights": [{"insight_title": "No savior", "insight_content": "The core insight has a cost."}],
        "rounds": [
            {
                "topic": "Can a person be saved by another?",
                "core_question": "Who pays for salvation?",
                "stances": [
                    {"expert": "Expert A", "stance": "The savior myth hides cost."},
                    {"expert": "Expert B", "stance": "Systems create the conditions."},
                ],
                "clash_rounds": [
                    {
                        "attacker": "Expert A",
                        "target": "Expert B",
                        "attack_type": "cost challenge",
                        "attack_content": "Your explanation ignores the price.",
                        "defense": "The price is exactly the point.",
                    }
                ],
            }
        ],
    }

    pages = plan_open_design_pages(data, showoff=True)

    assert any(page.display_logic != "neutral" for page in pages if page.page_type != "cover")
    assert any(page.layout_variant.endswith("_extreme") for page in pages)


def test_regular_planner_keeps_legacy_reading_route():
    pages = plan_open_design_pages({"title": "Test", "rounds": []}, showoff=False)

    assert all(not page.layout_variant.endswith("_extreme") for page in pages)
