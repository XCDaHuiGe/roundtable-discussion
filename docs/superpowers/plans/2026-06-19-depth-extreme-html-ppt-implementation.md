# Depth Extreme HTML-PPT Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a depth-first and extreme-design generation layer so HTML-PPT decks produce deeper content and stronger visual expression while preserving the fixed no-scroll presentation runtime.

**Architecture:** First fix the real V13 book-generation entrypoint so show-off mode cannot bypass the open-design layer. Then add a content depth audit before rendering, attach slide-level beat and intensity metadata to planned pages, extend the display-logic selector with extreme variants, render the first extreme layouts with full-stage shells, and validate both depth and design strength. Keep the existing navigation runtime as the base.

**Tech Stack:** Python dataclasses, existing V13 HTML renderer, static HTML validator, pytest-style tests where available, Codex bundled Python for syntax and behavior checks.

---

## File Structure

- Create `engine/html_ppt_depth.py`
  - Owns `DepthScore`, `score_deep_content()`, and generic-term detection.
- Create or modify `engine/html_ppt_open_design_planner.py`
  - Bridges real V13 book JSON into open-design page families and show-off intensity.
- Modify `engine/render_html_ppt_v13.py`
  - Selects legacy reading planner only for regular reading mode; selects open-design planner for show-off/free-design mode.
- Create `engine/html_ppt_slide_beat.py`
  - Owns `SlideBeat`, intensity constants, and slide beat validation.
- Modify `engine/html_ppt_v13.py`
  - Adds optional `beat`, `reader_question`, `memory_hook`, `source_refs`, and `intensity` fields to `ReadingPage`.
- Modify `engine/html_ppt_display_logic.py`
  - Adds extreme variants and variant selection by intensity.
- Modify `engine/html_ppt_v13_renderer.py`
  - Adds three first-slice extreme renderers and dispatches them through `_VARIANT_RENDERERS`.
- Create `engine/html_ppt_design_strength.py`
  - Validates variant diversity, intensity requirements, and repeated layout rhythm.
- Modify `engine/validate_html_ppt_v13.py`
  - Adds optional design-strength checks for rendered decks.
- Create `tests/test_html_ppt_depth.py`
  - Tests depth scoring and failure thresholds.
- Create `tests/test_html_ppt_slide_beat.py`
  - Tests slide beat fields and validation.
- Create `tests/test_html_ppt_extreme_variants.py`
  - Tests extreme variant selection and rendered HTML markers.
- Create `output/html-ppt-depth-extreme-check.html`
  - Generated sample used for manual and validator review.

---

### Task 0: Fix Real V13 Book Generation Routing

**Files:**
- Modify: `engine/render_html_ppt_v13.py`
- Create: `engine/html_ppt_open_design_planner.py`
- Test: `tests/test_html_ppt_open_design_routing.py`

- [ ] **Step 1: Write failing routing tests**

Create `tests/test_html_ppt_open_design_routing.py`:

```python
from engine.html_ppt_open_design_planner import plan_open_design_pages


def test_showoff_planner_emits_display_logic_and_variants():
    data = {
        "title": "Test Book",
        "subtitle": "show-off deck",
        "insights": [{"insight_title": "No savior", "insight_content": "The core insight has a cost."}],
        "rounds": [
            {
                "topic": "Can a person be saved by another?",
                "core_question": "Who pays for salvation?",
                "stances": [
                    {"expert": "Expert A", "stance": "The savior myth hides cost."},
                    {"expert": "Expert B", "stance": "Systems create the conditions."},
                ],
                "clash_rounds": [
                    {
                        "attacker": "Expert A",
                        "target": "Expert B",
                        "attack_type": "cost challenge",
                        "attack_content": "Your explanation ignores the price.",
                        "defense": "The price is exactly the point.",
                    }
                ],
            }
        ],
    }

    pages = plan_open_design_pages(data, showoff=True)

    assert any(page.display_logic != "neutral" for page in pages if page.page_type != "cover")
    assert any(page.layout_variant.endswith("_extreme") for page in pages)
```

- [ ] **Step 2: Implement the open-design planner bridge**

Create `engine/html_ppt_open_design_planner.py`:

