# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import argparse
import re

from engine.validate_html_ppt_v12 import validate_html


@dataclass
class ReadingValidationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def validate_reading_html(html: str) -> ReadingValidationResult:
    errors: list[str] = []
    v12_result = validate_html(html)
    errors.extend(v12_result.errors)

    slides = _extract_slide_sections(html)
    if not slides:
        errors.append("no readable slides found")

    for index, slide in enumerate(slides, start=1):
        page_type = _page_type(slide)
        if "reading-title" not in slide:
            errors.append(f"slide {index} missing title")
        if page_type != "cover" and "最终洞见" not in slide:
            errors.append(f"slide {index} missing takeaway")

        block_count = slide.count("reading-block")
        minimum = 3 if page_type == "clash_reading" else 5
        if page_type != "cover" and block_count < minimum:
            errors.append(
                f"slide {index} information density too low: expected at least {minimum} reading blocks, got {block_count}"
            )

    if re.search(r"假小字|乱码|lorem|ipsum", html, re.IGNORECASE):
        errors.append("decorative or fake text marker found")

    return ReadingValidationResult(ok=not errors, errors=errors)


def _page_type(slide_html: str) -> str:
    match = re.search(r'data-page-type="([^"]+)"', slide_html)
    return match.group(1) if match else ""


def _extract_slide_sections(html: str) -> list[str]:
    starts = [match.start() for match in re.finditer(r'<section class="slide(?: visible)?"', html)]
    slides: list[str] = []
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else html.find("<script>", start)
        if end == -1:
            end = len(html)
        slides.append(html[start:end])
    return slides


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate readable HTML-PPT V13 output")
    parser.add_argument("html_path", help="HTML file to validate")
    args = parser.parse_args()

    html = Path(args.html_path).read_text(encoding="utf-8")
    result = validate_reading_html(html)
    if result.ok:
        print("HTML-PPT V13 validation passed")
        return 0

    print("HTML-PPT V13 validation failed")
    for error in result.errors:
        print(f"- {error}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
