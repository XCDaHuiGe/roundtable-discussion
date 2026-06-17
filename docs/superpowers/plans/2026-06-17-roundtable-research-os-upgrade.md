# Roundtable Research OS Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first working slice of the Roundtable Research OS upgrade: a validated `CognitiveModel.v1`, V8 compatibility adapter, cognitive and roundtable quality gates, cognitive page planner, V13 renderer integration, and publish-time validation hooks.

**Architecture:** Keep V12/V13 as the stable HTML base. Add a new structured cognitive layer in `engine/cognitive_model/`, quality checks in `engine/quality_gates/`, and a page planner in `engine/html_ppt/` that converts `CognitiveModel` into existing V13 `ReadingPage` objects. The first slice must be useful with existing `content/*_V8.json` files and must never require direct Agent-generated HTML.

**Tech Stack:** Python 3, dataclasses, standard-library `json`, existing V13 planner/renderer/validator modules, pytest.

---

## Scope

This plan implements the first production slice of the larger upgrade. It proves the new bottom layer, validation layer, and HTML planning layer without rewriting old templates.

In scope:

- Define `CognitiveModel.v1` data structures.
- Validate cognitive, roundtable, and HTML-facing model quality.
- Convert existing V8 JSON into partial `CognitiveModel`.
- Convert `CognitiveModel` into V13 `ReadingPage` slides.
- Add a CLI that renders V14-style cognitive HTML through the V13 renderer.
- Add tests and documentation for the new default path.

Out of scope for this plan:

- Rewriting every legacy template.
- Generating new book content from scratch.
- Browser automation for every historical output.
- PPTX export.
- External LLM API integration.

## File Structure

Create:

- `engine/cognitive_model/__init__.py`  
  Public exports for model types and adapter helpers.

- `engine/cognitive_model/schema.py`  
  Dataclasses for `CognitiveModel`, nested sections, `QualityIssue`, and serialization helpers.

- `engine/cognitive_model/adapters.py`  
  `from_v8(data: dict) -> CognitiveModel` compatibility adapter.

- `engine/quality_gates/__init__.py`  
  Public exports for quality validators.

- `engine/quality_gates/cognitive_quality.py`  
  Cognitive quality rules: core question, baseline, delta, signature terms, root rank, QA chain.

- `engine/quality_gates/roundtable_quality.py`  
  Roundtable quality rules: participant roles, tension axes, response relationships, moderator cracks.

- `engine/html_ppt/cognitive_page_contracts.py`  
  Page type constants and required field contracts.

- `engine/html_ppt/cognitive_page_planner.py`  
  Convert `CognitiveModel` into `list[ReadingPage]`.

- `engine/render_cognitive_html.py`  
  CLI and function entry point for V14-style cognitive HTML output.

- `tests/test_cognitive_model_schema.py`
- `tests/test_cognitive_model_adapter.py`
- `tests/test_cognitive_quality_gates.py`
- `tests/test_roundtable_quality_gates.py`
- `tests/test_cognitive_page_planner.py`
- `tests/test_render_cognitive_html_cli.py`

Modify:

- `SKILL.md`  
  Add a short V14 / Research OS section after V13, pointing to the new render command and preserving V13 as the visual base.

- `README.md`  
  Add a short project status note that Research OS is now the structured upgrade path. Do not rewrite the whole mojibake file in this plan.

Do not touch:

- Existing dirty template files unless a later task explicitly chooses to integrate them.
- Existing `output/` artifacts.
- Existing deleted files shown in `git status`.

---

### Task 1: CognitiveModel Schema

**Files:**
- Create: `engine/cognitive_model/__init__.py`
- Create: `engine/cognitive_model/schema.py`
- Test: `tests/test_cognitive_model_schema.py`

- [ ] **Step 1: Write the failing schema tests**

Create `tests/test_cognitive_model_schema.py`:

```python
from engine.cognitive_model.schema import CognitiveModel, QualityIssue


def test_cognitive_model_defaults_to_v1_and_serializes_to_dict():
    model = CognitiveModel(title="测试书", source_type="book")

    data = model.to_dict()

    assert data["meta"]["title"] == "测试书"
    assert data["meta"]["source_type"] == "book"
    assert data["meta"]["version"] == "CognitiveModel.v1"
    assert data["book_spine"]["core_question"] == ""
    assert data["roundtable"]["rounds"] == []


def test_quality_issue_serializes_level_code_message_and_path():
    issue = QualityIssue(level="warning", code="missing_delta", message="缺少作者位移", path="book_spine.delta_sentence")

    assert issue.to_dict() == {
        "level": "warning",
        "code": "missing_delta",
        "message": "缺少作者位移",
        "path": "book_spine.delta_sentence",
    }


def test_cognitive_model_can_store_quality_issues():
    model = CognitiveModel(title="测试书", source_type="book")
    model.quality.checks.append(QualityIssue("warning", "partial_model", "旧数据只能形成部分模型", "meta"))

    assert model.to_dict()["quality"]["checks"][0]["code"] == "partial_model"
```

- [ ] **Step 2: Run the new tests and confirm they fail**

Run:

```powershell
python -m pytest tests/test_cognitive_model_schema.py -v
```

Expected:

```text
ModuleNotFoundError: No module named 'engine.cognitive_model'
```

- [ ] **Step 3: Implement the schema**

Create `engine/cognitive_model/schema.py`:

