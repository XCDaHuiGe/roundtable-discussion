# -*- coding: utf-8 -*-
"""V11 训练 CLI。

第一阶段只消费 Agent 已准备好的 JSON，不在 Python 内部直接联网。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from engine.v11_roundtable_training import (
    RoundScore,
    TrainingRound,
    TrainingTopic,
    render_full_markdown,
    render_report_markdown,
)
from engine.v11_training_protocol import slugify, write_training_markdown_pair


def _topic_from_dict(data: dict) -> TrainingTopic:
    rounds = []
    for item in data["rounds"]:
        score = RoundScore(**item["score"])
        rounds.append(
            TrainingRound(
                round_number=item["round_number"],
                purpose=item["purpose"],
                original=item["original"],
                score=score,
                lowest_dimension=item.get("lowest_dimension") or score.lowest_dimension(),
                rewrite_instruction=item["rewrite_instruction"],
                rewritten=item["rewritten"],
            )
        )
    return TrainingTopic(
        title=data["title"],
        definition=data["definition"],
        controversy_map=data["controversy_map"],
        experts=data["experts"],
        rounds=rounds,
        final_insights=data["final_insights"],
    )


def run_from_prepared_json(input_path: Path, base_dir: Path) -> list[tuple[Path, Path]]:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    run_id = payload["run_id"]
    run_dir = base_dir / "training_runs" / run_id
    outputs = []
    for topic_data in payload["topics"]:
        topic = _topic_from_dict(topic_data)
        topic_slug = slugify(topic.title)
        outputs.append(
            write_training_markdown_pair(
                run_dir=run_dir,
                topic_slug=topic_slug,
                full_content=render_full_markdown(topic),
                report_content=render_report_markdown(topic),
            )
        )
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="V11 圆桌训练 Markdown 生成")
    parser.add_argument("--input", required=True, help="Agent 准备好的训练 JSON")
    parser.add_argument("--base-dir", default=".", help="项目根目录")
    args = parser.parse_args()

    outputs = run_from_prepared_json(Path(args.input), Path(args.base_dir))
    for full_path, report_path in outputs:
        print(f"[FULL] {full_path}")
        print(f"[REPORT] {report_path}")


if __name__ == "__main__":
    main()
