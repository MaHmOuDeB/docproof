# Section by Section: from the title line to languages

Examples use the fictional candidate in `examples/profile/fact-base.md`: Jordan Rivera, Product
Analyst, three years at Northwind Apps (a subscription mobile app, 2022–2025), BSc Economics
(2021), MSc Business Analytics (2022), English native, Spanish C1, German A2.

## Section order

**English CV default:** Header & title line → Summary → Experience → Skills → Education →
Languages → Projects → (Interests).

- Lift **Projects** above Education when a project is core evidence for the role.
- Graduates with little experience may put Education or Projects before Experience; experienced
  candidates keep Experience first, because it's the strongest evidence.
- Skills sub-order: the group the ad weights most comes first (usually Tools & Languages).

**German Lebenslauf:** Kurzprofil → Berufserfahrung → Ausbildung → Sprachen → Kenntnisse →
Projekte → (Interessen). Wording rules in `cv-rules-de.md`.

Reorder with `docproof reorder <in> <out> sections "A,B,…"`, never by hand.

---

## 1. Header

**Contains:** full name · target title line · city, country · phone · email · LinkedIn ·
GitHub/portfolio only if it holds real, own work · photo only where the target market expects
one and the user wants it.

**Leave out:** full street address on an English CV, date of birth, marital status,
nationality, religion, "CV" or "Résumé" as a heading.

**Work authorisation:** only if the fact base states it, in the fact base's exact wording. Never
infer or round up a status.

**Protect the header.** In a tailoring run, the title line is the only header paragraph that
changes (`docproof edit` with `"zone": "title"`). Any other header change needs the user's OK.
`docproof check --orig <base.docx>` confirms the rest of the header is byte-identical.

**ATS note:** contact details inside a table or in the page header/footer can fail to parse. The
rendered PDF outputs them as real text; for Word-only portals, offer a `docproof build` version.

---

## 2. The title line

The highest-weight text on the page after the name. It answers "who are you?" before anything
else is read.

**Rules**
- Mirror the ad's job title (or its closest honest equivalent) as the first element.
- 2–3 elements separated by `|`, under ~12 words.
- Title, then specialisation, then a differentiator.
- Never claim a seniority the candidate doesn't hold (no "Senior", no "Lead").
- Don't stack every plausible title; pick the story for *this* role. A third identity usually
  dilutes the first two.

**Tailored examples (all honest for Jordan):**
| Role type | Title line |
|---|---|
| Product analyst | `Product Analyst \| Experimentation & A/B Testing \| SQL, dbt` |
| Data analyst (generalist) | `Data Analyst \| KPI Design & Reporting Automation \| SQL, dbt` |
| Growth analyst | `Growth Analyst \| A/B Testing \| Churn & Retention Analytics` |
| Analytics engineer (junior) | `Analytics Engineer \| SQL & dbt Modelling \| KPI Layer Design` |

---

## 3. Professional summary

**Length:** 2–4 sentences, ~3–4 lines. Never a paragraph wall.

**It answers four questions:**
1. Who is the candidate right now? (title/identity + level)
2. What are they strong in, shown in real work? (2–3 strengths)
3. What have they done, with scale? (one flagship, quantified)
4. What are they looking for? (targeted direction)

**Formula:**
> `[Title / identity] with [X years] in [domain], known for [signature strength]. [Quantified flagship achievement]. Now seeking [targeted direction].`

**Rules**
- Written for *this* role. A reused generic summary is the most visible sign of an untailored CV.
- Put the ad's 2–3 most weighted terms here, where true.
- At least one number; it's what the eye catches.
- No: hardworking, motivated, passionate, team player, results-oriented, dynamic, detail-oriented.
- No first person, no "seeking a challenging opportunity".
- Don't restate the header.
- Summaries are written without the pronoun ("Product analyst with…", "Built…"). Keep it
  consistent.

**Calibration.**

Weak: *"Passionate, data-driven product analyst who owns the full analytics lifecycle, from
raw data to boardroom decisions, driving growth across the business."* Metaphor-led, "owns"
overstates, no number, a dash-and-comma chain, "passionate".

Stronger:
> Product analyst with three years in subscription mobile apps, running 40+ A/B tests of which
> 30+ shipped. Built the SQL + dbt KPI layer used by 5 teams and automated weekly reporting from
> ~6 hours to ~45 minutes. MSc Business Analytics. Seeking a product analytics role focused on
> experimentation.

**German Lebenslauf:** a 3–4 line **Kurzprofil** plays this role (`cv-rules-de.md`). Insert it
with `docproof add-summary` if the base document lacks one.