```python
# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


IssueLevel = Literal["error", "warning"]


@dataclass
class QualityIssue:
    level: IssueLevel
    code: str
    message: str
    path: str

    def to_dict(self) -> dict[str, str]:
        return {
            "level": self.level,
            "code": self.code,
            "message": self.message,
            "path": self.path,
        }


@dataclass
class Meta:
    title: str
    source_type: str = "book"
    version: str = "CognitiveModel.v1"


@dataclass
class SourceUnderstanding:
    material_map: list[dict[str, Any]] = field(default_factory=list)
    author_problem: str = ""
    paragraph_roles: list[dict[str, Any]] = field(default_factory=list)
    key_terms: list[str] = field(default_factory=list)


@dataclass
class BookSpine:
    core_question: str = ""
    baseline_positions: list[str] = field(default_factory=list)
    consensus_baseline: str = ""
    author_move: str = ""
    delta_sentence: str = ""
    delta_type: str = ""
    signature_terms: list[str] = field(default_factory=list)
    landing_sentence: str = ""
    carryaway: str = ""


@dataclass
class RootRank:
    domain_assumptions: list[str] = field(default_factory=list)
    phenomena: list[str] = field(default_factory=list)
    candidate_generators: list[str] = field(default_factory=list)
    root_generators: list[str] = field(default_factory=list)
    regeneration_matrix: list[dict[str, Any]] = field(default_factory=list)
    prediction_tests: list[str] = field(default_factory=list)


@dataclass
class Roundtable:
    participants: list[dict[str, Any]] = field(default_factory=list)
    tension_axes: list[str] = field(default_factory=list)
    rounds: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class Distillation:
    insights: list[dict[str, Any]] = field(default_factory=list)
    qa_chain: list[dict[str, Any]] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)
    future_bets: list[str] = field(default_factory=list)


@dataclass
class Publishing:
    slides: list[dict[str, Any]] = field(default_factory=list)
    cards: list[dict[str, Any]] = field(default_factory=list)
    index_summary: str = ""


@dataclass
class Quality:
    checks: list[QualityIssue] = field(default_factory=list)


@dataclass
class CognitiveModel:
    title: str
    source_type: str = "book"
    source_understanding: SourceUnderstanding = field(default_factory=SourceUnderstanding)
    book_spine: BookSpine = field(default_factory=BookSpine)
    root_rank: RootRank = field(default_factory=RootRank)
    roundtable: Roundtable = field(default_factory=Roundtable)
    distillation: Distillation = field(default_factory=Distillation)
    publishing: Publishing = field(default_factory=Publishing)
    quality: Quality = field(default_factory=Quality)

    @property
    def meta(self) -> Meta:
        return Meta(title=self.title, source_type=self.source_type)

    def to_dict(self) -> dict[str, Any]:
        data = {
            "meta": asdict(self.meta),
            "source_understanding": asdict(self.source_understanding),
            "book_spine": asdict(self.book_spine),
            "root_rank": asdict(self.root_rank),
            "roundtable": asdict(self.roundtable),
            "distillation": asdict(self.distillation),
            "publishing": asdict(self.publishing),
            "quality": {"checks": [issue.to_dict() for issue in self.quality.checks]},
        }
        return data
```

Create `engine/cognitive_model/__init__.py`:

```python
from engine.cognitive_model.schema import (
    BookSpine,
    CognitiveModel,
    Distillation,
    QualityIssue,
    RootRank,
    Roundtable,
    SourceUnderstanding,
)

__all__ = [
    "BookSpine",
    "CognitiveModel",
    "Distillation",
    "QualityIssue",
    "RootRank",
    "Roundtable",
    "SourceUnderstanding",
]
```

- [ ] **Step 4: Run schema tests**

Run:

```powershell
python -m pytest tests/test_cognitive_model_schema.py -v
```

Expected:

```text
3 passed
```

- [ ] **Step 5: Commit Task 1**

```powershell
git add engine/cognitive_model tests/test_cognitive_model_schema.py
git commit -m "feat: add cognitive model schema"
```

---

### Task 2: V8 Compatibility Adapter

**Files:**
- Create: `engine/cognitive_model/adapters.py`
- Modify: `engine/cognitive_model/__init__.py`
- Test: `tests/test_cognitive_model_adapter.py`

- [ ] **Step 1: Write adapter tests**

Create `tests/test_cognitive_model_adapter.py`:

```python
from engine.cognitive_model.adapters import from_v8


def sample_v8():
    return {
        "title": "《测试书》圆桌洞见",
        "subtitle": "文化属性与命运",
        "experts": [
            {"name": "丁元英", "title": "思想者", "core_belief": "如实观照"},
            {"name": "韩非子", "title": "法家", "core_belief": "制度约束"},
        ],
        "rounds": [
            {
                "topic": "文化属性真的决定命运吗",
                "core_question": "文化是原因还是结果？",
                "stances": [
                    {"expert": "丁元英", "stance": "文化属性决定行动方式。"},
                    {"expert": "韩非子", "stance": "制度才决定路径。"},
                ],
                "clash_rounds": [
                    {
                        "attacker": "韩非子",
                        "target": "丁元英",
                        "attack_type": "制度优先",
                        "attack_content": "文化解释掩盖规则缺失。",
                        "defense": "规则也来自长期文化选择。",
                    }
                ],
            }
        ],
        "insights": [
            {"insight_title": "文化不是宿命", "insight_content": "文化更像行动系统。"}
        ],
        "open_questions": ["弱势文化是原因还是结果？"],
    }


def test_from_v8_preserves_title_experts_rounds_and_insights():
    model = from_v8(sample_v8())

    assert model.title == "《测试书》圆桌洞见"
    assert model.source_type == "book"
    assert model.book_spine.core_question == "文化是原因还是结果？"
    assert model.roundtable.participants[0]["name"] == "丁元英"
    assert model.roundtable.rounds[0]["guiding_question"] == "文化是原因还是结果？"
    assert model.distillation.insights[0]["title"] == "文化不是宿命"
    assert model.distillation.open_questions == ["弱势文化是原因还是结果？"]


def test_from_v8_marks_missing_deep_fields_as_warnings():
    model = from_v8(sample_v8())
    codes = {issue.code for issue in model.quality.checks}

    assert "partial_model" in codes
    assert "missing_delta_sentence" in codes
    assert "missing_root_rank" in codes
    assert "missing_qa_chain" in codes
```

