# Action-rule ledger for new systematic overviews (v0.5.8-beta)

An action rule is a material-supported condition → action → reason relation. Capture prerequisites, exceptions and stop conditions separately when present. Do not turn the model's outside advice into a material fact. A material may have no action rules; record that finding instead of inventing cards.

## Work in bounded units

1. Read one complete content unit and the source blocks mapped to it in `coverage-audit.json.sourceBlocks`. Search is a supplement to sequential reading, not a substitute. Include tables, figures and OCR/visual limits in the unit note.
2. Immediately save or update that unit's `units[]` entry in `action-rule-ledger.json`. `reviewedSourceIds` must equal all `covered` source blocks mapped to the unit. Mark `reviewed` when one or more candidates were found; mark `no-rules` only after rereading and explain why. An absent entry means unfinished work. Save the ledger after each unit so a context reset can resume from the first missing unit.
3. Record each candidate before deduplication. Look for prerequisites, parameter choices, "must first", "unless", failure handling, feedback, retention and stop conditions. Use `quote` copied exactly from one declared source block. A condition or reason not stated by the material should be recorded as such in explanatory prose, not fabricated as a quote.
4. After every unit is recorded, compare candidates across the whole material. Use `retained` for each visible card's primary candidate, `merged` for a genuinely equivalent additional candidate mapped to that card, and `excluded` only with a reason. Different conditions or exceptions are not duplicates. A merged candidate keeps its own ID and source IDs.
5. Re-read the original specifically for missing conditions, exceptions, failures and stopping rules. Update the ledger, then create `decisionRules` cards. A retained candidate's `when`, `do` and `because` must exactly match its card. Every card must have a retained candidate. Put rule IDs in the relevant `methodology.nodes[].methodIds`; for a rule that cannot belong in the overall structure, record it in `independentRules` and keep its card visible.
6. Check the framework-only relationship graph against the page that users actually see. Framework → action-rule links do not draw in that graph. Document independently standing frameworks in `independentFrameworks`. If the material supports no framework-to-framework edge, set `relationStatus: "unsupported"` with a concrete `relationReason`; leave the graph's edge array empty rather than inventing one. Otherwise use `mapped`.
7. Complete `relationReview.framework` and `relationReview.methodology` after both graphs are drafted. Review every listed relationship kind against the original material. A `mapped` row lists exactly the edge IDs of that kind in the visible graph and explains why the type applies; an `unsupported` row has no edge IDs and gives a material-specific reason. This is a review of possibilities, not a quota requiring each kind to appear. Read the whole material again if the graph is a single line despite source-supported branches, parallel routes, comparisons or feedback. A valid all-linear source remains linear.
8. Validate and deliver with `scripts/finalize.py`. New systematic overviews require the v2 ledger and fail on incomplete unit, candidate, card or map mapping. Quick overviews retain their lighter workflow. `--legacy-rule-ledger` is exclusively for re-delivering a page produced before this contract; it must not be used to present new work as complete.

## Schema

Save `action-rule-ledger.json` next to `methods.json` in the knowledge base:

```json
{
  "schemaVersion": "learn-from-materials/action-rule-ledger-v2",
  "pageId": "same-as-page-meta-pageId",
  "learningDepth": "systematic",
  "units": [
    {"unitId": "u01", "status": "reviewed", "reviewedSourceIds": ["source-id-1"], "note": "Reviewed the full unit and its chart."},
    {"unitId": "u02", "status": "no-rules", "reviewedSourceIds": ["source-id-2"], "note": "Descriptive background; no condition-action relation."}
  ],
  "candidates": [{
    "id": "candidate-01", "unitId": "u01", "sourceIds": ["source-id-1"],
    "quote": "exact short passage from that block", "when": "condition",
    "do": "action", "because": "reason", "prerequisites": [], "exceptions": [],
    "stopCondition": "", "status": "retained", "targetRuleId": "rule-01",
    "reason": "Primary evidence for the visible rule card"
  }],
  "independentRules": [],
  "independentFrameworks": [],
  "relationStatus": "mapped",
  "relationReason": "Framework links were checked against the source",
  "relationReview": {
    "framework": [
      {"type":"prerequisite","status":"mapped","edgeIds":["edge-01"],"reason":"The cited passage makes the first framework a necessary input."},
      {"type":"sequence","status":"unsupported","edgeIds":[],"reason":"The frameworks are concepts, not consecutive steps."}
    ],
    "methodology": [
      {"type":"main","status":"mapped","edgeIds":["method-edge-01"],"reason":"The cited passage orders these actions."},
      {"type":"parallel","status":"unsupported","edgeIds":[],"reason":"The reviewed units describe one route only."}
    ]
  }
}
```

The `relationReview` arrays above show only two entries each to illustrate the fields. Before delivery, `framework` must have exactly one entry for each of `prerequisite/sequence/causes/supports/contrasts/part_of/applies/feedback/parallel`; `methodology` must cover `main/branch/feedback/supports/contains/causes/prerequisite/parallel/contrasts`. Each row uses `type/status/edgeIds/reason`, and edge IDs must exactly match that type in its actual graph. A missing type, invented ID or claim of "unsupported" while an edge exists fails validation. An absence reason should name what the material does or does not establish, not simply say "not applicable".

`status` for a candidate is `retained`, `merged` or `excluded`. `targetRuleId` is the visible `decisionRules[].id` for retained/merged, and `null` for excluded. `independentRules[]` entries contain `ruleId` and `reason`; `independentFrameworks[]` entries contain `frameworkId` and `reason`.

The validator checks the record's structure, all units and mapped source blocks, original quote existence and hashes, candidate dispositions, every visible card, and every card's methodology-node or independent placement. A completed ledger is an audit trail for the extraction work. It cannot independently prove that the first reading noticed every candidate; the deliberate final reread is part of the workflow.
