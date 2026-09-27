# docproof for Claude Code

The Claude Code half of docproof: one skill, three agents and one slash command that write,
audit and review a fact-grounded document. The reference use case is a CV tailored to a job ad.
Everything here drives the `docproof` CLI, and every claim comes from one file: the user's
**fact base**.

## What's here

| Path | Type | Does |
|---|---|---|
| `skills/doc-craft/` | Skill | The knowledge layer: how CVs are read, section-by-section rules, bullet writing, vocabulary, honest job-ad tailoring, layout/ATS rules, English and German conventions, eight review modes, and the CLI pipeline (`references/pipeline.md`). |
| `agents/document-tailor.md` | Agent (author) | Go/no-go, evidence map (`docproof match`), section-by-section edits through the CLI, then the gates: `docproof verify`, `docproof check`, and a look at the rendered PNGs. Cover letter only on request. |
| `agents/claim-auditor.md` | Agent (auditor) | Reads the finished document and the fact base, runs `docproof verify`, then judges what the script can't (ownership inflation, implied tools, misleading phrasing). Returns claim → source line → verdict → fix. Never edits. |
| `agents/fresh-eyes-reviewer.md` | Agent (reviewer) | Reviews the document as a named persona with no access to the fact base or memory. Score, top 5 fixes, what to cut. Run 2–3 personas in parallel. |
| `commands/tailor.md` | Slash command | `/tailor <job ad>`: author → auditor → one reviewer, then triage and a short summary. |

## How they hand off

```
job ad ──► document-tailor ──► CV.docx + CV.pdf  (verify + check passed, PNGs looked at)
                                    │
                                    ├──► claim-auditor       (document + fact base)   → backed / overstated / unbacked
                                    └──► fresh-eyes-reviewer (document + ad only)      → score, top 5 fixes
                                                 │
                         orchestrator (you, or /tailor) triages both against the fact base,
                         applies true fixes via the CLI, re-runs the gates
```

The separation is deliberate. The author optimises; the auditor only checks truth; the reviewer
only sees what a stranger sees. None of them submits anything.

## The fact base

A Markdown file with `## Identity`, `## Experience` (facts plus safe-wording notes per role),
`## Projects`, `## Education`, `## Skills` (honest depth), `## Known gaps` (terms never to claim)
and optionally `## Bullet variants`. See `../examples/profile/fact-base.md` (a fictional
candidate).

The agents look for it in this order: a path in the request → a line in your `~/.claude/CLAUDE.md`
such as `docproof fact base: ~/career/fact-base.md` → `profile/fact-base.md` in the working folder.

## Install

```bash
# 1. install the docproof CLI (see the repo README)
scripts/install.sh          # 2. copies skills/, agents/ and commands/ into ~/.claude/
docproof demo               # 3. end-to-end check on the fictional example
```

`install.sh` copies the files; re-run it after pulling updates. The agents have no `tools:` line,
so they inherit all your tools, including MCP servers. Rendering needs Google Chrome (headless).

## Keeping it honest

After editing any skill or agent file, run `docproof lint claude/ --rules examples/lint-rules.json` (your own rules file) and leave zero hits. When a
rule changes, update the one reference that owns it rather than repeating it elsewhere.
