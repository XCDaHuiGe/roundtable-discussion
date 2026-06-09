# -*- coding: utf-8 -*-
"""Browser-based verification for V13 HTML-PPT output using Playwright."""
from __future__ import annotations

from pathlib import Path
import pytest

try:
    from playwright.sync_api import sync_playwright, expect
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

pytestmark = pytest.mark.skipif(not HAS_PLAYWRIGHT, reason="playwright not installed")

HTML_PATH = Path(__file__).resolve().parents[1] / "output" / "遥远的救世主_圆桌洞见.html"


@pytest.fixture(scope="module")
def page():
    if not HTML_PATH.exists():
        pytest.skip(f"HTML not found: {HTML_PATH}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()
        page.goto(f"file:///{HTML_PATH.as_posix()}")
        page.wait_for_timeout(500)
        yield page
        browser.close()


def test_keyboard_navigation(page):
    """ArrowDown advances to next slide, ArrowUp goes back."""
    # initial: first slide visible
    visible_before = page.locator(".slide.visible").count()
    assert visible_before == 1

    # press ArrowDown
    page.keyboard.press("ArrowDown")
    page.wait_for_timeout(600)
    visible_after = page.locator(".slide.visible").count()
    assert visible_after == 1

    # press ArrowUp to go back
    page.keyboard.press("ArrowUp")
    page.wait_for_timeout(600)
    first_visible = page.locator(".slide.visible")
    assert first_visible.count() == 1


def test_nav_dots_exist_and_clickable(page):
    """Nav dots are rendered and clickable."""
    dots = page.locator("#navDots .nav-dot")
    assert dots.count() >= 5, f"Expected at least 5 nav dots, got {dots.count()}"

    # click second dot
    dots.nth(1).click()
    page.wait_for_timeout(600)
    # check that second dot is now active
    assert dots.nth(1).evaluate("el => el.classList.contains('active')")


def test_no_slide_overflow(page):
    """Each visible slide should not have internal scroll."""
    slides = page.locator(".slide")
    count = slides.count()
    for i in range(min(count, 5)):
        slide = slides.nth(i)
        # make it visible
        slide.evaluate("el => el.classList.add('visible')")
        page.wait_for_timeout(100)
        scroll_h = slide.evaluate("el => el.scrollHeight")
        client_h = slide.evaluate("el => el.clientHeight")
        # allow 5px tolerance
        assert scroll_h <= client_h + 5, f"Slide {i} overflows: scrollHeight={scroll_h} > clientHeight={client_h}"
        if i > 0:
            slide.evaluate("el => el.classList.remove('visible')")


def test_clash_page_has_attack_and_defense(page):
    """First clash page should have both attack and defense blocks on the same slide."""
    clash_slide = page.locator('[data-page-type="clash_reading"]').first
    if clash_slide.count() == 0:
        pytest.skip("No clash_reading slides found")

    # make it visible
    clash_slide.evaluate("el => el.classList.add('visible')")
    page.wait_for_timeout(200)

    attack = clash_slide.locator('[data-kind="attack"]')
    defense = clash_slide.locator('[data-kind="defense"]')

    assert attack.count() >= 1, "No attack block found on clash page"
    assert defense.count() >= 1, "No defense block found on clash page"

    # both should have non-empty text
    attack_text = attack.first.inner_text().strip()
    defense_text = defense.first.inner_text().strip()
    assert len(attack_text) > 5, f"Attack text too short: '{attack_text}'"
    assert len(defense_text) > 5, f"Defense text too short: '{defense_text}'"


def test_progress_bar_updates(page):
    """Progress bar width should update when navigating."""
    progress = page.locator("#progress")
    initial_width = progress.evaluate("el => parseFloat(el.style.width) || 0")

    # advance a few slides
    for _ in range(3):
        page.keyboard.press("ArrowDown")
        page.wait_for_timeout(400)

    new_width = progress.evaluate("el => parseFloat(el.style.width) || 0")
    assert new_width > initial_width, f"Progress bar didn't advance: {initial_width} -> {new_width}"


def test_click_blank_advances(page):
    """Clicking on blank area should advance to next slide."""
    # go to first slide
    page.keyboard.press("Home")
    page.wait_for_timeout(600)

    # click on a blank area (not on nav dots or buttons)
    page.mouse.click(640, 450)
    page.wait_for_timeout(600)

    # counter should show page 2
    counter = page.locator("#counter")
    text = counter.inner_text()
    assert "2" in text, f"Expected page 2 after click, got: {text}"
