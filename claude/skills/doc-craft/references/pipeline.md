# File pipeline: the one way to build, edit, render and verify a document

Every skill, agent and command that touches a document file follows this page. Facts come from
the fact base; *what* to write comes from `section-by-section.md`, `bullet-writing.md` and
`jd-tailoring.md`. This page is only about files and gates.

## Where things live

| What | Default | Configure |
|---|---|---|
| Fact base | `profile/fact-base.md` in the working folder | a path in the request or in the user's `CLAUDE.md` |
| Base document (source of truth) | `profile/base.docx`, or `profile/resume.json` built with `docproof build` | same |
| Backups of the base | `profile/_backups/`, latest one per base only | — |
| Tailored output | `applications/<company>/<First_Last>_CV.docx` + `.pdf` (German: `<First_Last>_Lebenslauf.*`) | same |
| Page images to look at | a scratch folder, e.g. `applications/<company>/png/` | — |
| Job ad text | `applications/<company>/job-ad.txt` | — |

**File-name rules:** files sent to employers carry the candidate's name, never the company name
(`Jordan_Rivera_CV.pdf`, not `CV_for_Acme.pdf`); the company goes in the folder name. Plain ASCII
in file and folder names. Never overwrite the base without a fresh backup. Delete old files by
moving them to the system trash, not with `rm`.

## The pipeline (tailored CV)

```bash
A=applications/acme; F=profile/fact-base.md

# 0. Evidence first
docproof match $A/job-ad.txt --facts $F

# 1. Start from the base (each step writes a new file, so every stage can be inspected;
#    in = out is also safe — writes are atomic)
cp profile/base.docx $A/work-0.docx
docproof dump $A/work-0.docx --runs                     # ALWAYS dump before writing ops

# 2. Text edits (one batched ops file), then structure as needed
docproof edit $A/work-0.docx $A/ops.json $A/work-1.docx
docproof reorder $A/work-1.docx $A/work-2.docx sections "SUMMARY,PROFESSIONAL EXPERIENCE,PROJECTS,SKILLS,EDUCATION,LANGUAGES"
docproof reorder in.docx out.docx move "<paragraph prefix>" "<before paragraph prefix>"
docproof add-entry in.docx out.docx entry.json          # title⇥date line + bullets + meta line
docproof add-link in.docx out.docx "<line prefix>" "Live demo" https://example.com
docproof add-summary in.docx out.docx KURZPROFIL "<text>" BERUFSERFAHRUNG   # German CVs

# 3. Emphasis, after the text is final
docproof keywords $A/work-2.docx $A/Jordan_Rivera_CV.docx $A/kw.json  # {"<bullet prefix>": ["phrase"]}

# 4. Gates
docproof verify $A/Jordan_Rivera_CV.docx --facts $F
docproof check  $A/Jordan_Rivera_CV.docx --orig profile/base.docx --png $A/png   # also writes the PDF next to the .docx
```

Then **open and look at every PNG.** Not optional. The scripts catch what they were written to
catch; your eyes catch the rest (a cramped page, a stranded line, a heading alone at a page end).

**Clean build** (a broken base file, or a large corporate portal that chokes on photos and
header tables): write `resume.json`, run `docproof build resume.json out.docx`, then run the
same gates, with `check` but without `--orig`.

**Demo:** `docproof demo --out /tmp/docproof-demo` builds the fictional example CV, renders,
checks, verifies and matches it end to end. Run it once after install to confirm Chrome and the
fonts work.

## The gates

| Gate | Passes when | On failure |
|---|---|---|
| `docproof verify` | every number in the document appears in the fact base and no `## Known gaps` term appears (hard fail); skills-row items not backed by the fact base are WARNs. Tools named inside bullets are not machine-checked — that is the claim-auditor's job | remove or reword the claim; never add the claim to the fact base to make it pass unless the user confirms it's true |
| `docproof check` | real .docx; header identical to `--orig` (title line excepted); every word in the PDF; page starts at a heading; no one-word widows; every link listed (open them yourself); no job-search framing | fix every FAIL; fix each WARN or state in the delivery why it's acceptable |
| PNGs looked at | you opened each page image and found nothing wrong | fix, re-run both gates |

Nothing is delivered until all three pass.

## The CLI at a glance