```python
# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from engine.html_ppt_v13 import ReadingBlock, ReadingPage
from engine.html_ppt_v13_planner import plan_reading_pages


def plan_open_design_pages(data: dict[str, Any], showoff: bool = False) -> list[ReadingPage]:
    pages = plan_reading_pages(data)
    if not showoff:
        return pages

    upgraded: list[ReadingPage] = []
    for page in pages:
        if page.page_type == "cover":
            upgraded.append(page)
            continue
        if page.page_type == "clash_reading":
            upgraded.append(_upgrade_clash(page))
        elif page.page_type == "roundtable_reading":
            upgraded.append(_upgrade_roundtable(page))
        elif page.page_type in {"insight_reading", "summary_reading"}:
            upgraded.append(_upgrade_manifesto(page))
        else:
            upgraded.append(page)
    return upgraded


def _upgrade_clash(page: ReadingPage) -> ReadingPage:
    return ReadingPage(
        page_type="clash",
        title=page.title,
        thesis=page.thesis,
        takeaway=page.takeaway,
        layout="clash_courtroom",
        display_logic="cross_exam",
        layout_variant="interrogation_room_extreme",
        intensity="extreme",
        blocks=page.blocks,
        meta=page.meta,
    )


def _upgrade_roundtable(page: ReadingPage) -> ReadingPage:
    return ReadingPage(
        page_type="response_graph",
        title=page.title,
        thesis=page.thesis,
        takeaway=page.takeaway,
        layout="stance_spectrum",
        display_logic="spectrum",
        layout_variant="stance_radar",
        intensity="dramatic",
        blocks=page.blocks,
        meta=page.meta,
    )


def _upgrade_manifesto(page: ReadingPage) -> ReadingPage:
    return ReadingPage(
        page_type="insight",
        title=page.title,
        thesis=page.thesis,
        takeaway=page.takeaway,
        layout="magazine_focus",
        display_logic="manifesto",
        layout_variant="manifesto_poster_extreme",
        intensity="extreme",
        blocks=page.blocks,
        meta=page.meta,
    )
```

- [ ] **Step 3: Add CLI option to render route**

Modify `engine/render_html_ppt_v13.py`:

```python
from engine.html_ppt_open_design_planner import plan_open_design_pages
```

Add CLI flag:

```python
parser.add_argument("--showoff", action="store_true", help="Use open-design extreme route")
```

In `render_file()`, accept `showoff: bool = False` and choose:

```python
pages = plan_open_design_pages(data, showoff=showoff)
```

- [ ] **Step 4: Run routing tests**

Run:

```powershell
& 'C:\Users\gai\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests/test_html_ppt_open_design_routing.py -v
```

Expected: tests pass.

---

### Task 1: Add Depth Scoring

**Files:**
- Create: `engine/html_ppt_depth.py`
- Test: `tests/test_html_ppt_depth.py`

- [ ] **Step 1: Write failing depth score tests**

Create `tests/test_html_ppt_depth.py`:

```python
from engine.html_ppt_depth import score_deep_content


def test_depth_score_rewards_complete_deep_model():
    model = {
        "author_problem": "为什么个人努力会在结构性约束面前失效？",
        "consensus_baseline": "常见理解把失败归因于意志不够强。",
        "author_delta": "作者把问题从意志强弱移动到结构条件与行动回路。",
        "root_mechanism": "资源、身份和反馈回路共同塑造行动空间。",
        "reality_cases": ["案例A", "案例B"],
        "counter_positions": ["个人责任仍然不能被取消。"],
        "costs": ["接受该洞见会削弱简单归因。"],
        "boundaries": ["不能解释所有个体差异。"],
        "transferable_insights": ["先看结构条件，再评价行动选择。"],
        "uncertainty_notes": ["材料不足以判断长期效果。"],
    }

    result = score_deep_content(model)

    assert result.score >= 85
    assert result.can_render is True


def test_depth_score_blocks_shallow_model():
    result = score_deep_content({
        "author_problem": "这本书讲了什么？",
        "transferable_insights": ["要有深度思考。"],
    })

    assert result.score < 70
    assert result.can_render is False
    assert "baseline_delta" in result.missing
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
& 'C:\Users\gai\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests/test_html_ppt_depth.py -v
```

