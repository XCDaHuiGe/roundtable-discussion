# 圆桌 Skill V11 自动训练升级实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立一个本地 Markdown 训练流水线：实时热点候选进入 6 专家 3 轮圆桌训练，Agent 评分后局部重写，最终标准更新专家库。

**Architecture:** 先实现纯本地、可测试的训练协议和评分/更新模块，再把实时联网搜索作为 Agent 采集层接入。训练产物保存在 `training_runs/`，不提交；专家库更新是长期资产，可以提交。

**Tech Stack:** Python 标准库、`pytest`、Markdown 文件、现有 `expert-library/experts/` 专家库、Agent 负责联网搜索与内容生成。

---

## 文件结构

本计划新增这些文件：

- `.gitignore`：追加 `training_runs/`。
- `engine/v11_training_protocol.py`：训练运行目录、slug、Markdown 模板、读写工具。
- `engine/v11_hot_topics.py`：热点候选、争议地图、候选评分、top 10/top 3 选择。
- `engine/v11_roundtable_training.py`：3 轮训练记录、评分、最低分项、局部重写记录的数据结构和报告生成。
- `engine/v11_expert_evolution.py`：从训练结果生成专家库更新块，并追加到专家 Markdown。
- `engine/v11_cli.py`：本地 CLI，先支持从 Agent 准备好的热点 JSON 生成训练 Markdown 和专家更新预览。
- `tests/test_v11_training_protocol.py`
- `tests/test_v11_hot_topics.py`
- `tests/test_v11_roundtable_training.py`
- `tests/test_v11_expert_evolution.py`
- `tests/test_v11_cli.py`

本计划不修改现有 V6/V10 HTML 生成链路。HTML 发布链路放到后续计划。

---

## Task 1: 建立训练目录协议

**Files:**
- Modify: `.gitignore`
- Create: `engine/v11_training_protocol.py`
- Test: `tests/test_v11_training_protocol.py`

- [ ] **Step 1: 写失败测试**

创建 `tests/test_v11_training_protocol.py`：

```python
from pathlib import Path

from engine.v11_training_protocol import (
    build_run_dir,
    slugify,
    write_training_markdown_pair,
)


def test_slugify_keeps_chinese_and_normalizes_symbols():
    assert slugify("AI 情感陪伴：年轻人还需要真实恋爱吗？") == "ai-情感陪伴-年轻人还需要真实恋爱吗"


def test_build_run_dir_uses_kind_and_date(tmp_path):
    run_dir = build_run_dir(tmp_path, "hot-topics", "2026-06-08")
    assert run_dir == tmp_path / "training_runs" / "2026-06-08-hot-topics"


def test_write_training_markdown_pair_creates_full_and_report(tmp_path):
    run_dir = tmp_path / "training_runs" / "2026-06-08-hot-topics"
    full_path, report_path = write_training_markdown_pair(
        run_dir=run_dir,
        topic_slug="ai-情感陪伴",
        full_content="# 完整日志\n",
        report_content="# 最终报告\n",
    )

    assert full_path.read_text(encoding="utf-8") == "# 完整日志\n"
    assert report_path.read_text(encoding="utf-8") == "# 最终报告\n"
    assert full_path.name == "ai-情感陪伴.full.md"
    assert report_path.name == "ai-情感陪伴.report.md"
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```powershell
pytest tests/test_v11_training_protocol.py -q
```

Expected: FAIL，提示 `ModuleNotFoundError: No module named 'engine.v11_training_protocol'`。

- [ ] **Step 3: 实现最小协议模块**

创建 `engine/v11_training_protocol.py`：

```python
# -*- coding: utf-8 -*-
"""V11 本地训练产物协议。"""

from __future__ import annotations

import re
from pathlib import Path


def slugify(value: str, max_length: int = 80) -> str:
    """生成适合文件名的短 slug，保留中文。"""
    value = value.strip().lower()
    value = re.sub(r"[\\/:*?\"<>|，。、“”‘’！!？?；;：:（）()\[\]{}]+", "-", value)
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    if not value:
        value = "topic"
    return value[:max_length].rstrip("-")


