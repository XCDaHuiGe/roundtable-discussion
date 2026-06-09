# HTML-PPT V13 Readable Design System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a no-GPT readable PPT design layer on top of V12 so generated decks become dense, readable slide documents instead of sparse presentation backgrounds.

**Architecture:** Keep V12 as the stable rendering and navigation base. Add V13 page contracts, reading layout planning, renderer extensions, and quality validation. The V13 CLI reuses V12 navigation stability while enforcing higher information density and readable page contracts.

**Tech Stack:** Python standard library, existing `engine/html_ppt_v12*.py` modules, `pytest`, optional Playwright verification after static validation.

---

## File Structure

- Create `engine/html_ppt_v13.py`: V13 dataclasses, reading page contracts, block helpers, and layout constants.
- Create `engine/html_ppt_v13_planner.py`: converts existing V8/V12 JSON into V13 reading pages without GPT.
- Create `engine/html_ppt_v13_renderer.py`: renders V13 reading layouts while reusing V12 navigation shell conventions.
- Create `engine/validate_html_ppt_v13.py`: validates information density, required takeaways, no internal scroll, and V12 navigation constraints.
- Create `engine/render_html_ppt_v13.py`: CLI entrypoint for V13.
- Create `tests/test_html_ppt_v13_contracts.py`: page contract and classification tests.
- Create `tests/test_html_ppt_v13_planner.py`: no-GPT page planning tests.
- Create `tests/test_html_ppt_v13_renderer.py`: reading layout rendering tests.
- Create `tests/test_validate_html_ppt_v13.py`: quality validator tests.
- Create `tests/test_render_html_ppt_v13_cli.py`: CLI integration test.
- Modify `SKILL.md`: document V13 as readable PPT quality layer and keep V12 as stable base.

## Task 1: Add V13 Page Contracts

**Files:**
- Create: `engine/html_ppt_v13.py`
- Test: `tests/test_html_ppt_v13_contracts.py`

- [ ] **Step 1: Write failing contract tests**

Create `tests/test_html_ppt_v13_contracts.py`:

```python
import pytest

from engine.html_ppt_v13 import (
    ReadingBlock,
    ReadingPage,
    classify_position_label,
    ensure_reading_layout,
)


def test_reading_page_requires_known_layout():
    with pytest.raises(ValueError, match="unknown reading layout"):
        ReadingPage(page_type="roundtable_reading", title="标题", layout="bad_layout")


def test_reading_page_keeps_takeaway_and_blocks():
    page = ReadingPage(
        page_type="roundtable_reading",
        title="文化属性",
        thesis="文化不是宿命，而是情境应对系统。",
        takeaway="读者应带走结构视角。",
        layout="stance_spectrum",
        blocks=[ReadingBlock(kind="stance", title="丁元英", text="文化决定行动方式。")],
    )
    assert page.title == "文化属性"
    assert page.takeaway == "读者应带走结构视角。"
    assert page.blocks[0].kind == "stance"


def test_classify_position_label_without_gpt():
    assert classify_position_label("文化属性决定人的选择") == "文化解释"
    assert classify_position_label("制度和法律塑造路径") == "制度解释"
    assert classify_position_label("资本和生产关系放大结果") == "资本解释"
    assert classify_position_label("道法自然，遵循规律") == "规律解释"
    assert classify_position_label("复杂问题需要综合判断") == "综合解释"


def test_ensure_reading_layout_rejects_unknown_layout():
    with pytest.raises(ValueError, match="unknown reading layout"):
        ensure_reading_layout("poster")
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```powershell
python -m pytest tests/test_html_ppt_v13_contracts.py -q
```

Expected: import failure because `engine.html_ppt_v13` does not exist.

- [ ] **Step 3: Implement V13 contracts**

Create `engine/html_ppt_v13.py`:

```python
# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from engine.html_ppt_v12 import normalize_text, summarize_text


READING_LAYOUTS = {
    "reading_brief_4zone",
    "stance_spectrum",
    "clash_courtroom",
}

READING_PAGE_TYPES = {
    "cover",
    "insight_reading",
    "roundtable_reading",
    "clash_reading",
    "summary_reading",
}


def ensure_reading_layout(layout: str) -> str:
    if layout not in READING_LAYOUTS:
        raise ValueError(f"unknown reading layout: {layout}")
    return layout


