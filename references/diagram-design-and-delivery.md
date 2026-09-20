# Designed diagrams and complete delivery · v0.5.12-beta

> **关系图数据门禁（v0.5.8-beta）**：`scripts/verify_relations.py` 检查框架页实际可见的框架间关系边。无有据关系或独立框架由 `action-rule-ledger.json` 逐项说明；v2 账本还逐类复核两张图的关系。`finalize.py` 会阻断未经说明的空图或孤立框架。详见 `references/relation-gate.md`。

## Module ownership

- Core frameworks: cards on first open; Framework relationships toggles the framework-only map. Extract supported framework-to-framework relationships explicitly into relationships, not merely links from frameworks to action rules. Review actual dependencies, contrasts, membership and causal arguments. Isolated concepts remain isolated; missing evidence is never permission to manufacture connections.
- Action rules: whole-material methodology, application button and original action-rule cards. The whole structure stays together, with branches and feedback. A copied application prompt includes the canonical whole structure and saved method cards. A causal diagram is still a causal diagram; its display order is not an instruction to execute steps.

## Visual standard

The goal is an editorial information graphic with coherent composition. Use warm paper, sage, slate blue and muted gold; title hierarchy, layered surfaces and generous margins. Node numbers may be shown, but a number never stands alone: every numbered node always shows its title and type beside it, and relationship text names both endpoints ("覆铜板是 PCB 的核心组件 → 特种电子树脂的产品升级"), never "06 → 07". Names and relationship phrases must make sense without consulting another card. Color alone must not encode relationships.

Framework card and graph numbers must identify the same framework: both use its stable `sourceOrder`, while graph placement may change to clarify dependencies. Render double digits without a leading extra zero. Methodology graph numbering is local to that graph; action-rule card numbers refer to rules, so never imply that equal numerals across these two different sets mean the same item.

Keep node titles concise and precise. Core frameworks starts with cards. Its graph follows supported dependencies and groups disconnected branches separately. Before rendering, review framework relationships against the source: thickness classification and material generations, for example, can be independent dimensions rather than a part-of relationship. Add a common parent or shared outcome only when grounded, explicitly labeling synthesis. Never connect consecutive display positions merely to fill a gap. Describe any unsupported connection as unknown.

Action rules opens with the application button and graph. Remove the duplicated heading block, long introductory note and outcome quotation above it. Preserve the note, limits, synthesis labels and sources in the collapsed complete-structure disclosure and canonical methodology files. Under each graph show one localized instruction: click a card to see its direct connections; click empty space to reset. Selection highlights its neighbors and arrows, dims unrelated cards and shows a compact list with full source/target names and the relationship. Detailed reasoning and sources remain hidden until an explicit Details action. Reset and Escape clear selection. Never populate a large detail card on initial load.

Measure actual card heights after fonts load. Allocate columns from the graph's real branches and connected components; a one-column chain must not reserve three empty columns. Keep supported prerequisite, comparison, parallel and feedback edges without inventing branches for the sake of layout. The desktop graph viewport uses most of the available screen height while keeping a compact heading and toolbar. Its default **Fit width** keeps cards readable; **Overview** fits both width and height and may make long graphs too small to read, so selection and fullscreen remain available. Preserve the reader's focal point when using +/- zoom. Narrow screens retain a scrollable canvas.

Use large contrasting arrowheads offset from card borders and reserved routing corridors. Next-row links use the open gap between cards; skipping or feedback links may use exterior lanes. Relationship text belongs in protected chips beside the source or in clear line labels; never overlap text with wires. The card surface shows a concise title, at most a short summary preview, and compact relationship labels; the full reasoning remains in hover and click details. A relationship chip must still show its complete concise relation label and destination name: allow wrapping instead of single-line ellipsis. Do not solve clipping by shrinking all node text or forcing the whole graph into Overview scale. After a chip wraps, measure the resulting card height before placing the next row and routing arrows. Evidence class is carried by COLOUR plus text, never by line style alone: source-evidence, inference and feedback are all solid lines in three distinct themed colours (neutral / inference / gold), and only actual feedback is gold (a backward screen position is not feedback). Never reintroduce a dashed inference wire. Only warm-paper, minimal and dark themes are offered; removed saved themes fall back to warm-paper.

For visual QA, inspect at least one real long-title/branching material and one feedback-loop material at desktop and narrow widths. Include a true one-column chain, disconnected branches, and a node with several long Chinese relation chips. Check that every chip's label and destination are readable without hovering, and that taller cards leave intact row spacing and arrow clearance at ordinary and enlarged browser text sizes. Check module ownership, initial cards, graph/card toggle, long titles, line/card intersections, node selection, Fit width, Overview, centered zoom, fullscreen exit, reduced motion and the application prompt. In Fit width, check that all columns fit horizontally on first open; Overview may make long graphs too small to read. A static syntax check alone cannot establish visual quality. Report any unperformed browser checks accurately. Do not install browser dependencies without authorization.

For long hover explanations, position the floating detail once against its node. Keep the node-to-panel transit corridor active so a slow or diagonal pointer move does not close it. Only begin a short close delay after the pointer leaves the node, corridor and panel; re-entry cancels it. The panel remains scrollable, selectable and stationary. While the pointer is over the panel, wheel events never move the background page, even at the scroll limits. Check framework and methodology hover details separately, including narrow screens and fullscreen.

## Wire motion and state

`graph-studio.js` plays a brief **draw-in** when a graph first becomes visible. After that, the map stays still. Selecting a node plays one short directional cue only on its active relationships; there is no perpetual flow or pulsing feedback. Reduced motion gets fully drawn, static wires. The draw uses `is-drawn`; the selected cue uses `is-flowing` on a separate path.