- [ ] **Step 2: Run adapter tests and confirm they fail**

Run:

```powershell
python -m pytest tests/test_cognitive_model_adapter.py -v
```

Expected:

```text
ModuleNotFoundError or ImportError for engine.cognitive_model.adapters
```

- [ ] **Step 3: Implement `from_v8`**

Create `engine/cognitive_model/adapters.py`:

```python
# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from engine.cognitive_model.schema import CognitiveModel, QualityIssue


def from_v8(data: dict[str, Any]) -> CognitiveModel:
    model = CognitiveModel(title=str(data.get("title") or "圆桌洞见"), source_type="book")
    model.source_understanding.author_problem = str(data.get("subtitle") or "")
    model.roundtable.participants = _participants(data.get("experts") or [])
    model.roundtable.rounds = [_round(round_data, index) for index, round_data in enumerate(data.get("rounds") or [], start=1)]
    model.roundtable.tension_axes = [
        str(round_data.get("topic") or round_data.get("core_question") or f"第{index}轮张力")
        for index, round_data in enumerate(data.get("rounds") or [], start=1)
    ]
    model.distillation.insights = _insights(data.get("insights") or [])
    model.distillation.open_questions = [str(item) for item in (data.get("open_questions") or [])]

    if model.roundtable.rounds:
        first_round = model.roundtable.rounds[0]
        model.book_spine.core_question = str(first_round.get("guiding_question") or "")
    if model.distillation.insights:
        model.book_spine.landing_sentence = str(model.distillation.insights[0].get("content") or "")
        model.book_spine.carryaway = str(model.distillation.insights[0].get("title") or "")

    _mark_partial(model)
    return model


def _participants(experts: list[dict[str, Any]]) -> list[dict[str, str]]:
    participants: list[dict[str, str]] = []
    for expert in experts:
        name = str(expert.get("name") or expert.get("expert") or "")
        if not name:
            continue
        participants.append({
            "name": name,
            "role": str(expert.get("title") or expert.get("category") or "专家"),
            "function": str(expert.get("core_belief") or expert.get("stance") or "提供解释框架"),
        })
    return participants


def _round(round_data: dict[str, Any], index: int) -> dict[str, Any]:
    speeches = []
    previous_id: str | None = None
    for speech_index, stance in enumerate(round_data.get("stances") or [], start=1):
        speech_id = f"r{index}s{speech_index}"
        speeches.append({
            "id": speech_id,
            "expert": str(stance.get("expert") or stance.get("expert_name") or "专家"),
            "stance": str(stance.get("stance") or stance.get("content") or stance.get("speech") or ""),
            "responds_to": previous_id,
            "action_type": "definition" if previous_id is None else "response",
            "claim": str(stance.get("stance") or stance.get("content") or stance.get("speech") or ""),
            "evidence": "",
            "one_line": str(stance.get("stance") or stance.get("content") or stance.get("speech") or "")[:60],
        })
        previous_id = speech_id
    return {
        "round_index": index,
        "guiding_question": str(round_data.get("core_question") or round_data.get("topic") or ""),
        "tension_axis": str(round_data.get("topic") or round_data.get("core_question") or ""),
        "speeches": speeches,
        "clashes": list(round_data.get("clash_rounds") or []),
        "moderator": {
            "core_crack": str(round_data.get("summary") or round_data.get("topic") or ""),
            "structure_map": "",
            "next_question": "",
        },
    }


def _insights(insights: list[dict[str, Any]]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for insight in insights:
        result.append({
            "title": str(insight.get("insight_title") or insight.get("title") or "洞见"),
            "content": str(insight.get("insight_content") or insight.get("content") or insight.get("attack_content") or ""),
            "evidence": str(insight.get("evidence") or ""),
        })
    return result


def _mark_partial(model: CognitiveModel) -> None:
    model.quality.checks.append(QualityIssue("warning", "partial_model", "V8 输入只能形成部分 CognitiveModel", "meta"))
    if not model.book_spine.delta_sentence:
        model.quality.checks.append(QualityIssue("warning", "missing_delta_sentence", "缺少作者位移 delta 句", "book_spine.delta_sentence"))
    if not model.root_rank.root_generators:
        model.quality.checks.append(QualityIssue("warning", "missing_root_rank", "缺少根秩生成器", "root_rank.root_generators"))
    if not model.distillation.qa_chain:
        model.quality.checks.append(QualityIssue("warning", "missing_qa_chain", "缺少问答链", "distillation.qa_chain"))
```

Modify `engine/cognitive_model/__init__.py`:

```python
from engine.cognitive_model.adapters import from_v8
from engine.cognitive_model.schema import (
    BookSpine,
    CognitiveModel,
    Distillation,
    QualityIssue,
    RootRank,
    Roundtable,
    SourceUnderstanding,
)

__all__ = [
    "BookSpine",
    "CognitiveModel",
    "Distillation",
    "QualityIssue",
    "RootRank",
    "Roundtable",
    "SourceUnderstanding",
    "from_v8",
]
```

- [ ] **Step 4: Run adapter and schema tests**

Run:

```powershell
python -m pytest tests/test_cognitive_model_schema.py tests/test_cognitive_model_adapter.py -v
```

Expected:

```text
5 passed
```

- [ ] **Step 5: Commit Task 2**

```powershell
git add engine/cognitive_model tests/test_cognitive_model_adapter.py
git commit -m "feat: adapt v8 data to cognitive model"
```

---

### Task 3: Cognitive Quality Gate

**Files:**
- Create: `engine/quality_gates/__init__.py`
- Create: `engine/quality_gates/cognitive_quality.py`
- Test: `tests/test_cognitive_quality_gates.py`

- [ ] **Step 1: Write cognitive quality tests**