Expected before implementation: import failure for `engine.html_ppt_depth`.

- [ ] **Step 3: Implement depth scoring**

Create `engine/html_ppt_depth.py`:

```python
# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


GENERIC_TERMS = {"深度思考", "圆桌张力", "观点冲突", "认知升级", "值得反思"}


@dataclass
class DepthScore:
    score: int
    can_render: bool
    missing: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _present(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return any(_present(item) for item in value)
    return value is not None


def _specific_text(value: Any) -> bool:
    text = str(value or "").strip()
    return len(text) >= 12 and text not in GENERIC_TERMS


def score_deep_content(model: dict[str, Any]) -> DepthScore:
    score = 0
    missing: list[str] = []
    warnings: list[str] = []

    if _specific_text(model.get("author_problem")):
        score += 10
    else:
        missing.append("author_problem")

    if _specific_text(model.get("consensus_baseline")) and _specific_text(model.get("author_delta")):
        score += 15
    else:
        missing.append("baseline_delta")

    if _specific_text(model.get("root_mechanism")):
        score += 15
    else:
        missing.append("root_mechanism")

    if len(model.get("reality_cases") or []) >= 2:
        score += 10
    else:
        missing.append("reality_cases")

    if _present(model.get("counter_positions")):
        score += 10
    else:
        missing.append("counter_positions")

    if _present(model.get("costs")) and _present(model.get("boundaries")):
        score += 15
    else:
        missing.append("costs_boundaries")

    insights = model.get("transferable_insights") or []
    if insights and all(str(item).strip() not in GENERIC_TERMS for item in insights):
        score += 15
    else:
        missing.append("transferable_insights")

    if _present(model.get("uncertainty_notes")):
        score += 10
    else:
        warnings.append("uncertainty_not_named")

    return DepthScore(score=score, can_render=score >= 70, missing=missing, warnings=warnings)
```

- [ ] **Step 4: Run depth tests**

Run:

```powershell
& 'C:\Users\gai\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests/test_html_ppt_depth.py -v
```

Expected after implementation: both tests pass.

---

### Task 2: Add SlideBeat Metadata

**Files:**
- Create: `engine/html_ppt_slide_beat.py`
- Modify: `engine/html_ppt_v13.py`
- Test: `tests/test_html_ppt_slide_beat.py`

- [ ] **Step 1: Write failing slide beat tests**

Create `tests/test_html_ppt_slide_beat.py`:

```python
from engine.html_ppt_slide_beat import SlideBeat, validate_slide_beat
from engine.html_ppt_v13 import ReadingPage


def test_valid_slide_beat_passes():
    beat = SlideBeat(
        page_type="case_shock",
        display_logic="cost",
        layout_variant="cost_blast_extreme",
        depth_role="make the cost visible",
        visual_intent="explode the hidden cost into the main composition",
        reader_question="What does this idea cost when accepted?",
        memory_hook="Every idea sends an invoice.",
        required_blocks=["event", "cost"],
        source_refs=["rounds[0].reality_cases[0]"],
        intensity="extreme",
    )

    assert validate_slide_beat(beat) == []


def test_reading_page_accepts_intensity_and_reader_question():
    page = ReadingPage(
        page_type="case_shock",
        title="cost",
        intensity="extreme",
        reader_question="What does this cost?",
        memory_hook="The idea sends an invoice.",
    )

    assert page.intensity == "extreme"
    assert page.reader_question == "What does this cost?"
```

- [ ] **Step 2: Implement slide beat contract**

Create `engine/html_ppt_slide_beat.py`:

