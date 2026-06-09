# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import argparse
import re


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def validate_html(html: str) -> ValidationResult:
    errors: list[str] = []

    _expect_count(html, "function go(", 1, "go() navigation function", errors)
    _expect_count(html, "let wheelTimer", 1, "wheelTimer throttle", errors)
    _expect_count(html, 'id="navDots"', 1, "navDots container", errors)

    if re.search(r"overflow(?:-y)?\s*:\s*(auto|scroll)", html, re.IGNORECASE):
        errors.append("internal scroll is forbidden in HTML-PPT V12")

    slide_count = len(re.findall(r'<section\s+class="slide(?:\s+visible)?"', html))
    if slide_count == 0:
        errors.append("no .slide sections found")

    if html.count('class="slide visible"') != 1:
        errors.append("exactly one initial visible slide is required")

    compact = re.sub(r"\s+", "", html)
    if ".slide{height:100vh" not in compact or "overflow:hidden" not in compact:
        errors.append(".slide must define height:100vh and overflow:hidden")

    required_snippets = [
        ("e.preventDefault();go(cur+1)", "next keyboard navigation"),
        ("e.preventDefault();go(cur-1)", "previous keyboard navigation"),
        ("setTimeout(()=>wheelTimer=null,400)", "400ms wheel throttle"),
        ("{passive:false}", "non-passive wheel listener"),
        ("document.body.addEventListener('click'", "click navigation"),
        ("dot.onclick=()=>go(i)", "nav dot navigation"),
        ("progress.style.width=pct+'%'", "progress update"),
    ]
    for snippet, label in required_snippets:
        if snippet not in html:
            errors.append(f"missing {label}")

    return ValidationResult(ok=not errors, errors=errors)


def _expect_count(html: str, needle: str, expected: int, label: str, errors: list[str]) -> None:
    actual = html.count(needle)
    if actual != expected:
        errors.append(f"{label} count mismatch: expected {expected}, got {actual}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate final HTML-PPT V12 output")
    parser.add_argument("html_path", help="HTML file to validate")
    args = parser.parse_args()

    html_path = Path(args.html_path)
    html = html_path.read_text(encoding="utf-8")
    result = validate_html(html)
    if result.ok:
        print("HTML-PPT V12 validation passed")
        return 0

    print("HTML-PPT V12 validation failed")
    for error in result.errors:
        print(f"- {error}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