Create `tests/test_cognitive_quality_gates.py`:

```python
from engine.cognitive_model.schema import CognitiveModel
from engine.quality_gates.cognitive_quality import validate_cognitive_quality


def complete_model():
    model = CognitiveModel(title="测试书")
    model.book_spine.core_question = "人为什么会把适应误认为命运？"
    model.book_spine.consensus_baseline = "常见回答把命运理解为个人努力不足。"
    model.book_spine.author_move = "作者把问题转向脑与环境的互动机制。"
    model.book_spine.delta_sentence = "之前大家以为命运来自意志强弱，作者说命运来自脑的适应回路。"
    model.book_spine.signature_terms = ["适应回路"]
    model.root_rank.candidate_generators = ["奖励回路", "注意力筛选"]
    model.root_rank.root_generators = ["适应回路"]
    model.root_rank.phenomena = ["习惯形成", "情绪反应", "学习迁移"]
    model.root_rank.regeneration_matrix = [
        {"generator": "适应回路", "phenomenon": "习惯形成"},
        {"generator": "适应回路", "phenomenon": "情绪反应"},
        {"generator": "适应回路", "phenomenon": "学习迁移"},
    ]
    model.distillation.qa_chain = [
        {"question": "问题是什么？", "answer": {"conclusion": "问题是适应被误读。", "boundary": "不解释全部人生。"}}
    ]
    return model


def test_validate_cognitive_quality_passes_complete_model():
    result = validate_cognitive_quality(complete_model())

    assert result["ok"] is True
    assert result["errors"] == []


def test_validate_cognitive_quality_reports_missing_delta_and_rank():
    model = CognitiveModel(title="测试书")
    model.book_spine.core_question = "测试问题？"

    result = validate_cognitive_quality(model)
    codes = {issue["code"] for issue in result["errors"]}

    assert "missing_consensus_baseline" in codes
    assert "missing_delta_sentence" in codes
    assert "insufficient_candidate_generators" in codes
    assert "missing_qa_chain" in codes
```

- [ ] **Step 2: Run the tests and confirm failure**

Run:

```powershell
python -m pytest tests/test_cognitive_quality_gates.py -v
```

Expected:

```text
ModuleNotFoundError: No module named 'engine.quality_gates'
```

- [ ] **Step 3: Implement cognitive validator**

Create `engine/quality_gates/cognitive_quality.py`:

```python
# -*- coding: utf-8 -*-
from __future__ import annotations

from engine.cognitive_model.schema import CognitiveModel, QualityIssue


def validate_cognitive_quality(model: CognitiveModel) -> dict[str, object]:
    errors: list[QualityIssue] = []

    if not model.book_spine.core_question.strip():
        errors.append(QualityIssue("error", "missing_core_question", "缺少核心问题", "book_spine.core_question"))
    if not model.book_spine.consensus_baseline.strip():
        errors.append(QualityIssue("error", "missing_consensus_baseline", "缺少旧共识或常见回答", "book_spine.consensus_baseline"))
    if not model.book_spine.delta_sentence.strip():
        errors.append(QualityIssue("error", "missing_delta_sentence", "缺少作者位移 delta 句", "book_spine.delta_sentence"))
    elif "之前" not in model.book_spine.delta_sentence or "作者说" not in model.book_spine.delta_sentence:
        errors.append(QualityIssue("error", "invalid_delta_sentence", "delta 句必须表达旧回答与作者新回答", "book_spine.delta_sentence"))
    if not model.book_spine.signature_terms:
        errors.append(QualityIssue("error", "missing_signature_terms", "缺少作者指纹术语", "book_spine.signature_terms"))
    if len(model.root_rank.candidate_generators) < 2:
        errors.append(QualityIssue("error", "insufficient_candidate_generators", "候选生成器少于 2 个", "root_rank.candidate_generators"))
    if not model.root_rank.root_generators:
        errors.append(QualityIssue("error", "missing_root_generators", "缺少最终根生成器", "root_rank.root_generators"))
    if len(model.root_rank.regeneration_matrix) < 3:
        errors.append(QualityIssue("error", "insufficient_regeneration_matrix", "根生成器回测少于 3 个现象", "root_rank.regeneration_matrix"))
    if not model.distillation.qa_chain:
        errors.append(QualityIssue("error", "missing_qa_chain", "缺少问答链", "distillation.qa_chain"))

    return {
        "ok": not errors,
        "errors": [issue.to_dict() for issue in errors],
    }
```

Create `engine/quality_gates/__init__.py`:

```python
from engine.quality_gates.cognitive_quality import validate_cognitive_quality

__all__ = ["validate_cognitive_quality"]
```

- [ ] **Step 4: Run cognitive quality tests**

Run:

```powershell
python -m pytest tests/test_cognitive_quality_gates.py -v
```

Expected:

```text
2 passed
```

- [ ] **Step 5: Commit Task 3**

```powershell
git add engine/quality_gates tests/test_cognitive_quality_gates.py
git commit -m "feat: add cognitive quality gate"
```

---

### Task 4: Roundtable Quality Gate

**Files:**
- Create: `engine/quality_gates/roundtable_quality.py`
- Modify: `engine/quality_gates/__init__.py`
- Test: `tests/test_roundtable_quality_gates.py`

- [ ] **Step 1: Write roundtable quality tests**

Create `tests/test_roundtable_quality_gates.py`:

```python
from engine.cognitive_model.schema import CognitiveModel
from engine.quality_gates.roundtable_quality import validate_roundtable_quality


def test_roundtable_quality_requires_responses_after_first_speech():
    model = CognitiveModel(title="测试书")
    model.roundtable.participants = [{"name": "A", "function": "定义问题"}]
    model.roundtable.rounds = [
        {
            "round_index": 1,
            "guiding_question": "问题？",
            "tension_axis": "个人选择 / 结构约束",
            "speeches": [
                {"id": "r1s1", "expert": "A", "responds_to": None, "action_type": "definition"},
                {"id": "r1s2", "expert": "B", "responds_to": None, "action_type": "response"},
            ],
            "moderator": {"core_crack": "裂缝", "next_question": "下一问？"},
        }
    ]

    result = validate_roundtable_quality(model)
    codes = {issue["code"] for issue in result["errors"]}

    assert "missing_response_link" in codes


def test_roundtable_quality_passes_when_round_has_tension_responses_and_moderator():
    model = CognitiveModel(title="测试书")
    model.roundtable.participants = [{"name": "A", "function": "定义问题"}]
    model.roundtable.rounds = [
        {
            "round_index": 1,
            "guiding_question": "问题？",
            "tension_axis": "个人选择 / 结构约束",
            "speeches": [
                {"id": "r1s1", "expert": "A", "responds_to": None, "action_type": "definition"},
                {"id": "r1s2", "expert": "B", "responds_to": "r1s1", "action_type": "response"},
            ],
            "moderator": {"core_crack": "裂缝", "next_question": "下一问？"},
        }
    ]

    result = validate_roundtable_quality(model)

    assert result["ok"] is True
```

- [ ] **Step 2: Run tests and confirm failure**

Run:

```powershell
python -m pytest tests/test_roundtable_quality_gates.py -v
```

Expected:

```text
ModuleNotFoundError or ImportError for roundtable_quality
```

- [ ] **Step 3: Implement roundtable validator**

Create `engine/quality_gates/roundtable_quality.py`:

```python
# -*- coding: utf-8 -*-
from __future__ import annotations

from engine.cognitive_model.schema import CognitiveModel, QualityIssue


def validate_roundtable_quality(model: CognitiveModel) -> dict[str, object]:
    errors: list[QualityIssue] = []
    if not model.roundtable.participants:
        errors.append(QualityIssue("error", "missing_participants", "缺少专家参与者", "roundtable.participants"))

    for round_index, round_data in enumerate(model.roundtable.rounds, start=1):
        path = f"roundtable.rounds[{round_index - 1}]"
        if not str(round_data.get("tension_axis") or "").strip():
            errors.append(QualityIssue("error", "missing_tension_axis", "每轮必须有张力轴", f"{path}.tension_axis"))
        speeches = list(round_data.get("speeches") or [])
        for speech_index, speech in enumerate(speeches):
            speech_path = f"{path}.speeches[{speech_index}]"
            if not str(speech.get("action_type") or "").strip():
                errors.append(QualityIssue("error", "missing_action_type", "发言缺少行动类型", f"{speech_path}.action_type"))
            if speech_index > 0 and not speech.get("responds_to"):
                errors.append(QualityIssue("error", "missing_response_link", "非首条发言必须回应上一发言", f"{speech_path}.responds_to"))
        moderator = round_data.get("moderator") or {}
        if not str(moderator.get("core_crack") or "").strip():
            errors.append(QualityIssue("error", "missing_moderator_crack", "主持人缺少裂缝提炼", f"{path}.moderator.core_crack"))
        if not str(moderator.get("next_question") or "").strip():
            errors.append(QualityIssue("error", "missing_next_question", "主持人缺少下一问", f"{path}.moderator.next_question"))

    return {
        "ok": not errors,
        "errors": [issue.to_dict() for issue in errors],
    }
```

Modify `engine/quality_gates/__init__.py`:

```python
from engine.quality_gates.cognitive_quality import validate_cognitive_quality
from engine.quality_gates.roundtable_quality import validate_roundtable_quality

__all__ = ["validate_cognitive_quality", "validate_roundtable_quality"]
```

- [ ] **Step 4: Run roundtable quality tests**

Run:

```powershell
python -m pytest tests/test_roundtable_quality_gates.py -v
```

Expected:

```text
2 passed
```

- [ ] **Step 5: Commit Task 4**

```powershell
git add engine/quality_gates tests/test_roundtable_quality_gates.py
git commit -m "feat: add roundtable quality gate"
```

---

### Task 5: Cognitive Page Planner

**Files:**
- Create: `engine/html_ppt/cognitive_page_contracts.py`
- Create: `engine/html_ppt/cognitive_page_planner.py`
- Test: `tests/test_cognitive_page_planner.py`

- [ ] **Step 1: Write planner tests**

Create `tests/test_cognitive_page_planner.py`:

```python
from engine.cognitive_model.schema import CognitiveModel
from engine.html_ppt.cognitive_page_planner import plan_cognitive_pages


def sample_model():
    model = CognitiveModel(title="测试书")
    model.book_spine.core_question = "人为什么误把适应当命运？"
    model.book_spine.consensus_baseline = "旧共识把命运归因于意志。"
    model.book_spine.author_move = "作者把问题转向脑的适应机制。"
    model.book_spine.delta_sentence = "之前大家以为命运来自意志强弱，作者说命运来自脑的适应回路。"
    model.root_rank.root_generators = ["适应回路"]
    model.root_rank.candidate_generators = ["奖励回路", "注意力筛选"]
    model.root_rank.regeneration_matrix = [
        {"generator": "适应回路", "phenomenon": "习惯形成"},
        {"generator": "适应回路", "phenomenon": "情绪反应"},
        {"generator": "适应回路", "phenomenon": "学习迁移"},
    ]
    model.distillation.qa_chain = [
        {"question": "问题是什么？", "answer": {"conclusion": "适应被误读。", "boundary": "不解释全部人生。"}}
    ]
    model.distillation.insights = [{"title": "适应不是宿命", "content": "它是可被重新训练的回路。"}]
    model.roundtable.rounds = [
        {
            "round_index": 1,
            "guiding_question": "适应是否能改变？",
            "tension_axis": "神经机制 / 行动选择",
            "speeches": [
                {"id": "r1s1", "expert": "神经科学家", "claim": "脑会重塑。", "action_type": "definition"},
                {"id": "r1s2", "expert": "哲学家", "claim": "选择需要意识。", "responds_to": "r1s1", "action_type": "response"},
            ],
            "moderator": {"core_crack": "机制解释不能替代行动选择。", "next_question": "训练从哪里开始？"},
        }
    ]
    return model


def test_plan_cognitive_pages_includes_new_page_family():
    pages = plan_cognitive_pages(sample_model())
    types = [page.page_type for page in pages]

    assert types[0] == "cover"
    assert "core_question" in types
    assert "baseline_delta" in types
    assert "rank_map" in types
    assert "response_graph" in types
    assert "qa" in types
    assert types[-1] == "ending"


def test_planned_pages_use_v13_reading_page_contracts():
    pages = plan_cognitive_pages(sample_model())

    assert all(page.title for page in pages)
    assert all(page.takeaway for page in pages)
    assert all(page.layout in {"reading_brief_4zone", "stance_spectrum"} for page in pages)
```

