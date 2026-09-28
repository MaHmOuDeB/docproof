"""docproof prose — check a cover letter, LinkedIn About, bio or pitch against the fact base.

  docproof prose <doc.md|.txt|.docx> --kind letter|email|about|headline|bio|pitch
                 [--facts fact-base.md] [--ad job-ad.txt] [--strict] [--json]

Prose is where invented numbers and stock phrases slip in most easily: there is no bullet structure
to keep a model honest. The same rules as for the CV apply, plus the ones that make a text read
like a person wrote it.

Hard failures (exit 1)
  numbers    (with --facts) every figure must appear in the fact base; dates, phone numbers and
             postcodes are ignored.
  gaps       (with --facts) no term from the fact base's "## Known gaps" may appear.
  length     over a platform's hard limit (LinkedIn headline 220 characters, About 2,600).
Warnings
  length     outside the usual range for the kind (a letter fits one page: 150–400 words; an
             email 4–8 sentences; a spoken pitch ≤ 90 words; a bio 40–200 words).
  phrases    stock phrases readers skip or distrust ("I am passionate", "perfect fit",
             "results-driven", "Dear Sir or Madam" …).
  contrast   "not X, but Y" / "it's not about X, it's about Y" — a pattern readers now associate
             with generated text; say the positive claim directly.
  evidence   (with --facts) no figure at all — show the fit with one concrete result.
  openers    most sentences start with "I" (letters, About sections).
  repeat     two paragraphs do the same job.
  echo       (with --ad) a sentence re-types one of the ad's duties.
  fit        (with --ad, letters) the text speaks to fewer than two of the ad's requirements.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

from docproof.facts import FactBase, docx_paragraphs, tokens
from docproof.verify import DATE, NUMBER, PHONE, gap_in

# kind → (min words, max words, hard max characters)
LIMITS = {
    "letter": (150, 400, None),
    "email": (40, 150, None),
    "about": (60, 450, 2600),
    "headline": (None, None, 220),
    "bio": (40, 200, None),
    "pitch": (20, 90, None),
}
PHRASES = [
    # English
    "i am excited", "i'm excited", "i am thrilled", "i'm thrilled", "passionate about", "i am passionate",
    "i would like to inform you", "with great interest", "always admired", "i firmly believe",
    "perfect candidate", "perfect match", "perfect fit", "ideal candidate", "exactly aligns", "aligns perfectly",
    "world-class", "cutting-edge", "results-driven", "detail-oriented", "team player", "self-starter",
    "go-getter", "highly motivated", "proven track record", "think outside the box", "hit the ground running",
    "fast-paced environment", "i am writing to apply", "i am writing to express", "to whom it may concern",
    "dear sir or madam", "dear hiring manager", "leverage my", "unique opportunity", "great fit",
    "testament to", "ever-evolving", "in today's", "delve", "tapestry", "synergy", "dynamic professional",
    # German
    "hiermit bewerbe ich mich", "mit großem interesse", "sehr geehrte damen und herren", "teamfähig",
    "belastbar", "hochmotiviert", "ich bin überzeugt", "perfekt geeignet",
]
CONTRAST = re.compile(
    r"\bnot (?:just |only |merely |simply )?[\w'’ /-]{1,40}?[,;:—–-]?\s+but (?:also )?\w"
    r"|\b(?:it|this|that)(?:'s| is)(?:n't| not) (?:just )?(?:about )?[^.;]{1,40}[,;—–]\s*(?:it|this|that)(?:'s| is)\b"
    r"|\bnicht nur\b[^.]{1,60}\bsondern\b",
    re.I,
)
POSTCODE = re.compile(r"\b\d{4,5}\s+[A-ZÄÖÜ][a-zäöüß]+")
# a known gap named in a negated sentence is an honest disclosure, not a claim
NEGATION = re.compile(r"\b(not|never|no(?!-)|haven't|hasn't|don't|didn't|yet to|nicht|kein\w*|noch nie)\b", re.I)
YOU = re.compile(r"\b(you|your|yours|Sie|Ihr\w*)\b")


def read_paragraphs(path: str) -> List[str]:
    """Paragraphs of a .docx, or of a .md/.txt file split on blank lines (Markdown marks removed)."""
    if path.endswith(".docx"):
        return docx_paragraphs(path)
    text = Path(path).read_text(encoding="utf-8")
    paras = []
    for block in re.split(r"\n\s*\n", text):
        block = re.sub(r"^\s*(#+|[-*•])\s*", "", block, flags=re.M)
        block = re.sub(r"\*\*|__|`", "", block)
        block = " ".join(block.split())
        if block:
            paras.append(block)
    return paras


def _sentences(text: str) -> List[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def analyse(path: str, kind: str, facts_path: Optional[str] = None, ad_path: Optional[str] = None) -> Dict:
    paras = read_paragraphs(path)
    text = "\n".join(paras)
    body = [p for p in paras if len(p.split()) >= 6]  # skip greeting, sign-off, address lines
    sentences = [s for p in body for s in _sentences(p)]
    words = len(text.split())
    out: Dict[str, list] = {"fail": [], "warn": [], "stats": [{"words": words, "characters": len(text)}]}

    def add(level, check, message, fix):
        out[level].append({"check": check, "message": message, "fix": fix})

    lo, hi, hard = LIMITS[kind]
    if hard and len(text) > hard:
        add("fail", "length", f"{len(text)} characters — the platform cuts at {hard}", "cut to the limit")
    if lo and words < lo:
        add("warn", "length", f"{words} words — short for a {kind} ({lo}–{hi})", "add one concrete example")
    if hi and words > hi:
        add("warn", "length", f"{words} words — long for a {kind} ({lo}–{hi})", "cut what repeats the CV")

    low = text.lower().replace("’", "'")
    for ph in PHRASES:
        if re.search(rf"(?<![\w-]){re.escape(ph)}(?![\w-])", low):
            add("warn", "phrases", f"stock phrase '{ph}'", "replace it with the concrete fact it stands for")
    for m in CONTRAST.finditer(text.replace("’", "'")):
        add("warn", "contrast", f"'{m.group(0)[:70]}…'", "state the positive claim directly")

    if facts_path:
        fb = FactBase(facts_path)
        found = 0
        for p in paras:
            clean = POSTCODE.sub(" ", PHONE.sub(" ", DATE.sub(" ", p)))
            for m in NUMBER.finditer(clean):
                found += 1
                if not fb.has_number(m.group(0)):
                    ctx = clean[max(0, m.start() - 35) : m.end() + 25].strip()
                    add("fail", "numbers", f"'{m.group(0)}' is not in the fact base: …{ctx}…",
                        "use the fact base's figure, or drop the number")
            for sent in _sentences(p):
                for gap in fb.gaps:
                    if gap_in(gap, sent) and not NEGATION.search(sent.replace("’", "'")):
                        add("fail", "gaps", f"claims the known gap '{gap}': {sent[:90]}",
                            "remove the claim, or say plainly that it is a gap")
        if kind != "headline" and not found:
            add("warn", "evidence", "no concrete figure anywhere", "show the fit with one result from the fact base")

    if kind in ("letter", "about") and len(sentences) >= 6:
        share = sum(bool(re.match(r"(I|I'm|I’m|I've|I’ve|Ich)\b", s)) for s in sentences) / len(sentences)
        if share > 0.5:
            add("warn", "openers", f"{share:.0%} of sentences start with 'I'",
                "open with the result or the reader's problem instead")

    bsets = [set(tokens(p)) for p in body]
    for i in range(len(bsets)):
        for j in range(i + 1, len(bsets)):
            small = min(len(bsets[i]), len(bsets[j]))
            if small >= 8 and len(bsets[i] & bsets[j]) / small >= 0.6:
                add("warn", "repeat", f"paragraphs {i + 1} and {j + 1} say much the same",
                    "give each paragraph one job; merge or cut")

    if ad_path:
        from docproof.match import requirements
        from docproof.story import echoes

        ad = Path(ad_path).read_text(encoding="utf-8")
        facts_text = Path(facts_path).read_text(encoding="utf-8") if facts_path else None
        # sentences about the employer ("you", the company's name) quote the ad on purpose; claims don't
        first = next((ln for ln in ad.splitlines() if ln.strip()), "")
        names = {w for w in re.findall(r"\b[A-Z][\w&-]{2,}", first)} - {"Senior", "Junior", "Lead"}
        claims = [c for s in sentences if not YOU.search(s) and not any(n in s for n in names)
                  for c in re.split(r"[:;]\s", s)]
        for s in echoes(claims, ad, facts_text):
            add("warn", "echo", f"'{s[:90]}' repeats the ad's own wording",
                "name the concrete thing that was done; mirror single key terms, not sentences")
        if kind in ("letter", "email"):
            tt = set(tokens(text))
            reqs = [r for r, nice in requirements(ad) if not nice]
            spoken = [r for r in reqs if len(set(tokens(r)) & tt) >= 2]
            if reqs and len(spoken) < 2:
                add("warn", "fit", f"speaks to {len(spoken)} of the ad's {len(reqs)} requirements",
                    "chain requirement → what was done → what it means for them, for the two that matter most")
    return out


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if not a or "--kind" not in a or a[a.index("--kind") + 1] not in LIMITS:
        sys.exit(__doc__)
    opt = lambda k: a[a.index(k) + 1] if k in a else None  # noqa: E731
    r = analyse(a[0], opt("--kind"), opt("--facts"), opt("--ad"))
    if "--json" in a:
        print(json.dumps(r, indent=2, ensure_ascii=False))
    else:
        st = r["stats"][0]
        print(f"{opt('--kind')}: {st['words']} words, {st['characters']} characters")
        for level in ("fail", "warn"):
            for f in r[level]:
                print(f"{level.upper():<4} {f['check']:<9} {f['message']}\n     fix: {f['fix']}")
        if not r["fail"] and not r["warn"]:
            print("PROSE PASSED" + ("" if opt("--facts") else " (add --facts to check figures and known gaps)"))
        else:
            print(f"\n{len(r['fail'])} fail, {len(r['warn'])} warning(s)")
    sys.exit(1 if r["fail"] or ("--strict" in a and r["warn"]) else 0)


if __name__ == "__main__":
    main()
