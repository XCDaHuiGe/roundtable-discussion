# -*- coding: utf-8 -*-
from __future__ import annotations

from collections import Counter
import re
from typing import Any


def validate_design_strength(pages: list[dict[str, Any]], showoff: bool = False) -> list[str]:
    issues: list[str] = []
    variants = [str(page.get("layout_variant") or "") for page in pages]

    for page in pages:
        intensity = str(page.get("intensity") or "editorial")
        variant = str(page.get("layout_variant") or "")
        if intensity == "extreme" and not variant.endswith("_extreme"):
            issues.append("extreme_without_extreme_variant")

    if not showoff:
        for left, right in zip(variants, variants[1:]):
            if left and left == right:
                issues.append("adjacent_variant_repeat")
                break

        if len(pages) >= 8:
            counts = Counter(variants)
            if counts and counts.most_common(1)[0][1] / len(pages) > 0.4:
                issues.append("layout_family_overused")

    if showoff and not any(str(page.get("shell") or "") == "stage" for page in pages):
        issues.append("showoff_without_stage_shell")

    if showoff and not any(str(page.get("layout_variant") or "").endswith("_extreme") for page in pages):
        issues.append("showoff_without_extreme_variant")

    return issues


def validate_rendered_design_strength(html: str, showoff: bool = False) -> list[str]:
    pages: list[dict[str, Any]] = []
    for section in re.findall(r'<section class="slide(?: visible)?"[^>]*>.*?(?=<section class="slide|\Z)', html, re.S):
        variant = _attr(section, "data-layout-variant")
        pages.append({
            "layout_variant": variant,
            "intensity": "extreme" if variant.endswith("_extreme") else "editorial",
            "shell": "stage" if 'data-stage-shell="true"' in section else "reading",
        })
    return validate_design_strength(pages, showoff=showoff)


def _attr(text: str, name: str) -> str:
    match = re.search(rf'{re.escape(name)}="([^"]*)"', text)
    return match.group(1) if match else ""
