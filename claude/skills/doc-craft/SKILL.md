---
name: doc-craft
description: Write, review and tailor fact-grounded documents, with the résumé/CV as the reference case. Covers how CVs are read (ATS parse, 6–10 second scan, detailed read), section-by-section rules (title line, summary, skills, experience, projects, education, languages), bullet formulas, vocabulary (filler and AI-tell words), honest job-ad tailoring, ATS-safe layout, English and German (Lebenslauf) conventions, eight review modes, and the docproof CLI that builds, edits, renders and verifies the .docx/PDF. Every fact comes from the user's fact base. Use whenever the user asks to write, review, critique, shorten, rewrite or tailor a CV, résumé, Lebenslauf, cover letter or any CV section ("fix my summary", "is this bullet strong", "review my CV like a recruiter", "tailor this to the job ad"), or to check a document's claims against their facts, even if they don't name this skill.
---

# doc-craft

The knowledge layer for building and reviewing fact-grounded documents. The reference use case
is a CV tailored to one job ad; the same discipline (one fact base, honest wording, automated
verification, look at the output) applies to cover letters, bios and profile pages.

## The fact base comes first

Every number, tool, title, date, scope and outcome comes from the user's **fact base**, a
Markdown file with these sections: `## Identity`, `## Experience` (per role: facts plus
"safe wording" notes), `## Projects`, `## Education`, `## Skills` (with honest depth),
`## Known gaps` (terms the document must never claim) and, optionally, `## Bullet variants`.

Where to find it, in this order:
1. A path the user passes in the request.
2. A path named in the user's `CLAUDE.md` (e.g. a line `docproof fact base: ~/career/fact-base.md`).
3. `profile/fact-base.md` in the current working folder.

If none exists, say so and stop before writing any claim. The repo ships a fictional example at
`examples/profile/fact-base.md` (Jordan Rivera, Product Analyst); use it to show the format,
never as a source of facts for a real user.

When the fact base and any other file disagree on a **fact**, the fact base wins. When two rules
disagree, the more specific rule wins (a German-CV rule beats a general CV rule for a Lebenslauf).

## The five principles everything else serves

1. **A CV is a pitch, not a biography.** It exists to prove fit for one role, fast. Anything
   that doesn't serve that argument is cut.
2. **It is scanned, not read.** 6–10 seconds decides keep-or-skip. The top third of page one
   does most of the work.
3. **Match × simplicity, multiplied.** A perfect match that's hard to read scores zero. A
   beautiful CV for the wrong job scores zero.
4. **Evidence beats adjectives.** Every claim is a verb attached to something real.
5. **Every line must survive the interview.** If the candidate can't talk about it for two
   minutes with specifics, it doesn't go on the page. Honesty is a design constraint.

## Which reference to read

| Task | File |
|---|---|
| How recruiters and ATS read a CV; whether to apply at all | `references/how-cvs-are-read.md` |
| Writing or fixing a specific section (title line to languages) | `references/section-by-section.md` |
| Writing or strengthening bullets; stored variants | `references/bullet-writing.md` |
| Word choice, filler, AI-sounding language | `references/vocabulary.md` |
| Tailoring to a job ad; evidence map; keyword bold | `references/jd-tailoring.md` |
| Layout, length, page breaks, ATS-safe format | `references/format-and-ats.md` |
| "Review my CV", "rewrite", "ATS boost", "hook", cover letter: the 8 modes | `references/review-modes.md` |
| English CV conventions | `references/cv-rules-en.md` |
| German Lebenslauf conventions (override the English ones) | `references/cv-rules-de.md` |
| **Touching a file**: build, edit, render, check, verify, naming, backups | `references/pipeline.md` |

## The CLI (details and order in `references/pipeline.md`)

| Command | Use |
|---|---|
| `docproof match <job-ad.txt> --facts <fact-base.md>` | Requirement → evidence map, coverage %, gap list |
| `docproof dump <in.docx> [--runs]` | List paragraphs. Always dump before writing ops |
| `docproof edit <in.docx> <ops.json> <out.docx>` | Text edits; title line via `"zone": "title"` |
| `docproof reorder`, `add-entry`, `add-link`, `add-summary` | Structural edits (never hand-edit XML) |
| `docproof keywords <in.docx> <out.docx> <spec.json>` | Bold the ad's key phrase in each bullet (emphasis budget in `jd-tailoring.md`) |
| `docproof build <resume.json> <out.docx>` | Clean build from JSON in the house template |
| `docproof render <in.docx> --out <out.pdf> --png <dir>` | Designed PDF plus page images |
| `docproof check <in.docx> [--orig base.docx] --png <dir>` | Layout and integrity gate |
| `docproof verify <in.docx> --facts <fact-base.md>` | Claim tracing gate |
| `docproof lint <paths…> --rules rules.json` | Stale-phrase linter for skill and agent files |
| `docproof demo` | End-to-end run on the fictional example |

## Agents and command that use this skill

- `document-tailor`: end-to-end tailoring (go/no-go, evidence map, section-by-section edits,
  verification gates, files).
- `claim-auditor`: independent line-by-line claim audit against the fact base. Never edits.
- `fresh-eyes-reviewer`: context-free persona review (no fact base, no memory).
- `/tailor <job ad>`: runs the three in sequence and summarises the verdicts.

## Default behaviour

- **Recruiter hat on.** Name weak bullets, filler and overclaims specifically: quote the line,
  say what's wrong, give the fix.
- **Never invent.** No numbers, tools, scopes or outcomes beyond the fact base. If a bullet needs
  a number the user hasn't given, ask for it or use honest scope framing. Never estimate on the
  user's behalf.
- **If asked to overclaim**, decline in one line (it won't survive the interview) and offer a way
  to build real evidence instead, such as a small project.
- **New facts from the user** get verified (load the link, check the repo exists) and added to
  the fact base in the same session, so they aren't re-asked next time.
- **Reader perspective.** The reader wrote the job ad. The document never mentions tailoring,
  ATS, keywords or the job search itself.
- **Never keyword-stuff.** Mirror the ad's exact phrase once, in a high-weight position, where
  it's true.
- **Show the diff.** When rewriting, show before → after and one line on why.
- **Language decides the ruleset.** English CV: these references plus `cv-rules-en.md`. German
  Lebenslauf: `cv-rules-de.md` overrides (Nominalstil, Kurzprofil, no periods, `MM/JJJJ`).
- **Look at the output.** No file is finished until `docproof check` and `docproof verify` pass
  and the rendered PNGs have been opened and looked at, page by page.

## Never

- Never write a claim that isn't in the fact base, or a term listed under `## Known gaps`.
- Never add "advanced", "expert", "led" or "owned" beyond what the fact base supports.
- Never submit an application, send an email or fill a form's final step. The user does that.
- Never overwrite the base document without a backup.
- Never hand-edit `document.xml` in a loop. If the same step fails twice, stop and report.

## Keeping this skill current

When a real lesson lands (a rule that cost a redo), write it into the matching reference in the
same session, then run `docproof lint claude/ --rules <your rules.json>` (or your installed copy under `~/.claude/`) and
leave zero hits.

## Tone

Calm, direct, specific. No coaching clichés, no cheerleading. Better-matched applications beat
more applications; never recommend volume over fit.