```python
# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field


INTENSITIES = {"quiet", "editorial", "dramatic", "extreme"}


@dataclass
class SlideBeat:
    page_type: str
    display_logic: str
    layout_variant: str
    depth_role: str
    visual_intent: str
    reader_question: str
    memory_hook: str
    required_blocks: list[str] = field(default_factory=list)
    source_refs: list[str] = field(default_factory=list)
    intensity: str = "editorial"


def validate_slide_beat(beat: SlideBeat) -> list[str]:
    issues: list[str] = []
    if beat.intensity not in INTENSITIES:
        issues.append("invalid_intensity")
    if not beat.depth_role.strip():
        issues.append("missing_depth_role")
    if not beat.visual_intent.strip():
        issues.append("missing_visual_intent")
    if not beat.reader_question.strip():
        issues.append("missing_reader_question")
    if not beat.memory_hook.strip():
        issues.append("missing_memory_hook")
    if beat.intensity == "extreme" and not beat.layout_variant.endswith("_extreme"):
        issues.append("extreme_requires_extreme_variant")
    return issues
```

- [ ] **Step 3: Extend ReadingPage**

Modify `engine/html_ppt_v13.py` by adding these fields to `ReadingPage`:

```python
beat: str = ""
reader_question: str = ""
memory_hook: str = ""
source_refs: list[str] = field(default_factory=list)
intensity: str = "editorial"
```

In `__post_init__`, keep the values bounded:

```python
self.beat = summarize_text(self.beat, 120)
self.reader_question = summarize_text(self.reader_question, 100)
self.memory_hook = summarize_text(self.memory_hook, 80)
if self.intensity not in {"quiet", "editorial", "dramatic", "extreme"}:
    raise ValueError(f"unknown intensity: {self.intensity}")
```

- [ ] **Step 4: Run slide beat tests**

Run:

```powershell
& 'C:\Users\gai\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests/test_html_ppt_slide_beat.py -v
```

Expected: both tests pass.

---

### Task 3: Select Extreme Variants

**Files:**
- Modify: `engine/html_ppt_display_logic.py`
- Test: `tests/test_html_ppt_extreme_variants.py`

- [ ] **Step 1: Write failing variant selection tests**

Create `tests/test_html_ppt_extreme_variants.py`:

```python
from engine.html_ppt_display_logic import select_layout_variant


def test_extreme_cost_uses_cost_blast_extreme():
    assert select_layout_variant("cost", "case_shock", intensity="extreme") == "cost_blast_extreme"


def test_editorial_cost_uses_existing_cost_blast():
    assert select_layout_variant("cost", "case_shock", intensity="editorial") == "cost_blast"


def test_extreme_evidence_uses_evidence_wall_extreme():
    assert select_layout_variant("evidence", "case_shock", intensity="extreme") == "evidence_wall_extreme"
```

- [ ] **Step 2: Update selector signature**

Change `select_layout_variant()` in `engine/html_ppt_display_logic.py` to:

```python
def select_layout_variant(display_logic: str, page_type: str = "", intensity: str = "editorial") -> str:
```

Add this mapping before existing non-extreme mappings:

```python
if intensity == "extreme":
    extreme = {
        "impact": "shock_poster_extreme",
        "evidence": "evidence_wall_extreme",
        "cross_exam": "interrogation_room_extreme",
        "diagnosis": "xray_diagnosis_extreme",
        "cost": "cost_blast_extreme",
        "delta": "delta_map_extreme",
        "mechanism": "mechanism_cutaway_extreme",
        "manifesto": "manifesto_poster_extreme",
    }
    if display_logic in extreme:
        return extreme[display_logic]
```

Add the new names to `LAYOUT_VARIANTS`.

- [ ] **Step 3: Pass intensity from ReadingPage**

Modify `ReadingPage.__post_init__` in `engine/html_ppt_v13.py`:

```python
self.layout_variant = ensure_layout_variant(
    self.layout_variant or select_layout_variant(self.display_logic, self.page_type, self.intensity)
)
```

- [ ] **Step 4: Run variant tests**

Run:

```powershell
& 'C:\Users\gai\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests/test_html_ppt_extreme_variants.py -v
```

Expected: all tests pass.

---

### Task 4: Render First Three Extreme Layouts With Stage Shells

**Files:**
- Modify: `engine/html_ppt_v13_renderer.py`
- Test: `tests/test_html_ppt_extreme_variants.py`

- [ ] **Step 1: Add renderer tests**

Append to `tests/test_html_ppt_extreme_variants.py`:

```python
from engine.html_ppt_v13 import ReadingBlock, ReadingPage
from engine.html_ppt_v13_renderer import render_reading_html


def test_render_cost_blast_extreme_contains_stage_markers():
    page = ReadingPage(
        page_type="case_shock",
        title="cost",
        layout="case_file",
        intensity="extreme",
        blocks=[ReadingBlock("event", "event", "impact"), ReadingBlock("cost", "cost", "system cost")],
    )

    html = render_reading_html([page], title="extreme")

    assert 'data-layout-variant="cost_blast_extreme"' in html
    assert "cost-blast-extreme" in html
    assert "EXTREME" in html
```

- [ ] **Step 2: Add CSS for three extreme stages**

In `READING_CSS` in `engine/html_ppt_v13_renderer.py`, add classes:

```css
.shock-poster-extreme{height:100%;display:grid;grid-template-columns:1fr 340px;gap:34px;overflow:hidden}
.shock-poster-extreme-main{background:#07080b;color:var(--paper);position:relative;padding:38px;display:flex;flex-direction:column;justify-content:center;overflow:hidden}
.shock-poster-extreme-main h2{font-family:var(--serif);font-size:clamp(72px,9vw,136px);line-height:.86;font-weight:900}
.evidence-wall-extreme{height:100%;position:relative;overflow:hidden;background:#16120f}
.evidence-wall-extreme .evidence-pin{position:absolute;width:260px;min-height:140px;background:#f6efe4;color:#111;padding:18px;border:1px solid rgba(0,0,0,.25);box-shadow:12px 18px 30px rgba(0,0,0,.28);overflow:hidden}
.cost-blast-extreme{height:100%;display:grid;grid-template-columns:1fr 410px;gap:38px;overflow:hidden}
.cost-blast-extreme-word{display:flex;flex-direction:column;justify-content:center;position:relative;overflow:hidden}
.cost-blast-extreme-word h2{font-family:var(--serif);font-size:clamp(82px,11vw,160px);line-height:.82;font-weight:900}
```

- [ ] **Step 3: Add full-stage render functions**

Add:

```python
def _render_cost_blast_extreme(page: ReadingPage) -> str:
    cost_blocks = [block for block in page.blocks if block.kind == "cost"]
    lead = cost_blocks[0] if cost_blocks else (page.blocks[0] if page.blocks else ReadingBlock("cost", "cost", page.thesis))
    cards = "".join(
        f'<article class="cost-card" data-anim="fade-up">{_render_block_inner(block, 140)}</article>'
        for block in page.blocks[:4]
    )
    body = f"""<div class="cost-blast-extreme">
  <section class="cost-blast-extreme-word" data-anim="fade-left">
    <div class="reading-kicker">EXTREME / COST</div>
    <h2>{escape(lead.title)}</h2>
    <p class="reading-block-text">{escape(_clip_text(lead.text, 180))}</p>
  </section>
  <aside class="cost-panel" data-anim="fade-right" data-stagger>{cards}</aside>
</div>"""
    return _render_stage(page, body)
```

Add `_render_stage(page, body)`:

```python
def _render_stage(page: ReadingPage, body: str) -> str:
    return f"""<div class="stage-page" data-stage-shell="true">
  {body}
</div>"""
```

Add similar functions for `_render_shock_poster_extreme()` and `_render_evidence_wall_extreme()` using the same helper functions. Keep text clipped and all containers `overflow:hidden`.

Do not wrap these extreme renderers in `_render_shell()`. That is the key difference between a polite variant and a free-design stage.

- [ ] **Step 4: Register renderers**

Add to `_VARIANT_RENDERERS`:

```python
"shock_poster_extreme": _render_shock_poster_extreme,
"evidence_wall_extreme": _render_evidence_wall_extreme,
"cost_blast_extreme": _render_cost_blast_extreme,
```

- [ ] **Step 5: Run renderer tests**

Run:

```powershell
& 'C:\Users\gai\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests/test_html_ppt_extreme_variants.py tests/test_html_ppt_open_design.py -v
```

Expected: all tests pass.

---

### Task 5: Add Design Strength Validation

**Files:**
- Create: `engine/html_ppt_design_strength.py`
- Test: `tests/test_html_ppt_extreme_variants.py`