| Command | Does | Never |
|---|---|---|
| `dump [--runs]` | lists paragraphs with index, zone, flags, text (`--runs`: run indices and formatting for `set_segments`) | — |
| `edit` | `set_text` / `replace` / `delete` / `set_segments` / `insert_after` on body paragraphs; the title line via `"zone": "title"`. Every `match` must hit exactly one paragraph or the whole run aborts | create tab lines, links or entries (use the commands below) |
| `reorder` | moves whole sections or single paragraphs; content byte-identical | — |
| `add-entry` | inserts a title⇥date line + bullets + meta line, cloned from existing lines | — |
| `add-link` | appends a "· Label" hyperlink next to an existing line | — |
| `add-summary` | inserts a heading + paragraph before a given heading; proves nothing else changed | a second summary |
| `keywords` | bolds the given phrase(s) per bullet; replaces existing bold in listed paragraphs; proves the text is unchanged | bold in the summary, Skills lines or low-relevance roles |
| `build` | JSON → .docx in the house template | default use when a good base .docx exists |
| `render` | designed PDF (Inter, headless Chrome) + optional PNGs; read-only on the .docx | edit the .docx |
| `check` | the layout and integrity gate above | — |
| `verify` | the claim-tracing gate above | — |
| `match` | requirement → evidence map, coverage %, gap list | decide go/no-go for you; it's input to your judgment |
| `lint` | flags stale phrases in skill/agent files against a rules file | — |

Example `ops.json` (works on the fictional example built from `examples/resume.json`):

```json
[
  {"op": "set_text", "zone": "title", "match": "Product Analyst",
   "text": "Experimentation Analyst  |  A/B Testing & Retention Analytics  |  SQL, dbt"},
  {"op": "replace", "match": "Designed and analysed 40+", "old": "Designed", "new": "Planned"},
  {"op": "delete", "match": "Cleaned and reconciled 2 years"},
  {"op": "insert_after", "anchor": "Automated the weekly KPI report with", "like": "Automated the weekly KPI report with",
   "text": "Presented monthly experiment reviews to product leadership."}
]
```

A `match` must hit exactly one paragraph: "Automated the weekly KPI report" alone would also match
the summary, so the ops above use a longer prefix.

(Scope verbs like "Designed" only where the fact base uses them.)

## Hard-won rules (each one cost a redo)

- **Dump before every ops file.** Old ops files match text that no longer exists.
- **Rewrite an ops list in full; don't layer patches.** Post-checks fail when a later op deletes
  text an earlier op wrote, or when a merged `set_text` still contains a later `delete` match.
  Start again from the pristine base with one complete ops file.
- **Batch text edits into one ops file**; every `match` must be unique. Prefer `replace` or
  `set_segments` on formatted lines; don't flatten formatting with a blanket `set_text`.
- **Argument order is `in.docx out.docx …`**, and the commands refuse non-.docx paths. Swapped
  arguments once wrote a stray file into the tool's own folder.
- **Time-box.** If the same step fails twice, stop and report the exact command and error. No
  manual `document.xml` surgery loops. Every structural need has a command above; if one is
  genuinely missing, write a small script that proves only the intended part changed.
- **Never write to a .docx that Word has open.** Check with `lsof | grep "<file>"` (a `~$` lock
  file alone can be stale). If it's open, ask the user to close it.
- **Layout QA:** short sections never split across pages; entries with ≤4 bullets never split;
  long entries keep ≥2 bullets on each side; no stranded meta line; no one-word widows. **Tighten
  wording instead of shrinking type.** Trim words, never drop numbers.
- **Emphasis budget:** at most 2 bold items per bullet or summary, at most 1 of them a keyword,
  distinctive terms only. Keyword bold counts first; the renderer fills the rest with figures.
  Bold is ~5% wider, so re-check two-line bullets.
- **OOXML regex trap:** `<w:bCs?` means "C required" and never matches a plain `<w:b/>`. Write
  `<w:b(?:Cs)?\b` (same for `<w:i`). After any bold or italic change, list the bold runs
  (`docproof dump --runs`) to confirm.
- **Measure, don't assume** formatting from XML: a run with no size set inherits one. Check the
  rendered output before calling something a bug.
- **Page count: trust the Chrome PDF.** LibreOffice substitutes fonts and over-reports overflow;
  never cut content on its evidence.
- **Chrome headless on macOS** can write the PDF and then hang. `docproof render` polls for the
  finished file and kills the process; don't "fix" it with `--virtual-time-budget`. If a render
  still hangs, kill Chrome and run once more; if it hangs twice, stop and report (time-box).
- **Design changes go in the renderer**, never into one CV. Don't add `text-wrap: pretty` or
  chained `break-after: avoid` rules; both have caused ragged lines and a half-empty page 1.
- **Before handing anything over:** `verify` and `check` pass, PNGs looked at, files named per
  the table above. Claude never submits an application or sends an email; the user does.
