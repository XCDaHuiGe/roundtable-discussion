# HTML-PPT V12 Stability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the unstable HTML-PPT main path with a V12 pipeline that plans pages, applies capacity rules, renders one navigation system, and validates final HTML.

**Architecture:** Add focused V12 modules under `engine/` instead of expanding legacy generators. The new CLI reads existing roundtable JSON, produces a structured page plan, renders a single-file HTML deck, then validates the final artifact before reporting success.

**Tech Stack:** Python standard library, `pytest`, existing project JSON content, optional browser validation after static validation.

---

## File Structure

- Create `engine/html_ppt_v12.py`: shared dataclasses, page type whitelist, text helpers, and capacity constants.
- Create `engine/html_ppt_v12_planner.py`: converts existing roundtable JSON into structured `Page` objects.
- Create `engine/html_ppt_v12_renderer.py`: renders `Page` objects into one complete HTML document with exactly one CSS/JS/navigation system.
- Create `engine/validate_html_ppt_v12.py`: validates final HTML for duplicate navigation, internal scroll, slide rules, and required interactions.
- Create `engine/render_html_ppt_v12.py`: CLI entrypoint that reads JSON, plans, renders, writes, validates, and exits non-zero on validation failure.
- Create `tests/test_html_ppt_v12_planner.py`: planner and capacity tests.
- Create `tests/test_html_ppt_v12_renderer.py`: renderer tests.
- Create `tests/test_validate_html_ppt_v12.py`: validator tests.
- Create `tests/test_render_html_ppt_v12_cli.py`: CLI integration tests.
- Modify `SKILL.md`: mark V12 as default HTML-PPT main path and legacy paths as reference only.
- Modify `.trae/skills/roundtable-html-ppt/SKILL.md`: replace free HTML-fragment protocol with V12 structured plan protocol.

## Task 1: Add Shared V12 Types And Capacity Rules

**Files:**
- Create: `engine/html_ppt_v12.py`
- Test: `tests/test_html_ppt_v12_planner.py`

- [ ] **Step 1: Write failing tests for text splitting and page type whitelist**

Create `tests/test_html_ppt_v12_planner.py` with:

```python
import pytest

from engine.html_ppt_v12 import Page, split_text, ensure_page_type


def test_split_text_keeps_short_text_as_one_chunk():
    assert split_text("短文本", 20) == ["短文本"]


def test_split_text_prefers_chinese_sentence_boundaries():
    text = "第一句很重要。第二句也重要。第三句继续推进。"
    assert split_text(text, 12) == [
        "第一句很重要。",
        "第二句也重要。",
        "第三句继续推进。",
    ]


def test_ensure_page_type_rejects_unknown_type():
    with pytest.raises(ValueError, match="unknown page_type"):
        ensure_page_type("random_html")


def test_page_rejects_unknown_type():
    with pytest.raises(ValueError, match="unknown page_type"):
        Page(page_type="bad", title="Bad")
```

- [ ] **Step 2: Run the tests and verify they fail**

Run:

```powershell
python -m pytest tests/test_html_ppt_v12_planner.py -q
```

Expected: import failure because `engine.html_ppt_v12` does not exist.

- [ ] **Step 3: Implement shared V12 primitives**

Create `engine/html_ppt_v12.py` with:

```python
# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any


PAGE_TYPES = {
    "cover",
    "insight_overview",
    "hypothesis_evolution",
    "tension_map",
    "experts",
    "round_overview",
    "speech",
    "clash",
    "cost_analysis",
    "human_nature",
    "consensus_state",
    "open_questions",
    "summary",
}


CAPACITY = {
    "title": 28,
    "subtitle": 60,
    "expert_belief": 60,
    "speech": 220,
    "clash_attack": 180,
    "clash_defense": 180,
    "insight_overview": 90,
    "open_question": 80,
    "summary": 120,
}


LAYOUT_BY_PAGE_TYPE = {
    "cover": "hero_split",
    "insight_overview": "list_compact",
    "hypothesis_evolution": "two_column_compare",
    "tension_map": "two_column_compare",
    "experts": "card_grid_2x3",
    "round_overview": "stacked_cards",
    "speech": "two_speeches",
    "clash": "single_clash",
    "cost_analysis": "stacked_cards",
    "human_nature": "stacked_cards",
    "consensus_state": "stacked_cards",
    "open_questions": "list_compact",
    "summary": "final_statement",
}


def ensure_page_type(page_type: str) -> str:
    if page_type not in PAGE_TYPES:
        raise ValueError(f"unknown page_type: {page_type}")
    return page_type


def normalize_text(value: Any) -> str:
    text = "" if value is None else str(value)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def summarize_text(value: Any, max_chars: int) -> str:
    text = normalize_text(value)
    if len(text) <= max_chars:
        return text
    chunks = split_text(text, max_chars)
    return chunks[0]


def split_text(value: Any, max_chars: int) -> list[str]:
    text = normalize_text(value)
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    sentences = [s for s in re.split(r"(?<=[。！？!?])", text) if s.strip()]
    chunks: list[str] = []
    current = ""
    for sentence in sentences or [text]:
        sentence = sentence.strip()
        if not sentence:
            continue
        if len(sentence) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(_hard_split(sentence, max_chars))
            continue
        if current and len(current) + len(sentence) > max_chars:
            chunks.append(current)
            current = sentence
        else:
            current += sentence
    if current:
        chunks.append(current)
    return chunks


def _hard_split(text: str, max_chars: int) -> list[str]:
    return [text[i:i + max_chars] for i in range(0, len(text), max_chars)]


@dataclass
class Page:
    page_type: str
    title: str
    layout: str | None = None
    items: list[dict[str, Any]] = field(default_factory=list)
    body: str = ""
    subtitle: str = ""
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.page_type = ensure_page_type(self.page_type)
        if self.layout is None:
            self.layout = LAYOUT_BY_PAGE_TYPE[self.page_type]
        self.title = summarize_text(self.title, CAPACITY["title"])
        self.subtitle = summarize_text(self.subtitle, CAPACITY["subtitle"])
        self.body = normalize_text(self.body)
```

- [ ] **Step 4: Run tests and verify pass**

Run:

```powershell
python -m pytest tests/test_html_ppt_v12_planner.py -q
```

Expected: `4 passed`.

- [ ] **Step 5: Commit**

```powershell
git add engine/html_ppt_v12.py tests/test_html_ppt_v12_planner.py
git commit -m "feat: add HTML-PPT V12 primitives"
```

## Task 2: Build Page Planner With Capacity-Based Splitting

**Files:**
- Modify: `engine/html_ppt_v12_planner.py`
- Modify: `tests/test_html_ppt_v12_planner.py`

- [ ] **Step 1: Add failing planner tests**

Append to `tests/test_html_ppt_v12_planner.py`:

```python
from engine.html_ppt_v12_planner import plan_pages


def sample_roundtable():
    return {
        "title": "《测试书》圆桌洞见",
        "subtitle": "六位专家讨论一个复杂问题",
        "experts": [
            {"name": f"专家{i}", "title": "思想家", "belief": "核心信念" * 20}
            for i in range(1, 7)
        ],
        "rounds": [
            {
                "topic": "第一轮主题",
                "core_question": "真正的问题是什么？",
                "stances": [
                    {"expert": f"专家{i}", "stance": "这是一个很长的观点。" * 20}
                    for i in range(1, 7)
                ],
                "clash_rounds": [
                    {
                        "attacker": "专家1",
                        "target": "专家2",
                        "attack_type": "逻辑攻击",
                        "attack_content": "攻击内容。" * 30,
                        "defense": "回应内容。" * 30,
                    }
                ],
            }
        ],
        "insights": [
            {"insight_title": "洞见一", "insight_content": "洞见内容。" * 30}
        ],
        "open_questions": ["开放问题。" * 20],
    }


def test_plan_pages_creates_core_page_sequence():
    pages = plan_pages(sample_roundtable())
    page_types = [p.page_type for p in pages]
    assert page_types[0] == "cover"
    assert "experts" in page_types
    assert "round_overview" in page_types
    assert "speech" in page_types
    assert "clash" in page_types
    assert page_types[-1] == "summary"


def test_plan_pages_splits_six_speeches_into_three_pages():
    pages = plan_pages(sample_roundtable())
    speech_pages = [p for p in pages if p.page_type == "speech"]
    assert len(speech_pages) == 3
    assert all(len(p.items) <= 2 for p in speech_pages)
    assert all(len(item["text"]) <= 220 for p in speech_pages for item in p.items)


def test_plan_pages_splits_long_clash_fields():
    pages = plan_pages(sample_roundtable())
    clash_pages = [p for p in pages if p.page_type == "clash"]
    assert len(clash_pages) >= 1
    assert all(len(item["attack"]) <= 180 for p in clash_pages for item in p.items)
    assert all(len(item["defense"]) <= 180 for p in clash_pages for item in p.items)
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```powershell
python -m pytest tests/test_html_ppt_v12_planner.py -q
```

Expected: import failure for `engine.html_ppt_v12_planner`.

- [ ] **Step 3: Implement planner**

Create `engine/html_ppt_v12_planner.py` with:

```python
# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from engine.html_ppt_v12 import CAPACITY, Page, summarize_text, split_text