- [ ] **Step 1: Add validation tests**

Append to `tests/test_html_ppt_extreme_variants.py`:

```python
from engine.html_ppt_design_strength import validate_design_strength


def test_design_strength_requires_extreme_variant_for_extreme_page():
    issues = validate_design_strength([
        {"layout_variant": "cost_blast", "intensity": "extreme", "display_logic": "cost"},
    ])

    assert "extreme_without_extreme_variant" in issues


def test_design_strength_accepts_extreme_variant():
    issues = validate_design_strength([
        {"layout_variant": "cost_blast_extreme", "intensity": "extreme", "display_logic": "cost"},
        {"layout_variant": "quiet_notes", "intensity": "quiet", "display_logic": "quiet_reading"},
    ])

    assert issues == []


def test_design_strength_rejects_all_reading_shell_showoff_deck():
    issues = validate_design_strength([
        {"layout_variant": "quiet_notes", "intensity": "editorial", "display_logic": "quiet_reading", "shell": "reading"},
        {"layout_variant": "stance_radar", "intensity": "dramatic", "display_logic": "spectrum", "shell": "reading"},
        {"layout_variant": "quiet_notes", "intensity": "editorial", "display_logic": "quiet_reading", "shell": "reading"},
    ], showoff=True)

    assert "showoff_without_stage_shell" in issues
```

- [ ] **Step 2: Implement validator**

Create `engine/html_ppt_design_strength.py`:

```python
# -*- coding: utf-8 -*-
from __future__ import annotations

from collections import Counter
from typing import Any


def validate_design_strength(pages: list[dict[str, Any]], showoff: bool = False) -> list[str]:
    issues: list[str] = []
    variants = [str(page.get("layout_variant") or "") for page in pages]

    for page in pages:
        intensity = str(page.get("intensity") or "editorial")
        variant = str(page.get("layout_variant") or "")
        if intensity == "extreme" and not variant.endswith("_extreme"):
            issues.append("extreme_without_extreme_variant")

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
```

- [ ] **Step 3: Run validation tests**

Run:

```powershell
& 'C:\Users\gai\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests/test_html_ppt_extreme_variants.py -v
```

Expected: all tests pass.

---

### Task 6: Generate Extreme Check HTML

**Files:**
- Create: `output/html-ppt-depth-extreme-check.html`

- [ ] **Step 1: Generate check HTML**

Run this PowerShell command:

```powershell
@'
from pathlib import Path
from engine.html_ppt_v13 import ReadingBlock, ReadingPage
from engine.html_ppt_v13_renderer import render_reading_html

pages = [
    ReadingPage(
        page_type="case_shock",
        title="Every idea sends an invoice",
        thesis="The point is not that the idea is wrong. The point is that reality charges for it.",
        takeaway="A deep claim must reveal its cost.",
        layout="case_file",
        intensity="extreme",
        reader_question="What does this idea cost?",
        memory_hook="The idea sends an invoice.",
        blocks=[
            ReadingBlock("event", "The clean theory breaks", "A beautiful explanation enters a messy system and immediately starts producing debt."),
            ReadingBlock("cost", "Trust cost", "Every later collaboration begins with defensive interpretation."),
            ReadingBlock("cost", "Time cost", "The team spends more time repairing alignment than making progress."),
        ],
    ),
    ReadingPage(
        page_type="case_shock",
        title="Evidence does not sit politely",
        thesis="Evidence should look like evidence: pinned, connected, and accusing the old frame.",
        takeaway="When evidence is spatial, the argument becomes harder to ignore.",
        layout="case_file",
        intensity="extreme",
        display_logic="evidence",
        reader_question="Which evidence cornered the old idea?",
        memory_hook="The wall starts talking.",
        blocks=[
            ReadingBlock("source", "Claim", "Personal effort explains the outcome."),
            ReadingBlock("event", "Resistance", "Resources, rules, and identity compress the available choices."),
            ReadingBlock("outcome", "Turn", "The event does not prove effort is useless. It proves effort needs conditions."),
            ReadingBlock("cost", "Verdict", "A theory without cost is only a slogan."),
        ],
    ),
]

Path("output/html-ppt-depth-extreme-check.html").write_text(
    render_reading_html(pages, title="Depth Extreme Check", theme="obsidian"),
    encoding="utf-8",
)
print("output/html-ppt-depth-extreme-check.html")
'@ | & 'C:\Users\gai\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -
```