- [ ] **Step 2: Run planner tests and confirm failure**

Run:

```powershell
python -m pytest tests/test_cognitive_page_planner.py -v
```

Expected:

```text
ModuleNotFoundError: No module named 'engine.html_ppt'
```

- [ ] **Step 3: Implement page contracts**

Create `engine/html_ppt/cognitive_page_contracts.py`:

```python
# -*- coding: utf-8 -*-
from __future__ import annotations

COGNITIVE_PAGE_TYPES = {
    "cover",
    "core_question",
    "baseline_delta",
    "rank_map",
    "response_graph",
    "qa",
    "insight",
    "ending",
}

PAGE_LAYOUTS = {
    "cover": "reading_brief_4zone",
    "core_question": "reading_brief_4zone",
    "baseline_delta": "reading_brief_4zone",
    "rank_map": "reading_brief_4zone",
    "response_graph": "stance_spectrum",
    "qa": "reading_brief_4zone",
    "insight": "reading_brief_4zone",
    "ending": "reading_brief_4zone",
}
```

- [ ] **Step 4: Implement cognitive page planner**

Create `engine/html_ppt/cognitive_page_planner.py`:

```python
# -*- coding: utf-8 -*-
from __future__ import annotations

from engine.cognitive_model.schema import CognitiveModel
from engine.html_ppt_v12 import summarize_text
from engine.html_ppt_v13 import ReadingBlock, ReadingPage


def plan_cognitive_pages(model: CognitiveModel) -> list[ReadingPage]:
    pages = [_cover(model)]
    if model.book_spine.core_question:
        pages.append(_core_question(model))
    if model.book_spine.delta_sentence or model.book_spine.consensus_baseline:
        pages.append(_baseline_delta(model))
    if model.root_rank.root_generators or model.root_rank.candidate_generators:
        pages.append(_rank_map(model))
    for round_data in model.roundtable.rounds:
        pages.append(_response_graph(model, round_data))
    if model.distillation.qa_chain:
        pages.append(_qa(model))
    if model.distillation.insights:
        pages.append(_insight(model))
    pages.append(_ending(model))
    return pages


def _cover(model: CognitiveModel) -> ReadingPage:
    return ReadingPage(
        page_type="cover",
        title=model.title,
        thesis="认知蒸馏型圆桌洞见",
        takeaway=model.book_spine.carryaway or "从问题、位移、根秩与圆桌张力进入这份材料。",
        layout="reading_brief_4zone",
        blocks=[
            ReadingBlock("metric", "专家", str(len(model.roundtable.participants))),
            ReadingBlock("metric", "轮次", str(len(model.roundtable.rounds))),
            ReadingBlock("metric", "洞见", str(len(model.distillation.insights))),
        ],
        meta={"cover_meta": model.source_understanding.author_problem or "CognitiveModel.v1"},
    )


def _core_question(model: CognitiveModel) -> ReadingPage:
    return ReadingPage(
        page_type="core_question",
        title="作者真正回答的问题",
        thesis=model.book_spine.core_question,
        takeaway="先固定问题轴，后面的圆桌才不会滑成观点堆叠。",
        layout="reading_brief_4zone",
        blocks=[
            ReadingBlock("question", "核心问题", model.book_spine.core_question),
            ReadingBlock("baseline", "旧共识", model.book_spine.consensus_baseline),
            ReadingBlock("move", "作者转向", model.book_spine.author_move),
            ReadingBlock("landing", "落点", model.book_spine.landing_sentence),
        ],
    )


def _baseline_delta(model: CognitiveModel) -> ReadingPage:
    return ReadingPage(
        page_type="baseline_delta",
        title="旧共识与作者位移",
        thesis=model.book_spine.delta_sentence or model.book_spine.author_move,
        takeaway="洞见来自位移，不来自把原书换一种说法。",
        layout="reading_brief_4zone",
        blocks=[
            ReadingBlock("baseline", "之前大家以为", model.book_spine.consensus_baseline),
            ReadingBlock("move", "作者说", model.book_spine.author_move),
            ReadingBlock("delta", "位移句", model.book_spine.delta_sentence),
            ReadingBlock("signature", "作者指纹", " / ".join(model.book_spine.signature_terms)),
        ],
    )


def _rank_map(model: CognitiveModel) -> ReadingPage:
    blocks = [ReadingBlock("root", "根生成器", item) for item in model.root_rank.root_generators]
    blocks.extend(ReadingBlock("candidate", "候选生成器", item) for item in model.root_rank.candidate_generators[:4])
    blocks.extend(
        ReadingBlock("regeneration", str(item.get("phenomenon", "现象")), str(item.get("generator", "")))
        for item in model.root_rank.regeneration_matrix[:3]
    )
    return ReadingPage(
        page_type="rank_map",
        title="根秩图",
        thesis="找到少数能重新生成现象的底层机制。",
        takeaway="根秩页用来防止洞见停在关键词层。",
        layout="reading_brief_4zone",
        blocks=blocks,
    )


def _response_graph(model: CognitiveModel, round_data: dict) -> ReadingPage:
    blocks = []
    for speech in list(round_data.get("speeches") or [])[:6]:
        label = str(speech.get("action_type") or "response")
        blocks.append(ReadingBlock("stance", str(speech.get("expert") or "专家"), str(speech.get("claim") or speech.get("stance") or ""), label=label))
    return ReadingPage(
        page_type="response_graph",
        title=f"第{round_data.get('round_index', 1)}轮：回应关系",
        thesis=summarize_text(str(round_data.get("tension_axis") or round_data.get("guiding_question") or "圆桌张力"), 90),
        takeaway=str((round_data.get("moderator") or {}).get("core_crack") or "真正的圆桌发生在回应关系里。"),
        layout="stance_spectrum",
        blocks=blocks,
    )


def _qa(model: CognitiveModel) -> ReadingPage:
    blocks = []
    for item in model.distillation.qa_chain[:6]:
        answer = item.get("answer") or {}
        if isinstance(answer, dict):
            text = f"{answer.get('conclusion', '')} {answer.get('boundary', '')}".strip()
        else:
            text = str(answer)
        blocks.append(ReadingBlock("qa", str(item.get("question") or "问题"), text))
    return ReadingPage(
        page_type="qa",
        title="问答链",
        thesis="用问题链复现作者的推理路线。",
        takeaway="读者能顺着问题走，才说明洞见被蒸馏成了结构。",
        layout="reading_brief_4zone",
        blocks=blocks,
    )


def _insight(model: CognitiveModel) -> ReadingPage:
    return ReadingPage(
        page_type="insight",
        title="核心洞见",
        thesis="从模型中提取可带走的判断。",
        takeaway="洞见必须能脱离原材料继续使用。",
        layout="reading_brief_4zone",
        blocks=[ReadingBlock("insight", str(item.get("title") or "洞见"), str(item.get("content") or "")) for item in model.distillation.insights[:5]],
    )


def _ending(model: CognitiveModel) -> ReadingPage:
    return ReadingPage(
        page_type="ending",
        title="最终带走什么",
        thesis=model.book_spine.landing_sentence or "把材料压缩成一个可复用的判断框架。",
        takeaway=model.book_spine.carryaway or "下一次面对类似问题时，先找问题轴、位移和根生成器。",
        layout="reading_brief_4zone",
        blocks=[
            ReadingBlock("carryaway", "行囊", model.book_spine.carryaway),
            ReadingBlock("future", "未来预测", " / ".join(model.distillation.future_bets[:3])),
            ReadingBlock("open", "开放问题", " / ".join(model.distillation.open_questions[:3])),
        ],
    )
```

