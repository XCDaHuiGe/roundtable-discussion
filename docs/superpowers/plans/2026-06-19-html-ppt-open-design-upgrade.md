# HTML PPT Open Design Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade V13 HTML-PPT generation so page rendering is selected by content display logic, not locked to one fixed template per page type.

**Architecture:** Keep the existing fixed presentation player, `ReadingPage`, planner, and renderer. Add a small open-design layer: `display_logic` describes what the content is trying to do, and `layout_variant` chooses the visual composition. Existing `layout` remains the fallback.

**Tech Stack:** Python dataclasses, existing V13 HTML renderer, pytest.

---

### Task 1: Add Open-Design Contract

**Files:**
- Modify: `engine/html_ppt_v13.py`
- Create: `engine/html_ppt/display_logic.py`
- Test: `tests/test_html_ppt_open_design.py`

- [ ] **Step 1: Add failing tests**

Create tests that prove two `case_shock` pages can choose different variants based on blocks:

```python
from engine.html_ppt_v13 import ReadingBlock, ReadingPage


def test_case_shock_with_cost_uses_cost_blast():
    page = ReadingPage(
        page_type="case_shock",
        title="case",
        layout="case_file",
        blocks=[ReadingBlock("event", "事件", "冲击"), ReadingBlock("cost", "代价", "系统代价")],
    )
    assert page.display_logic == "cost"
    assert page.layout_variant == "cost_blast"


def test_case_shock_without_cost_uses_shock_poster():
    page = ReadingPage(
        page_type="case_shock",
        title="case",
        layout="case_file",
        blocks=[ReadingBlock("event", "事件", "冲击")],
    )
    assert page.display_logic == "impact"
    assert page.layout_variant == "shock_poster"
```

- [ ] **Step 2: Implement selector**

Add `select_display_logic()` and `select_layout_variant()` with deterministic rules. Keep the rules small and readable.

- [ ] **Step 3: Wire fields into `ReadingPage`**

Add `display_logic` and `layout_variant` fields. If callers omit them, infer values in `__post_init__`.

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_html_ppt_open_design.py -v`

Expected: PASS.

### Task 2: Render Variant-Specific Layouts

**Files:**
- Modify: `engine/html_ppt_v13_renderer.py`
- Test: `tests/test_html_ppt_open_design.py`

- [ ] **Step 1: Add failing renderer tests**

Assert rendered HTML includes `data-display-logic`, `data-layout-variant`, and the selected variant class.

- [ ] **Step 2: Add variant renderer dispatch**

Before falling back to `_LAYOUT_RENDERERS`, check `_VARIANT_RENDERERS`.

- [ ] **Step 3: Add first variant renderers**

Implement `shock_poster`, `evidence_wall`, `cost_blast`, `interrogation_room`, and `xray_diagnosis`. Each layout must stay inside the existing slide shell and avoid internal scrolling.

- [ ] **Step 4: Run renderer tests**

Run: `python -m pytest tests/test_html_ppt_open_design.py tests/test_html_ppt_v13_renderer.py -v`

Expected: PASS.

### Task 3: Preserve Presentation Bottom Contract

**Files:**
- Test: `tests/test_html_ppt_open_design.py`

- [ ] **Step 1: Add contract assertions**

Assert the rendered HTML still contains nav dots, `function go(`, wheel throttle, and `.slide{height:100vh`.

- [ ] **Step 2: Run validation tests**

Run: `python -m pytest tests/test_validate_html_ppt_v13.py tests/test_html_ppt_open_design.py -v`

Expected: PASS.

### Self-Review

- The plan changes only V13 reading PPT generation.
- It does not replace the whole renderer.
- It keeps old `layout` as fallback, so older pages remain compatible.
- It directly targets the root problem: page type no longer equals fixed visual template.