def build_run_dir(base_dir: Path, run_kind: str, run_date: str) -> Path:
    """返回训练运行目录，不负责写入 Git。"""
    return base_dir / "training_runs" / f"{run_date}-{run_kind}"


def write_training_markdown_pair(
    run_dir: Path,
    topic_slug: str,
    full_content: str,
    report_content: str,
) -> tuple[Path, Path]:
    """写入 full/report 两个训练 Markdown 文件。"""
    run_dir.mkdir(parents=True, exist_ok=True)
    full_path = run_dir / f"{topic_slug}.full.md"
    report_path = run_dir / f"{topic_slug}.report.md"
    full_path.write_text(full_content, encoding="utf-8", newline="\n")
    report_path.write_text(report_content, encoding="utf-8", newline="\n")
    return full_path, report_path
```

- [ ] **Step 4: 更新 `.gitignore`**

在 `.gitignore` 末尾追加：

```gitignore
training_runs/
```

- [ ] **Step 5: 验证通过**

Run:

```powershell
pytest tests/test_v11_training_protocol.py -q
```

Expected: `3 passed`。

- [ ] **Step 6: 提交**

```powershell
git add .gitignore engine/v11_training_protocol.py tests/test_v11_training_protocol.py
git commit -m "feat: add v11 training artifact protocol"
```

---

## Task 2: 实现热点候选评分和选择

**Files:**
- Create: `engine/v11_hot_topics.py`
- Test: `tests/test_v11_hot_topics.py`

- [ ] **Step 1: 写失败测试**

创建 `tests/test_v11_hot_topics.py`：

```python
from engine.v11_hot_topics import HotTopicCandidate, rank_candidates, select_training_topics


def test_rank_candidates_prefers_high_controversy_and_filters_gossip():
    candidates = [
        HotTopicCandidate(
            title="某明星机场穿搭争议",
            summary="纯娱乐争议",
            sources=["微博"],
            heat=9,
            position_split=2,
            value_conflict=1,
            practical_relevance=1,
            expert_decomposability=1,
            non_gossip_signal=0,
        ),
        HotTopicCandidate(
            title="AI 情感陪伴是否会替代真实亲密关系",
            summary="涉及技术、两性、心理与商业化。",
            sources=["Bing", "知乎", "小红书"],
            heat=7,
            position_split=8,
            value_conflict=9,
            practical_relevance=8,
            expert_decomposability=9,
            non_gossip_signal=9,
        ),
    ]

    ranked = rank_candidates(candidates)
    assert ranked[0].title.startswith("AI 情感陪伴")
    assert ranked[0].score > ranked[1].score


def test_select_training_topics_returns_top_10_and_top_3():
    candidates = [
        HotTopicCandidate(
            title=f"议题{i}",
            summary="可讨论议题",
            sources=["Bing", "知乎"],
            heat=i,
            position_split=i,
            value_conflict=i,
            practical_relevance=i,
            expert_decomposability=i,
            non_gossip_signal=9,
        )
        for i in range(1, 31)
    ]

    top10, top3 = select_training_topics(candidates)
    assert len(top10) == 10
    assert len(top3) == 3
    assert [t.title for t in top3] == ["议题30", "议题29", "议题28"]
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```powershell
pytest tests/test_v11_hot_topics.py -q
```

Expected: FAIL，提示模块不存在。

- [ ] **Step 3: 实现候选模型和评分**

创建 `engine/v11_hot_topics.py`：

