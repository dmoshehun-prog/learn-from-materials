# Changelog

## v0.2.0 · 2026-09-20

- Consolidated the unpublished development snapshots into the next public version after v0.1.0-beta. The earlier v0.5.x numbers below identify local experiments, not prior public releases.
- Preserved complete relation-chip labels, adaptive graph layout, heading-source checks, relation review and the per-unit action-rule ledger.
- Fixed nested wheel handling in framework hover details: the relation list scrolls first, then the outer panel; methodology hover behavior is unchanged. Both internal and outer scrollbars remain available when content overflows.
- Removed a byte-for-byte duplicated mojibake example directory from the release package; the normal Chinese-named fixture remains.

## Unpublished development snapshots

## v0.5.12-beta · 2026-09-20

- Relation chips in both graphs wrap their complete concise label and destination instead of clipping them with a single-line ellipsis.
- Added a static layout invariant and visual QA requirements for long labels, taller cards, narrow screens and enlarged text.
- Hover popups and wheel behavior are unchanged. Version 0.5.11 was withdrawn before release.

## v0.5.10-beta · 2026-09-20

- Both relationship maps allocate only the columns supported by their actual branches, use a taller reading area, and compact the heading, toolbar and node previews.
- Fit width and Overview are separate controls. +/- zoom keeps the current viewport center; narrow screens remain scrollable.
- Direct next-row links use the open card gap; only skipping and feedback links use exterior lanes. The first entrance is brief, and only selected links receive one directional cue.
- Shared visual, hover, arrow, reduced-motion and QA guidance was updated for the new design.

## v0.5.9-beta · 2026-09-20

- New systematic PDF deliveries require a reviewed `source-heading-index.json`. The gate checks that displayed heading paths and PDF ranges match indexed original headings and that text-verified headings appear on the recorded source page. Visual checks remain explicitly labeled manual.
- Graph hover details are anchored to the node, protect the mouse transit corridor, delay closing outside it, and keep wheel scrolling inside the detail even at its ends.
- The prompt-language routing and learning-depth question remain unchanged; no extra language question was added.

## v0.5.8-beta · 2026-09-19

- Framework cards and graph nodes now display the same stable `sourceOrder` number, including two-digit numbers. Graph layout can reorder nodes without renumbering them.
- The systematic ledger v2 reviews every supported relation kind for both visible graphs and checks its recorded edge IDs against the actual graph. Unsupported kinds remain valid with a reason; a main-only process receives a review warning, not an invented branch.
- Methodology relations now support prerequisites, parallel tracks and comparisons, with type-specific labels. Node and link explanations use clearer reader-facing wording.
- Floating graph details remain open when the pointer moves from a card into the popover. Wheel scrolling reaches long content while preserving page scroll at the ends.
- Existing page schema 4.3 remains readable. Older systematic knowledge bases with a v1 ledger need the documented legacy delivery option or a new v2 review before release.

## v0.5.7-beta · 2026-09-19

- New systematic overviews save a per-unit `action-rule-ledger.json`. The delivery gate checks reviewed source blocks, verbatim evidence, candidate dispositions, visible rule cards and methodology-node or independent-rule placement.
- Framework relation checks now use the edges actually shown in the framework graph. Documented unsupported relationships and independent frameworks can pass without invented lines.
- Whole-material node details can expand their associated action-rule cards, including conditions, reasons and sources. The six-module page structure and existing card/graph switch are retained.
- `finalize.py` validates in a staging directory, then publishes a complete bundle. Failed checks no longer leave a partial delivery that blocks a same-name retry.
- Quick overviews keep their existing scope. Old systematic examples can be re-delivered with the explicit `--legacy-rule-ledger` option; their manifest does not claim the new ledger check.
- Version and three-theme descriptions were aligned. Release packaging omits duplicated mojibake fixtures and local `.bak` files.

The ledger checks traceability and downstream retention of recorded rules. It cannot prove that an agent's first reading found every applicable rule, so the final source reread remains required.