def plan_pages(data: dict[str, Any]) -> list[Page]:
    pages: list[Page] = []
    title = data.get("title", "圆桌洞见")
    pages.append(Page("cover", title=title, subtitle=data.get("subtitle", "")))

    insights = data.get("insights") or []
    if insights:
        pages.append(_plan_insight_overview(insights))

    experts = data.get("experts") or []
    if experts:
        pages.append(_plan_experts(experts))

    for round_index, round_data in enumerate(data.get("rounds") or [], start=1):
        pages.append(_plan_round_overview(round_data, round_index))
        pages.extend(_plan_speeches(round_data, round_index))
        pages.extend(_plan_clashes(round_data, round_index))

    questions = data.get("open_questions") or []
    if questions:
        pages.append(_plan_open_questions(questions))

    pages.append(Page("summary", title="最终结论", body="深度不等于页数，深度等于认知增量。"))
    return pages


def _plan_insight_overview(insights: list[dict[str, Any]]) -> Page:
    items = []
    for insight in insights[:5]:
        items.append({
            "title": summarize_text(insight.get("insight_title", "洞见"), CAPACITY["title"]),
            "text": summarize_text(
                insight.get("insight_content", insight.get("attack_content", "")),
                CAPACITY["insight_overview"],
            ),
        })
    return Page("insight_overview", title="五大核心洞见", items=items)


def _plan_experts(experts: list[dict[str, Any]]) -> Page:
    items = []
    for expert in experts[:6]:
        items.append({
            "name": summarize_text(expert.get("name", ""), 12),
            "title": summarize_text(expert.get("title", expert.get("role", "")), 18),
            "belief": summarize_text(
                expert.get("belief", expert.get("core_belief", expert.get("description", ""))),
                CAPACITY["expert_belief"],
            ),
        })
    return Page("experts", title="专家阵容", items=items)


def _plan_round_overview(round_data: dict[str, Any], round_index: int) -> Page:
    return Page(
        "round_overview",
        title=f"第{round_index}轮：{round_data.get('topic', '讨论')}",
        body=summarize_text(round_data.get("core_question", ""), 160),
        meta={"round_index": round_index},
    )


def _plan_speeches(round_data: dict[str, Any], round_index: int) -> list[Page]:
    speech_items = []
    for stance in round_data.get("stances") or []:
        expert = stance.get("expert", stance.get("expert_name", "专家"))
        text = stance.get("stance", stance.get("content", stance.get("speech", "")))
        for part_index, chunk in enumerate(split_text(text, CAPACITY["speech"]), start=1):
            suffix = f"（{part_index}）" if part_index > 1 else ""
            speech_items.append({"expert": expert, "text": chunk, "part": suffix})

    pages = []
    for index in range(0, len(speech_items), 2):
        page_items = speech_items[index:index + 2]
        pages.append(Page(
            "speech",
            title=f"第{round_index}轮发言 {index // 2 + 1}",
            items=page_items,
            meta={"round_index": round_index},
        ))
    return pages


