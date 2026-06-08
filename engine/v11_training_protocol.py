# -*- coding: utf-8 -*-
"""V11 本地训练产物协议。"""

from __future__ import annotations

import re
from pathlib import Path


def slugify(value: str, max_length: int = 80) -> str:
    """生成适合文件名的短 slug，保留中文。"""
    value = value.strip().lower()
    value = re.sub(r"[\\/:*?\"<>|，。、“”‘’！!？?；;：:（）()\[\]{}]+", "-", value)
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    if not value:
        value = "topic"
    return value[:max_length].rstrip("-")


def build_run_dir(base_dir: Path, run_kind: str, run_date: str) -> Path:
    """返回训练运行目录，不负责写入 Git。"""
    return base_dir / "training_runs" / f"{run_date}-{run_kind}"


def write_training_markdown_pair(
    run_dir: Path,
    topic_slug: str,
    full_content: str,
    report_content: str,
) -> tuple[Path, Path]:
    """写入 full/report 两个训练 Markdown 文件。"""
    run_dir.mkdir(parents=True, exist_ok=True)
    full_path = run_dir / f"{topic_slug}.full.md"
    report_path = run_dir / f"{topic_slug}.report.md"
    full_path.write_text(full_content, encoding="utf-8", newline="\n")
    report_path.write_text(report_content, encoding="utf-8", newline="\n")
    return full_path, report_path
