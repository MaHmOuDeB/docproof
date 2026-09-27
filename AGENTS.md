# AGENTS.md — instructions for any coding agent (Codex CLI, Gemini CLI, Cursor, Claude Code, …)

This repository builds **fact-grounded documents** (the reference case: a CV tailored to a job ad).
You drive the `docproof` CLI; you never edit `.docx` XML by hand.

## Ground rules
1. **Facts come only from the fact base** (`profile/fact-base.md`, or the path the user gives).
   Never invent experience, numbers, tools, titles or dates. Never claim anything listed under
   `## Known gaps`. If a fact is missing, ask the user; add it to the fact base only when they confirm.
2. **The reader wrote the job ad.** The document never mentions tailoring, keywords, ATS or the search.
3. **Trim words, never drop numbers.** At most one bolded key phrase per bullet.
4. **Nothing is delivered until the gates pass:** `docproof verify` (figures + known gaps),
   `docproof check` (layout), and you have looked at the PNG of every page.
5. Never submit an application or send anything on the user's behalf.

## Workflow for "tailor my CV to this ad"
```bash
docproof match ad.txt --facts profile/fact-base.md            # go/no-go: coverage ≥70% genuine, 50–70% say so, <50% stretch
docproof dump profile/base.docx                               # see the exact paragraph texts first
# write ops.json (see `docproof edit` help) and kw.json ({"<bullet start>": ["phrase"]})
docproof edit profile/base.docx ops.json applications/<co>/work.docx
docproof keywords applications/<co>/work.docx applications/<co>/<First_Last>_CV.docx kw.json
docproof verify applications/<co>/<First_Last>_CV.docx --facts profile/fact-base.md
docproof check  applications/<co>/<First_Last>_CV.docx --orig profile/base.docx --png applications/<co>/png
```
Then open every PNG. Report: the verdict, the honest gaps, every changed line (before → after),
and the gate results.

## Deeper guidance
The full writing and layout rules live in `claude/skills/doc-craft/` (plain Markdown, usable by any
agent): `references/section-by-section.md`, `bullet-writing.md`, `jd-tailoring.md`,
`format-and-ats.md`, `pipeline.md`. The review roles are in `claude/agents/` — an independent
claim auditor and a context-free reviewer are worth running as separate passes.

## Development
`python -m unittest discover -s tests -v` must pass; keep `docproof lint claude --rules examples/lint-rules.json` clean.
