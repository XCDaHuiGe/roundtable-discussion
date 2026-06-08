# Roundtable Skill V11 Automatic Training Design

## Purpose

Upgrade the roundtable skill from a mixed V7/V9/V10 generation workspace into an automatic training system that improves content quality, output stability, and expert-library evolution.

The system has two primary entry points:

- Book insight generation from `epub`, `docx`, `txt`, `md`, and degraded `pdf` input.
- Real-time Chinese internet hot-topic training across all domains, including social issues, business, technology, AI, education, workplace, international topics, culture, personal growth, and relationships.

Training outputs Markdown. HTML is only produced on an explicit publish request.

## Confirmed Product Direction

The main product is book-based roundtable insight. Hot-topic training is the automatic practice loop. Expert-library evolution is the long-term memory layer.

The design optimizes for:

- Source-grounded structure.
- High-quality insight rather than summary.
- Strong expert conflict.
- Stable training artifacts.
- Standard expert-library updates after training.
- Minimal manual intervention.

## Current Project Issues

The local workspace currently mixes several generations of the system:

- `README.md` still describes V7/V8 behavior.
- `SKILL.md` describes V9 training and adds V10 HTML fragment normalization.
- `engine/generate_v6.py` appears to be the most mature current book-output generator.
- `engine/page-fragment-normalizer.py` is the V10 HTML fragment normalizer.
- Some generated HTML outputs contain duplicate navigation scripts.
- Training artifacts and publish artifacts are not cleanly separated.

The upgrade should first establish workflow boundaries before adding more generators.

## Entry Points

### Book Entry

Supported inputs:

- `epub`
- `docx`
- `txt`
- `md`
- `pdf` as a lower-confidence fallback

The book pipeline extracts content into source text blocks, then performs a two-layer reading process:

1. Full-book structure understanding.
2. High-tension issue extraction.

JSON may exist as an intermediate artifact, but Markdown is the training output and HTML is a publish output.

### Hot-Topic Entry

The hot-topic pipeline uses real-time online search. It should not default to a stale cache.

Available source types:

- Fact confirmation: Bing, news, official statements, primary reports.
- Dispute positions: Zhihu MCP, Weibo, Xiaohongshu, Bilibili, public accounts, comment-section sampling where available.
- Deep interpretation: long-form articles, columns, research, historical cases.
- Noise filtering: remove pure gossip, rumor, title bait, duplicated reposts, and topics without cognitive value.

Default mode:

```text
real-time search -> 30 candidates -> 10 high-controversy topics -> top 3 topics -> 3 training iterations per topic
```

## Training Artifacts

Every training run creates a local run directory:

```text
training_runs/YYYY-MM-DD-hot-topics/
training_runs/YYYY-MM-DD-book-<slug>/
```

Training run directories are local-only and must not be committed to GitHub.

Each trained topic produces two Markdown files:

```text
<topic-slug>.full.md
<topic-slug>.report.md
```

### Full Log

`full.md` records the complete training trace:

- Source list and source confidence.
- Controversy map.
- Expert selection rationale.
- Original draft for each round.
- Agent scores for each round.
- Lowest-scoring dimension.
- Local rewrite instructions.
- Rewritten content.
- Final scoring summary.
- Expert-library update suggestions.

### Final Report

`report.md` is the readable final result:

- One-sentence topic definition.
- Controversy map.
- Selected experts.
- Final 3-round roundtable.
- Key insights.
- Preserved tensions.
- Practical judgment.
- Score summary.

## Hot-Topic Candidate Scoring

Candidate topics are scored on:

- Heat.
- Position split.
- Value conflict.
- Practical relevance.
- Expert-decomposability.
- Non-gossip signal.

A topic should only enter the top 10 if it can support at least two strong opposing positions and has enough factual material for grounded discussion.

## Expert Selection

Each topic uses 6 automatically selected experts.

The selector should satisfy these role slots where possible:

- Reality or institution expert.
- Economic or business expert.
- Psychology or human-nature expert.
- Philosophy or ethics expert.
- Contrarian, risk, or black-swan expert.
- Chinese lived-context expert.

Selection considers:

- Topic fit.
- Conflict complementarity.
- Recent appearance frequency.
- Expert growth needs.
- Persona stability.

The selector should avoid repeatedly using the same strongest experts unless they are unusually appropriate for the topic.

## Three-Round Training Structure

Each topic uses exactly three rounds.

### Round 1: Position Modeling

Each expert states a core judgment grounded in facts or dispute materials.