```python
# -*- coding: utf-8 -*-
"""V11 热点候选评分与选择。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class HotTopicCandidate:
    title: str
    summary: str
    sources: list[str]
    heat: int
    position_split: int
    value_conflict: int
    practical_relevance: int
    expert_decomposability: int
    non_gossip_signal: int
    score: float = field(default=0.0)


def _clamp_score(value: int) -> int:
    return max(0, min(10, int(value)))


def score_candidate(candidate: HotTopicCandidate) -> float:
    """争议价值评分，非八卦信号是硬门槛之一。"""
    heat = _clamp_score(candidate.heat)
    split = _clamp_score(candidate.position_split)
    conflict = _clamp_score(candidate.value_conflict)
    relevance = _clamp_score(candidate.practical_relevance)
    decomposable = _clamp_score(candidate.expert_decomposability)
    non_gossip = _clamp_score(candidate.non_gossip_signal)
    source_bonus = min(len(set(candidate.sources)), 4) * 0.5

    weighted = (
        heat * 0.12
        + split * 0.22
        + conflict * 0.22
        + relevance * 0.18
        + decomposable * 0.18
        + non_gossip * 0.08
        + source_bonus
    )
    if non_gossip < 3:
        weighted *= 0.35
    if split < 4 or conflict < 4:
        weighted *= 0.65
    return round(weighted, 2)


def rank_candidates(candidates: list[HotTopicCandidate]) -> list[HotTopicCandidate]:
    ranked = []
    for candidate in candidates:
        candidate.score = score_candidate(candidate)
        ranked.append(candidate)
    return sorted(ranked, key=lambda item: item.score, reverse=True)


def select_training_topics(
    candidates: list[HotTopicCandidate],
) -> tuple[list[HotTopicCandidate], list[HotTopicCandidate]]:
    ranked = rank_candidates(candidates)
    top10 = ranked[:10]
    top3 = top10[:3]
    return top10, top3
```

- [ ] **Step 4: 验证通过**

Run:

```powershell
pytest tests/test_v11_hot_topics.py -q
```

Expected: `2 passed`。

- [ ] **Step 5: 提交**

```powershell
git add engine/v11_hot_topics.py tests/test_v11_hot_topics.py
git commit -m "feat: add v11 hot topic scoring"
```

---

## Task 3: 实现三轮训练记录和 Markdown 渲染

**Files:**
- Create: `engine/v11_roundtable_training.py`
- Test: `tests/test_v11_roundtable_training.py`

- [ ] **Step 1: 写失败测试**

创建 `tests/test_v11_roundtable_training.py`：

```python
from engine.v11_roundtable_training import (
    RoundScore,
    TrainingRound,
    TrainingTopic,
    render_full_markdown,
    render_report_markdown,
)


def test_lowest_dimension_is_selected_from_scores():
    score = RoundScore(
        factual_robustness=8,
        insight_delta=7,
        conflict_strength=3,
        persona_consistency=8,
        structure=7,
        practical_usefulness=6,
        empty_talk_rate=2,
    )
    assert score.lowest_dimension() == "conflict_strength"


def test_render_full_markdown_keeps_original_and_rewrite():
    topic = TrainingTopic(
        title="AI 情感陪伴是否会替代真实亲密关系",
        definition="围绕 AI 伴侣、亲密关系和商业化的争议。",
        controversy_map="支持方认为它降低孤独，反对方认为它削弱真实关系。",
        experts=["弗洛姆", "尼采", "芒格", "项飙", "韩非子", "刘润"],
        rounds=[
            TrainingRound(
                round_number=1,
                purpose="立场建模",
                original="原稿内容",
                score=RoundScore(8, 6, 4, 8, 7, 6, 3),
                lowest_dimension="conflict_strength",
                rewrite_instruction="增强直接攻击。",
                rewritten="重写内容",
            )
        ],
        final_insights=["亲密关系的核心不是陪伴时长，而是互相承担现实后果。"],
    )

    full_md = render_full_markdown(topic)
    report_md = render_report_markdown(topic)

    assert "原稿内容" in full_md
    assert "重写内容" in full_md
    assert "增强直接攻击" in full_md
    assert "原稿内容" not in report_md
    assert "重写内容" in report_md
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```powershell
pytest tests/test_v11_roundtable_training.py -q
```

Expected: FAIL，提示模块不存在。

- [ ] **Step 3: 实现训练记录模块**

创建 `engine/v11_roundtable_training.py`：

```python
# -*- coding: utf-8 -*-
"""V11 三轮圆桌训练记录与 Markdown 渲染。"""