Expected: file path printed.

- [ ] **Step 2: Validate generated HTML**

Run:

```powershell
& 'C:\Users\gai\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' engine\validate_html_ppt_v13.py output\html-ppt-depth-extreme-check.html
```

Expected: `HTML-PPT V13 validation passed`.

- [ ] **Step 3: Static contract check**

Run:

```powershell
@'
from pathlib import Path
html = Path("output/html-ppt-depth-extreme-check.html").read_text(encoding="utf-8")
assert "cost-blast-extreme" in html
assert "evidence-wall-extreme" in html
assert "height:100vh" in html
assert "overflow:hidden" in html
assert "setTimeout(()=>wheelTimer=null,400)" in html
print("depth extreme static checks passed")
'@ | & 'C:\Users\gai\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -
```

Expected: `depth extreme static checks passed`.

---

### Task 7: Browser QA Gate

**Files:**
- Modify: `engine/validate_html_ppt_v13.py` or add `engine/html_ppt_browser_audit.py`

- [ ] **Step 1: Define browser audit result**

Create a small result shape in `engine/html_ppt_browser_audit.py`:

```python
# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BrowserAuditResult:
    slide_count: int
    nav_dot_count: int
    visible_count: int
    overflow_pages: list[int] = field(default_factory=list)
    missing_extreme_markers: list[int] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return (
            self.slide_count == self.nav_dot_count
            and self.visible_count == 1
            and not self.overflow_pages
            and not self.missing_extreme_markers
        )
```

- [ ] **Step 2: Implement browser automation in the existing project style**

Use the project’s current browser-control path if present. The audit must collect:

```javascript
{
  slideCount: document.querySelectorAll('.slide').length,
  navDotCount: document.querySelectorAll('.nav-dot').length,
  visibleCount: document.querySelectorAll('.slide.visible').length,
  overflowPages: [...document.querySelectorAll('.slide')].map((s,i)=>({
    i,
    overX: s.scrollWidth > s.clientWidth,
    overY: s.scrollHeight > s.clientHeight
  })).filter(x=>x.overX || x.overY),
  extremeMarkers: [...document.querySelectorAll('[data-layout-variant$="_extreme"]')].length
}
```

- [ ] **Step 3: Verify manually if browser automation is unavailable**

If the in-app browser is blocked by sandboxing, run the static checks from Task 6 and record in the final report that browser QA is pending due to browser control availability.

---

## Final Verification

Run these commands before claiming completion:

```powershell
& 'C:\Users\gai\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m compileall engine\html_ppt_depth.py engine\html_ppt_slide_beat.py engine\html_ppt_display_logic.py engine\html_ppt_v13.py engine\html_ppt_v13_renderer.py engine\html_ppt_design_strength.py
```

```powershell
& 'C:\Users\gai\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' engine\validate_html_ppt_v13.py output\html-ppt-depth-extreme-check.html
```

If `pytest` is installed:

```powershell
& 'C:\Users\gai\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests/test_html_ppt_depth.py tests/test_html_ppt_slide_beat.py tests/test_html_ppt_extreme_variants.py -v
```

If `pytest` is not installed, run equivalent inline Python assertions for:

- `score_deep_content()` returns `can_render=False` for shallow content.
- `ReadingPage(intensity="extreme")` selects an `_extreme` variant.
- rendered HTML contains `cost-blast-extreme`.
- show-off rendered HTML contains `data-layout-variant`.
- show-off rendered HTML contains `data-stage-shell="true"`.
- generated HTML passes `validate_html_ppt_v13.py`.

## Implementation Order

1. Real V13 book-generation routing.
2. Depth scoring.
3. Slide beat metadata.
4. Extreme variant selection.
5. First three extreme renderers with stage shells.
6. Design strength validator.
7. Check HTML generation from a real book input.
8. Browser QA gate.

This order prevents the exact observed failure: real book output staying in the regular reading planner while extreme design exists only in demos.