No pure opinion is allowed. Each position must connect to either a confirmed fact, platform dispute, historical analogy, or named real-world mechanism.

### Round 2: Cross-Attack

Experts quote or clearly reference another expert's position, then attack:

- Logical gaps.
- Real-world blind spots.
- Value bias.
- Hidden cost.
- Missing stakeholder.

Generic disagreement is not enough.

### Round 3: Insight Reconstruction

The system does not force consensus.

The round should produce:

- Collapsed assumptions.
- Preserved tensions.
- Higher-level explanatory frame.
- Practical judgment boundaries.
- What an ordinary person or organization should watch next.

## Agent Scoring And Rewrite Loop

After every generated round, an Agent reviewer scores the content.

Scoring dimensions:

- Faithfulness and factual robustness.
- Insight delta.
- Conflict strength.
- Expert persona consistency.
- Structural coherence.
- Practical usefulness.
- Empty-talk rate.

The lowest-scoring dimension drives the next rewrite.

If a dimension falls below threshold, the system performs an automatic local rewrite of the weak section. The original and rewritten versions both remain in `full.md`; only the final version enters `report.md`.

Example rewrite rules:

- Low factual robustness: add source-grounded facts and remove unsupported claims.
- Low insight delta: introduce a new explanatory frame rather than restating the dispute.
- Low conflict strength: require direct attack against another position and name the specific flaw.
- Low persona consistency: rewrite using the expert's known models and style.
- Low practical usefulness: add cost, boundary conditions, and action judgment.
- Low structural coherence: split, reorder, or retitle the argument.

## Expert-Library Evolution

Training logs are not committed. Expert-library improvements may be committed because they are durable system memory.

Update mode is standard, not aggressive.

### Layer Rules

Soul layer:

- Do not update automatically.
- Only change with explicit user confirmation.

Strategy layer:

- Update only when the candidate pattern is high-scoring, reusable, and persona-consistent.
- Merge or enhance existing patterns instead of rewriting wholesale.

Material layer:

- Append high-scoring quotes, successful attacks, useful cases, and failure cases.
- Every entry must include source training run, topic, round, score basis, and update type.

Failure cases:

- Record when an expert is effectively attacked or exposed.
- Do not immediately convert one failure into a permanent weakness.

## Publish Branch

Publishing is separate from training.

Only when the user explicitly asks to publish should the system generate HTML and update site files.

Publish validation must check:

- No internal page scrolling.
- Keyboard, wheel, click, and navigation-dot paging.
- Exactly one navigation script.
- No duplicate progress/dot creation.
- Template validation passes.
- Browser check passes when practical.
- `README.md` and `index.html` are updated.
- Git commit and push happen only for approved publish changes.

## Implementation Phases

### Phase 1: Markdown Training Protocol

Create the local training directory convention, `.gitignore` rule, and Markdown schemas for `full.md` and `report.md`.

Success criteria:

- Training artifacts are generated in a predictable local-only directory.
- The format is stable enough for later scoring and expert-library updates.

### Phase 2: Real-Time Hot-Topic Search

Implement the multi-source hot-topic candidate workflow.

Success criteria:

- A standard run produces 30 candidates, 10 scored high-controversy topics, and 3 selected topics.
- Each selected topic has source support and a controversy map.

### Phase 3: Roundtable Training Core

Implement the 6-expert, 3-round training loop with Agent scoring and automatic local rewrites.

Success criteria:

- Each selected topic has three training iterations.
- Each iteration identifies the lowest-scoring dimension and records a targeted improvement.

### Phase 4: Expert-Library Standard Update

Implement safe expert-library updates from final training reports and full logs.

Success criteria:

- Material-layer updates are traceable.
- Strategy-layer updates require high score, reuse value, and persona consistency.
- Soul-layer content is unchanged.

### Phase 5: Publish Chain Cleanup

Clean up the HTML publishing path after the training system is stable.

Success criteria:

- Generated HTML has one navigation system.
- Slides obey the no-internal-scroll rule.
- Publish updates README and index only when explicitly requested.

## Open Decisions

No product-level blockers remain.

Implementation still needs exact thresholds for scoring and file schema details. These should be set in the implementation plan with simple defaults, then adjusted after the first real run.

## Non-Goals

- Do not submit training logs to GitHub.
- Do not auto-modify expert soul layers.
- Do not generate HTML during normal training.
- Do not rebuild the whole site before the Markdown training loop works.
- Do not introduce broad abstractions before one end-to-end standard hot-topic run works.
