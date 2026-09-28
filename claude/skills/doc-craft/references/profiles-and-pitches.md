# Profiles and pitches: LinkedIn headline and About, bios, elevator pitches

Short positioning texts follow the same rule as the CV: every line is something the candidate can
defend in an interview, and every figure is in the fact base. Check them with
`docproof prose <file> --kind headline|about|bio|pitch --facts <fact base>`.

## The three-line positioning

Use it for a CV title line, a LinkedIn headline, or the opening of an About section.

1. **Core expertise:** two or three disciplines, pipe-separated. These are categories, not a skills dump:
   "Product Analyst | Experimentation | KPI Modelling".
2. **Method and stack:** four or five tools or methods from the fact base's skills section that
   support line 1 (SQL, dbt, Python, A/B testing and power analysis).
3. **Direction:** one optional sentence of 20 words or fewer on the kind of problem the candidate
   wants next. Only claim a trend (AI, sustainability …) when the fact base has evidence for it.

## LinkedIn headline (`--kind headline`, 220 characters)

- Role first, then the two or three terms a recruiter would search for, then one proof point:
  "Product Analyst | A/B Testing, dbt, SQL | 40+ experiments, 30+ shipped".
- Keep it consistent with the CV title. A reader who sees both should see the same person.

## LinkedIn About (`--kind about`, 2,600 characters)

- The first two lines show before "see more", so they must work alone: what the candidate does
  plus one result. Don't open with "I am a results-driven professional".
- Then two or three short paragraphs: the strongest evidence, how they work, and a side project
  if it adds something new.
- One line of tools (from the fact base), then what they are looking for.
- Write in the first person, but most sentences should not start with "I".

## Bio (`--kind bio`, 40–200 words)

Third person, for talks, team pages and newsletters: identity → what they've done (one figure) →
the thread that connects it → what they're doing now.

## Elevator pitch (`--kind pitch`, 90 words or fewer, about 30 seconds)

Pick the framing for the setting:
- **Networking:** "I help [who] with [outcome] by combining [skill 1] and [skill 2]. Most people in
  this space come from [typical background]; I come from [actual background], which means [advantage]."
- **Casual:** what they focus on now → how they got there (one unexpected turn) → the thread that
  connects it.
- **Online bio:** identity → range → thread → current chapter.

Fill the brackets only with facts. Spoken rhythm: short sentences, one number at most.

## Anti-fluff (all kinds)

- No "passionate", "motivated", "dynamic", "team player", "results-driven", "go-getter" (`prose` warns).
- Show someone who builds and ships: name the thing built and its result.
- No "not X, but Y" constructions.
- Every claim can be defended in an interview.

## Done means

- [ ] `docproof prose --kind … --facts …`: no FAIL; warnings fixed or kept for a stated reason
- [ ] Headline, About and CV title tell the same story
- [ ] Every figure traces to the fact base; no known gap claimed