def _plan_clashes(round_data: dict[str, Any], round_index: int) -> list[Page]:
    pages = []
    for clash_index, clash in enumerate(round_data.get("clash_rounds") or [], start=1):
        attack_parts = split_text(clash.get("attack_content", ""), CAPACITY["clash_attack"]) or [""]
        defense_parts = split_text(clash.get("defense", clash.get("defense_content", "")), CAPACITY["clash_defense"]) or [""]
        count = max(len(attack_parts), len(defense_parts))
        for part_index in range(count):
            pages.append(Page(
                "clash",
                title=f"{clash.get('attacker', '攻击方')} → {clash.get('target', '回应方')}",
                items=[{
                    "attacker": clash.get("attacker", "攻击方"),
                    "target": clash.get("target", "回应方"),
                    "attack_type": clash.get("attack_type", "观点碰撞"),
                    "attack": attack_parts[part_index] if part_index < len(attack_parts) else "",
                    "defense": defense_parts[part_index] if part_index < len(defense_parts) else "",
                }],
                meta={"round_index": round_index, "clash_index": clash_index, "part_index": part_index + 1},
            ))
    return pages


def _plan_open_questions(questions: list[Any]) -> Page:
    items = [{"text": summarize_text(q, CAPACITY["open_question"])} for q in questions[:5]]
    return Page("open_questions", title="开放问题", items=items)
```

- [ ] **Step 4: Run planner tests**

Run:

```powershell
python -m pytest tests/test_html_ppt_v12_planner.py -q
```

Expected: all planner tests pass.

- [ ] **Step 5: Commit**

```powershell
git add engine/html_ppt_v12_planner.py tests/test_html_ppt_v12_planner.py
git commit -m "feat: plan HTML-PPT V12 pages"
```

## Task 3: Render One Stable HTML-PPT Document

**Files:**
- Create: `engine/html_ppt_v12_renderer.py`
- Test: `tests/test_html_ppt_v12_renderer.py`

- [ ] **Step 1: Write failing renderer tests**

Create `tests/test_html_ppt_v12_renderer.py` with:

```python
from engine.html_ppt_v12 import Page
from engine.html_ppt_v12_renderer import render_html


def test_render_html_has_single_navigation_system():
    html = render_html([
        Page("cover", title="封面"),
        Page("summary", title="总结", body="结论"),
    ], title="测试")
    assert html.count("function go(") == 1
    assert html.count("wheelTimer") == 3
    assert html.count('id="navDots"') == 1
    assert html.count('class="slide visible"') == 1
    assert html.count('class="slide"') == 1


def test_render_html_contains_required_navigation_contract():
    html = render_html([Page("cover", title="封面")], title="测试")
    assert "e.preventDefault()" in html
    assert "setTimeout(()=>wheelTimer=null,400)" in html
    assert "ArrowDown" in html
    assert "PageDown" in html
    assert "Home" in html
    assert "End" in html
    assert "document.body.addEventListener('click'" in html
```

- [ ] **Step 2: Run renderer tests and verify failure**

Run:

```powershell
python -m pytest tests/test_html_ppt_v12_renderer.py -q
```

Expected: import failure for `engine.html_ppt_v12_renderer`.

- [ ] **Step 3: Implement renderer**

Create `engine/html_ppt_v12_renderer.py` with focused escaping helpers, layout renderers, global CSS, and the exact AGENTS navigation contract. Keep generated content class-based and avoid inline style except the progress width changed by JS.

- [ ] **Step 4: Run renderer tests**

Run:

```powershell
python -m pytest tests/test_html_ppt_v12_renderer.py -q
```

Expected: renderer tests pass.

- [ ] **Step 5: Commit**

```powershell
git add engine/html_ppt_v12_renderer.py tests/test_html_ppt_v12_renderer.py
git commit -m "feat: render stable HTML-PPT V12 deck"
```

## Task 4: Validate Final HTML Output

**Files:**
- Create: `engine/validate_html_ppt_v12.py`
- Test: `tests/test_validate_html_ppt_v12.py`

- [ ] **Step 1: Write failing validator tests**

Create `tests/test_validate_html_ppt_v12.py` with:

```python
from engine.html_ppt_v12 import Page
from engine.html_ppt_v12_renderer import render_html
from engine.validate_html_ppt_v12 import validate_html


