---
description: Tailor the CV to a job ad, then audit every claim and get a fresh-eyes review
argument-hint: <path to job ad | URL | pasted ad text> [--no-review] [--persona "<name>"]
---

Tailor the user's CV to this job ad, audit it, and summarise the verdicts.

Job ad: $ARGUMENTS

## Steps

1. **Resolve inputs.**
   - If the argument is a file path, read it. If it's a URL, fetch it (prefer the company's own
     careers page). Otherwise treat the text as the ad.
   - Resolve the fact base: a path in the arguments → the user's `CLAUDE.md` →
     `profile/fact-base.md`. If none exists, stop and tell the user how to create one (see
     `examples/profile/fact-base.md` in the docproof repo).
   - Check `docproof --help` runs. If not, stop and point to the install steps.

2. **Author.** Run the `document-tailor` agent with the ad text and the fact-base path. Wait for
   it. If it returns a **no-go** or **long shot** verdict and the user hasn't confirmed, stop
   here: show the verdict and ask whether to proceed. Don't run later steps on a document that
   doesn't exist yet.

3. **Audit.** Run the `claim-auditor` agent on the finished `.docx` it produced, with the same
   fact base. Don't pass it the author's notes or change log; it audits the document cold.

4. **Review (on by default; skip only with `--no-review`).** Run one
   `fresh-eyes-reviewer` with **only** the rendered PDF (or PNGs) and the ad. Persona: the value
   of `--persona`, else "hiring manager for <role title>"; for a German Lebenslauf, "German HR".
   Don't give it the fact base.

5. **Triage.** You (not the sub-agents) decide what to act on:
   - Auditor **unbacked** rows: must be fixed before sending.
   - Auditor **overstated** rows: apply the honest wording.
   - Reviewer fixes: apply only those about clarity, order, emphasis or cutting that stay true
     to the fact base; turn any that need new facts into questions for the user.
   - If you change the document, do it through the `docproof` CLI per the doc-craft pipeline,
     then re-run `docproof verify`, `docproof story --ad` and `docproof check` and look at the PNGs again.
   - When a reviewer's fix conflicts with approved wording in the fact base, the fact base wins.
   - After applying fixes, ask the same reviewer to re-score once and report both scores.
   - Ask before applying reviewer suggestions that change structure (section order, cutting a
     whole entry).

6. **Summarise** in chat, tight:
   - **Verdict**: go / long shot, coverage %, hard-filter notes
   - **Files**: CV .docx and .pdf paths
   - **Gates**: `verify`, `story` and `check` results, "PNGs reviewed"
   - **Audit**: N claims: B backed / O overstated / U unbacked, and what was fixed
   - **Review**: persona, score before → after, top 3 fixes and which were applied or rejected (and why)
   - **Open gaps and questions** for the user

## Never

- Never submit the application, send an email or fill a form's final step.
- Never add a claim that isn't in the fact base, whatever a reviewer suggests.
- Never write a cover letter unless the user asks for one.
