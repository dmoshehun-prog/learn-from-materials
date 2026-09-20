# Whole-material methodology (v0.5)

Read this for every new overview, in both learning depths. The goal is a coherent account of the entire material: its central problem, outcome, reasoning, decisions and justified feedback. Display it inside Action rules. Core frameworks defaults to cards with a separate framework relationship map. Read diagram-design-and-delivery.md for visual and final packaging requirements. Do not substitute a graph of loosely related framework cards, pagination, or a fixed eight-step recipe.

## Synthesize before drawing

1. Identify the material's central problem and intended outcome. Account for each content unit as core reasoning, evidence, context or a reasoned exclusion; coverage is not an extraction quota.
2. Choose a structure that matches the material: `process`, `decision_tree`, `causal`, or `hierarchy`. Procedural content can become an application workflow. Descriptive material should retain its causal or conceptual logic; do not invent actions, feedback, or success criteria. Use `not-applicable` if a coherent structure cannot be supported and explain why.
3. Each node states its input, action (or conceptual meaning), output and check/exit condition. For non-procedural structures these fields explain premises, relationships, conclusions and evidentiary limits; they need not pretend to be executable steps.
4. Each transition states WHEN it applies, WHAT is handed off, and WHY the next node follows. Branches need real conditions; feedback names its destination and the changed evidence. Stop when the objective/check is satisfied or a stated boundary is reached. Do not imply endless autonomous execution.
5. Link nodes to source-backed frameworks/rules and content units. Keep examples and supporting cases in node details. Show the whole structure without node-count pagination; offer detail inspection and a complete text equivalent.
6. Recheck each node and link against original passages. A connected graph and valid citations are not proof of semantic fidelity. Preserve conflict, uncertainty and external control. Don't assert causality from co-occurrence.

Before finalizing a systematic overview, review the entire structure for genuine sequence, conditional branches, parallel tracks, prerequisites, comparisons, causal links, supporting evidence, containment and feedback/revision. Record each supported kind with its actual edge IDs, or a concrete reason it is unsupported, in `action-rule-ledger.json.relationReview.methodology`. A single main path is valid when the source really describes one; inspect whether it has hidden alternatives or independent consequences before accepting it. Parallel branches may share a starting result without one causing the other. `contrasts` names the compared dimension; `causes` needs causal support beyond chronology. A feedback edge must identify the changed evidence or decision; uncertainty alone is a limit, not proof that the source prescribes a revision loop.

## Evidence boundary

Save the original method cards in `methods.json`. Save the integrated structure separately in `methodology.json` beside INDEX.md; derive `methodology.md`. This file is an explicitly labeled analytical layer, not a revision of material facts or original cards. `evidence: synthesis` means the agent combined the whole material into a structure; it does not mean the author stated the flow verbatim. Individual nodes/edges use `material` only when their specific action or relationship is supported, otherwise `inference` with limits explained. Arbitrary external advice does not belong here. Source quotes prove traceability, not entailment.
When the material offers a candidate structure, tentative mechanism or unresolved identification, keep that status in the node and any outgoing relationship. A source for each endpoint does not prove the proposed link between them; do not turn a plausible model into a confirmed pathway, complete reaction or measured outcome.

## Schema

The root has exactly:

- `schemaVersion: learn-from-materials/methodology-v1`
- `id`, semantic `version`, `language: en | zh-CN`
- `status: ready | not-applicable`
- `structure: process | decision_tree | causal | hierarchy | none`
- `title`, `problem`, `outcome`, `note` (nonempty user-language strings)
- `evidence: material | synthesis`
- `entryNodes`: valid starting node IDs; `mainPath`: ordered IDs for a process, empty for non-sequential structures if appropriate
- `nodes`, `edges`, `constraints`, `coverage` as described below

Node fields exactly: `id/title/role/input/action/output/check/unitIds/methodIds/evidence/sources`. Role is `action/decision/concept`. The first six content fields are nonempty strings. `unitIds` references one or more contentUnits; `methodIds` can be empty, otherwise references page framework/rule IDs. Each source is `{source, sourceIds, quote}`: full locator, extraction source IDs and short verbatim evidence quote. IDs and evidence hashes are checked against the original extraction. Do not create quotes by joining PDF lines that contain a newline.

Edge fields exactly: `id/from/to/kind/condition/handoff/why/evidence/source`. All fields are nonempty strings; endpoints must exist and differ. Kind is `main/branch/feedback/supports/contains/causes/prerequisite/parallel/contrasts`. Main-path adjacent nodes require an explicit main edge. Feedback may cycle; all nodes must be reachable from an entry. Non-sequential relations should use the corresponding kind rather than fake sequence. `condition` can state an applicability premise for non-procedural relationships; `handoff` then states what is shared, compared, contained or affected, rather than pretending to pass an output to the next step.

Constraint fields exactly: `text/evidence/source`. Coverage fields exactly: `unitId/nodeIds/role/reason`, with role `core/evidence/context/out-of-scope`. Every content unit appears once; core/evidence units map to real nodes. Exclusions explain why. No repeated boilerplate pretending a missing chapter was integrated.

For `not-applicable`, use structure `none`, empty entryNodes/mainPath/nodes/edges/constraints, and account for all units in coverage as context or out-of-scope with reasons. Explain the limitation in note, problem and outcome; do not manufacture a workflow.

The optional overview field `methodology` embeds an exact validated snapshot. Older 4.2/4.3 JSON remains compatible; every NEW overview in v0.4 must produce the canonical file and bind it. The renderer rejects drift between the snapshot and file.

```bash
python3 scripts/methodology.py validate --model topic.learnkb/methodology.json --page page-with-methods.json --knowledge-base topic.learnkb
python3 scripts/methodology.py export --model topic.learnkb/methodology.json --page page-with-methods.json --knowledge-base topic.learnkb --output topic.learnkb/methodology.md
python3 scripts/methodology.py bind --model topic.learnkb/methodology.json --page page-with-methods.json --knowledge-base topic.learnkb --output page-final.json
python3 scripts/render_page.py page-final.json --knowledge-base topic.learnkb --output learning.html --markdown learning.md
```

Keep output page beside its original so relative knowledgeBase paths resolve. Preserve stable IDs, source provenance and old versions. Cross-material merging still requires explicit user scope and labeled synthesis; no automatic global scan or destructive merge.

## Application

The default application choice is the WHOLE structure, with the full snapshot and saved method cards in the copied prompt. First assess applicability and choose an entry node for the user's actual situation, explaining skipped prerequisites. Follow each input/action/output/check and conditional transition; identify failures, return paths and stopping conditions. Do not treat the drawing as authority to perform external actions. For causal/hierarchical material, explain its logic and label any proposed application rather than fabricating a procedure. Single-method selection remains available.

## Content-guide source behavior

Every core statement, takeaway and conclusion supports hover and keyboard-focus source disclosure, including after unit switches. Each unit also has an always-visible, clickable `Original sources` disclosure for touch devices. The tooltip is a viewport-clamped fixed overlay, not an offscreen pseudo-element on a tall parent card.

Optional `contentUnits[].sourceDetails` adds finer locators without changing the text arrays:

```json
{"core":"exact locator", "frameworks":["locator aligned with each framework"], "takeaways":["locator aligned with each takeaway"], "conclusions":[{"summary":"summary locator", "points":["locator aligned with each point"]}]}
```

Omitted arrays fall back to the unit source; omitted conclusions fall back to each conclusion's own source. Supplied array lengths must match. Only provide precise pages when verified. Fallbacks visibly say Unit range or Conclusion range. Each fine locator is checked by the same source-type and range gates. No guessed page numbers.
