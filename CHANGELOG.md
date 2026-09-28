# Changelog

## 0.3.0 — 2026-09-28 · Cover letters, profiles and requirement coverage

The documents around the CV now follow the same rules: one fact base, checked by a tool.

**New**
- `docproof prose <file> --kind letter|email|about|headline|bio|pitch [--facts f] [--ad a]` checks
  cover letters, application emails, LinkedIn headlines and About sections, bios and elevator pitches
  (`.md`, `.txt` or `.docx`):
  - FAIL: a figure not in the fact base, a claimed known gap (a plainly stated gap, "I haven't used
    X", passes), a platform limit exceeded (LinkedIn headline 220, About 2,600 characters).
  - WARN: length for the kind, stock phrases ("passionate", "perfect fit", "Dear Sir or Madam" …),
    "not X, but Y", most sentences opening with "I", two paragraphs doing the same job, sentences
    re-typing the ad, a letter that speaks to fewer than two requirements.
- `docproof coverage <ad> --doc <doc> [--facts f]`: the ATS view of a document. Each requirement is
  shown, partly shown, closable from the fact base, or open; it reports *coverage now → reachable*
  and the ad's terms the fact base backs but the document never uses.
- `docproof prompt write --kind …`: paste-ready prompt to draft any of those kinds with ChatGPT,
  Gemini or another assistant.
- Claude Code: `/letter` command; `doc-craft` gains `cover-letters.md`, `profiles-and-pitches.md` and
  `requirement-coverage.md` (how applicant tracking systems really parse and match, the "75%
  auto-rejected" myth, closing gaps honestly). `document-tailor` reports coverage before → after
  and checks letters with `prose`; `claim-auditor` uses `prose` for text documents.
- Examples: a fictional cover letter and LinkedIn About in `examples/documents/`; the demo checks both.

**Changed**
- `story`'s echo check compares full wording: a line is exempt only when it is closer to the fact
  base's wording than to the ad's, so a duty copied from the ad is caught even when the facts behind
  it are true.

## 0.2.0 — 2026-09-28 · One story

A document can pass every fact check and still read wrong. This release adds a gate for that.

**New**
- `docproof story <doc.docx> [--ad ad.txt] [--facts fact-base.md] [--strict] [--json]` checks that the
  whole document tells one story:
  - **identity** (FAIL): the summary's role noun contradicts the title ("Business Analyst" title, "Data
    analyst" summary). A shorter form of the same role is fine.
  - **tagline**: a title phrase that nothing in the body proves.
  - **scope**: a figure repeated in the summary attached to something else than in the body.
  - **echo** (with `--ad`): a line that re-types one of the ad's duties. Lines in the fact base's own
    wording are exempt with `--facts`.
  - **relevance** (with `--ad`): a bullet that shares nothing with any requirement of the ad.
- `docproof apply … --ad ad.txt` now runs `story` as well as `verify`; `docproof demo` includes a story step.

**Agents and guides**
- New rule "One story, every line earns its place" in `jd-tailoring.md`, and an identity rule for the
  summary in `section-by-section.md`.
- `document-tailor`: a one-story pass plus `docproof story` before delivery, and a mandatory fresh-eyes
  review that is applied and re-scored (both scores reported). The fact base wins over any reviewer suggestion.
- `/tailor`, `fresh-eyes-reviewer`, `AGENTS.md` and the paste-ready prompts carry the same rules.

**Fixes**
- Word stems no longer turn "process" into "proces", so "process" and "processes" match.

## 0.1.0 — 2026-09-26

First release: fact base, build/render/check/verify/match, safe edits, prompts for any assistant, and
the Claude Code agents (document-tailor, claim-auditor, fresh-eyes-reviewer, `/tailor`).
