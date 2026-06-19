# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.cognitive_model.adapters import from_v8
from engine.html_ppt.cognitive_page_planner import plan_cognitive_pages
from engine.html_ppt_v13_renderer import render_reading_html
from engine.validate_html_ppt_v13 import validate_reading_html


def render_file(input_path: Path, output_path: Path, theme: str = "editorial") -> int:
    data = _read_json(input_path)
    model = from_v8(data)
    pages = plan_cognitive_pages(model)
    html = render_reading_html(pages, title=model.title, theme=theme)
    result = validate_reading_html(html)
    if not result.ok:
        print("Roundtable OS validation failed")
        for error in result.errors:
            print(f"- {error}")
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print("Roundtable OS validation passed")
    print(f"[GENERATED] {len(pages)} pages")
    print(f"[SAVE] {output_path}")
    return 0


def _read_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("input JSON must be an object")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a Roundtable OS HTML-PPT deck")
    parser.add_argument("json_path", help="Input roundtable JSON path")
    parser.add_argument("--output", "-o", help="Output HTML path")
    parser.add_argument(
        "--theme",
        choices=["editorial", "obsidian", "blueprint"],
        default="editorial",
        help="Visual theme for the unified HTML-PPT renderer",
    )
    args = parser.parse_args()

    input_path = Path(args.json_path)
    if not input_path.exists():
        print(f"input JSON not found: {input_path}")
        return 1

    output_path = Path(args.output) if args.output else Path("output") / f"{input_path.stem}_roundtable_os.html"
    return render_file(input_path, output_path, theme=args.theme)


if __name__ == "__main__":
    raise SystemExit(main())
