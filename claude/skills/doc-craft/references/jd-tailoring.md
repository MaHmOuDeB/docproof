# Tailoring to a Job Ad

A CV isn't a life history; it's an argument for *this* role at *this* company. Tailoring means
reading the ad line by line and mirroring its language wherever it's honestly true.

The examples below use the repo's fictional candidate, Jordan Rivera (Product Analyst, three
years at Northwind Apps). See `examples/profile/fact-base.md`.

## Step 1: Decompose the ad

1. **Extract 8–10 key terms**: skills, tools, methods, certifications, domain words. Use the
   ad's exact phrasing.
2. **Classify each:** must-have (under "Requirements", repeated, or stated as required) vs.
   nice-to-have ("ideally", "a plus", "bonus").
3. **Group into 4–6 themes.** If the ad has six key requirements, those become the themes the CV
   must visibly address.
4. **Note the hard filters first:** language level, years, degree, enrolment status, work
   authorisation, location/onsite. A hard-filter miss changes the decision, not the wording.

## Step 2: Ask five questions of every line

1. **What is this line actually testing for?** "Manages competing priorities" = can the
   candidate handle ambiguity and deadlines at once?
2. **What exact words does the ad use, and are they true of the candidate?** Mirror only what's
   accurate.
3. **Is there a real, specific example?** Search the fact base for the closest match; a
   different industry or smaller scale still counts.
4. **What tool, method or number proves it?** A claim becomes proof when it gets a specific.
5. **Does this line belong on this version?** Cut or demote experience that doesn't build the
   case for this role.

## Step 3: Map requirements to evidence

Run `docproof match <job-ad.txt> --facts <fact-base.md>` for the first pass. It proposes the
map, the coverage % against the 70% rule, and the gap list. Then review it by hand: the script
matches terms, you judge whether the evidence really answers the requirement.

| Ad requirement (exact words) | Must/Nice | Evidence in fact base | Where it goes | Status |
|---|---|---|---|---|
| "A/B testing" | Must | 40+ A/B tests run, 30+ shipped | Title, summary, bullet 1 | ✅ Strong |
| "SQL, dbt" | Must | SQL + dbt KPI layer used by 5 teams | Skills, bullet 2 | ✅ Strong |
| "causal inference" | Nice | A/B tests with power analysis; MSc dissertation on uplift modelling | Name the real methods, not the umbrella term | ⚠️ Partial, interview topic |
| "Snowflake" | Nice | None; listed under Known gaps | — | ❌ Gap, leave open |
| "German B2" | Must | German A2 | — | Hard filter: go/no-go question |

Status key: ✅ strong evidence · ⚠️ partial or adjacent · ❌ no evidence.

For every ❌, **ask** once, in one batched question: "I have nothing real for X, Y. Do you have
relevant experience, or do we leave them open?" Never fill a gap yourself.

**If the user answers with something new** (a project, tool or claim not in the fact base):
verify it before writing it anywhere. Load the live URL, check the repo exists and matches the
description. Use the user's own scope boundaries verbatim (what to claim, what never to claim).
Add it to the fact base immediately, in the same format as existing entries, so the next
application has it too. When the new fact goes into an existing bullet, keep the bullet the same
length: swap out weaker words, don't append.

## Step 4: Place for weight, not frequency

- **High-weight positions:** title line, first sentence of the summary, first bullet of the most
  recent role, project titles, the start of a bullet. One strong placement beats repetition.
- **Inside dated roles:** tie skills to dated entries (a bullet, or an optional "Skills used"
  line), not only the flat Skills list. Some parsers only attach recency to a skill inside a
  dated entry.
- **Spell out abbreviations once** where natural: "Customer Relationship Management (CRM)".
- **Order by relevance:** most relevant bullet first in each role; most relevant skills first in
  each group.
- **Use stored variants:** if the fact base has `## Bullet variants`, pick the variant whose
  emphasis matches the ad (e.g. a stakeholder-led or a metric-design-led version of the same
  fact) before writing a new one.

### Keyword bold

After the text is final, bold the one phrase per bullet that best matches the ad's
highest-weight terms (the "Must" rows first), only where the bullet honestly shows that term,
preferably in the ad's own wording. Use `docproof keywords <in.docx> <out.docx> <spec.json>` with a spec of
`{"<bullet prefix>": ["phrase"]}`.

- **Emphasis budget:** at most 2 bold items per bullet in total, and at most 1 of them a keyword.
  The renderer bolds figures automatically and counts keyword bold first, so keywords and numbers
  never pile up.
- **Distinctive terms only.** Bold "A/B tests" or "dbt", never "data" or "teams".
- No keyword bold in the summary, the Skills lines or low-relevance roles.
- Replace the base document's generic bold where this ad cares about something else. A spec
  replaces all bold in the paragraphs it lists, so start the spec fresh rather than stacking.
- Bold text is about 5% wider: re-check that two-line bullets still fit.

## Mirroring honestly

Mirroring removes the translation work so the reader sees their own vocabulary. It only works
because it's true. If a phrase has to stretch to fit, find a better real example or leave the
gap open.

| Candidate would say | Ad might say | Use |
|---|---|---|
| ran A/B tests | experimentation / controlled experiments | the ad's term |
| worked across teams | cross-functional collaboration / stakeholder management | the ad's term |
| weekly KPI report | stakeholder reporting / executive reporting | the ad's term |
| churn model | retention modelling / churn prediction | the ad's term, if accurate |
| automated the report | process automation / workflow automation | the ad's term |

Never mirror: a tool the candidate hasn't used, a seniority they don't hold, "advanced" or
"expert" on project-level skills, "owned" on shared work, or anything under `## Known gaps`.

## Gap handling

- **Core gap** (central to the role): don't disclose it on the CV. In a cover letter (if the
  user asked for one) or the interview, reframe forward: "ready to go deep on X, building on
  strong Y fundamentals."
- **Secondary gap:** a direct, honest mention is fine, or leave it out.
- **Hard-filter gap** (a required language level, required enrolment): a go/no-go question, not a
  wording question. Say so.

## Reader perspective

The reader wrote the job ad. Nothing in the document mentions tailoring, ATS, keywords, "job
postings", "applications" or the candidate's search. If the candidate has a project that is
itself about job hunting (a scraper, a CV pipeline), describe the engineering (agents, a single
fact base, automated verification), never "analysed job ads" or "tailored CVs".
`docproof check` warns on this framing.

## Final tailoring checklist

**Keywords and language**
- [ ] The ad's own terms used wherever they honestly apply
- [ ] No keyword forced in for something the candidate didn't do
- [ ] Every must-have visibly addressed somewhere
- [ ] Bullet bold = this ad's key terms, within the emphasis budget

**Evidence, not adjectives**
- [ ] Every skill claim backed by an example, tool or number from the fact base
- [ ] `vocabulary.md` pass: filler and AI tells removed
- [ ] Every bullet ends on a result, scale or adoption

**Relevance and priority**
- [ ] Most relevant experience at the top of each section
- [ ] Irrelevant experience cut or shortened
- [ ] Summary speaks to this role and company

**Consistency and credibility**
- [ ] `docproof verify` passes (every number and tool traced; no Known-gaps term)
- [ ] Verbs vary; no three identical openers
- [ ] Reads as a case for this job, not a list of everything
- [ ] Title line fitted to this job; ~1–1.5 pages; Interests dropped unless they add signal
- [ ] `docproof check` passes and the PNGs were looked at
