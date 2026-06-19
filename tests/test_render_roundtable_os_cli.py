import json
import subprocess
import sys


def test_render_roundtable_os_cli_generates_valid_html(tmp_path):
    input_path = tmp_path / "sample.json"
    output_path = tmp_path / "sample.html"
    input_path.write_text(
        json.dumps(
            {
                "title": "Sample Book",
                "subtitle": "Sample subtitle",
                "experts": [{"name": "Expert A", "title": "Framer", "core_belief": "Define the question first."}],
                "rounds": [
                    {
                        "topic": "Question",
                        "core_question": "What is the real question?",
                        "stances": [{"expert": "Expert A", "stance": "Define the question before answering."}],
                    }
                ],
                "insights": [{"insight_title": "Insight", "insight_content": "A useful answer starts with a sharper frame."}],
                "open_questions": ["What should be tested next?"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "engine/render_roundtable_os.py", str(input_path), "--output", str(output_path)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    html = output_path.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in html
    assert 'data-page-type="cover"' in html
    assert "Roundtable OS validation passed" in result.stdout
