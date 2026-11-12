# Docproof

**Fact-grounded documents with automated verification.** Docproof keeps every fact a document
may state in one Markdown fact base, and lets a Python CLI and a small team of Claude Code agents
build, edit, fact-check and typeset Word/PDF documents from it. Every figure in the output is
traced back to the fact base, and the layout is checked before anything is published.

The engineering is the point: multi-agent orchestration (an author, an independent claim
auditor and a context-free reviewer) on top of deterministic tools that prove what they changed.
A typical case is a policy document or a community notice whose dates, figures and names must
match a fact base exactly, checked against a short brief that says what the document has to
cover.

## Why

LLMs are good at rewriting and bad at staying honest. Letting a model revise a document drifts
into claims the source never made. Docproof separates the two jobs:

- **A single fact base** (`profile/fact-base.md`) is the only source of truth, including a
  `## Known gaps` list of things the document must never claim.
- **Deterministic tools** do the risky parts: they edit Word files surgically and prove that only
  the intended paragraph changed, check every number against the fact base, and verify the
  rendered PDF (page breaks, widows, links, every word present).
- **Agents with separate roles** do the judgment: an author edits, an auditor checks every claim
  against the fact base, and a context-free reviewer reads the result like a stranger would.

## Quick start

Needs Python ≥ 3.9 and Google Chrome or Chromium (for PDF rendering). Poppler (`pdftotext`,
`pdftoppm`) is recommended for page checks and PNG previews.

```bash
git clone https://github.com/MaHmOuDeB/docproof && cd docproof
pip install -e .                 # installs the `docproof` command (no runtime dependencies)
docproof doctor                  # checks Chrome, poppler and fonts
docproof demo                    # build → check → verify → story → match → coverage → prose on the fictional example
docproof init ~/workspace        # your own private workspace: profile/fact-base.md + a JSON template
```

`brew install poppler` on macOS, `sudo apt install poppler-utils` on Debian/Ubuntu. Without
poppler, `pip install -e ".[pdf]"` gives a pypdf fallback for text checks (no PNG previews).

## The CLI

| Command | What it does |
|---|---|
| `docproof build doc.json out.docx` | Build a Word document from JSON in the house template |
| `docproof render doc.docx --out doc.pdf --png previews/` | Typeset a designed PDF (Inter, embedded) with headless Chrome |
| `docproof check doc.docx [--orig base.docx] --png dir/` | Full gate: real .docx, protected header unchanged, every word in the PDF, page starts, widows, links, phrasing that points at the brief |
| `docproof verify doc.docx --facts fact-base.md` | Every figure must appear in the fact base; no "known gap" may be claimed; skills rows are cross-checked |
| `docproof story doc.docx --ad brief.txt --facts fact-base.md` | One story: the summary matches the title, every title phrase is proven in the body, repeated figures keep their scope, no line re-types the brief, every point serves the brief |
| `docproof coverage brief.txt --doc doc.docx --facts fact-base.md` | Which requirements of the brief the document shows, which the fact base could add, which stay open; coverage now → reachable |
| `docproof prose text.md --kind … --facts … --ad …` | Free-text companions (letters, short bios, summaries): figures and known gaps (FAIL), length limits, stock phrases, "not X but Y", echo, fit |
| `docproof match brief.txt --facts fact-base.md` | Requirement → evidence map with a coverage score (≥70% genuine, 50–70% honest middle, <50% stretch) and the gaps |
| `docproof dump / edit / keywords / reorder` | Safe edits: every change is proven to touch only its target |
| `docproof add-entry / add-link / add-summary / set-metadata` | Structural additions that clone the document's own formatting |
| `docproof lint paths… --rules rules.json` | Catch stale facts and rules in your own prompt/skill files |
| `docproof prompt tailor\|audit\|review\|write …` | Paste-ready prompt for ChatGPT, Gemini or any LLM, with all the context (`write` drafts free text) |
| `docproof apply in.docx reply.json out.docx --facts … --ad …` | Apply an LLM's JSON answer safely, then run `story` and `verify` on it |
| `docproof init [DIR]` | Create a private workspace with fact-base and document templates |

