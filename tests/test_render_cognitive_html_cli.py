import json
import subprocess
import sys


def test_render_cognitive_html_cli_generates_valid_html(tmp_path):
    input_path = tmp_path / "sample_v8.json"
    output_path = tmp_path / "sample.html"
    input_path.write_text(
        json.dumps(
            {
                "title": "测试书",
                "subtitle": "测试副标题",
                "experts": [{"name": "专家A", "core_belief": "定义问题"}],
                "rounds": [
                    {
                        "topic": "问题",
                        "core_question": "问题是什么？",
                        "stances": [{"expert": "专家A", "stance": "先定义问题。"}],
                    }
                ],
                "insights": [{"insight_title": "洞见", "insight_content": "洞见内容。"}],
                "open_questions": ["下一问？"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "engine/render_cognitive_html.py", str(input_path), "--output", str(output_path)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    html = output_path.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in html
    assert 'data-page-type="cover"' in html
    assert "HTML-PPT cognitive validation passed" in result.stdout
