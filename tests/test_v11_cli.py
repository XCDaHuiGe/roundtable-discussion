import json

from engine.v11_cli import run_from_prepared_json


def test_run_from_prepared_json_writes_training_files(tmp_path):
    prepared = {
        "run_id": "2026-06-08-hot-topics",
        "topics": [
            {
                "title": "AI 情感陪伴是否会替代真实亲密关系",
                "definition": "围绕 AI 伴侣和真实亲密关系的争议。",
                "controversy_map": "支持方认为降低孤独，反对方认为削弱现实关系。",
                "experts": ["弗洛姆", "尼采", "芒格", "项飙", "韩非子", "刘润"],
                "rounds": [
                    {
                        "round_number": 1,
                        "purpose": "立场建模",
                        "original": "原稿",
                        "score": {
                            "factual_robustness": 8,
                            "insight_delta": 7,
                            "conflict_strength": 5,
                            "persona_consistency": 8,
                            "structure": 7,
                            "practical_usefulness": 6,
                            "empty_talk_rate": 3,
                        },
                        "lowest_dimension": "conflict_strength",
                        "rewrite_instruction": "增强交叉攻击。",
                        "rewritten": "重写稿",
                    }
                ],
                "final_insights": ["真实亲密关系包含后果共担。"],
            }
        ],
    }
    input_path = tmp_path / "prepared.json"
    input_path.write_text(json.dumps(prepared, ensure_ascii=False), encoding="utf-8")

    outputs = run_from_prepared_json(input_path=input_path, base_dir=tmp_path)

    assert len(outputs) == 1
    full_path, report_path = outputs[0]
    assert full_path.exists()
    assert report_path.exists()
    assert "原稿" in full_path.read_text(encoding="utf-8")
    assert "重写稿" in report_path.read_text(encoding="utf-8")