def classify_position_label(text: Any) -> str:
    value = normalize_text(text)
    if any(token in value for token in ("制度", "法律", "法治", "法度")):
        return "制度解释"
    if any(token in value for token in ("资本", "生产关系", "阶级", "市场")):
        return "资本解释"
    if any(token in value for token in ("道", "自然", "规律", "无为")):
        return "规律解释"
    if "文化" in value:
        return "文化解释"
    return "综合解释"


@dataclass
class ReadingBlock:
    kind: str
    title: str
    text: str
    label: str = ""
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.kind = normalize_text(self.kind)
        self.title = summarize_text(self.title, 32)
        self.text = summarize_text(self.text, 180)
        self.label = summarize_text(self.label, 24)


@dataclass
class ReadingPage:
    page_type: str
    title: str
    thesis: str = ""
    takeaway: str = ""
    layout: str = "reading_brief_4zone"
    blocks: list[ReadingBlock] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.page_type not in READING_PAGE_TYPES:
            raise ValueError(f"unknown reading page_type: {self.page_type}")
        self.layout = ensure_reading_layout(self.layout)
        self.title = summarize_text(self.title, 36)
        self.thesis = summarize_text(self.thesis, 90)
        self.takeaway = summarize_text(self.takeaway, 120)
```

- [ ] **Step 4: Run contract tests**

Run:

```powershell
python -m pytest tests/test_html_ppt_v13_contracts.py -q
```

Expected: all contract tests pass.

- [ ] **Step 5: Commit**

```powershell
git add engine/html_ppt_v13.py tests/test_html_ppt_v13_contracts.py
git commit -m "feat: add HTML-PPT V13 reading contracts"
```

## Task 2: Add No-GPT Reading Planner

**Files:**
- Create: `engine/html_ppt_v13_planner.py`
- Test: `tests/test_html_ppt_v13_planner.py`

- [ ] **Step 1: Write failing planner tests**

Create `tests/test_html_ppt_v13_planner.py`:

```python
from engine.html_ppt_v13_planner import plan_reading_pages


def sample_data():
    return {
        "title": "《测试书》圆桌洞见",
        "subtitle": "文化属性与命运",
        "experts": [{"name": f"专家{i}", "title": "思想家", "core_belief": "核心信念"} for i in range(1, 7)],
        "rounds": [
            {
                "topic": "文化属性真的决定命运吗",
                "core_question": "文化是原因还是结果？",
                "stances": [
                    {"expert": "丁元英", "stance": "文化属性决定行动方式。"},
                    {"expert": "韩非子", "stance": "制度和法律才决定路径。"},
                    {"expert": "马克思", "stance": "资本和生产关系放大结果。"},
                    {"expert": "老子", "stance": "道法自然，规律不可违。"},
                    {"expert": "芒格", "stance": "复杂问题需要多元模型。"},
                    {"expert": "尼采", "stance": "选择来自强力意志。"},
                ],
                "clash_rounds": [
                    {
                        "attacker": "马克思",
                        "target": "丁元英",
                        "attack_type": "因果倒置",
                        "attack_content": "文化解释掩盖了资本结构。",
                        "defense": "规律不是资本发明的。",
                    }
                ],
            }
        ],
        "insights": [
            {"insight_title": "文化属性不是宿命", "insight_content": "文化属性更像情境应对系统。"},
            {"insight_title": "合法不等于合情", "insight_content": "杀富济贫暴露法律和人性的裂缝。"},
            {"insight_title": "理性也有井底", "insight_content": "如实观照也有认知边界。"},
        ],
        "open_questions": ["弱势文化是原因还是结果？"],
    }


def test_plan_reading_pages_creates_reading_page_family():
    pages = plan_reading_pages(sample_data())
    page_types = [page.page_type for page in pages]
    assert page_types[0] == "cover"
    assert "insight_reading" in page_types
    assert "roundtable_reading" in page_types
    assert "clash_reading" in page_types
    assert page_types[-1] == "summary_reading"


