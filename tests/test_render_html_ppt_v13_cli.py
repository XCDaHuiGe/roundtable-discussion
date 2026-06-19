import json
import subprocess
import sys


def test_render_html_ppt_v13_cli_outputs_reading_deck(tmp_path):
    input_path = tmp_path / "input.json"
    output_path = tmp_path / "deck.html"
    input_path.write_text(json.dumps({
        "title": "测试圆桌",
        "subtitle": "阅读型 PPT",
        "experts": [{"name": "专家1"}],
        "rounds": [{
            "topic": "文化属性真的决定命运吗",
            "core_question": "文化是原因还是结果？",
            "stances": [
                {"expert": "丁元英", "stance": "文化属性决定行动方式。"},
                {"expert": "韩非子", "stance": "制度和法律塑造路径。"},
                {"expert": "马克思", "stance": "资本和生产关系放大结果。"},
                {"expert": "老子", "stance": "道法自然，规律不可违。"},
                {"expert": "芒格", "stance": "复杂问题需要多元模型。"},
            ],
        }],
        "insights": [
            {"insight_title": "洞见一", "insight_content": "内容一"},
            {"insight_title": "洞见二", "insight_content": "内容二"},
            {"insight_title": "洞见三", "insight_content": "内容三"},
        ],
    }, ensure_ascii=False), encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, "engine/render_html_ppt_v13.py", str(input_path), "--output", str(output_path)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    html = output_path.read_text(encoding="utf-8")
    assert "HTML-PPT V13 validation passed" in completed.stdout
    assert "阅读重点" in html
    assert "最终洞见" in html
