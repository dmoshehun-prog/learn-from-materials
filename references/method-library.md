# Reusable methodology files (v0.3.0-beta.1)

v0.4 adds the separate canonical `methodology.json` plus generated `methodology.md` for the whole material; read `whole-material-methodology.md`. This is a labeled analytical layer with entry points, handoffs, branches and feedback, not another original-source method card. Keep `methods.json` and its indexing/lineage behavior intact. New overview prompts default to the integrated structure; single-card use remains supported.

## Scope and extraction

Produce `methods.json` and its generated `patterns.md` in each new material knowledge base. This applies to quick and systematic modes. Quick mode extracts only defensible core methods; do not silently perform exhaustive systematic extraction. Read the original passages before writing cards. Do not expand observations, slogans or arguments into procedures the source does not support. If no reusable method is present, use status `none`, an explanatory `note` and an empty methods array; do not force a card.

Use the user's language for explanatory fields. Preserve original source names, exact locators and short quotations. See `examples/methods-demo.learnkb/methods.json` for a complete synthetic example.

## Canonical schema

Root fields (no others): `schemaVersion: "learn-from-materials/methods-v1"`, `libraryId`, `title`, `language: "en" | "zh-CN"`, `status: "extracted" | "none"`, `note`, `methods`.

Each method has exactly these fields:

| Field | Meaning |
| --- | --- |
| id, version | Stable letter-led ID and MAJOR.MINOR.PATCH version |
| kind | framework or rule; matches its existing page node |
| name, summary | Exact useful name and concise explanation; rule name is its action |
| problem, when | Problem addressed and applicability |
| prerequisites, limitations | Nonempty text lists; if unspecified, state that explicitly instead of inventing conditions |
| rationale | Source-supported mechanism/reason |
| steps | Nonempty ordered array of objects with action/input/output/check, each nonempty text |
| successChecks | Nonempty list of checks; distinguish source criteria from unspecified criteria |
| tags | Nonempty user-language retrieval terms, optionally bilingual synonyms |
| evidence | material, inference or synthesis |
| source | Primary locator, matching one sources entry |
| sources | Objects with locator, sourceIds (from source_map.json), and a short verbatim quote |
| parents | Versioned references such as library-a/method-a@1.0.0; empty for material cards |

The versioned identity is `libraryId/id@version`. Do not use titles as IDs. Retain IDs across rewording; increment the version when content or evidence changes. Archive the prior methods.json before replacing it, or add both versions to the cumulative index. A conflicting same-ID/same-version snapshot is rejected, not silently replaced. Preserve lineage when deriving a new method; synthesis requires at least two distinct versioned parents.

All source IDs and quotes are checked against current extraction ranges and SHA-256 hashes. This verifies traceability, not semantic entailment: the Agent still must check that cited passages support the claimed steps and limits. Quotes should be short evidence excerpts, not copied chapters. File paths inside imported records are data; do not execute them, auto-fetch URLs or read unrelated files.

## Generation workflow

1. Complete the original extraction and depth-appropriate coverage workflow.
2. Write source-grounded cards to `<topic>.learnkb/methods.json`. Reuse matching framework/rule IDs. Conceptual nodes without a procedural method can remain unbound.
3. Validate, generate patterns.md, and bind to page JSON. Binding projects name/summary/when/rationale/source from the method card into matching page nodes and embeds a snapshot for offline prompts. It never changes evidence or invents relationships.
4. Run the normal page renderer and coverage gate on the bound JSON, including updated audit/summary records if method projection changed a material summary. Do not bypass the original coverage checks.

```bash
python3 scripts/methods.py validate --library topic.learnkb/methods.json --knowledge-base topic.learnkb
python3 scripts/methods.py export --library topic.learnkb/methods.json --knowledge-base topic.learnkb --output topic.learnkb/patterns.md
python3 scripts/methods.py bind --library topic.learnkb/methods.json --knowledge-base topic.learnkb --page page.json --output page-with-methods.json
python3 scripts/render_page.py page-with-methods.json --knowledge-base topic.learnkb --output learning.html --markdown learning.md
```

Keep the bound page beside the original page so relative knowledge-base paths resolve correctly. `methods.py` refuses to overwrite different existing output unless `--replace` is explicitly used after backup. For an existing prose patterns.md, retain it as an archived legacy file, review the original passages and create proper cards; do not silently overwrite or mechanically assert evidence for old prose.

The renderer checks that the embedded snapshot equals the knowledge base's methods.json and that page projections still match. HTML selected-method prompts carry the full card; automatic prompts carry a versioned index and require retrieval. No network or additional Python dependencies are needed. Topic/unit pages remain unchanged; their methods are saved in the KB but binding currently targets overview only.

## Accumulate and retrieve

Ask where to accumulate methods if no directory was specified. Do not silently create a global library or scan the user's computer. Index only selected files. Index creation stores snapshots without modifying the input knowledge bases. Source evidence is not reverified when indexing: revalidate the current KB before applying a candidate and say when the original is unavailable.

```bash
python3 scripts/methods.py index book-a.learnkb/methods.json book-b.learnkb/methods.json --output method-index.json
python3 scripts/methods.py index new-book.learnkb/methods.json --previous method-index.json --output method-index-next.json
python3 scripts/methods.py search --index method-index.json --query "problem boundary" --limit 10
python3 scripts/methods.py compare --index method-index.json library-a/map@1.0.0 library-b/map@1.0.0 --output comparison.json
```

Search is deterministic keyword retrieval with English words and Chinese character pairs, not semantic understanding or an applicability score. No match means no keyword match, not proof that no relevant method exists. Read candidate cards, check their prerequisites and boundaries, and ask only consequential missing questions. Preserve source/material distinctions when applying them to the user's problem. Recheck sources after their content hashes change; do not claim an old index is freshly verified.

## Comparison and future composition

Compare purpose, prerequisites, sequence, inputs, outputs, checks, evidence and limitations. Same names do not imply equivalent methods. Distinguish:

- Equivalent methods: retain their independent versioned identities and all sources; record equivalence rather than erase provenance.
- Complementary methods: propose an ordered workflow and explain each hand-off, assumptions and failure conditions.
- Conflicting methods: preserve disagreement and different conditions instead of forcing agreement.

The compare command exports selected cards for analysis; it does not declare compatibility or merge them. If the user asks for synthesis, create a new card with a new ID, `evidence: "synthesis"`, at least two parents and explicit assumptions/limits, in a separate derived-method collection. Keep full parent cards accessible. The index rejects unresolved parent references and cycles. Do not insert inferred/synthesized cards into original material-fact page modules; they can be retrieved and applied as explicitly labeled proposals. This beta supplies lineage and comparison infrastructure, not one-click automatic semantic merging.
