# Depth × Extreme HTML-PPT Upgrade Spec

## Goal

Build the next generation HTML-PPT pipeline around two non-negotiable ambitions:

1. **Depth first:** every deck must extract the deepest possible content from the source, not merely summarize or decorate it.
2. **Extreme design by default:** the renderer should spend tokens, visual imagination, layout variation, animation, and browser QA to produce the strongest design it can within the fixed HTML-PPT safety contract.

The upgrade should not make the system vague or unstable. It should make deep output and ambitious design **explicit, inspectable, and testable**.

## Fixed Constraints

These constraints remain unchanged and override all visual ambition:

- Every slide is exactly one viewport: `height:100vh`.
- No slide may use internal scrolling: `overflow:hidden`; no `overflow-y:auto` or `overflow-y:scroll`.
- The deck must keep keyboard, wheel, blank-click, nav-dot, and progress navigation.
- Overflow content must be split across slides, not hidden casually.
- Design intensity cannot delete required content.
- The renderer must produce a single HTML file that works locally.

## Problem Statement

The current system has begun to break the fixed-template problem with `display_logic` and `layout_variant`, but the next failure mode is predictable:

- Content may still be shallow: pages can look better while saying little.
- Visual variants may still be polite: pages can differ structurally but fail to reach the force of `html-ppt-extreme-case-shock.html`.
- Validation may still be too technical: “HTML passes” does not prove depth, drama, or design strength.
- Real book generation may bypass the open-design layer entirely if it still uses the legacy V13 reading planner.

The next upgrade must therefore separate and enforce three contracts:

```text
Depth Contract -> Design Ambition Contract -> HTML Runtime Contract
```

## Production Gap Found In V13 Output

The audited file `output/遥远的救世主_圆桌洞见_V13.html` proves that the current plan needs one more correction.

The output is orderly, but it is not free design:

- body slides repeatedly use the same `.reading-page` shell
- no `data-display-logic` appears
- no `data-layout-variant` appears
- no `*_extreme` variant appears
- real book generation uses `engine/html_ppt_v13_planner.py`, which emits legacy reading page types such as `roundtable_reading`, `clash_reading`, and `summary_reading`

This means show-off instructions are currently trapped behind the wrong entrypoint. The system must first ensure that real book outputs enter the open-design pipeline.

New rule:

```text
If the user requests "炫技", "自由设计", "极限设计", or "不节约 tokens",
the renderer must not use the legacy reading-only planner as the final route.
```

## Design Principles

### 1. Do Not Save Tokens During Creative Work

Generation should use enough reasoning and drafting to produce the best available result. Token economy is not the goal during:

- book distillation
- roundtable argument construction
- slide beat planning
- visual route exploration
- variant selection
- design repair
- browser QA diagnosis

The system may still trim final visible text to fit a slide, but it must not trim thinking before it has produced the strongest source model.

### 2. Depth Is Not Length

Depth means the output exposes structure that a normal summary would miss:

- the author’s real question
- the prior consensus or default reading
- the author’s displacement from that consensus
- the mechanism that regenerates many surface phenomena
- the strongest counter-position
- the cost of accepting the insight
- the boundary where the insight stops working
- the transferable takeaway

Long paragraphs are not enough. A slide is deep only if it contains a decision-relevant judgment.

### 3. Beauty Is a Requirement, Not Decoration

Visual ambition should be measured by whether form increases cognition:

- shock pages should hit before they explain
- evidence pages should feel like evidence
- clash pages should feel like pressure
- diagnosis pages should reveal hidden structure
- delta pages should make movement visible
- manifesto pages should leave a sentence in memory

The design system should allow aggressive composition, large typography, asymmetry, cinematic staging, texture, motion, and unusual layout when the content calls for it.

### 4. Fixed Runtime, Open Stage

The runtime is fixed. The stage is open.

Fixed:

- navigation
- one-page viewport
- no internal scroll
- progress
- keyboard and wheel handling
- browser validation

Open:

- composition
- visual language
- animation
- information density
- page choreography
- theme atmosphere
- typography scale
- spatial metaphor

