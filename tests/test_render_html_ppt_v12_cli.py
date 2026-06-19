import json
import subprocess
import sys


def test_render_html_ppt_v12_cli_writes_valid_html(tmp_path):
    input_path = tmp_path / "input.json"
    output_path = tmp_path / "deck.html"
    input_path.write_text(json.dumps({
        "title": "测试圆桌",
        "subtitle": "稳定生成",
        "experts": [{"name": "专家1", "title": "研究者", "belief": "保持质疑"}],
        "rounds": [
            {
                "topic": "主题",
                "core_question": "问题",
                "stances": [{"expert": "专家1", "stance": "观点"}],
            }
        ],
        "insights": [{"insight_title": "洞见", "insight_content": "内容"}],
    }, ensure_ascii=False), encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, "engine/render_html_ppt_v12.py", str(input_path), "--output", str(output_path)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    html = output_path.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in html
    assert "测试圆桌" in html
    assert "HTML-PPT V12 validation passed" in completed.stdout
