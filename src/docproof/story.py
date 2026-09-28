"""docproof story — does the whole document tell ONE story, and does every line earn its place?

  docproof story <doc.docx> [--ad job-ad.txt] [--facts fact-base.md] [--strict] [--json]

A tailored CV can pass every fact check and still read wrong: the title says one role and the summary
another, a number slides into a different context when it is repeated in the summary, a line parrots
the job ad, or a bullet proves nothing the ad asks for. Recruiters notice all four within seconds.

Checks
  identity   FAIL  the summary's role noun contradicts the title line ("Business Analyst" title,
                   "Data analyst" summary). A neutral "Analyst" is fine.
  tagline    WARN  a phrase in the title line that nothing in the body proves ("Lifecycle Campaigns"
                   when the body shows no lifecycle campaign).
  scope      WARN  a figure repeated in the summary is attached to something else than where it
                   appears in the body ("40+ A/B tests across 5 teams" when the 5 teams belong to
                   a different bullet).
  echo       WARN  (with --ad) a line that repeats one of the ad's duties in its own words and order
                   instead of naming the concrete thing done — reads as keyword stuffing. With
                   --facts, lines that follow the fact base's own wording are never flagged: matching
                   the ad because the candidate really did that is fine; copying the ad is not.
  relevance  WARN  (with --ad) a bullet that shares nothing with any requirement of the ad: cut it or
                   reframe it with the fact base's words.

Exit code 1 on FAIL (or on any WARN with --strict). The checks are heuristics — each finding names
the exact line so a person or an agent can judge it.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from docproof.facts import stem, tokens
from docproof.headings import SUMMARY_KEYS

ROLE_NOUNS = {
    "analyst", "manager", "engineer", "scientist", "consultant", "specialist", "designer", "developer",
    "marketer", "associate", "lead", "coordinator", "architect", "strategist", "researcher", "writer",
    "owner", "director", "officer", "administrator", "assistant", "executive", "planner", "advisor",
    "berater", "entwickler", "referent", "leiter",
}
NUM = re.compile(r"(?<![\w.])\d+(?:[.,]\d+)?\+?%?")
DATEISH = re.compile(r"^(19|20)\d{2}$")
CLAUSE_SPLIT = re.compile(r"[,;:()]|\.\s|\s[-–—]\s")


def _role(phrase: str) -> Tuple[Optional[str], Tuple[str, ...]]:
    """('analyst', ('business',)) from 'Business Analyst …'; (None, ()) when there is no role noun."""
    words = re.findall(r"[a-zäöüß]+", phrase.lower())
    for i, w in enumerate(words):
        if w in ROLE_NOUNS:
            qualifiers = tuple(x for x in words[max(0, i - 3) : i] if x not in ("and", "und", "the", "a", "an", "der", "die"))
            return w, qualifiers
    return None, ()


def _content(text: str) -> List[str]:
    return tokens(text)


def _in_order(needles: List[str], hay: List[str]) -> bool:
    """Tokens appear in this order, each within two positions of the previous one."""
    for start, tok in enumerate(hay):
        if tok != needles[0]:
            continue
        pos, ok = start, True
        for n in needles[1:]:
            window = hay[pos + 1 : pos + 3]
            if n in window:
                pos = pos + 1 + window.index(n)
            else:
                ok = False
                break
        if ok:
            return True
    return False


def _lcs(a: List[str], b: List[str]) -> int:
    """Length of the longest common subsequence (word order preserved)."""
    prev = [0] * (len(b) + 1)
    for x in a:
        cur = [0]
        for j, y in enumerate(b):
            cur.append(prev[j] + 1 if x == y else max(prev[j + 1], cur[j]))
        prev = cur
    return prev[-1]


GENERIC = {"build", "use", "work", "team", "data", "new", "make", "help", "manag", "support", "strong", "role"}
EVIDENCE_SECTIONS = {"PROFESSIONAL EXPERIENCE", "EXPERIENCE", "PROJECTS", "BERUFSERFAHRUNG", "PROJEKTE"}


def _words(text: str) -> List[str]:
    """Every word, stemmed, stop words included — for comparing wording rather than content."""
    return [stem(w) for w in re.findall(r"[a-zäöüß0-9]+", text.lower())] or [""]


def _sentences(text: str) -> List[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if s.strip()]


def echoes(lines: List[str], ad_text: str, facts_text: Optional[str] = None) -> List[str]:
    """Lines that repeat one of the ad's duties — the same words in the same order.

    Sharing key terms with the ad is expected (and good); re-typing its sentence is not. A line that
    follows the fact base's own wording is never an echo: the candidate really did that.
    """
    ad_seqs = [_content(s) for s in _sentences(ad_text) if len(_content(s)) >= 3]
    # the ad's individual duties/requirements (one sentence often lists several, split by ; or •)
    ad_units = [u for u in (_content(x) for x in re.split(r"[.;:\n•]|\s[-–]\s", ad_text)) if len(set(u)) >= 5]
    # fact-base items (a bullet may wrap over several lines)
    items = re.split(r"\n\s*(?:[-*•]|\d+\.)\s+|\n\s*\n|\n#+\s", "\n" + (facts_text or ""))
    fact_lines = [_content(x) for x in items if len(_content(x)) >= 4]
    fact_words = [_words(x) for x in items if len(_content(x)) >= 4]
    ad_words = [_words(x) for x in re.split(r"[.;:\n•]|\s[-–]\s", ad_text) if len(_content(x)) >= 3]
    hits = []
    for b in lines:
        full = _content(b)
        if not full:
            continue
        hit = any(_lcs(full, u) / len(u) >= 0.65 for u in ad_units)
        if not hit:
            for clause in CLAUSE_SPLIT.split(b):
                seq = _content(clause)
                if len(set(seq)) >= 5 and any(
                    len(set(seq) & set(a)) / len(set(seq)) >= 0.8 and _lcs(seq, a) / len(seq) >= 0.75
                    for a in ad_seqs
                ):
                    hit = True
                    break
        if hit and fact_lines and any(_lcs(full, f) / len(full) >= 0.7 for f in fact_lines):
            # the same facts as the fact base: an echo only if the wording is closer to the ad's
            w = _words(b)
            to_fact = max(_lcs(w, f) for f in fact_words) / len(w)
            to_ad = max((_lcs(w, x) for x in ad_words), default=0) / len(w)
            hit = to_ad > to_fact
        if hit:
            hits.append(b)
    return hits


def analyse(docx: str, ad_text: Optional[str] = None, facts_text: Optional[str] = None) -> Dict[str, list]:
    from docproof.render import parse

    header, sections, _, _ = parse(docx)
    title = header.get("title", "")
    summary = ""
    body_paras: List[str] = []
    bullets: List[str] = []
    for s in sections:
        for b in s["blocks"]:
            if b["type"] == "plain":
                if s["key"] in SUMMARY_KEYS and not summary:
                    summary = b["text"]
                else:
                    body_paras.append(b["text"])
            elif b["type"] == "label":
                body_paras.append(b["text"])
            elif b["type"] == "entry":
                for runs in b["bullets"]:
                    t = "".join(x for x, _, _ in runs)
                    if s["key"] in EVIDENCE_SECTIONS:
                        bullets.append(t)
                    body_paras.append(t)
                body_paras += [rest for _, rest in b["meta"]]
    out: Dict[str, list] = {"fail": [], "warn": []}

    # identity: title role vs summary role
    parts = [p.strip() for p in re.split(r"\s*[|·]\s*", title) if p.strip()]
    t_role, t_q = _role(parts[0]) if parts else (None, ())
    first = _sentences(summary)[0] if summary else ""
    opener = re.split(r"\bwith\b|\bmit\b|,|:|\.", first, maxsplit=1)[0]
    s_role, s_q = _role(opener)
    if t_role and s_role:
        # contradiction = a different role noun, or qualifiers with nothing in common ("Business" vs "Data");
        # a shorter or reordered form of the same role ("Marketing analyst" under "CRM & Marketing Analyst") is fine
        if s_role != t_role or (s_q and t_q and not (set(s_q) & set(t_q))):
            out["fail"].append({
                "check": "identity",
                "message": f"title says '{parts[0]}' but the summary opens with '{opener.strip()}'",
                "fix": f"open the summary with the title's role ('{' '.join(t_q + (t_role,)).title()}') "
                       "or the neutral role noun alone",
            })

    # tagline: every title phrase after the role must be proven somewhere in the body
    body_tokens = [_content(p) for p in body_paras]
    for seg in parts[1:]:
        for phrase in [x.strip() for x in re.split(r",|&|\band\b|\bund\b|/(?=\s)", seg) if x.strip()]:
            toks = _content(phrase)
            if not toks:
                continue
            backed = any(_in_order(toks, bt) for bt in body_tokens) if len(toks) > 1 else any(
                toks[0] in bt for bt in body_tokens)
            if not backed:
                out["warn"].append({
                    "check": "tagline",
                    "message": f"title phrase '{phrase}' is not shown anywhere in the body",
                    "fix": "prove it in a bullet, or replace it with what the body actually shows",
                })

    # scope: a summary figure must describe the same thing as where it appears in the body
    for sent in _sentences(summary):
        for m in NUM.finditer(sent):
            num = m.group(0)
            if DATEISH.match(num):
                continue
            clause = re.split(r"\s(?:and|und)\s", CLAUSE_SPLIT.split(sent[: m.start()])[-1])[-1]
            after = CLAUSE_SPLIT.split(sent[m.end() :])[0]
            # what the figure is about: the words around it in the same clause (numbers excluded)
            before = [
                t for t in _content(clause) + _content(after)[:4] if not re.fullmatch(r"[~]?[\d.,+%]+", t)
            ]
            homes = [p for p in body_paras if re.search(rf"(?<![\w.]){re.escape(num)}(?![\d])", p)]
            if not before or not homes:
                continue
            best = max(len(set(before) & set(_content(h))) / len(set(before)) for h in homes)
            if best < 0.34:
                home = min(homes, key=len)
                out["warn"].append({
                    "check": "scope",
                    "message": f"summary attaches '{num}' to '{clause.strip()}', but in the body it belongs to: "
                               f"'{home[:90]}…'",
                    "fix": "keep the figure with the fact it describes in the fact base",
                })

    if ad_text:
        for b in echoes(bullets + _sentences(summary), ad_text, facts_text):
            out["warn"].append({
                "check": "echo",
                "message": f"'{b[:90]}' repeats the ad's own wording",
                "fix": "name the concrete thing that was done; mirror single key terms, not sentences",
            })
        # relevance: a bullet that shares nothing with any requirement
        from docproof.match import requirements

        ad_sents = [set(_content(s)) for s in _sentences(ad_text) if len(_content(s)) >= 3]
        reqs = [set(_content(r)) for r, _ in requirements(ad_text)] + ad_sents
        emphasised = {t for t, n in Counter(_content(ad_text)).items() if n >= 2} - GENERIC
        for b in bullets:
            bt = set(_content(b))
            # relevant = shares two terms with one requirement, or uses a term the ad repeats (e.g. "SQL")
            if bt and max((len(bt & r) for r in reqs), default=0) < 2 and not (bt & emphasised):
                out["warn"].append({
                    "check": "relevance",
                    "message": f"'{b[:80]}…' proves nothing the ad asks for",
                    "fix": "cut it, or pick the fact-base variant that speaks to a requirement",
                })
    return out


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if not a or not a[0].endswith(".docx"):
        sys.exit(__doc__)
    ad = Path(a[a.index("--ad") + 1]).read_text(encoding="utf-8") if "--ad" in a else None
    facts = Path(a[a.index("--facts") + 1]).read_text(encoding="utf-8") if "--facts" in a else None
    r = analyse(a[0], ad, facts)
    if "--json" in a:
        print(json.dumps(r, indent=2, ensure_ascii=False))
    else:
        for level in ("fail", "warn"):
            for f in r[level]:
                print(f"{level.upper():<4} {f['check']:<9} {f['message']}\n     fix: {f['fix']}")
        n_f, n_w = len(r["fail"]), len(r["warn"])
        if not n_f and not n_w:
            print("STORY PASSED: one consistent story" + (", every bullet serves the ad." if ad else "."))
        else:
            print(f"\n{n_f} fail, {n_w} warning(s)" + ("" if ad else " — add --ad job-ad.txt for echo and relevance"))
    failed = bool(r["fail"]) or ("--strict" in a and bool(r["warn"]))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