def test_roundtable_reading_page_has_six_stance_blocks_and_takeaway():
    pages = plan_reading_pages(sample_data())
    page = next(p for p in pages if p.page_type == "roundtable_reading")
    stance_blocks = [block for block in page.blocks if block.kind == "stance"]
    assert len(stance_blocks) == 6
    assert page.layout == "stance_spectrum"
    assert page.takeaway
    assert {block.label for block in stance_blocks} >= {"文化解释", "制度解释", "资本解释", "规律解释"}


def test_clash_reading_page_has_attack_defense_essence_and_takeaway():
    pages = plan_reading_pages(sample_data())
    page = next(p for p in pages if p.page_type == "clash_reading")
    kinds = {block.kind for block in page.blocks}
    assert {"attack", "defense", "essence"} <= kinds
    assert page.takeaway
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```powershell
python -m pytest tests/test_html_ppt_v13_planner.py -q
```

Expected: import failure for `engine.html_ppt_v13_planner`.

- [ ] **Step 3: Implement planner**

Create `engine/html_ppt_v13_planner.py` with no-GPT extraction rules:

```python
# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from engine.html_ppt_v12 import summarize_text
from engine.html_ppt_v13 import ReadingBlock, ReadingPage, classify_position_label


def plan_reading_pages(data: dict[str, Any]) -> list[ReadingPage]:
    pages: list[ReadingPage] = []
    pages.append(_cover_page(data))

    insights = data.get("insights") or []
    if insights:
        pages.append(_insight_page(insights))

    for round_index, round_data in enumerate(data.get("rounds") or [], start=1):
        pages.append(_roundtable_page(round_data, round_index))
        for clash_index, clash in enumerate(round_data.get("clash_rounds") or [], start=1):
            pages.append(_clash_page(clash, round_index, clash_index))

    pages.append(_summary_page(data))
    return pages


def _cover_page(data: dict[str, Any]) -> ReadingPage:
    return ReadingPage(
        page_type="cover",
        title=data.get("title", "圆桌洞见"),
        thesis=data.get("subtitle", "阅读型圆桌洞见"),
        takeaway="本 deck 以阅读型结构呈现核心争议、专家立场和最终洞见。",
        layout="reading_brief_4zone",
        blocks=[
            ReadingBlock("metric", "专家", str(len(data.get("experts") or []))),
            ReadingBlock("metric", "轮次", str(len(data.get("rounds") or []))),
            ReadingBlock("metric", "洞见", str(len(data.get("insights") or []))),
        ],
    )


def _insight_page(insights: list[dict[str, Any]]) -> ReadingPage:
    blocks = []
    for insight in insights[:5]:
        blocks.append(ReadingBlock(
            kind="insight",
            title=insight.get("insight_title", "洞见"),
            text=insight.get("insight_content", insight.get("attack_content", "")),
        ))
    return ReadingPage(
        page_type="insight_reading",
        title="核心洞见",
        thesis="先看结论，再进入圆桌讨论。",
        takeaway="这些洞见是后续专家冲突的阅读索引。",
        layout="reading_brief_4zone",
        blocks=blocks,
    )


def _roundtable_page(round_data: dict[str, Any], round_index: int) -> ReadingPage:
    blocks = [
        ReadingBlock(
            kind="stance",
            title=stance.get("expert", stance.get("expert_name", "专家")),
            text=stance.get("stance", stance.get("content", stance.get("speech", ""))),
            label=classify_position_label(stance.get("stance", stance.get("content", ""))),
        )
        for stance in (round_data.get("stances") or [])[:6]
    ]
    return ReadingPage(
        page_type="roundtable_reading",
        title=f"第{round_index}轮：{round_data.get('topic', '圆桌讨论')}",
        thesis=summarize_text(round_data.get("core_question", "这一轮讨论的核心争议是什么？"), 90),
        takeaway="阅读重点：看清专家不是在重复观点，而是在不同解释框架之间竞争。",
        layout="stance_spectrum",
        blocks=blocks,
        meta={"round_index": round_index},
    )


def _clash_page(clash: dict[str, Any], round_index: int, clash_index: int) -> ReadingPage:
    attacker = clash.get("attacker", "攻击方")
    target = clash.get("target", "回应方")
    attack = clash.get("attack_content", "")
    defense = clash.get("defense", clash.get("defense_content", clash.get("counter_attack", "")))
    essence = clash.get("attack_type", "观点冲突")
    return ReadingPage(
        page_type="clash_reading",
        title=f"{attacker} 对 {target}：{essence}",
        thesis="真正值得读的不是谁赢了，而是冲突背后的解释框架。",
        takeaway=f"本页冲突本质：{summarize_text(essence, 40)}。",
        layout="clash_courtroom",
        blocks=[
            ReadingBlock("attack", attacker, attack, label="攻击"),
            ReadingBlock("defense", target, defense, label="回应"),
            ReadingBlock("essence", "冲突本质", essence, label="判读"),
        ],
        meta={"round_index": round_index, "clash_index": clash_index},
    )


def _summary_page(data: dict[str, Any]) -> ReadingPage:
    questions = data.get("open_questions") or []
    blocks = [
        ReadingBlock("takeaway", "结论一", "文化、制度、资本和行动共同塑造命运。"),
        ReadingBlock("takeaway", "结论二", "强势文化不是口号，而是识别规律并承担代价。"),
        ReadingBlock("question", "开放问题", questions[0] if questions else "读者如何把洞见放回自己的处境？"),
    ]
    return ReadingPage(
        page_type="summary_reading",
        title="读者最终带走什么",
        thesis="不要寻找救世主，要识别自己的解释框架。",
        takeaway="阅读完成后，至少应带走一个可复用的判断框架。",
        layout="reading_brief_4zone",
        blocks=blocks,
    )
```