## Required Pipeline

The next generation pipeline should become:

```text
source material
  -> DeepContentModel
  -> RoundtableArgumentModel
  -> DepthScore audit
  -> DeckNarrativePlan
  -> OpenDesignPlanner
  -> DesignIntentMap
  -> ExtremeVariantPlan
  -> HTML render
  -> static validation
  -> browser visual validation
  -> repair loop
  -> final HTML-PPT
```

## Deep Content Contract

### DeepContentModel

Create or extend a content model with these required fields:

```python
DeepContentModel(
    title: str,
    author_problem: str,
    consensus_baseline: str,
    author_delta: str,
    root_mechanism: str,
    signature_terms: list[str],
    reality_cases: list[RealityCase],
    tension_axes: list[TensionAxis],
    counter_positions: list[CounterPosition],
    costs: list[CostAnalysis],
    boundaries: list[Boundary],
    transferable_insights: list[TransferableInsight],
    uncertainty_notes: list[str],
)
```

### Required Depth Questions

Before a deck can be planned, the source must answer these questions:

1. What question is the author really answering?
2. What did readers commonly believe before this book?
3. What exact displacement does the author introduce?
4. What mechanism explains more than one phenomenon?
5. Which case makes the thesis hurt?
6. Which expert would attack the thesis most strongly?
7. What does the insight cost if accepted?
8. Where does the insight fail or become dangerous?
9. What can the reader carry to another domain?

### Depth Score

Add a `DepthScore` audit with a 0-100 score:

| Dimension | Points |
|---|---:|
| author problem is specific | 10 |
| baseline and delta are explicit | 15 |
| root mechanism is generative | 15 |
| at least two reality cases exist | 10 |
| counter-position is steelmanned | 10 |
| costs and boundaries are present | 15 |
| insights are transferable | 15 |
| uncertainty is named instead of hidden | 10 |

Minimum gate:

- below 70: do not render
- 70-84: render with warning
- 85+: render normally

## Roundtable Argument Contract

The roundtable is not a panel of isolated quotes. It is an argument machine.

Each round must include:

- `guiding_question`
- `tension_axis`
- `speeches`
- `response_edges`
- `clashes`
- `moderator_crack`
- `reality_case_pressure`
- `cognitive_upgrade`

Every expert speech must either:

- define a concept
- attack a prior claim
- defend against an attack
- introduce a case
- expose a cost
- revise the frame

Generic speeches fail validation.

## Deck Narrative Contract

Each slide must have:

```python
SlideBeat(
    page_type: str,
    display_logic: str,
    layout_variant: str,
    depth_role: str,
    visual_intent: str,
    reader_question: str,
    memory_hook: str,
    required_blocks: list[str],
    source_refs: list[str],
    intensity: str,
)
```

Allowed `intensity` values:

- `quiet`
- `editorial`
- `dramatic`
- `extreme`

Rules:

- A deck must include at least one `extreme` page when source material contains conflict, cost, or a reality case.
- A deck over 10 pages must include at least four display logics.
- No adjacent slides may use the same `layout_variant`.
- Every `extreme` page must be followed within two slides by a quieter explanatory page.
- Every slide must answer one reader question.

## Extreme Design Contract

### Intensity Levels

`quiet`:

- high readability
- restrained layout
- dense but calm text

`editorial`:

- magazine-like grid
- strong hierarchy
- visible typographic rhythm

`dramatic`:

- cinematic contrast
- asymmetric staging
- larger typography
- stronger motion

`extreme`:

- independent stage metaphor
- dominant visual gesture
- high contrast
- aggressive typography
- animation or spatial effect
- no generic card grid unless the card grid itself is the concept
- no mandatory `.reading-page` shell unless the variant explicitly chooses an editorial reading stage

### Shell Policy

There are two rendering shells:

```text
reading shell: header + main + takeaway strip
stage shell: full-slide composition owned by the variant
```

Rules:

- `quiet` and `editorial` pages may use the reading shell.
- `dramatic` pages may use either shell.
- `extreme` pages should use the stage shell by default.
- a deck in show-off mode fails if every non-cover page uses the reading shell.
- an extreme renderer must own the full stage composition, not merely place an extreme block inside the same reading wrapper.

### Extreme Variant Requirements

The first extreme variant library should include:

| Variant | Required Feeling | Must Include |
|---|---|---|
| `shock_poster_extreme` | a thesis slams into the reader | oversized type, dark/light rupture, one visual wound |
| `evidence_wall_extreme` | evidence is pinned and connected | absolute-position evidence cards, connecting lines, forensic tags |
| `interrogation_room_extreme` | an idea is cross-examined | opposing zones, central pressure object, question/answer strip |
| `xray_diagnosis_extreme` | hidden structure is scanned | diagnostic labels, scan line, exposed mechanism diagram |
| `cost_blast_extreme` | accepting the idea has consequences | huge cost word, stacked costs, contrasting danger block |
| `delta_map_extreme` | worldview displacement is visible | before/after field, vector or fault line, new coordinate |
| `mechanism_cutaway_extreme` | the engine is opened | layered mechanism, feedback arrows, cause/effect chambers |
| `manifesto_poster_extreme` | one sentence remains | one dominant sentence, minimal support, poster finish |

## Token Policy

The system should explicitly support a `generation_budget` profile.

Default for high-quality book decks:

```json
{
  "content_reasoning": "max",
  "roundtable_depth": "max",
  "design_exploration": "max",
  "visible_text_trim": "fit-slide",
  "repair_iterations": 3
}
```

Meaning:

- spend more tokens before rendering
- generate more candidate beats and visual routes than finally used
- keep final slide text bounded by viewport
- never reduce analysis depth just to save generation cost

## Validation Contract

### Depth Validation

Fail if:

- `author_problem` is generic
- no baseline/delta pair exists
- no cost or boundary exists
- insights are only slogans
- roundtable speeches do not respond to each other

### Design Strength Validation

Fail or warn if:

- more than 40% of slides use the same layout family
- an `extreme` deck has no `*_extreme` variants
- a slide marked `extreme` has no dominant visual gesture
- all pages look like cards in a grid
- adjacent slides have the same rhythm
- real book output contains no `data-layout-variant`
- show-off output contains no stage-shell slides
- all body slides contain `.reading-page`

### Browser Validation

Check:

- no slide overflows its viewport
- nav dots equal slide count
- only one slide is visible
- extreme pages render their core gesture
- text does not overlap controls
- mobile layout does not hide required content

## Non-Goals

This upgrade does not:

- build a separate editor
- generate PPTX
- replace the one-file HTML output
- remove the fixed navigation runtime
- chase every possible visual style at once

## Success Criteria

The next upgrade is successful when:

- a generated book deck has a `DepthScore >= 85`
- every slide has a `SlideBeat`
- at least one deck can produce `shock_poster_extreme`, `evidence_wall_extreme`, and `cost_blast_extreme` from real content
- `output/遥远的救世主_圆桌洞见_V13.html` or its regenerated successor contains `data-display-logic` and `data-layout-variant`
- show-off mode creates at least 25% stage-shell slides
- the deck passes static and browser validation
- the visual result is closer to `output/html-ppt-extreme-case-shock.html` than to the older fixed-template reading deck
- final HTML still obeys the no-internal-scroll rule

## Recommended First Slice

Implement the smallest complete slice:

1. Fix the V13 real-book entrypoint so show-off mode uses the open-design planner, not the legacy reading-only planner.
2. Add `DepthScore` and validation.
3. Add `SlideBeat` fields to `ReadingPage` or a companion plan object.
4. Add `intensity`.
5. Add three extreme renderers:
   - `shock_poster_extreme`
   - `evidence_wall_extreme`
   - `cost_blast_extreme`
6. Add stage-shell rendering for extreme pages.
7. Regenerate a real book deck and confirm `data-layout-variant` is present.
8. Validate static HTML and browser layout.

This slice proves both ambitions at once: deeper content gates and stronger visual output.
