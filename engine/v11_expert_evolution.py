# -*- coding: utf-8 -*-
"""V11 专家库标准更新器。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ExpertUpdate:
    expert_name: str
    layer: str
    update_type: str
    topic: str
    round_number: int
    score_basis: str
    content: str


def render_update_block(update: ExpertUpdate, run_id: str) -> str:
    return (
        "\n\n### V11 自动训练沉淀\n"
        f"- 来源 run: {run_id}\n"
        f"- 话题: {update.topic}\n"
        f"- 轮次: 第 {update.round_number} 轮\n"
        f"- 层级: {update.layer}\n"
        f"- 类型: {update.update_type}\n"
        f"- 评分依据: {update.score_basis}\n"
        f"- 内容: {update.content}\n"
    )


def append_expert_updates(expert_path: Path, updates: list[ExpertUpdate], run_id: str) -> None:
    if not expert_path.exists():
        raise FileNotFoundError(f"专家文件不存在: {expert_path}")
    text = expert_path.read_text(encoding="utf-8")
    blocks = [render_update_block(update, run_id) for update in updates]
    expert_path.write_text(text.rstrip() + "".join(blocks) + "\n", encoding="utf-8", newline="\n")
