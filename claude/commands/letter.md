---
description: Write a cover letter, application email, LinkedIn headline/About, bio or pitch from the fact base, checked and revised
argument-hint: [letter|email|about|headline|bio|pitch] [<path to job ad | URL | pasted ad text>]
---

Write a fact-grounded prose document for the user, check it, critique it once and revise it.

Arguments: $ARGUMENTS

## Steps

1. **Resolve inputs.**
   - The kind: the first argument if it is one of `letter`, `email`, `about`, `headline`, `bio`,
     `pitch`; otherwise `letter` when a job ad is given, else ask.
   - The job ad (needed for `letter` and `email`, optional otherwise): a file path, a URL (prefer
     the company's own careers page) or pasted text. Save it as `applications/<company>/job-ad.txt`.
   - The fact base: a path in the arguments → the user's `CLAUDE.md` → `profile/fact-base.md`. If
     none exists, stop and say how to create one.
   - If a tailored CV exists for this company, read it: the letter must tell the same story.

2. **Read the rules**: `doc-craft/references/cover-letters.md` for `letter` and `email`,
   `doc-craft/references/profiles-and-pitches.md` for the others, and `vocabulary.md`.

3. **Plan in one short list** (for letters): the two requirements that matter most and the
   fact-base line that proves each; what the candidate would build on for a central gap, if any.

4. **Draft** to `applications/<company>/Cover_Letter_<First_Last>.md` (letters and emails) or
   `profile/<kind>.md` (the others). Every figure and tool comes from the fact base.

5. **Check**: `docproof prose <file> --kind <kind> --facts <fact base> [--ad <job-ad.txt>]`.
   Fix every FAIL. Fix each WARN or keep it for a stated reason.

6. **Critique once**: run the `fresh-eyes-reviewer` agent with only the draft (and the ad), as
   "hiring manager for <role>" (letters) or "recruiter searching for <role>" (profiles). Apply the
   fixes that stay true to the fact base; the fact base wins over any suggestion. Re-run step 5 and
   ask the reviewer to re-score once.

7. **Deliver**, tight: the text (ready to paste), the file path, `prose` result, score before →
   after, and anything the user must decide (a named addressee, a gap to mention or not, work status).
   Offer to render a PDF when a letter will be attached.

## Never

- Never invent a figure, tool, scope or outcome; never claim a `## Known gaps` term.
- Never send, post or submit anything. The user does that.
- Never write in a language the candidate couldn't also interview in.
