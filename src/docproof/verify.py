"""docproof verify — trace every claim in a document back to the fact base.

  docproof verify <doc.docx> --facts fact-base.md [--json]

Hard failures (exit 1):
  numbers     every figure in the document (40+, ~45 minutes, 0.84, 5 teams …) must appear in the
              fact base. Dates and years are ignored.
  known gaps  no term from the fact base's "## Known gaps" list may appear in the document.
Warnings:
  skills      every item in a "Label: a, b, c" skills row should be backed by the fact base (all
              of its keywords appear there). Descriptive items can be backed in other words, so
              this is a prompt to look, not a verdict.

This is the mechanical half of a claim audit. The judgment half — ownership inflation ("led" vs
"supported"), implied tools, scope words — belongs to a reviewer (see the claim-auditor agent).
"""
import json
import re
import sys

from docproof.facts import FactBase, docx_paragraphs, tokens

MONTHS = (r"Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec|Januar|Februar|März|Mai|Juni|Juli|"
          r"Okt|Dez|January|February|March|April|June|July|August|September|October|November|December")
DATE = re.compile(rf"\b(?:{MONTHS})\.?\s+\d{{4}}\b|\b\d{{1,2}}/\d{{4}}\b|\b(?:19|20)\d{{2}}\b(?!\+)")
NUMBER = re.compile(r"(?<![\w.])\d+(?:[.,]\d+)?\+?%?")
PHONE = re.compile(r"\+?\d[\d\s()/-]{7,}\d")


def gap_in(gap, text):
    """Known-gap term as a whole word; very short terms ("R") also refuse &, -, / neighbours (R&D, R-squared)."""
    if len(gap) <= 2:
        return re.search(rf"(?<![\w/&-]){re.escape(gap)}(?![\w/&'-])", text) is not None
    return re.search(rf"(?<![\w/]){re.escape(gap)}(?![\w/])", text, re.I) is not None


def split_items(s):
    """Split 'a, b (c, d), e.' on commas outside parentheses."""
    items, depth, cur = [], 0, ""
    for ch in s.rstrip("."):
        depth += ch == "("
        depth -= ch == ")"
        if ch == "," and depth == 0:
            items.append(cur.strip())
            cur = ""
        else:
            cur += ch
    return [i for i in items + [cur.strip()] if i]


def verify(docx, facts_path):
    fb = FactBase(facts_path)
    paras = docx_paragraphs(docx)
    report = {"numbers": [], "gaps": [], "skills": [], "checked_numbers": 0}
    for p in paras:
        text = PHONE.sub(" ", DATE.sub(" ", p))
        for m in NUMBER.finditer(text):
            num = m.group(0)
            report["checked_numbers"] += 1
            if not fb.has_number(num):
                ctx = text[max(0, m.start() - 35):m.end() + 25].strip()
                report["numbers"].append({"number": num, "context": ctx})
        for gap in fb.gaps:
            if gap_in(gap, p):
                report["gaps"].append({"term": gap, "context": p[:110]})
        m = re.match(r"^([A-Z][\w &/-]{1,40}):\s+(.+)$", p)
        if m and "," in m.group(2) and not p.startswith(("Technologies", "Technologien")):
            for item in split_items(m.group(2)):
                missing = [t for t in set(tokens(item)) if t not in fb.tokens]
                if missing:
                    report["skills"].append({"item": item, "unbacked_words": sorted(missing)})
    return report


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if not a or not a[0].endswith(".docx") or "--facts" not in a:
        sys.exit(__doc__)
    facts = a[a.index("--facts") + 1]
    r = verify(a[0], facts)
    if "--json" in a:
        print(json.dumps(r, indent=2, ensure_ascii=False))
    else:
        print(f"numbers   : {r['checked_numbers']} checked, {len(r['numbers'])} not in the fact base")
        for x in r["numbers"]:
            print(f"  FAIL {x['number']!r:>8}  …{x['context']}…")
        print(f"known gaps: {len(r['gaps'])} claimed")
        for x in r["gaps"]:
            print(f"  FAIL '{x['term']}' in: {x['context']}")
        print(f"skills    : {len(r['skills'])} item(s) with words the fact base doesn't mention")
        for x in r["skills"]:
            print(f"  WARN {x['item']!r} — {', '.join(x['unbacked_words'])}")
    failed = bool(r["numbers"] or r["gaps"])
    if "--json" not in a:
        print("VERIFY FAILED" if failed else "VERIFY PASSED: every figure traces to the fact base; no known gap claimed.")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