Run any command without arguments for its help.

Run any command without arguments for its help. In the CLI the brief is passed with `--ad`.

### What the checks report

- `verify` lists every figure that is not in the fact base and every claimed known gap, and fails
  the run if there is one.
- `story` checks that the document tells one consistent story: the title and the summary agree,
  repeated figures keep their scope, and no line merely re-types the brief.
- `coverage` and `match` map each requirement in the brief to evidence: shown in the document,
  closable from the fact base, or open. Above "reachable", only invention would help, and Docproof
  never invents.
- `prose` applies the same figure and known-gap checks to free text.

## Use it with any AI assistant

The CLI contains no AI and runs on its own. The assistant only proposes; the tools check.

| You use | How |
|---|---|
| **Claude Code** | `scripts/install.sh`, then the `/tailor` command with a brief — see the agents below |
| **Codex CLI, Gemini CLI, Cursor** | open the repo (or your workspace) — they read [`AGENTS.md`](AGENTS.md) / [`GEMINI.md`](GEMINI.md) and drive the CLI |
| **ChatGPT, Gemini, Claude.ai (in the browser)** | `docproof prompt …` builds a paste-ready prompt with your fact base, the brief and the match report; `docproof apply` applies the JSON answer and verifies it |

```bash
docproof prompt tailor --facts profile/fact-base.md --ad brief.txt --doc profile/base.docx --out prompt.txt
# paste prompt.txt into any assistant, save its JSON answer as reply.json, then:
docproof apply profile/base.docx reply.json notice.docx --facts profile/fact-base.md
docproof check notice.docx --orig profile/base.docx --png previews/
docproof prompt audit  --facts profile/fact-base.md --doc notice.docx   # second opinion on every claim
docproof prompt review --doc notice.docx --persona "first-time reader"   # fresh eyes, no fact base
```

If the model invents a number or claims a known gap, `apply` fails the verification and names it.

## The Claude Code agents

`scripts/install.sh` copies the Claude side into `~/.claude/` (or `--project` for `./.claude/`):

| | Role |
|---|---|
| `doc-craft` skill | Writing and layout rules the agents follow: section structure, wording, emphasis, page layout, English and German conventions, review modes |
| `document-tailor` agent | The author: checks fit with `match`, edits section by section through the CLI, and cannot finish until `verify`, `story` and `check` pass, the PNGs have been looked at and a fresh-eyes review has been applied and re-scored |
| `claim-auditor` agent | Independent line-by-line claim audit against the fact base (numbers, tools, "led" vs "supported"); never edits |
| `fresh-eyes-reviewer` agent | Reviews with **no** access to the fact base, as a named reader persona; run 2–3 in parallel |
| `/tailor` | Runs author → auditor → reviewer and triages the findings |
| `/letter` | Drafts a free-text companion from the fact base, checks it with `prose`, critiques it once and revises |

See [`claude/README.md`](claude/README.md) and [`docs/architecture.md`](docs/architecture.md).

## Your own fact base

Start from the fictional example in [`examples/profile/`](examples/profile/). Keep your own fact
base **outside** this repository or in a private fork; `profile/` and `applications/` are
git-ignored by default.

## Design rules baked in

- Never invent: a fact that isn't in the fact base doesn't go in a document.
- Trim words, never drop numbers.
- One story: the title, the summary and every point serve the same purpose; a line that doesn't
  serve the brief gives its space to one that does.
- Emphasis budget: at most two bold items per bullet (one key phrase plus figures).
- Short sections and entries with ≤ 4 bullets never split across pages; no one-word widows.
- Tighten wording instead of shrinking type.
- Always look at the rendered pages.

## Development

```bash
python -m unittest discover -s tests -v
docproof lint claude --rules examples/lint-rules.json
```

CI runs the tests (including a real Chrome render) and the demo on every push.

## License

MIT for the code. The bundled Inter font is under the SIL Open Font License
(`src/docproof/assets/fonts/LICENSE.txt`).
