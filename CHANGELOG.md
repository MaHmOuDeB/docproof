# Changelog

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
