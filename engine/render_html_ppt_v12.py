# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.html_ppt_v12_planner import plan_pages
from engine.html_ppt_v12_renderer import render_html
from engine.validate_html_ppt_v12 import validate_html


def render_file(input_path: Path, output_path: Path) -> int:
    data = _read_json(input_path)
    pages = plan_pages(data)
    html = render_html(pages, title=data.get("title", "圆桌洞见"))

    result = validate_html(html)
    if not result.ok:
        print("HTML-PPT V12 validation failed")
        for error in result.errors:
            print(f"- {error}")
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print("HTML-PPT V12 validation passed")
    print(f"[GENERATED] {len(pages)} pages")
    print(f"[SAVE] {output_path}")
    return 0


def _read_json(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8-sig")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("input JSON must be an object")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a stable HTML-PPT V12 deck")
    parser.add_argument("json_path", help="Input roundtable JSON path")
    parser.add_argument("--output", "-o", help="Output HTML path")
    args = parser.parse_args()

    input_path = Path(args.json_path)
    if not input_path.exists():
        print(f"input JSON not found: {input_path}")
        return 1

    output_path = Path(args.output) if args.output else Path("output") / f"{input_path.stem}_v12.html"
    return render_file(input_path, output_path)


if __name__ == "__main__":
    raise SystemExit(main())
