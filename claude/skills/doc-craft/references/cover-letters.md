# Cover letters and application emails

A cover letter is a fact-grounded document like the CV: every claim comes from the fact base, and
`docproof prose --kind letter` checks it. What changes is the form: a letter has no bullet
structure to keep it honest, so invented numbers, stock phrases and assertions of fit slip in
more easily.

## When and in what form

- **Only when the user asks.** A tailored CV does not imply a letter.
- Output next to the CV: `applications/<company>/Cover_Letter_<First_Last>.pdf` (or `.md` / `.docx`
  when a form wants it pasted in or the user has a letterhead template).
- Same language as the CV for that application — and only in a language the candidate can also
  interview in. A polished letter in a language they can't speak at interview reads as misleading,
  not resourceful.

## Process

1. Read the ad, the `match` report and the tailored CV. Pick the **two** requirements that matter
   most to this employer and have the strongest evidence.
2. Draft (or use `docproof prompt write --kind letter` with any assistant).
3. `docproof prose letter.md --kind letter --facts <fact base> --ad <job-ad.txt>` — fix every FAIL.
4. Critique as the hiring manager (the `fresh-eyes-reviewer` agent, or `docproof prompt review`)
   and revise once.
5. Re-run `prose`. Read it aloud once: does it sound like the candidate?

## Show the fit, don't assert it

Chain every claim: **requirement → what the candidate did (with a figure) → what it means for this
employer.**

- Weak: "My experience perfectly matches your requirements."
- Strong: "You want faster decisions from experiments. At Northwind I designed and analysed 40+ A/B
  tests from power analysis to a ship/no-ship recommendation; 30+ shipped."

Concrete verbs beat adjectives: not "I am analytical" but "I analysed X and found Y"; not "highly
motivated" but a finished project.

## Structure

1. **Why this role**: tied to something this employer said (the ad, their site), not a generic opener.
2. **Evidence**: one or two requirement → evidence → benefit chains.
3. **How the candidate works**: one short paragraph, backed by a fact.
4. **A friendly close**: invite a conversation.

Each paragraph answers one question; `prose` warns when two paragraphs do the same job.
150–400 words, one page. Address a named person when one can be found.

## Gaps

- Never claim anything under `## Known gaps`; `prose` fails on it.
- **A gap the ad treats as central:** name the closest real evidence and what the candidate would
  build on ("I haven't used Braze in production; my CRM experiment work is the base I'd build on").
  A negated mention is a disclosure, not a claim, and `prose` accepts it.
- **A secondary gap:** leave it out, or give it one plain sentence. Don't apologise at length.

## Language that gets skipped

`prose` warns on stock phrases: "I am passionate/excited/thrilled", "perfect fit/match", "ideal
candidate", "results-driven", "team player", "proven track record", "I am writing to apply",
"Dear Sir or Madam", "with great interest", "hiermit bewerbe ich mich", "mit großem Interesse" and
similar. Also avoid:
- **"not X, but Y"** and "it's not about X, it's about Y": say the positive claim directly.
- **Most sentences starting with "I"**: open with the result or the reader's problem.
- **Re-typing the ad**: mirror single key terms where they are true; never its sentences. A sentence
  about the employer ("You want…", "Brightleaf is…") may quote them; a claim about the candidate may not.
- Flattery of the company, and interest asserted instead of explained.

Register: many European employers value precision and modest confidence over enthusiasm; keep it
warm but never salesy.

## Application emails

When the application goes by email: a short email (4–8 sentences, `--kind email`) plus the letter
and CV as attachments. The email gives the reader one reason to open them; it never repeats the letter.

## Unsolicited applications

With no ad to react to, the letter does more of the work: name the one or two role types that fit
the company, build the case from the fact base, and use specific detail from the company's own site.
Say "Unsolicited application" in the subject line, invite a first conversation, follow up once
after about two weeks.

## Work status and salary

- Mention work authorisation only when it affects the start date, and never claim a status the
  fact base doesn't record. The user approves that wording.
- Salary only when the ad asks for it in the letter; otherwise it belongs in the form or the first call.

## Done means

- [ ] `docproof prose --kind letter --facts … --ad …`: no FAIL; every WARN fixed or kept for a stated reason
- [ ] Every figure and tool traces to the fact base; no known gap claimed
- [ ] Two requirement → evidence → benefit chains, specific to this employer
- [ ] One page, one job per paragraph, in a language the candidate can interview in
- [ ] Read once as the hiring manager, revised, re-checked