from __future__ import annotations

from dataclasses import dataclass, fields


@dataclass
class RoundScore:
    factual_robustness: int
    insight_delta: int
    conflict_strength: int
    persona_consistency: int
    structure: int
    practical_usefulness: int
    empty_talk_rate: int

    def lowest_dimension(self) -> str:
        values = {
            "factual_robustness": self.factual_robustness,
            "insight_delta": self.insight_delta,
            "conflict_strength": self.conflict_strength,
            "persona_consistency": self.persona_consistency,
            "structure": self.structure,
            "practical_usefulness": self.practical_usefulness,
            "empty_talk_rate": 10 - self.empty_talk_rate,
        }
        return min(values, key=values.get)

    def as_markdown(self) -> str:
        lines = []
        for field in fields(self):
            lines.append(f"- {field.name}: {getattr(self, field.name)}")
        return "\n".join(lines)


@dataclass
class TrainingRound:
    round_number: int
    purpose: str
    original: str
    score: RoundScore
    lowest_dimension: str
    rewrite_instruction: str
    rewritten: str


@dataclass
class TrainingTopic:
    title: str
    definition: str
    controversy_map: str
    experts: list[str]
    rounds: list[TrainingRound]
    final_insights: list[str]


def render_full_markdown(topic: TrainingTopic) -> str:
    parts = [
        f"# {topic.title} - 完整训练日志",
        "",
        "## 话题定义",
        topic.definition,
        "",
        "## 争议地图",
        topic.controversy_map,
        "",
        "## 入选专家",
        "\n".join(f"- {expert}" for expert in topic.experts),
    ]
    for item in topic.rounds:
        parts.extend(
            [
                "",
                f"## 第 {item.round_number} 轮：{item.purpose}",
                "",
                "### 原稿",
                item.original,
                "",
                "### Agent 评分",
                item.score.as_markdown(),
                "",
                "### 最低分项",
                item.lowest_dimension,
                "",
                "### 局部重写指令",
                item.rewrite_instruction,
                "",
                "### 重写稿",
                item.rewritten,
            ]
        )
    parts.extend(["", "## 最终洞见"])
    parts.extend(f"- {insight}" for insight in topic.final_insights)
    return "\n".join(parts).rstrip() + "\n"


def render_report_markdown(topic: TrainingTopic) -> str:
    parts = [
        f"# {topic.title} - 最终报告",
        "",
        "## 话题定义",
        topic.definition,
        "",
        "## 争议地图",
        topic.controversy_map,
        "",
        "## 入选专家",
        "\n".join(f"- {expert}" for expert in topic.experts),
    ]
    for item in topic.rounds:
        parts.extend(
            [
                "",
                f"## 第 {item.round_number} 轮：{item.purpose}",
                item.rewritten,
            ]
        )
    parts.extend(["", "## 关键洞见"])
    parts.extend(f"- {insight}" for insight in topic.final_insights)
    return "\n".join(parts).rstrip() + "\n"
```

- [ ] **Step 4: 验证通过**

Run:

```powershell
pytest tests/test_v11_roundtable_training.py -q
```

Expected: `2 passed`。

- [ ] **Step 5: 提交**

```powershell
git add engine/v11_roundtable_training.py tests/test_v11_roundtable_training.py
git commit -m "feat: add v11 roundtable training markdown"
```

---

## Task 4: 实现专家库标准更新器

**Files:**
- Create: `engine/v11_expert_evolution.py`
- Test: `tests/test_v11_expert_evolution.py`

- [ ] **Step 1: 写失败测试**

创建 `tests/test_v11_expert_evolution.py`：

```python
from pathlib import Path

from engine.v11_expert_evolution import ExpertUpdate, append_expert_updates, render_update_block


