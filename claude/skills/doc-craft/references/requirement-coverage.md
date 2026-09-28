# Requirement coverage: the ATS view, done honestly

`docproof match` asks whether the candidate fits the ad (ad ↔ fact base). `docproof coverage`
asks whether the document shows that fit (ad ↔ document), and what the fact base could add.
This file covers applicant-tracking systems (ATS), the coverage score and closing gaps without
inventing anything.

## How applicant tracking systems work

Two layers, and they matter differently:

1. **Parsing.** The system extracts the document into fields (name, titles, dates, skills,
   education) before it looks at any ad. Multi-column bodies, text boxes, tables and graphics in
   the body can lose real information here. That is why the body stays single-column (see
   `format-and-ats.md`).
2. **Matching.** The parsed fields are compared with the ad and the recruiter's search filters.
   Some systems match semantically; many match literally and would miss "A/B tests" when the ad
   says "experimentation". When in doubt, use the ad's exact term, but only where it is true.

**"75% of CVs are rejected by ATS" is a myth.** It traces back to an undocumented marketing claim.
Most applications get a human look. Automatic rejection is usually a hard knock-out question (work
authorisation, a required degree, years of experience), not a hidden keyword score. Silence after
applying is mostly a volume problem. Say so plainly when a user worries about it.

## Pick the document language first

- An ad written entirely in one language gets a document in that language.
- The ad is in the local language but says the working language is English, or it mixes both:
  **ask the user.** A document in the wrong language is worse than a five-second question.

## Score, then close, then re-score

```bash
docproof coverage ad.txt --doc applications/<co>/<First_Last>_CV.docx --facts profile/fact-base.md
```

Each requirement gets one status:
- **✓ shown / ~ partly:** the document backs it (fully or in part).
- **+ closable:** the document misses it, but the fact base has evidence. This is the honest room
  for tailoring.
- **✗ open:** neither has it. Leave it open; if it is a known gap, never write it in.

The summary line reads *coverage now X% → reachable Y%*. Report both, and after editing report
before → after. Reaching more than "reachable" would take invention, and that is never an option.
When the gap between the two is small and the score is low, the honest advice may be to skip the role.

The **mirror terms** line lists words from the ad that the fact base backs but the document never
uses. They are candidates for literal matching; use each one only where it describes what the
candidate really did.

## Closing a gap

Every edit is either a rewording of something real or a new fact the user just gave you (add it
to the fact base first, with its source). If there is no real backing, ask the user; if they have
none, the gap stays open.

Placement, by how matching systems and readers weight text:
- A term in the title line, a role title, or the start of a bullet counts more than one buried
  mid-paragraph. One strong placement beats repetition.
- Put skills inside dated experience bullets as well as in the skills section: some parsers only
  attach recency and duration to skills tied to a dated entry.
- Spell out an abbreviation once where it's natural ("customer relationship management (CRM)").
- Body strictly single-column: no tables, no text boxes, no graphics.
- The header stays byte-identical except the title line (and the location when the user asks);
  `docproof check --orig` enforces it.

A core requirement that is a real gap: frame the adjacent evidence forward in the letter, never
in a skills row. A secondary gap: leave it out or mention it plainly.

## Done means

- [ ] Right language for the ad (asked when ambiguous)
- [ ] `coverage` before → after reported, with the reachable ceiling stated
- [ ] Every closable requirement either closed or consciously left out (say why)
- [ ] Open gaps left open; `verify` passes (no known gap claimed)
- [ ] `story` and `check` pass, and the PNGs have been looked at