- [ ] **Step 4: Run planner tests**

Run:

```powershell
python -m pytest tests/test_html_ppt_v13_planner.py -q
```

Expected: all planner tests pass.

- [ ] **Step 5: Commit**

```powershell
git add engine/html_ppt_v13_planner.py tests/test_html_ppt_v13_planner.py
git commit -m "feat: plan readable HTML-PPT V13 pages"
```

## Task 3: Render Reading Layouts

**Files:**
- Create: `engine/html_ppt_v13_renderer.py`
- Test: `tests/test_html_ppt_v13_renderer.py`

- [ ] **Step 1: Write failing renderer tests**

Create `tests/test_html_ppt_v13_renderer.py`:

```python
from engine.html_ppt_v13 import ReadingBlock, ReadingPage
from engine.html_ppt_v13_renderer import render_reading_html


def test_render_reading_html_contains_dense_reading_regions():
    html = render_reading_html([
        ReadingPage(
            page_type="roundtable_reading",
            title="文化属性真的决定命运吗",
            thesis="文化不是宿命，而是解释框架。",
            takeaway="读者应带走结构视角。",
            layout="stance_spectrum",
            blocks=[
                ReadingBlock("stance", "丁元英", "文化决定行动方式。", label="文化解释"),
                ReadingBlock("stance", "韩非子", "制度和法律塑造路径。", label="制度解释"),
                ReadingBlock("stance", "马克思", "资本放大结果。", label="资本解释"),
                ReadingBlock("stance", "老子", "规律不可违。", label="规律解释"),
            ],
        )
    ], title="测试")
    assert "阅读重点" in html
    assert "最终洞见" in html
    assert "stance-spectrum" in html
    assert html.count("reading-block") >= 4


def test_render_reading_html_keeps_v12_navigation_contract():
    html = render_reading_html([
        ReadingPage(page_type="summary_reading", title="总结", takeaway="结论", blocks=[
            ReadingBlock("takeaway", "结论一", "内容"),
            ReadingBlock("takeaway", "结论二", "内容"),
            ReadingBlock("takeaway", "结论三", "内容"),
        ])
    ], title="测试")
    assert html.count("function go(") == 1
    assert 'id="navDots"' in html
    assert "setTimeout(()=>wheelTimer=null,400)" in html
    assert ".slide{height:100vh" in html.replace(" ", "")
```

- [ ] **Step 2: Run renderer tests and verify failure**

Run:

```powershell
python -m pytest tests/test_html_ppt_v13_renderer.py -q
```

Expected: import failure for `engine.html_ppt_v13_renderer`.

- [ ] **Step 3: Implement renderer**

Create `engine/html_ppt_v13_renderer.py` with:

- V12-compatible navigation JS.
- Reading CSS tokens.
- Renderers for `reading_brief_4zone`, `stance_spectrum`, and `clash_courtroom`.
- No internal scroll.
- No inline random styling.

- [ ] **Step 4: Run renderer tests**

Run:

```powershell
python -m pytest tests/test_html_ppt_v13_renderer.py -q
```

Expected: renderer tests pass.

- [ ] **Step 5: Commit**

```powershell
git add engine/html_ppt_v13_renderer.py tests/test_html_ppt_v13_renderer.py
git commit -m "feat: render readable HTML-PPT V13 layouts"
```

## Task 4: Add V13 Quality Validator

**Files:**
- Create: `engine/validate_html_ppt_v13.py`
- Test: `tests/test_validate_html_ppt_v13.py`

- [ ] **Step 1: Write failing validator tests**

Create `tests/test_validate_html_ppt_v13.py`:

```python
from engine.html_ppt_v13 import ReadingBlock, ReadingPage
from engine.html_ppt_v13_renderer import render_reading_html
from engine.validate_html_ppt_v13 import validate_reading_html


def valid_html():
    page = ReadingPage(
        page_type="roundtable_reading",
        title="文化属性真的决定命运吗",
        thesis="文化不是宿命，而是解释框架。",
        takeaway="读者应带走结构视角。",
        layout="stance_spectrum",
        blocks=[
            ReadingBlock("stance", "丁元英", "文化决定行动方式。", label="文化解释"),
            ReadingBlock("stance", "韩非子", "制度和法律塑造路径。", label="制度解释"),
            ReadingBlock("stance", "马克思", "资本放大结果。", label="资本解释"),
            ReadingBlock("stance", "老子", "规律不可违。", label="规律解释"),
            ReadingBlock("stance", "芒格", "多元模型避免单因归因。", label="综合解释"),
        ],
    )
    return render_reading_html([page], title="测试")


def test_validate_reading_html_accepts_dense_page():
    result = validate_reading_html(valid_html())
    assert result.ok, result.errors


def test_validate_reading_html_rejects_missing_takeaway():
    html = valid_html().replace("最终洞见", "最终")
    result = validate_reading_html(html)
    assert not result.ok
    assert any("takeaway" in error for error in result.errors)


def test_validate_reading_html_rejects_low_information_page():
    html = valid_html().replace("reading-block", "thin-block")
    result = validate_reading_html(html)
    assert not result.ok
    assert any("information density" in error for error in result.errors)
```

- [ ] **Step 2: Run validator tests and verify failure**

Run:

```powershell
python -m pytest tests/test_validate_html_ppt_v13.py -q
```

Expected: import failure for `engine.validate_html_ppt_v13`.

- [ ] **Step 3: Implement validator**

Create `engine/validate_html_ppt_v13.py` that first calls `validate_html()` from V12, then checks:

- each non-cover slide has `最终洞见`;
- every slide has a title;
- regular reading slides have at least 5 `reading-block` entries, with clash pages allowed 3;
- no forbidden internal scroll;
- no decorative fake text markers.

- [ ] **Step 4: Run validator tests**

Run:

```powershell
python -m pytest tests/test_validate_html_ppt_v13.py -q
```

Expected: validator tests pass.

- [ ] **Step 5: Commit**

```powershell
git add engine/validate_html_ppt_v13.py tests/test_validate_html_ppt_v13.py
git commit -m "feat: validate readable HTML-PPT V13 quality"
```

## Task 5: Add V13 CLI And Documentation

**Files:**
- Create: `engine/render_html_ppt_v13.py`
- Create: `tests/test_render_html_ppt_v13_cli.py`
- Modify: `SKILL.md`

- [ ] **Step 1: Write failing CLI test**

Create `tests/test_render_html_ppt_v13_cli.py`:

```python
import json
import subprocess
import sys


def test_render_html_ppt_v13_cli_outputs_reading_deck(tmp_path):
    input_path = tmp_path / "input.json"
    output_path = tmp_path / "deck.html"
    input_path.write_text(json.dumps({
        "title": "测试圆桌",
        "subtitle": "阅读型 PPT",
        "experts": [{"name": "专家1"}],
        "rounds": [{
            "topic": "文化属性真的决定命运吗",
            "core_question": "文化是原因还是结果？",
            "stances": [
                {"expert": "丁元英", "stance": "文化属性决定行动方式。"},
                {"expert": "韩非子", "stance": "制度和法律塑造路径。"},
                {"expert": "马克思", "stance": "资本和生产关系放大结果。"},
                {"expert": "老子", "stance": "道法自然，规律不可违。"},
                {"expert": "芒格", "stance": "复杂问题需要多元模型。"},
            ],
        }],
        "insights": [
            {"insight_title": "洞见一", "insight_content": "内容一"},
            {"insight_title": "洞见二", "insight_content": "内容二"},
            {"insight_title": "洞见三", "insight_content": "内容三"},
        ],
    }, ensure_ascii=False), encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, "engine/render_html_ppt_v13.py", str(input_path), "--output", str(output_path)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    html = output_path.read_text(encoding="utf-8")
    assert "HTML-PPT V13 validation passed" in completed.stdout
    assert "阅读重点" in html
    assert "最终洞见" in html
```

- [ ] **Step 2: Run CLI test and verify failure**

Run:

```powershell
python -m pytest tests/test_render_html_ppt_v13_cli.py -q
```

Expected: script missing failure.

- [ ] **Step 3: Implement CLI**

Create `engine/render_html_ppt_v13.py` that reads JSON, calls `plan_reading_pages()`, renders with `render_reading_html()`, validates with `validate_reading_html()`, writes output, and prints page count.

- [ ] **Step 4: Update `SKILL.md`**

Add a V13 section above V12:

```markdown
### 阅读型 HTML-PPT 主链路（V13.0）

默认质量入口：

```bash
python engine/render_html_ppt_v13.py content/书名_V8.json --output output/书名_圆桌洞见.html
```

V13 目标：

- 给人看的 PPT，不是给人讲的 PPT。
- 无 GPT 也能生成高信息密度阅读型页面。
- 页面合同、布局白名单、设计 token、质量验收共同保证输出下限。
- 生图/配图按规则降级：真实素材优先，信息图优先，宁可无图也不放错图。
```

- [ ] **Step 5: Run CLI test**

Run:

```powershell
python -m pytest tests/test_render_html_ppt_v13_cli.py -q
```

Expected: CLI test passes.

- [ ] **Step 6: Commit**

```powershell
git add engine/render_html_ppt_v13.py tests/test_render_html_ppt_v13_cli.py SKILL.md
git commit -m "feat: add readable HTML-PPT V13 CLI"
```

## Task 6: Full Verification

**Files:**
- Generated only: `output/遥远的救世主_圆桌洞见_v13.html`

- [ ] **Step 1: Run V13 focused tests**

Run:

```powershell
python -m pytest tests/test_html_ppt_v13_contracts.py tests/test_html_ppt_v13_planner.py tests/test_html_ppt_v13_renderer.py tests/test_validate_html_ppt_v13.py tests/test_render_html_ppt_v13_cli.py -q
```

Expected: all V13 tests pass.

- [ ] **Step 2: Run full test suite**

Run:

```powershell
python -m pytest -q
```

Expected: all tests pass.

- [ ] **Step 3: Generate real V13 deck**

Run:

```powershell
python engine/render_html_ppt_v13.py content/遥远的救世主_V8.json --output output/遥远的救世主_圆桌洞见_v13.html
```

Expected: output file created and stdout includes `HTML-PPT V13 validation passed`.

- [ ] **Step 4: Verify legacy templates**

Run:

```powershell
$env:PYTHONIOENCODING='utf-8'; python engine/validate_templates.py
```

Expected: `16/16` templates pass.

- [ ] **Step 5: Browser smoke check if Playwright is available**

Use Playwright to open `output/遥远的救世主_圆桌洞见_v13.html` and check:

- initial page visible;
- ArrowRight changes counter;
- wheel changes counter;
- visible slide does not overflow viewport.

If Playwright is unavailable, report that browser verification was skipped.

## Self-Review

Spec coverage:

- Page contracts: Task 1.
- No-GPT stable mode: Task 2 and Task 5.
- Reading layout family first phase: Task 3.
- Information density and readability validation: Task 4.
- Skill documentation: Task 5.
- Verification: Task 6.

Out of scope for this plan:

- GPT enhanced mode.
- Automatic image generation pipeline.
- External image search.
- Full multi-theme system.

Type consistency:

- `ReadingBlock`, `ReadingPage`, `plan_reading_pages`, `render_reading_html`, and `validate_reading_html` are used consistently across tasks.