def test_render_update_block_contains_traceability():
    update = ExpertUpdate(
        expert_name="弗洛姆",
        layer="素材层",
        update_type="高分发言",
        topic="AI 情感陪伴是否会替代真实亲密关系",
        round_number=3,
        score_basis="洞见增量 9/10，人格一致性 8/10",
        content="亲密不是持续陪伴，而是共同承担自由带来的焦虑。",
    )

    block = render_update_block(update, run_id="2026-06-08-hot-topics")
    assert "V11 自动训练沉淀" in block
    assert "素材层" in block
    assert "2026-06-08-hot-topics" in block
    assert "亲密不是持续陪伴" in block


def test_append_expert_updates_adds_block(tmp_path):
    expert_path = tmp_path / "弗洛姆.md"
    expert_path.write_text("# 弗洛姆\n\n## 素材层\n", encoding="utf-8")

    update = ExpertUpdate(
        expert_name="弗洛姆",
        layer="素材层",
        update_type="高分发言",
        topic="AI 情感陪伴",
        round_number=2,
        score_basis="人格一致性 9/10",
        content="逃避孤独不等于获得爱。",
    )
    append_expert_updates(expert_path, [update], run_id="run-1")

    text = expert_path.read_text(encoding="utf-8")
    assert "逃避孤独不等于获得爱" in text
    assert "run-1" in text
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```powershell
pytest tests/test_v11_expert_evolution.py -q
```

Expected: FAIL，提示模块不存在。

- [ ] **Step 3: 实现专家更新模块**

创建 `engine/v11_expert_evolution.py`：

```python
# -*- coding: utf-8 -*-
"""V11 专家库标准更新器。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ExpertUpdate:
    expert_name: str
    layer: str
    update_type: str
    topic: str
    round_number: int
    score_basis: str
    content: str


def render_update_block(update: ExpertUpdate, run_id: str) -> str:
    return (
        "\n\n### V11 自动训练沉淀\n"
        f"- 来源 run: {run_id}\n"
        f"- 话题: {update.topic}\n"
        f"- 轮次: 第 {update.round_number} 轮\n"
        f"- 层级: {update.layer}\n"
        f"- 类型: {update.update_type}\n"
        f"- 评分依据: {update.score_basis}\n"
        f"- 内容: {update.content}\n"
    )


def append_expert_updates(expert_path: Path, updates: list[ExpertUpdate], run_id: str) -> None:
    if not expert_path.exists():
        raise FileNotFoundError(f"专家文件不存在: {expert_path}")
    text = expert_path.read_text(encoding="utf-8")
    blocks = [render_update_block(update, run_id) for update in updates]
    expert_path.write_text(text.rstrip() + "".join(blocks) + "\n", encoding="utf-8", newline="\n")
```

- [ ] **Step 4: 验证通过**

Run:

```powershell
pytest tests/test_v11_expert_evolution.py -q
```

Expected: `2 passed`。

- [ ] **Step 5: 提交**

```powershell
git add engine/v11_expert_evolution.py tests/test_v11_expert_evolution.py
git commit -m "feat: add v11 expert evolution updater"
```

---

## Task 5: 增加本地 CLI 串联 JSON 输入到训练 Markdown

**Files:**
- Create: `engine/v11_cli.py`
- Test: `tests/test_v11_cli.py`

- [ ] **Step 1: 写失败测试**

创建 `tests/test_v11_cli.py`：

