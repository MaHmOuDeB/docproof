"""docproof coverage — which of the ad's requirements does the document show, and which can it show?

  docproof coverage <job-ad.txt> --doc <doc.docx|.md|.txt> [--facts fact-base.md] [--json]

`match` asks whether the candidate fits the ad (ad ↔ fact base). `coverage` asks whether the
document shows it (ad ↔ document), and with --facts, what can honestly be added:

  shown      the document backs the requirement
  partly     some of its key terms are there
  closable   the document misses it, but the fact base has evidence — add it (in the ad's words
             where they are true)
  open       neither has it — leave it open; never write it in

It also lists the ad's terms that the fact base backs but the document never uses: many applicant
tracking systems match literally, so a synonym ("A/B tests" for "experimentation") can be missed.
Mirror the ad's exact term where it is true.

Scores: coverage now = (shown + ½·partly) / must-haves; reachable = the same with every closable
requirement shown. The gap between the two is the honest room for tailoring; above "reachable",
only invention helps — and that is never an option.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

from docproof.facts import FactBase, surface_tokens, tokens
from docproof.match import grade, requirements
from docproof.prose import read_paragraphs


def doc_base(path: str) -> SimpleNamespace:
    lines = read_paragraphs(path)
    return SimpleNamespace(lines=lines, tokens=set(tokens(" ".join(lines))), gaps=[])


def coverage(ad_path: str, doc_path: str, facts_path: str | None = None) -> dict:
    ad = Path(ad_path).read_text(encoding="utf-8")
    doc = doc_base(doc_path)
    fb = FactBase(facts_path) if facts_path else None
    rows = []
    for req, nice in requirements(ad):
        d = grade(req, doc)
        status = {"evidence": "shown", "partial": "partly", "gap": "missing"}[d["verdict"]]
        row = {"requirement": req, "nice_to_have": nice, "status": status, "in_doc": d["evidence"]}
        if fb:
            f = grade(req, fb)
            row["fact_base"] = f["evidence"] if f["verdict"] != "gap" else ""
            row["known_gap"] = f["known_gap"]
            if status != "shown":
                if f["verdict"] == "evidence" and not f["known_gap"]:
                    row["status"] = "closable"
                elif status == "missing":
                    row["status"] = "open"
            # the ad's words that the fact base backs but the document never uses
            row["mirror"] = sorted({w for w, st in surface_tokens(req) if st in fb.tokens and st not in doc.tokens})
        rows.append(row)
    must = [r for r in rows if not r["nice_to_have"]] or rows
    n = len(must) or 1
    now = sum(1 if r["status"] == "shown" else 0.5 if r["status"] == "partly" else 0 for r in must)
    reach = now + sum(1 for r in must if r["status"] == "closable")
    return {
        "coverage_now": round(100 * now / n),
        "reachable": round(100 * reach / n) if fb else None,
        "must_haves": len(must),
        "requirements": rows,
        "mirror_terms": sorted({t for r in rows for t in r.get("mirror", []) if len(t) > 2}),
    }


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if not a or "--doc" not in a:
        sys.exit(__doc__)
    facts = a[a.index("--facts") + 1] if "--facts" in a else None
    r = coverage(a[0], a[a.index("--doc") + 1], facts)
    if "--json" in a:
        print(json.dumps(r, indent=2, ensure_ascii=False))
        return
    mark = {"shown": "✓", "partly": "~", "closable": "+", "open": "✗", "missing": "✗"}
    for row in r["requirements"]:
        tag = " (nice to have)" if row["nice_to_have"] else ""
        print(f"{mark[row['status']]} {row['status']:<8} {row['requirement'][:76]}{tag}")
        if row["status"] == "closable":
            print(f"      ↳ fact base: {row['fact_base'][:96]}")
        if row.get("known_gap"):
            print(f"      ↳ known gap: {', '.join(row['known_gap'])} — leave it open")
    line = f"\ncoverage now {r['coverage_now']}% of {r['must_haves']} must-haves"
    if r["reachable"] is not None:
        line += f" → reachable {r['reachable']}% from the fact base (the rest are open gaps)"
    print(line)
    if r["mirror_terms"]:
        print("ad terms the fact base backs but the document never uses:", ", ".join(r["mirror_terms"][:20]))


if __name__ == "__main__":
    main()
