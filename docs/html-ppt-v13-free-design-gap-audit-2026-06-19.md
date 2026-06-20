# V13 Free Design Gap Audit

## Audited Output

File:

```text
output/遥远的救世主_圆桌洞见_V13.html
```

Reference target:

```text
output/html-ppt-extreme-case-shock.html
```

## User Finding

The output is clean and orderly, but it is still far from free design and full visual ambition. The user explicitly asked the AI to show off, yet the result remained regular, restrained, and template-like.

This finding is correct.

## Static Evidence

The generated `遥远的救世主_圆桌洞见_V13.html` has these properties:

- 13 slides.
- Body slides repeatedly use the same `.reading-page` shell.
- No `data-layout-variant` attributes were found.
- No `data-display-logic` attributes were found.
- No `*_extreme` variants were found.
- No `shock-poster`, `evidence-wall`, `cost-blast`, `interrogation`, or `xray` stage classes were found in the output.
- The output has animation and grid structure, but not independent page-stage metaphors.

The visible result is therefore not a failure of CSS polish. It is a routing failure.

## Root Cause

The file was generated through:

```text
engine/render_html_ppt_v13.py
  -> engine/html_ppt_v13_planner.py
  -> engine/html_ppt_v13_renderer.py
```

The planner produces legacy reading page types:

```text
insight_reading
roundtable_reading
clash_reading
summary_reading
```

Those page types are optimized for a readable, regular deck. They do not produce:

```text
case_shock
baseline_delta
cognitive_upgrade
response_graph
tension_map
source_map
```

As a result, the current output bypasses the newer free-design route:

```text
content signal -> display_logic -> layout_variant -> extreme renderer
```

The new open-design machinery exists, but the real book-generation entrypoint did not feed it the right page family.

## Secondary Cause

Even when variant renderers are selected, most current renderers still wrap the body in:

```html
<div class="reading-page">
  <header class="reading-header">...</header>
  <main class="reading-body">...</main>
  <footer class="takeaway-strip">...</footer>
</div>
```

This common shell is excellent for safety and readability, but it visually normalizes pages. It makes many layouts feel like variations inside the same editorial container.

Extreme pages need a different rendering contract:

```text
extreme variant -> independent full-stage renderer
editorial variant -> reading shell renderer
```

## Why “Let AI Show Off” Did Not Work

The instruction was given at the wrong layer.

The agent could want to show off, but the system still asked it to produce pages through a regular reading planner and a regular reading shell. The runtime did not expose enough degrees of freedom.

The fix is not a stronger prompt alone. The fix is structural:

1. Route real book outputs through the cognitive/open-design planner.
2. Require `display_logic`, `layout_variant`, and `intensity` on every page.
3. Fail validation if a deck has no extreme variants when the user requests show-off mode.
4. Allow extreme renderers to bypass the reading shell.
5. Add a visual ambition validator that rejects “all pages are orderly reading cards”.

## Required Plan Correction

The previous `Depth × Extreme` plan is directionally right, but it needs a new first task:

```text
Task 0: Unify V13 book generation entrypoint
```

This task must happen before adding more extreme components.

Task 0 should:

- make `render_html_ppt_v13.py` use the cognitive/open-design planner when possible
- map legacy `roundtable_reading` data into richer page types
- ensure generated HTML includes `data-display-logic` and `data-layout-variant`
- reject decks where all non-cover pages use the same `.reading-page` shell

## New Acceptance Criteria

A generated book deck only satisfies “free design” if:

- at least 60% of non-cover slides have `data-layout-variant`
- at least 25% of slides use non-shell stage renderers in show-off mode
- show-off mode produces at least one `*_extreme` page
- no deck with conflict/case/cost data may render as only `reading_brief_4zone`, `stance_spectrum`, and `clash_courtroom`
- browser or static audit confirms the output is closer to the extreme demo than to the regular reading deck

## Design Decision

The next implementation should not start by making the renderer prettier.

It should start by fixing generation routing:

```text
legacy reading planner -> regular deck
cognitive/open-design planner -> free design deck
show-off mode -> cognitive/open-design planner + extreme intensity + full-stage renderer
```

After that, extreme renderers will actually appear in real book outputs.