---

## 4. Skills

**Rules**
- Group by type, e.g. **Tools & Languages** · **Analytics & Methods** · **Automation**.
  Spoken languages get their own section.
- Hard skills only; soft skills are shown in bullets, not listed.
- Only what the candidate can demonstrate in an interview or a test. The fact base's depth notes
  set the ceiling (never "advanced"/"expert" on project-level skills).
- Mirror the ad's exact tool names. If the ad says "Excel", Excel is visible.
- Order within a group by relevance to the ad, not alphabetically.
- Don't list the assumed (Word, email, internet research) or everything ever touched.
- 3–4 lines total.

**Do not:** `communication, teamwork, Microsoft Office, fast learner, adaptable`
**Do:** `Analytics & Methods: A/B testing, churn modelling (logistic regression), KPI design · Tools: SQL, dbt`

**No downgrading qualifiers in the Skills line.** "SQL (project-level)" or "Excel (pivot tables
only)" reads as self-downgrading in the spot recruiters scan fastest. List the tool plainly; that
stays honest as long as nothing claims "advanced" or "expert" and the bullets show what was
actually done. Honest depth belongs in the fact base and the interview. Neutral specifics are
fine: libraries, a method in brackets.

---

## 5. Professional experience

**Per-role structure:** Job title · Company (industry if unclear) · City · dates. One format for
every role. Reverse chronological. No unexplained overlaps.

**Bullets**
- 3–5 for the most recent or relevant role; 2–3 for older ones.
- 1–2 lines each. Achievement, not task (`bullet-writing.md`).
- Most relevant bullet first within each role.
- Vary opening verbs; never three in a row the same.
- Past tense for past roles.
- Every bullet ends on a result, a scale or an adoption.
- One idea per bullet.

**"Skills used" line (optional):** a closing line per role such as
`Skills used: A/B testing, SQL, dbt`. Add it only when tailoring, and only when it carries the
ad's keywords the bullets don't. Some parsers attach recency to a skill only inside a dated entry.
Skip it if space is tight.

**What counts as experience:** anything relevant: internships, working-student roles,
volunteering, part-time jobs. Irrelevant roles shrink to 1–2 bullets or a single line; they're
kept mainly to avoid unexplained gaps.

---

## 6. Projects

Especially valuable for juniors, graduates and career-changers. Include 1–3, **only** the ones
relevant to the role.

**Format:** `Project name · context (e.g. Personal project) · links ⇥ dates`, then 1–2 bullets
and a `Technologies:` line. Add new entries with `docproof add-entry` and links with
`docproof add-link`.

**Choosing:** keep a small selection table in the fact base ("role leans toward X → lead with
project Y"), so each tailoring run picks consistently.

**Reader perspective:** if a project is about the candidate's own job search (a CV pipeline, a
job-ad scraper), the reader of the CV wrote one of those ads. Describe the engineering (agents,
a single fact base, automated verification), never "analysed job postings" or "tailored CVs".

---

## 7. Education

**Contains:** degree · university · city · graduation month/year · 3–5 relevant courses
(juniors) · thesis (optional) · grade only if strong.

- Most recent degree first. If a university was renamed, write "New Name (formerly Old Name)"
  so background checks match.
- Keep coursework matched to the ad; swap courses per role.
- **Thesis and coursework are separate bullets**, never merged; merged, the thesis result gets
  buried. Split with `docproof edit` (`insert_after`).
- **A thesis or other one-line education entry carries up to 3 KPIs within 2 lines**, e.g.
  `Thesis: <title>; <result 1>, <result 2>, <result 3>`. Pick the KPIs the ad would care about;
  the exact wording lives in the fact base.

---

## 8. Certifications and awards

Only recent (≤5 years), recognised and relevant. No short online-course clutter. If there's
nothing to list, don't invent a section to fill space.

---

## 9. Languages

- Always CEFR (A1–C2) or Native. Never "good German", "very fluent", "basic English".
- One line, strongest first unless the ad weights a specific language:
  `English (Native) | Spanish (C1) | German (A2)`
- Never inflate a level. "Currently working toward B1" only if true at the time of writing.
- A strong second language is a real differentiator for multi-market or localisation roles:
  move it up and back it with a bullet if the fact base has the evidence.

---

## 10. Interests (optional)

- Up to 3, only if they add signal for *this* role. Tailored CVs usually drop the section.
- Drop anything that takes space without selling a relevant skill, even for companies in that
  hobby's industry.
- Skip ratings and rankings that invite skepticism.
- Never: "References available on request", marital status, driving licence (unless required).