def test_validate_html_accepts_v12_renderer_output():
    result = validate_html(render_html([Page("cover", title="封面")], title="测试"))
    assert result.ok, result.errors


def test_validate_html_rejects_internal_scroll():
    html = render_html([Page("cover", title="封面")], title="测试")
    result = validate_html(html + "<style>.x{overflow-y:auto}</style>")
    assert not result.ok
    assert any("internal scroll" in error for error in result.errors)


def test_validate_html_rejects_duplicate_navigation():
    html = render_html([Page("cover", title="封面")], title="测试")
    result = validate_html(html.replace("</body>", "<script>let wheelTimer=null;</script></body>"))
    assert not result.ok
    assert any("wheelTimer" in error for error in result.errors)
```

- [ ] **Step 2: Run validator tests and verify failure**

Run:

```powershell
python -m pytest tests/test_validate_html_ppt_v12.py -q
```

Expected: import failure for `engine.validate_html_ppt_v12`.

- [ ] **Step 3: Implement validator**

Create `engine/validate_html_ppt_v12.py` with a `ValidationResult` dataclass, `validate_html(html: str)`, and a CLI that exits `0` when valid and `1` when invalid.

- [ ] **Step 4: Run validator tests**

Run:

```powershell
python -m pytest tests/test_validate_html_ppt_v12.py -q
```

Expected: validator tests pass.

- [ ] **Step 5: Commit**

```powershell
git add engine/validate_html_ppt_v12.py tests/test_validate_html_ppt_v12.py
git commit -m "feat: validate HTML-PPT V12 output"
```

## Task 5: Add V12 CLI Entrypoint

**Files:**
- Create: `engine/render_html_ppt_v12.py`
- Test: `tests/test_render_html_ppt_v12_cli.py`

- [ ] **Step 1: Write failing CLI test**

Create `tests/test_render_html_ppt_v12_cli.py` with:

```python
import json
import subprocess
import sys