```python
import json

from engine.v11_cli import run_from_prepared_json


def test_run_from_prepared_json_writes_training_files(tmp_path):
    prepared = {
        "run_id": "2026-06-08-hot-topics",
        "topics": [
            {
                "title": "AI 情感陪伴是否会替代真实亲密关系",
                "definition": "围绕 AI 伴侣和真实亲密关系的争议。",
                "controversy_map": "支持方认为降低孤独，反对方认为削弱现实关系。",
                "experts": ["弗洛姆", "尼采", "芒格", "项飙", "韩非子", "刘润"],
                "rounds": [
                    {
                        "round_number": 1,
                        "purpose": "立场建模",
                        "original": "原稿",
                        "score": {
                            "factual_robustness": 8,
                            "insight_delta": 7,
                            "conflict_strength": 5,
                            "persona_consistency": 8,
                            "structure": 7,
                            "practical_usefulness": 6,
                            "empty_talk_rate": 3
                        },
                        "lowest_dimension": "conflict_strength",
                        "rewrite_instruction": "增强交叉攻击。",
                        "rewritten": "重写稿"
                    }
                ],
                "final_insights": ["真实亲密关系包含后果共担。"]
            }
        ]
    }
    input_path = tmp_path / "prepared.json"
    input_path.write_text(json.dumps(prepared, ensure_ascii=False), encoding="utf-8")

    outputs = run_from_prepared_json(input_path=input_path, base_dir=tmp_path)

    assert len(outputs) == 1
    full_path, report_path = outputs[0]
    assert full_path.exists()
    assert report_path.exists()
    assert "原稿" in full_path.read_text(encoding="utf-8")
    assert "重写稿" in report_path.read_text(encoding="utf-8")
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```powershell
pytest tests/test_v11_cli.py -q
```

Expected: FAIL，提示模块不存在。

- [ ] **Step 3: 实现 CLI 模块**

创建 `engine/v11_cli.py`：

```python
# -*- coding: utf-8 -*-
"""V11 训练 CLI。

第一阶段只消费 Agent 已准备好的 JSON，不在 Python 内部直接联网。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from engine.v11_roundtable_training import (
    RoundScore,
    TrainingRound,
    TrainingTopic,
    render_full_markdown,
    render_report_markdown,
)
from engine.v11_training_protocol import slugify, write_training_markdown_pair


def _topic_from_dict(data: dict) -> TrainingTopic:
    rounds = []
    for item in data["rounds"]:
        score = RoundScore(**item["score"])
        rounds.append(
            TrainingRound(
                round_number=item["round_number"],
                purpose=item["purpose"],
                original=item["original"],
                score=score,
                lowest_dimension=item.get("lowest_dimension") or score.lowest_dimension(),
                rewrite_instruction=item["rewrite_instruction"],
                rewritten=item["rewritten"],
            )
        )
    return TrainingTopic(
        title=data["title"],
        definition=data["definition"],
        controversy_map=data["controversy_map"],
        experts=data["experts"],
        rounds=rounds,
        final_insights=data["final_insights"],
    )


def run_from_prepared_json(input_path: Path, base_dir: Path) -> list[tuple[Path, Path]]:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    run_id = payload["run_id"]
    run_dir = base_dir / "training_runs" / run_id
    outputs = []
    for topic_data in payload["topics"]:
        topic = _topic_from_dict(topic_data)
        topic_slug = slugify(topic.title)
        outputs.append(
            write_training_markdown_pair(
                run_dir=run_dir,
                topic_slug=topic_slug,
                full_content=render_full_markdown(topic),
                report_content=render_report_markdown(topic),
            )
        )
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="V11 圆桌训练 Markdown 生成")
    parser.add_argument("--input", required=True, help="Agent 准备好的训练 JSON")
    parser.add_argument("--base-dir", default=".", help="项目根目录")
    args = parser.parse_args()

    outputs = run_from_prepared_json(Path(args.input), Path(args.base_dir))
    for full_path, report_path in outputs:
        print(f"[FULL] {full_path}")
        print(f"[REPORT] {report_path}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 验证通过**

Run:

```powershell
pytest tests/test_v11_cli.py -q
```

Expected: `1 passed`。

- [ ] **Step 5: 提交**

```powershell
git add engine/v11_cli.py tests/test_v11_cli.py
git commit -m "feat: add v11 training markdown cli"
```

---

## Task 6: 增加 Agent 联网采集操作说明

**Files:**
- Modify: `SKILL.md`
- Create: `docs/V11_AGENT_RESEARCH_PROTOCOL.md`

- [ ] **Step 1: 写采集协议文档**

创建 `docs/V11_AGENT_RESEARCH_PROTOCOL.md`：

```markdown
# V11 Agent 联网采集协议

## 热点标准模式

1. 实时联网搜索中文互联网热点。
2. 初筛 30 个候选。
3. 按争议价值筛出 10 个高争议话题。
4. 深挖前 3 个话题。
5. 每个话题选择 6 位专家。
6. 每个话题跑 3 轮训练。
7. 输出 `engine/v11_cli.py` 可消费的 prepared JSON。

## 信息源分层

- 事实确认层：Bing、新闻、官方说明、原始报道。
- 争议立场层：知乎 MCP、微博、小红书、B站、公众号、评论区抽样。
- 深度解释层：长文、专栏、研究、历史案例。
- 噪声过滤层：剔除纯八卦、谣言、标题党、重复搬运。

## prepared JSON 格式

见 `engine/v11_cli.py` 和 `tests/test_v11_cli.py`。
```

- [ ] **Step 2: 更新 `SKILL.md` 加 V11 入口**

在 `SKILL.md` 的可用 Skills 或渲染器前加入简短段落：

```markdown
## V11 自动训练入口

当用户要求“热点训练”“自动训练”“从互联网找争议话题训练”时，使用 V11 流程：

1. 按 `docs/V11_AGENT_RESEARCH_PROTOCOL.md` 实时联网采集。
2. 生成 prepared JSON。
3. 运行 `python engine/v11_cli.py --input <prepared.json> --base-dir .`。
4. 检查 `training_runs/` 下的 `full.md` 和 `report.md`。
5. 根据训练结果用标准更新模式更新专家库。

训练日志不提交 GitHub；专家库更新可以提交。
```

- [ ] **Step 3: 验证文档入口存在**

Run:

```powershell
Select-String -Path SKILL.md -Pattern "V11 自动训练入口"
Select-String -Path docs/V11_AGENT_RESEARCH_PROTOCOL.md -Pattern "prepared JSON"
```

Expected: 两个命令都能找到匹配行。

- [ ] **Step 4: 提交**

```powershell
git add SKILL.md docs/V11_AGENT_RESEARCH_PROTOCOL.md
git commit -m "docs: add v11 agent research protocol"
```

---

## Task 7: 全量验证

**Files:**
- No new files.

- [ ] **Step 1: 运行 V11 单元测试**

Run:

```powershell
pytest tests/test_v11_training_protocol.py tests/test_v11_hot_topics.py tests/test_v11_roundtable_training.py tests/test_v11_expert_evolution.py tests/test_v11_cli.py -q
```

Expected: 全部 PASS。

- [ ] **Step 2: 运行现有模板验证，确认没有破坏发布链路**

Run:

```powershell
$env:PYTHONIOENCODING='utf-8'; python engine\validate_templates.py
```

Expected: `16/16 通过`。

- [ ] **Step 3: 检查训练目录仍被忽略**

Run:

```powershell
git check-ignore training_runs/example.full.md
```

Expected: 输出 `training_runs/example.full.md`。

- [ ] **Step 4: 检查工作区，只包含预期改动**

Run:

```powershell
git status --short
```

Expected: 只显示本次计划内文件，或者显示用户之前已有的未提交实验文件；不要把 `training_runs/` 训练日志加入 Git。

---

## 第一轮真实训练验收

实现完成后，执行一次标准热点训练。Agent 实时联网搜索并准备 JSON，Python 只负责落盘和结构验证。

成功标准：

- 生成 30 个候选、10 个高争议话题、3 个训练话题的采集记录。
- 3 个话题都产出 `full.md` 和 `report.md`。
- 每个话题都有 6 位专家和 3 轮训练。
- 每轮都有 Agent 评分、最低分项和局部重写记录。
- 专家库更新只追加策略层/素材层，不修改灵魂层。
- `training_runs/` 没有进入 Git。

---

## 后续计划

本计划不处理 HTML 发布链路。V11 Markdown 训练闭环稳定后，再单独制定发布链路清理计划，重点解决：

- 重复导航脚本。
- 页面内部滚动。
- 浏览器视觉验证。
- README/index 自动更新。
- 发布提交和推送。