- [ ] **Step 5: Run planner tests**

Run:

```powershell
python -m pytest tests/test_cognitive_page_planner.py -v
```

Expected:

```text
2 passed
```

- [ ] **Step 6: Commit Task 5**

```powershell
git add engine/html_ppt tests/test_cognitive_page_planner.py
git commit -m "feat: plan cognitive pages"
```

---

### Task 6: Cognitive HTML Render CLI

**Files:**
- Create: `engine/render_cognitive_html.py`
- Test: `tests/test_render_cognitive_html_cli.py`

- [ ] **Step 1: Write CLI tests**

Create `tests/test_render_cognitive_html_cli.py`:

```python
import json
import subprocess
import sys


def test_render_cognitive_html_cli_generates_valid_html(tmp_path):
    input_path = tmp_path / "sample_v8.json"
    output_path = tmp_path / "sample.html"
    input_path.write_text(json.dumps({
        "title": "测试书",
        "subtitle": "测试副标题",
        "experts": [{"name": "专家A", "core_belief": "定义问题"}],
        "rounds": [{"topic": "问题", "core_question": "问题是什么？", "stances": [{"expert": "专家A", "stance": "先定义问题。"}]}],
        "insights": [{"insight_title": "洞见", "insight_content": "洞见内容。"}],
        "open_questions": ["下一问？"],
    }, ensure_ascii=False), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "engine/render_cognitive_html.py", str(input_path), "--output", str(output_path)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    html = output_path.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in html
    assert 'data-page-type="cover"' in html
    assert "HTML-PPT cognitive validation passed" in result.stdout
```

- [ ] **Step 2: Run CLI test and confirm failure**

Run:

```powershell
python -m pytest tests/test_render_cognitive_html_cli.py -v
```

Expected:

```text
can't open file ... engine/render_cognitive_html.py
```

- [ ] **Step 3: Implement CLI**

Create `engine/render_cognitive_html.py`:

```python
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
        print("HTML-PPT cognitive validation failed")
        for error in result.errors:
            print(f"- {error}")
        return 1
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print("HTML-PPT cognitive validation passed")
    print(f"[GENERATED] {len(pages)} cognitive pages")
    print(f"[SAVE] {output_path}")
    return 0


def _read_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("input JSON must be an object")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a Research OS cognitive HTML deck")
    parser.add_argument("json_path", help="Input V8 roundtable JSON path")
    parser.add_argument("--output", "-o", help="Output HTML path")
    parser.add_argument("--theme", choices=["editorial", "obsidian", "blueprint"], default="editorial")
    args = parser.parse_args()
    input_path = Path(args.json_path)
    if not input_path.exists():
        print(f"input JSON not found: {input_path}")
        return 1
    output_path = Path(args.output) if args.output else Path("output") / f"{input_path.stem}_cognitive.html"
    return render_file(input_path, output_path, theme=args.theme)


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run CLI test**

Run:

```powershell
python -m pytest tests/test_render_cognitive_html_cli.py -v
```

Expected:

```text
1 passed
```

- [ ] **Step 5: Run a real sample render**

Run:

```powershell
python engine/render_cognitive_html.py content/遥远的救世主_V8.json --output output/遥远的救世主_ResearchOS.html
```

Expected:

```text
HTML-PPT cognitive validation passed
[GENERATED] ...
[SAVE] output\遥远的救世主_ResearchOS.html
```

If the input file is unavailable because of local dirty deletions, use another existing V8 file from `content/`:

```powershell
python engine/render_cognitive_html.py content/穷查理宝典_v8.json --output output/穷查理宝典_ResearchOS.html
```

- [ ] **Step 6: Commit Task 6**

```powershell
git add engine/render_cognitive_html.py tests/test_render_cognitive_html_cli.py
git commit -m "feat: render cognitive html deck"
```

---

### Task 7: Documentation and Main Path Notes

**Files:**
- Modify: `SKILL.md`
- Modify: `README.md`
- Test: `tests/test_render_cognitive_html_cli.py`

- [ ] **Step 1: Add concise Research OS note to `SKILL.md`**

Insert after the V13 renderer section:

```markdown
### Research OS 认知蒸馏主链路（V14 第一阶段）

**入口**：`engine/render_cognitive_html.py`

**用途**：把现有 V8 JSON 先适配为 `CognitiveModel.v1`，再生成认知页面族，最后复用 V13 阅读型渲染器输出 HTML。

```bash
python engine/render_cognitive_html.py content/书名_V8.json --output output/书名_ResearchOS.html
```

**边界**：
- Agent 负责补齐问题轴、作者位移、根秩、问答链等认知字段。
- Python 负责适配、验证、页面计划、HTML 渲染。
- V8 输入缺少深度字段时给出 warning，不静默伪造。
- 最终 HTML 仍必须满足无内部滚动和四种翻页规则。
```

- [ ] **Step 2: Add short README project status note**

Append near the existing docs links:

```markdown
## Research OS 升级路径

项目正在从圆桌 HTML 生成器升级为认知蒸馏型圆桌研究引擎。第一阶段新增 `CognitiveModel.v1`、V8 适配器、认知质量门、圆桌质量门和 Research OS HTML 输出入口：

```bash
python engine/render_cognitive_html.py content/书名_V8.json --output output/书名_ResearchOS.html
```

设计规格见：`docs/superpowers/specs/2026-06-17-roundtable-research-os-upgrade-design.md`。
实施计划见：`docs/superpowers/plans/2026-06-17-roundtable-research-os-upgrade.md`。
```

- [ ] **Step 3: Run CLI smoke test**

Run:

```powershell
python -m pytest tests/test_render_cognitive_html_cli.py -v
```

Expected:

```text
1 passed
```

- [ ] **Step 4: Commit Task 7**

```powershell
git add SKILL.md README.md
git commit -m "docs: document research os render path"
```

---

### Task 8: Verification Pass

**Files:**
- No new files required.

- [ ] **Step 1: Run all new tests**

Run:

```powershell
python -m pytest `
  tests/test_cognitive_model_schema.py `
  tests/test_cognitive_model_adapter.py `
  tests/test_cognitive_quality_gates.py `
  tests/test_roundtable_quality_gates.py `
  tests/test_cognitive_page_planner.py `
  tests/test_render_cognitive_html_cli.py `
  -v
```

Expected:

```text
15 passed
```

- [ ] **Step 2: Run existing V13 validation tests**

Run:

```powershell
python -m pytest tests/test_html_ppt_v13_planner.py tests/test_html_ppt_v13_renderer.py tests/test_validate_html_ppt_v13.py -v
```

Expected:

```text
all selected tests pass
```

- [ ] **Step 3: Render one real output**

Run:

```powershell
python engine/render_cognitive_html.py content/穷查理宝典_v8.json --output output/穷查理宝典_ResearchOS.html
```

Expected:

```text
HTML-PPT cognitive validation passed
```

- [ ] **Step 4: Validate the generated HTML**

Run:

```powershell
python engine/validate_html_ppt_v13.py output/穷查理宝典_ResearchOS.html
```

Expected:

```text
HTML-PPT V13 validation passed
```

- [ ] **Step 5: Inspect git status**

Run:

```powershell
git status --short
```

Expected:

```text
Only intentional Research OS files and generated sample output are changed, plus pre-existing unrelated dirty files.
```

Do not stage unrelated dirty template, data-master, or deleted output files.

- [ ] **Step 6: Commit final verification sample only if wanted**

If the generated sample output should be tracked:

```powershell
git add output/穷查理宝典_ResearchOS.html
git commit -m "test: add research os sample output"
```

If generated output should stay untracked:

```powershell
Remove-Item -LiteralPath 'output/穷查理宝典_ResearchOS.html'
```

Use native PowerShell only for removal and verify the path is exactly inside `D:\vibe_coding\zhengliu\圆桌会议\output`.

---

## Self-Review Checklist

- Spec coverage:
  - Bottom layer is covered by Tasks 1 and 2.
  - Stability is covered by Tasks 3, 4, 6, and 8.
  - Output quality is covered by Tasks 3, 4, and 5.
  - HTML output is covered by Tasks 5, 6, and 8.
  - Documentation and default-path visibility are covered by Task 7.

- Placeholder scan:
  - The plan does not contain placeholder markers.
  - Each code task includes concrete files, test code, implementation code, run commands, expected outcomes, and commit commands.

- Type consistency:
  - `CognitiveModel`, `QualityIssue`, `from_v8`, `validate_cognitive_quality`, `validate_roundtable_quality`, `plan_cognitive_pages`, and `render_file` are introduced before use.
  - Page planner returns existing V13 `ReadingPage` objects.
  - CLI uses existing `render_reading_html` and `validate_reading_html`.
