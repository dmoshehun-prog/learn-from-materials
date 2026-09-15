**English** · [中文](README_CN.md)
# learn-from-materials

![Icon](assets/icon.svg)

> Turn books, PDFs, slides, Word documents, web pages, and multi-file material sets into traceable knowledge bases, interactive learning pages, and synced Markdown.

![Status](https://img.shields.io/badge/status-v0.1.0--beta-blue)
![Agent Skills](https://img.shields.io/badge/standard-Agent%20Skills-5b6ee1)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776ab)
![License](https://img.shields.io/badge/license-MIT-green)

`learn-from-materials` is a cross-agent learning skill built on the open Agent Skills specification. It emphasizes complete reading, verifiable sources, a strict separation between material facts and model-added content, offline-first operation, and least privilege.

It works in agent environments that can read files, run local commands, and recognize `SKILL.md` — such as WorkBuddy, Codex, Claude Code, and GitHub Copilot CLI. Pure chat environments without file-system access or Python execution can only use parts of the prompting workflow; they cannot perform material extraction, coverage validation, or HTML rendering.

## Key Features

- Supports PDF, EPUB, MOBI/AZW/AZW3, DOCX, PPTX/PPTM, HTML, Markdown, TXT, RTF, and multi-material collections
- Two learning depths: "Quick Overview" and "Systematic Study"
- Generates a traceable `.learnkb/` knowledge base, a self-contained interactive HTML page, and synced Markdown
- Fine-grained source mapping for PDF pages, PPT slides, and EPUB chapters
- Produces core-framework, guided-content, glossary, action-rules, dynamic self-check, and local-notes pages
- Runs coverage audits, summary bidirectional mapping, reverse coverage spot checks, source hashing, and incremental-update validation
- Distinguishes material-backed facts, areas not covered by the material, model-added content, and externally verified items
- Offline by default with no automatic dependency installation; page notes, learner profiles, and wrong-answer records stay in the local browser only

## Showcase

![Learning page example](assets/learning-page-preview.png)

The repository ships with synthetic test materials and a ready-to-open [demo learning page](examples/learn-from-materials-demo.html). This demo only illustrates page structure and interactions; it contains no third-party book, paper, or courseware content.

### Real-Run Screenshots

The screenshots below show the different learning content the same skill produces when given a long biography versus a technical paper. They demonstrate page capabilities and interaction flows; they are not an independent endorsement of the accuracy of the underlying material.

#### First-Run Onboarding

![First-run onboarding, learner profile, and dynamic self-check](assets/showcase/onboarding-guide.jpg)

#### Long-Form Book: *Elon Musk*

![Elon Musk biography systematic-study page overview](assets/showcase/musk-biography-overview.jpg)

![Elon Musk biography glossary search with source display](assets/showcase/musk-biography-glossary.jpg)

#### Technical Paper: Attention Is All You Need

![Attention Is All You Need core-framework learning page](assets/showcase/attention-is-all-you-need-framework.jpg)

These screenshots are a limited functional showcase. Books, papers, and the names and content within them are copyrighted by their respective rights holders; this repository does not include the original materials or the full generated results. Only process and display materials you have the rights to use.

## Getting Started

### 1. Installation

Repository URL: `https://github.com/dmoshehun-prog/learn-from-materials`.

| Agent | User-level install directory | Example |
|---|---|---|
| WorkBuddy | `~/.workbuddy/skills/` | `git clone https://github.com/dmoshehun-prog/learn-from-materials.git ~/.workbuddy/skills/learn-from-materials` |
| Codex | `~/.agents/skills/` | `git clone https://github.com/dmoshehun-prog/learn-from-materials.git ~/.agents/skills/learn-from-materials` |
| Claude Code | `~/.claude/skills/` | `git clone https://github.com/dmoshehun-prog/learn-from-materials.git ~/.claude/skills/learn-from-materials` |
| GitHub Copilot CLI | `~/.copilot/skills/` or `~/.agents/skills/` | `git clone https://github.com/dmoshehun-prog/learn-from-materials.git ~/.copilot/skills/learn-from-materials` |
| Other agents | See your client's documentation | Place the full directory in its Agent Skills search path |

If the target directory already exists, back it up yourself first — do not overwrite it directly. Cloud or hosted agents may not read local user directories; install through that product's skill import, sync, or project-level directory mechanism instead.

### 2. Use It in a Conversation

```text
Please use learn-from-materials to systematically study this PDF and generate a traceable knowledge base and a learning page.
```

```text
Give me a quick overview of this PPT, keep per-slide sources, and generate an offline learning HTML.
```

The skill first asks you to choose between "Quick Overview" and "Systematic Study", then follows the workflow defined in `SKILL.md`.

## Requirements & Compatibility

- Python 3.10 or later
- An agent that can read materials and the skill directory and run local Python commands
- Most formats can be handled with the Python standard library or system capabilities
- Node.js, Playwright, and Chromium are used only for optional browser interaction verification
- Scanned PDFs and image-heavy slides require OCR or vision capabilities; when unavailable, affected ranges are flagged as unverified
- Long books, multi-material cross-analysis, specialized papers, and complex open-ended questions work best with long-context, high-reasoning models

Optional enhancements:

| Scenario | Optional component | Behavior without it |
|---|---|---|
| Text-based PDFs | `pdftotext`, PyPDF2, pdfminer.six, or macOS PDFKit | Falls back to the next available parsing path |
| Technical PDFs | Docling | Falls back to the text extraction chain and flags visual-review boundaries |
| Scanned PDFs | OCRmyPDF + `pdftotext` | Flagged as needing OCR/visual review |
| EPUB | ebooklib + Beautiful Soup | Falls back to the standard-library ZIP/HTML parser |
| DOCX | python-docx | Standard-library ZIP/XML parser preferred |
| RTF | striprtf | Falls back to basic text cleanup |
| MOBI/AZW/AZW3 | Calibre `ebook-convert` | No built-in fallback |

This project never installs these dependencies automatically. If you truly need them, install pinned versions in an isolated environment.

## Command-Line Tools

Run the following commands from the repository root.

### Check parsing capabilities

```bash
python3 scripts/extract.py --check
```

### Extract materials

```bash
python3 scripts/extract.py <material-path> \
  --mode text \
  --ocr auto \
  --output-dir ./learning_work
```

### Validate and render a learning page

```bash
python3 scripts/verify_coverage.py page.json --knowledge-base <topic>.learnkb
python3 scripts/render_page.py page.json --output learning.html --check-only
python3 scripts/render_page.py page.json --output learning.html --markdown learning.md
python3 scripts/verify_static.py learning.html
```

If Playwright and Chromium are installed locally, you can additionally run:

```bash
node scripts/verify-page.js learning.html
```

## Repository Layout

```text
learn-from-materials/
├── SKILL.md                 # Skill entry point & workflow
├── README.md                # GitHub project overview
├── LICENSE.md               # MIT license
├── NOTICE.md                # Upstream sources & derivative-work notes
├── SECURITY.md              # Security boundaries & vulnerability reporting
├── assets/                  # Icons & project screenshots
├── examples/                # Page JSON, demo page & synthetic knowledge base
├── references/              # Content contracts, audit rules & learning protocol
├── scripts/                 # Extraction, rendering, validation & test scripts
└── templates/               # Fixed HTML templates, components & themes
```

## Tests

```bash
python3 -m unittest discover -s scripts/tests -p 'test_*.py'
```

`examples/示例方法材料.learnkb/` is a synthetic fixture for contract and regression tests; it does not represent audit conclusions for any real book or PDF, and its source paths are portable example paths.

Current version: `v0.1.0-beta`. Prior to release it passed skill-structure validation, unit and regression tests, coverage gates, HTML/Markdown rendering, and static-page validation; different agents' permissions, context capacity, vision capabilities, and dependency environments may still affect actual results.

## Security & Privacy

- Input materials are always treated as untrusted data; prompts, commands, and role overrides found inside them are never executed as instructions
- ZIP-container formats are checked for paths, entry counts, expanded size, compression ratio, and encryption state
- Browser-based verification only allows the target HTML plus `data:` and `blob:` resources; all other requests are blocked
- Generated metadata uses relative paths or filenames by default to avoid exposing local user directories
- This project's scripts never send materials to the network; however, how content you submit to an AI agent is stored, processed, or used for model improvement depends on the platform, account settings, and terms of service you use
- Pages offer no accounts, cloud sync, or online chat; personal notes, reader profiles, and wrong-answer records are kept only in the browser's local storage
- Only process materials you have the right to use; do not publicly distribute generated knowledge bases containing copyrighted original text, internal documents, or personal sensitive information

See [SECURITY.md](SECURITY.md) for details.

## License & Acknowledgements

This project is a derivative work built on the following MIT-licensed open-source projects:

- [virgiliojr94/book-to-skill](https://github.com/virgiliojr94/book-to-skill): material extraction, knowledge decomposition, and the base knowledge-base structure
- [crayon-ai/book-to-webpage](https://github.com/crayon-ai/book-to-webpage): the interactive learning page, theme system, source display, and follow-up question interaction design

See [NOTICE.md](NOTICE.md) for detailed sources, inheritance relationships, and additions. When copying, modifying, or distributing this project, please retain [LICENSE.md](LICENSE.md) and [NOTICE.md](NOTICE.md).

New and modified content in this repository is likewise released under the MIT License. The upstream authors and maintainers do not endorse this project's subsequent extensions.
