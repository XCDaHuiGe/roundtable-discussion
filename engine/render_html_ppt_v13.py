# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.html_ppt_v13_planner import plan_reading_pages
from engine.html_ppt_v13_renderer import render_reading_html
from engine.validate_html_ppt_v13 import validate_reading_html


def render_file(input_path: Path, output_path: Path, theme: str = "editorial") -> int:
    data = _read_json(input_path)
    pages = plan_reading_pages(data)
    html = render_reading_html(pages, title=data.get("title", "圆桌洞见"), theme=theme)
    result = validate_reading_html(html)
    if not result.ok:
        print("HTML-PPT V13 validation failed")
        for error in result.errors:
            print(f"- {error}")
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print("HTML-PPT V13 validation passed")
    print(f"[GENERATED] {len(pages)} readable pages")
    print(f"[SAVE] {output_path}")
    return 0


def _read_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("input JSON must be an object")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a readable HTML-PPT V13 deck")
    parser.add_argument("json_path", help="Input roundtable JSON path")
    parser.add_argument("--output", "-o", help="Output HTML path")
    parser.add_argument(
        "--theme",
        choices=["editorial", "obsidian", "blueprint"],
        default="editorial",
        help="Visual theme: editorial=杂志报告, obsidian=高端暗黑, blueprint=蓝图分析",
    )
    args = parser.parse_args()

    input_path = Path(args.json_path)
    if not input_path.exists():
        print(f"input JSON not found: {input_path}")
        return 1

    output_path = Path(args.output) if args.output else Path("output") / f"{input_path.stem}_v13.html"
    return render_file(input_path, output_path, theme=args.theme)


if __name__ == "__main__":
    raise SystemExit(main())
