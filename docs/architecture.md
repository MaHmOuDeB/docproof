# Architecture

docproof has two layers: deterministic tools that can prove what they did, and agents that make
judgment calls on top of them. Nothing an agent writes reaches the reader without passing the
tools' gates.

```mermaid
flowchart LR
    FB[(fact-base.md<br/>single source of truth)]
    AD[job ad / target]
    subgraph Agents [Claude Code agents]
        T[document-tailor<br/>author]
        A[claim-auditor<br/>truth]
        R[fresh-eyes-reviewer<br/>stranger's view]
    end
    subgraph CLI [docproof CLI]
        M[match<br/>requirement → evidence]
        E[dump / edit / keywords /<br/>reorder / add-*]
        V[verify<br/>figures + known gaps]
        C[check + render<br/>PDF, pages, widows, links]
    end
    AD --> M
    FB --> M
    M --> T
    T --> E --> V --> C
    FB --> V
    C -->|PDF + PNGs| A
    C -->|PDF only| R
    FB --> A
    A --> O{orchestrator<br/>/tailor}
    R --> O
    O -->|true fixes| E
```

## Gates

| Gate | Tool | Fails when |
|---|---|---|
| Structure | `inspect` | the file isn't a real .docx, or no body heading is found |
| Header | `header-diff` | anything in the protected header changed except the title line |
| Every edit | `edit`, `keywords`, `reorder`, `add-*` | the change touches more than its target (each tool diffs before/after) |
| Truth | `verify` | a figure isn't in the fact base, or a known gap is claimed |
| Rendering | `render` | a word of the .docx is missing from the PDF text |
| Layout | `check` | a page starts mid-entry, a bullet ends on one word, "tailored" phrasing appears (WARN) |
| Eyes | the agent | nobody looked at the PNGs |

## Why the agents are separate

- The **author** is optimising for fit, which is exactly the pressure that produces overclaiming.
- The **auditor** sees the fact base and only asks "is this true as written?" It never edits.
- The **reviewer** is deliberately denied the fact base and any memory, so it reads the document
  the way a recruiter does. Two or three personas in parallel disagree usefully.

The orchestrator (you, or `/tailor`) triages the auditor's and reviewers' findings against the
fact base, applies only the true fixes through the CLI, and re-runs the gates.

## Document model

The tools read and write `word/document.xml` directly, never re-serialising through a library,
so everything not explicitly edited stays byte-identical. A document is:

- a **header table** (name, title line, contact line, optional photo) — protected except the title;
- **ALL-CAPS section headings** (English and German sets, see `src/docproof/headings.py`);
- entries: a bold **role** line followed by a `company ⇥ date` line, or a bold `title ⇥ date` line;
- real list-numbered **bullets**, `Label: items` **skill rows**, and `Technologies:` **meta** lines.

`docproof build` writes exactly this structure; documents made elsewhere work if they follow it.
