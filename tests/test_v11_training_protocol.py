from pathlib import Path

from engine.v11_training_protocol import (
    build_run_dir,
    slugify,
    write_training_markdown_pair,
)


def test_slugify_keeps_chinese_and_normalizes_symbols():
    assert slugify("AI 情感陪伴：年轻人还需要真实恋爱吗？") == "ai-情感陪伴-年轻人还需要真实恋爱吗"


def test_build_run_dir_uses_kind_and_date(tmp_path):
    run_dir = build_run_dir(tmp_path, "hot-topics", "2026-06-08")
    assert run_dir == tmp_path / "training_runs" / "2026-06-08-hot-topics"


def test_write_training_markdown_pair_creates_full_and_report(tmp_path):
    run_dir = tmp_path / "training_runs" / "2026-06-08-hot-topics"
    full_path, report_path = write_training_markdown_pair(
        run_dir=run_dir,
        topic_slug="ai-情感陪伴",
        full_content="# 完整日志\n",
        report_content="# 最终报告\n",
    )

    assert full_path.read_text(encoding="utf-8") == "# 完整日志\n"
    assert report_path.read_text(encoding="utf-8") == "# 最终报告\n"
    assert full_path.name == "ai-情感陪伴.full.md"
    assert report_path.name == "ai-情感陪伴.report.md"
