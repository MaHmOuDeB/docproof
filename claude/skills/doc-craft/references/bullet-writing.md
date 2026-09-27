# Writing Bullets That Work

## The frameworks

| Framework | Use for |
|---|---|
| **CAR**: Context, Action, Result | The workhorse for CV bullets |
| **PAR**: Problem, Action, Result | Bullets where the candidate *fixed* something (an automation, a broken process) |
| **STAR**: Situation, Task, Action, Result | Mainly interviews; on a CV when CAR feels too compressed |

## The universal formula

> **[Strong action verb] + [what was done] + [how: tool, method, skill] + [scope or scale] + [result, ideally a number]**

Short version: **Verb + Task + Skill + Result.**

Not every bullet can carry all five. The minimum is **verb + specific task + one of (scope,
result, adoption)**. A bullet that ends on the task has no ending.

**One idea per bullet.** Two achievements in one bullet bury the second; split them. The same
goes for Education: a thesis line and a coursework line are separate bullets, never merged.

**Adding a new fact to an existing bullet:** keep the bullet the same length. Swap out weaker
words instead of appending, and add the fact to the fact base in the same session.

**Trim words, never drop numbers.** When a bullet runs one line too long, cut adjectives, "in
order to", doubled nouns and scope that another bullet already states. The figures are what the
eye catches; they are the last thing to go.

## Worked transformation

✗ *Responsible for the weekly KPI report.*
✓ *Automated the weekly KPI report with Python and scheduled dbt runs, cutting prep time from
~6 hours to ~45 minutes.*

What changed: passive phrase → active verb · vague task → named tools · trailing off → ends on a
number and a scope.

## Weak → strong

| Weak | Strong |
|---|---|
| Helped with A/B testing. | Ran 40+ A/B tests on onboarding and paywall flows; 30+ shipped to all users. |
| Worked on a churn project. | Built a logistic-regression churn model that improved targeting of save offers. |
| Made dashboards for other teams. | Built a SQL + dbt KPI layer used by 5 teams as their shared source of metrics. |
| Contributed to improving team processes. | Automated the weekly KPI report, cutting prep from ~6 hours to ~45 minutes. |

## Calibrated examples (fictional candidate)

These use only facts from `examples/profile/fact-base.md` (Jordan Rivera, Product Analyst,
Northwind Apps, 2022–2025). They show the standard; a real user's bullets come from their own
fact base.

**Experimentation**
- Ran 40+ A/B tests across onboarding, paywall and retention flows, taking each from hypothesis
  to a ship/no-ship recommendation; 30+ shipped.

**Data modelling**
- Built a SQL + dbt KPI layer that 5 teams use as their shared definition of core metrics.

**Automation (PAR)**
- Automated the weekly KPI report, cutting preparation from ~6 hours to ~45 minutes.

**Modelling**
- Built a churn-prediction model (logistic regression) that improved targeting of save offers.

Retired-wording pattern: when a phrasing gets corrected (it overstated scope, or claimed a team
result as a solo one), record the corrected version in the fact base and a one-line note of why
the old one was wrong, so it doesn't come back in a later tailoring run.

## Stored bullet variants

The base document carries one version of each bullet. The fact base's `## Bullet variants`
section holds verified alternates: **same facts, different emphasis**. Pick per ad instead of
rewriting from scratch. Jordan's fact base stores:

- **Stakeholder-led** (ads stressing communication): "Presented monthly experiment reviews to
  product leadership; 30+ of 40+ tests shipped."
- **Data-modelling-led** (analytics-engineering ads): "Modelled activation, retention and revenue
  in dbt, giving 5 teams one source of truth."

A variant is only stored after it has been checked against the facts. If a variant changes the
scope verb ("modelled" vs. "used"), the fact base must support that verb.

## Quantifying honestly

- Real number available → use it.
- No number → use **scope** (40+ tests, 5 teams), **adoption** ("used by 5 teams", "adopted
  team-wide") or **before/after state** ("replaced a manual weekly report").
- Approximate honestly: "roughly", "~", "an estimated". Never false precision.
- Confidential employer metrics (revenue, conversion) → never disclose, never invent. Use scope,
  adoption or the candidate's own efficiency metrics instead (`cv-rules-en.md`).
- If the user could get a real number by checking, **ask**. Don't guess.

## Team work

Frame shared work as shared: "Worked with X to…", "Contributed to…", "Supported…". Reserve
sole-ownership verbs (built, designed, led, owned) for things the candidate genuinely owned.
Readers treat over-owning as a credibility problem at the detailed-read stage, and interviewers
probe it. The `claim-auditor` agent checks exactly this.

## Phrase bank: templates by category

Borrow the *structure*, never paste the words. Every bracket gets something true.

1. **Leadership and people**: `[Led / Coordinated / Mentored] a team of [X] to [objective], using [method], resulting in [outcome].`
2. **Project and programme management**: `[Managed / Delivered / Coordinated] [scope] from [start] to [end], using [tool/method], achieving [result].`
3. **Sales, BD and growth**: `[Generated / Secured / Grew] [metric] by [method], resulting in [impact].`
4. **Customer service and client relations**: `[Resolved / Supported / Managed] [volume] using [tool], improving [metric].`
5. **Communication and collaboration**: `[Presented / Authored / Facilitated] [deliverable] for [audience], aligning [stakeholders] around [outcome].`
6. **Problem-solving and process improvement**: `[Identified / Diagnosed] [problem], [redesigned / automated] [process] using [tool], reducing [time/cost/errors] by [X].` (Jordan's report automation is this template.)
7. **Data, analysis and reporting**: `[Analyzed / Tracked / Modeled] [data/metric] using [tool], surfacing [insight] that informed [decision].`
8. **Technical, tools and systems**: `[Built / Configured / Implemented] [system] to [purpose], supporting [scope].`
9. **Initiative and innovation**: `[Proposed / Launched] [idea], beyond assigned duties, resulting in [adopted outcome].`
10. **Training and mentorship**: `[Trained / Coached] [X people] on [skill/tool], improving [metric].`

## The stranger test

Could a stranger picture exactly what the candidate did from this line alone? If they'd have to
take the candidate's word for it, the bullet needs another pass.
