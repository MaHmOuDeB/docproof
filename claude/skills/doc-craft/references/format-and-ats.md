# Format, Layout and ATS Safety

Two levers decide shortlisting: **layout and format** (scannability, ATS pass-through, first
impression) and **content** (relevance, credibility, impact). Great content in a bad layout never
gets read. A great layout with weak content gets read, and rejected.

## The house design

`docproof render` typesets any CV .docx as a designed PDF: one column, real selectable text,
working links, Inter (embedded), Title Case section headings, no heading rules, printed by
headless Chrome. The .docx stays the source of truth; the PDF is what gets sent unless a portal
demands Word. `docproof build` produces a clean .docx from JSON in the same house template, which
is also the safe choice for large corporate portals that choke on photos or header tables.

Fonts and sizes come from the renderer. Change the renderer, never hand-tune a single CV.

## Layout: one column

**Use**
- One column, top to bottom
- One font family; hierarchy by weight and tracking, not many sizes
- Standard headings: Summary, Experience, Skills, Education, Languages, Projects
- Standard round bullets
- One date format everywhere: EN `Mar 2022 – Aug 2025`, DE `03/2022 – 08/2025`
- White space; clutter is an instant reject
- PDF unless the posting asks for Word

**Avoid**
- Two-column layouts, sidebars, tables, text boxes
- Graphics, charts, skill bars, star ratings, decorative icons, logos
- Important information in page headers/footers
- Date of birth, marital status, religion, nationality; a full street address on an English CV
- "References available upon request"
- Excess colour
- Lines under section headings (not an ATS risk, but many readers see them as a template look)

## Length

| Level | Length |
|---|---|
| Junior / graduate (< 5 years relevant) | 1–2 pages |
| Mid-level | 1–2 pages |
| Senior / lead | 2 pages; 3 only if unavoidable |

A useful split: keep a **comprehensive base CV** (~2 pages) and **tailor down** to ~1–1.5 pages
per application. Convincing content beats page count; don't cut evidence the ad cares about just
to reach one page. The real rule is density: every line earns its place or goes.

## Layout QA: page-break rules

Check these on the rendered PNGs, every time:

- **Short sections never split across pages** (Skills, Languages, Interests, an Education
  section with ≤2 entries). White space at the bottom of page 1 is the lesser evil.
- **An entry with ≤4 bullets never splits.** A long entry may split with ≥2 bullets on each side.
- No stranded meta line ("Technologies: …") at the top of a page.
- **No one-word widow** on the last line of a bullet.
- A page starts with a section heading or an entry heading, never mid-entry.
- **Tighten wording instead of shrinking type.** If a CV runs long, cut words first. Don't push
  body text below ~8.8pt or side margins below ~16mm.

`docproof check` reports page starts, widows and stranded lines, but the PNGs are the final check.

## Page count: trust the Chrome PDF

The page count that matters is the rendered PDF, because that's what gets sent. LibreOffice
over-reports overflow through font substitution; use it only as a "what does Word roughly look
like" fallback, never to decide a content cut.

## Do's, don'ts and basic craft (European hiring)

**Do**
1. Name and contact details at the top
2. A professional email address
3. A one-liner (< 15 words) answering "who are you?": the title line plus the summary's first clause
4. The same format for every role: title, company, location, dates, achievements
5. An awards/extracurricular section only if something is genuinely distinctive
6. Language skills with CEFR levels
7. A GitHub link only if it holds real, own (non-forked) projects
8. Machine-readable text: no images of text
9. Optional: up to 3 interests that add signal

**Don't**
1. Add what isn't customary in the target market (religion, military status)
2. List every language, framework and concept ever touched
3. Include irrelevant detail (old minor certificates weaken the CV)
4. Leave unexplained gaps or full-time overlaps
5. Write grandiose self-declarations ("excellent problem solver with proven ability to execute")

**Basic craft**
One font family, one or two sizes, aligned elements, no spelling/grammar/punctuation errors,
reverse chronological order, one spelling of the name everywhere.

## Common source conflicts, resolved

| Topic | Conflict | Resolution |
|---|---|---|
| Columns | Older templates are two-column tables; newer guidance says one column, no tables | **One column.** Some parsers scramble two-column layouts. |
| Photo | US/UK: no photo. German-speaking markets: photo still common | Follow the target market and the user's choice. Offer a no-photo variant; never remove one silently. |
| Header in a table | Many Word templates put name, photo and contacts in a table | The rendered PDF outputs the header as real text. For Word-only portals, offer a `docproof build` version. |
| Summary length | 2–4 sentences vs. a < 15-word one-liner | Both: short title line + 2–4 sentence summary. |
| Marital status, date of birth | Some older guides include them | **Omit.** |
| Work-authorisation line | Some templates include one | Only if the fact base states it, in the fact base's wording. Never infer it. |
| Keywords | "Use the exact language" vs. "don't keyword-stuff" | Compatible: exact phrase, once, where true, in a high-weight spot. |
| Hobbies | "Up to 3" vs. silent | Tailored CVs usually drop Interests unless they add signal for the role. |

## ATS-specific rules

- Body strictly single-column, no tables or graphics: a hard check, not an assumption.
- Skills tied to dated roles where possible.
- Spell out abbreviations once.
- Keywords at the start of bullets, in titles and in project names outweigh keywords buried
  mid-sentence or repeated.
- Plain-text sanity check: `pdftotext` the PDF. If the reading order is scrambled or a section
  is missing, a parser will have the same problem. (`docproof render` already checks that every
  word of the .docx appears in the PDF.)

## Final visual check

- Is the target position clear in the first two lines?
- Can a stranger find the most relevant skill in 3 seconds?
- Are dates, bullets and spacing identical in style throughout?
- Does it look clean on a laptop screen, not only printed?
- Have you opened the PNGs, page by page?