Rules that must not regress:

- **The selected direction cue rides a second path, never the wire.** `.diagram-flow` is a duplicate path with identical geometry stacked above the solid line. It animates once on active edges and is removed at the end. Never animate the solid wire's own `stroke-dashoffset` for the cue.
- **Measure geometry AFTER insertion.** A `<path>` that is still detached reports a bogus `getTotalLength()` in Chromium. Append first, then read the length, then write `--wire-len`, `--draw-delay`, `--draw-dur`, `--flow-travel` and `--flow-dash`. Append → measure → set. Getting this order wrong freezes the head at its minimum travel.
- **`layout()` rebuilds every path, so it must re-arm and re-settle the state itself.** A freshly rebuilt wire may otherwise stay hidden after a tab switch, zoom, font load or resize. `layout()` ends with `armDraw(); settleWires();`; once the entrance has happened, rebuilding restores the static, fully drawn state without replaying the entrance.
- **`settleWires()` flips the class inside a `requestAnimationFrame`.** This separates path replacement from the final wire state and prevents an invisible intermediate frame becoming the final map.
- **Skip the rebuild when the panel reports `clientWidth <= 0`.** A `display:none` panel returns 0 for every descendant measurement. Guard with `if(viewport.clientWidth<=0 && !initial) return;` and read real numbers a frame later. After a panel becomes visible, a **double `requestAnimationFrame`** is the reliable point to call `refresh()`.
- **`IntersectionObserver` alone is not enough to report visibility.** Keep a separate visibility check (`announce()`) driven by `visibilitychange`, `scroll`, the `ResizeObserver` and the host's explicit `refresh()` call.
- **Reduced motion needs a composed still, not just disabled animations.** The terminal state is "every wire drawn, every arrowhead solid, nothing moving". The selected cue is gated in JS and CSS.
- **Expose `refresh()` from `mount()`** and have the host call it after a panel switch, via a small registry (`window.__rubinRegisterStudio`). Returning it from `mount()` is not enough on its own; the page needs a place to keep it.

## Theming and contrast

Every graph element is themed. `templates/graph-studio.css` declares a `--dg-*` palette and each of the three themes (`warm-paper`, `minimal`, `dark`) overrides it, so canvas, dot grid, card surface, card border, node title, summary, number, type tag, evidence/inference/feedback wires and their arrowheads and flow heads, legend, zoom and fullscreen buttons, hover preview and detail panel all change together.

Rules that must not regress:

- Never hard-code a graph colour in `graph-studio.js` or `graph-studio.css`. Arrowheads take their colour from the `dg-arrow-normal` / `dg-arrow-feedback` / `dg-arrow-inference` classes; a hard-coded `fill` on a marker path keeps a stale colour after a theme switch.
- Every arrowhead path is a SOLID FILLED triangle (`M 0 0 L 10 5 L 0 10 Z` with `stroke:none`). Markers use `markerUnits="userSpaceOnUse"` with a 10-unit viewBox compressed into an ~10–11px box, so a stroked wedge loses its interior to the stroke width and renders as a hollow chevron — which readers report as "the arrow disappeared".
- Never use `!important` to pin a wire or button colour; it defeats the theme variables.
- Unrelated nodes stay readable. They dim through a weaker surface (`--dg-dim-*`) with `opacity: 1`; never reintroduce `.is-muted { opacity: .28 }` or any low-opacity fade. Focus is expressed by the selected node's border, ring and shadow plus highlighted wires.
- In the dark theme the node surface must be explicitly dark and the title explicitly light — never rely on an inherited variable that may resolve to a light value.
- Node cards stay concise: number, short title, one summary line, type tag and relationship labels only. Inputs, checks and full citations belong in the detail panel and hover preview, not on the node.

## Two views, one wording source

Action rules keeps the 方法论卡片 ↔ 方法论关系图 switch. The cards view shows all material-backed `decisionRules`; reusable cards may also be saved in `methods.json`. For new systematic pages, `action-rule-ledger.json` records every card's candidate evidence and node/independent placement. Do NOT render a second, numbered per-node card list that mirrors `model.nodes`: the graph's hover preview and locked detail panel already carry each node's full input/action/output/check/sources and expand its associated action rules. Every node's wording lives in exactly one place — `model.nodes`, rendered through the shared `describe()` function for both the hover preview and the locked detail panel.

## Canonical files and final delivery

Create source-grounded methods.json and methodology.json first. Their schema, source hashes, quotations and synthesis labels follow the existing method references. A missing canonical JSON is a content gap, not something the exporter can infer. An unsupported whole structure still gets a valid not-applicable record and explanation.

Run:

```bash
python scripts/finalize.py page.json --knowledge-base topic.learnkb --output-dir delivery --name topic-learning
```

The command validates both canonical files, binds them into a copied page, copies the knowledge base, exports patterns.md and methodology.md, checks coverage and static HTML, and writes a .delivery.json manifest with hashes and a ZIP. Source files stay untouched. A differing old derived Markdown is retained under history/. Use a new output name or directory for each release. A failed run has no complete manifest or final archive; correct the content and use a fresh destination. No fallback to a low-level rendering function or --legacy to bypass a failed new-overview gate.

The ZIP contains HTML, Markdown, page JSON, the complete knowledge base and the delivery manifest. The original PDF is not automatically added; say so or include the user-designated source separately when requested. The returned methodology.md and methodology.json paths are explicit so the user can save them in a knowledge library. Final response links must include HTML, ZIP and methodology.md rather than only saying files were generated.

The command checks artifact completeness, not whether every host model followed all instructions. Across WorkBuddy and other agents, put this final command in the main task checklist and inspect its returned paths before declaring completion.
