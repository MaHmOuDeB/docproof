# The Eight Review Modes

Built from eight widely shared CV prompts. Each was useful in shape but risky as written: several
invite exactly the failures this skill forbids ("sound more quantifiable" invites invented
numbers; "enthusiastic" clashes with German-market tone and the AI-phrase list). Each mode keeps
the intent and adds the guardrail.

Recognise the mode from the request. Modes chain: the `document-tailor` agent runs
1 → 7 → 2/5 → 3 → 4 → 6, plus 8 only when the user asks for a letter.

---

## Mode 1: Spot the flaws (recruiter audit)

**Trigger:** "review my CV", "be brutally honest", "what's weak", "act as a recruiter".

**Do:**
1. Run the **8-second test** first: what would a recruiter conclude from the top third alone?
   Say it in one sentence.
2. Go section by section. For each issue: **quote the exact line → name the problem → give the fix.**
3. Check these categories:
   - Task-not-achievement bullets (no result, no scope)
   - Missing metrics where a real one exists in the fact base
   - Filler and AI-tell vocabulary (`vocabulary.md`)
   - Overclaims against the fact base (ownership, depth, scope, tenure)
   - Repeated openers, inconsistent tense, dates or spelling
   - Irrelevant content taking space from relevant content
   - ATS risks (tables, columns, header content, images)
   - Reader-perspective breaks (any mention of tailoring, ATS or the job search)
4. End with the **top 3 changes by impact**, not a flat list of thirty nits.
5. **Stress test** before calling any CV done: is the strongest item for this role missing or
   buried? Is the Skills section carrying tools that don't serve this role? Does any bullet end
   on the task instead of a result, scale or adoption? Does `docproof verify` pass?

For a second opinion without shared context, run the `fresh-eyes-reviewer` agent; for a
line-by-line claim audit, the `claim-auditor` agent.

**Guardrail:** brutal about the work, never contemptuous about the person.

---

## Mode 2: Rewrite for impact

**Trigger:** "make it more results-driven", "rewrite this", "stronger bullets".

**Do:** apply `bullet-writing.md` (verb + task + how + scope + result). Show before → after.

**Guardrail (critical):** "more quantifiable" means *surface real numbers and scope that are
already in the fact base*, never create new ones. If a bullet needs a number that doesn't exist,
use scope or adoption framing, or ask. "Sound compelling" is subordinate to "stay defensible".

---

## Mode 3: ATS boost

**Trigger:** "optimise for ATS", "keywords", "will this pass ATS".

**Do:**
1. Structure check first (parse layer): one column, no tables or graphics in the body, standard
   headings, nothing critical in page headers/footers (`format-and-ats.md`).
2. Keyword layer: `docproof match <ad> --facts <fact base>`, then `jd-tailoring.md` Steps 1–4.
   Mirror exact phrases where true, once, in high-weight positions.

**Guardrail:** never stuff; never add a tool the candidate hasn't used. If silence after applying
is worrying the user, remind them the "75% auto-rejected" figure is a myth.

---

## Mode 4: Craft the hook (summary)

**Trigger:** "write my summary", "3-line hook", "professional profile".

**Do:** use the formula in `section-by-section.md` §3. Target 3 lines. First clause = identity +
level + domain; one flagship number; end on the direction for *this* role. Offer two versions
with different flagship proof points (e.g. experimentation-led vs. automation-led) and say which
fits the ad better and why.

**Guardrail:** "powerful" means specific, not loud. No metaphors, no dash chains, no adjective
stacks, no "passionate". True line by line.

---

## Mode 5: Upgrade the experience section

**Trigger:** "rephrase my experience", "highlight transferable skills".

**Do:**
1. Reorder bullets by relevance to the ad.
2. Rewrite each with the formula; vary verbs. Check the fact base's `## Bullet variants` first:
   a stored alternate is already verified.
3. Make **transferable skills** explicit where the domain differs (e.g. subscription-app
   experimentation → e-commerce checkout testing: same hypothesis → test → measure → recommend
   loop).
4. Trim older or irrelevant roles to 1–2 lines.

**Guardrail:** transferable ≠ equivalent. "Experimentation transfers to checkout testing" is
honest. "Managed checkout optimisation" is not.

---

## Mode 6: Format fix

**Trigger:** "clean format", "modern layout", "make it ATS-friendly".

**Do:** apply `format-and-ats.md`. Report each deviation (column count, tables, date consistency,
length, page breaks, widows) and the fix. Render with `docproof render`, gate with
`docproof check`, then look at the PNGs. Design issues are fixed in the renderer, not per file.

**Guardrail:** don't rebuild the user's header or remove a photo without asking. Flag clearly
when a current element is an ATS risk.

---

## Mode 7: Tailor for the role

**Trigger:** a pasted job ad, "tailor this", "adapt my CV for this job".

**Do:** the full `jd-tailoring.md` process, section by section (`section-by-section.md`). Output:
1. Fit verdict (≥70–75% of must-haves?) and hard-filter check
2. Requirement → evidence map with ✅ / ⚠️ / ❌ (`docproof match`)
3. The tailored CV, every section
4. What changed and why, in a short list
5. Gaps left open, honestly

For the end-to-end flow with files and gates, use the `document-tailor` agent or `/tailor`.

**Guardrail:** select, trim and reorder from the fact base; never write a new claim to match a
keyword.

---

## Mode 8: Cover letter

**Trigger:** "write a cover letter", "Anschreiben", "motivation letter". Only when the user asks;
a tailored CV does not imply a letter.

**Process:** draft → explicit recruiter critique against this posting → revise → AI-phrase pass
(`vocabulary.md`) → read it once more for voice.

**Structure** (one job per paragraph):
1. Reason for applying, tied to this posting's own language
2. Education and relevant experience
3. Evidence of fit: 1–2 chains of **requirement → candidate's experience → benefit for the
   employer**, with numbers from the fact base
4. Working style
5. Short, friendly close

**Rules:**
- Show fit, never assert it. "My experience perfectly matches" is out; a concrete chain is in.
- Core gap → forward reframe ("ready to go deep on X, building on strong Y fundamentals").
  Secondary gap → brief honest mention, or leave it out.
- Name a person if one is findable; no generic "Dear Hiring Manager" when a name exists.
- Salary only if the posting explicitly asks for it in the letter.
- Write in a language the candidate can also interview in. A polished letter in a language they
  can't hold a conversation in reads as misleading.
- Email applications: a 4–6 sentence email plus the letter as an attachment; don't duplicate.

**Length:** full letter ~250–350 words, 4–5 short paragraphs. A **short variant** under 200
words for email bodies, messages or character-limited form fields.

**Guardrail:** "enthusiastic" becomes **specific and warm**: enthusiasm shows through precise
knowledge of the product and a concrete fit. Run `docproof verify`-style scrutiny on the letter's
claims too: every number must be in the fact base.