def test_render_html_ppt_v12_cli_writes_valid_html(tmp_path):
    input_path = tmp_path / "input.json"
    output_path = tmp_path / "deck.html"
    input_path.write_text(json.dumps({
        "title": "测试圆桌",
        "subtitle": "稳定生成",
        "experts": [{"name": "专家1", "title": "研究者", "belief": "保持质疑"}],
        "rounds": [{"topic": "主题", "core_question": "问题", "stances": [{"expert": "专家1", "stance": "观点"}]}],
        "insights": [{"insight_title": "洞见", "insight_content": "内容"}],
    }, ensure_ascii=False), encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, "engine/render_html_ppt_v12.py", str(input_path), "--output", str(output_path)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    html = output_path.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in html
    assert "测试圆桌" in html
    assert "HTML-PPT V12 validation passed" in completed.stdout
```

- [ ] **Step 2: Run CLI test and verify failure**

Run:

```powershell
python -m pytest tests/test_render_html_ppt_v12_cli.py -q
```

Expected: script missing failure.

- [ ] **Step 3: Implement CLI**

Create `engine/render_html_ppt_v12.py` that reads UTF-8/UTF-8-SIG JSON, calls `plan_pages()`, calls `render_html()`, writes output, runs `validate_html()`, prints page count, and exits `1` on validation errors.

- [ ] **Step 4: Run CLI test**

Run:

```powershell
python -m pytest tests/test_render_html_ppt_v12_cli.py -q
```

Expected: CLI test passes.

- [ ] **Step 5: Commit**

```powershell
git add engine/render_html_ppt_v12.py tests/test_render_html_ppt_v12_cli.py
git commit -m "feat: add HTML-PPT V12 renderer CLI"
```

## Task 6: Update Skills And Documentation Boundary

**Files:**
- Modify: `SKILL.md`
- Modify: `.trae/skills/roundtable-html-ppt/SKILL.md`

- [ ] **Step 1: Update main skill documentation**

Modify `SKILL.md` to state:

```markdown
### HTML-PPT 主链路（V12.0）

默认入口：

```bash
python engine/render_html_ppt_v12.py content/书名_V8.json --output output/书名_圆桌洞见.html
```

V12 规则：

- Python 负责页面计划、容量拆页、布局、渲染、验收。
- Agent 不再直接生成任意 HTML 片段作为默认主链路。
- 最终 HTML 只允许一套导航系统。
- 禁止内部滚动，内容过长必须拆页。
- 旧 `generate_v4/v5/v6` 和 `page-fragment-normalizer*` 是 legacy 参考，不再作为默认入口扩展。
```

- [ ] **Step 2: Update roundtable HTML-PPT skill**

Modify `.trae/skills/roundtable-html-ppt/SKILL.md` so it describes the V12 structured flow:

```markdown
Agent 提供内容理解和页面意图，Python V12 主链路负责：

1. Page Planner
2. Layout Engine
3. Capacity Engine
4. Single Renderer
5. Acceptance Validator

禁止 Agent 输出完整 HTML、重复导航脚本、inline style、内部滚动。
```

- [ ] **Step 3: Commit docs**

```powershell
git add SKILL.md .trae/skills/roundtable-html-ppt/SKILL.md
git commit -m "docs: make HTML-PPT V12 the default path"
```

## Task 7: Full Verification

**Files:**
- Generated only: `output/遥远的救世主_圆桌洞见_v12.html`

- [ ] **Step 1: Run focused tests**

Run:

```powershell
python -m pytest tests/test_html_ppt_v12_planner.py tests/test_html_ppt_v12_renderer.py tests/test_validate_html_ppt_v12.py tests/test_render_html_ppt_v12_cli.py -q
```

Expected: all V12 tests pass.

- [ ] **Step 2: Run full test suite**

Run:

```powershell
python -m pytest -q
```

Expected: all tests pass.

- [ ] **Step 3: Generate real sample deck**

Run:

```powershell
python engine/render_html_ppt_v12.py content/遥远的救世主_V8.json --output output/遥远的救世主_圆桌洞见_v12.html
```

Expected: output file created and stdout includes `HTML-PPT V12 validation passed`.

- [ ] **Step 4: Validate template registry remains healthy**

Run:

```powershell
python engine/validate_templates.py
```

Expected: existing template validation still passes or known legacy-only warnings are reported without blocking V12.

- [ ] **Step 5: Final commit if verification artifacts are intentionally tracked**

If no generated output should be tracked, commit only source/docs/tests:

```powershell
git status --short
git add engine/html_ppt_v12.py engine/html_ppt_v12_planner.py engine/html_ppt_v12_renderer.py engine/validate_html_ppt_v12.py engine/render_html_ppt_v12.py tests/test_html_ppt_v12_planner.py tests/test_html_ppt_v12_renderer.py tests/test_validate_html_ppt_v12.py tests/test_render_html_ppt_v12_cli.py SKILL.md .trae/skills/roundtable-html-ppt/SKILL.md
git commit -m "feat: stabilize HTML-PPT V12 main path"
```

## Self-Review

Spec coverage:

- Page Planner is covered by Tasks 1 and 2.
- Layout Engine is covered by page layouts in Task 3.
- Capacity Engine is covered by Task 2.
- Single Renderer is covered by Task 3.
- Acceptance Validator is covered by Task 4.
- CLI main path is covered by Task 5.
- Skill boundary updates are covered by Task 6.
- Verification is covered by Task 7.

Placeholder scan:

- No unfinished placeholder markers.
- The only legacy references are explicit boundaries from the design.

Type consistency:

- `Page`, `plan_pages`, `render_html`, and `validate_html` names are consistent across tasks.
- The validator returns a result object with `ok` and `errors`, used consistently by tests and CLI.
