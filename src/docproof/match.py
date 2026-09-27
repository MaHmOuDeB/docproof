"""docproof match — map a job ad's requirements to evidence in the fact base.

  docproof match <job-ad.txt> --facts fact-base.md [--json]

For every requirement line in the ad (bullets, or sentences under "requirements / what you'll do /
your profile …" headings) it finds the best-matching fact-base line and grades it:
  evidence   most of the requirement's key terms are backed by one fact line
  partial    some are
  gap        almost none are — or the requirement names a term from "## Known gaps"
Coverage = (evidence + ½·partial) / requirements, read against the 70% rule:
  ≥ 70 %  genuine match · 50–70 %  honest middle ground, say so · < 50 %  a stretch.

It is a deterministic first pass (keyword overlap with light stemming and synonyms), made to be
checked by a person or an agent — the "why" column shows exactly which terms matched.
"""
import json
import re
import sys
from pathlib import Path

from docproof.facts import FactBase, surface_tokens, tokens

HEAD = re.compile(r"(requirement|qualification|what you('|’)ll do|what you bring|responsibilit|your tasks|"
                  r"your profile|you have|you bring|about you|must|nice to have|aufgaben|profil|anforderung)", re.I)


NICE = re.compile(r"nice to have|bonus|a plus|plus:|preferred|von vorteil|wünschenswert", re.I)


def requirements(text):
    """[(requirement, is_nice_to_have)]"""
    reqs, in_list_section, nice_section = [], False, False
    for raw in text.splitlines():
        ln = raw.strip()
        if not ln:
            continue
        if HEAD.search(ln) and len(ln) < 60 and not ln.startswith(("-", "*", "•")):
            in_list_section, nice_section = True, bool(NICE.search(ln))
            continue
        bullet = re.match(r"^[-*•·▪]\s*(.+)", ln)
        item = bullet.group(1).strip() if bullet else (ln if in_list_section and len(ln.split()) >= 4 else None)
        if item and len(tokens(item)) >= 2:
            reqs.append((item, nice_section or bool(NICE.search(item))))
    return reqs


def grade(req, fb):
    req_tokens = set(tokens(req))
    from docproof.verify import gap_in
    gap_hits = [g for g in fb.gaps if gap_in(g, req)]
    best, best_line, best_hit = 0.0, "", set()
    for line in fb.lines:
        hit = req_tokens & set(tokens(line))
        score = len(hit) / max(1, len(req_tokens))
        if score > best:
            best, best_line, best_hit = score, line, hit
    # terms backed anywhere in the fact base (not only on the best line)
    anywhere = req_tokens & fb.tokens
    cover = max(best, 0.8 * len(anywhere) / max(1, len(req_tokens)))
    verdict = "evidence" if cover >= 0.5 else "partial" if cover >= 0.25 else "gap"
    if gap_hits:
        verdict = "gap" if cover < 0.75 else "partial"
    return {"requirement": req, "verdict": verdict, "score": round(cover, 2),
            "evidence": best_line[:140], "matched": sorted(best_hit or anywhere),
            "missing": sorted({w for w, st in surface_tokens(req) if st not in fb.tokens}),
            "known_gap": gap_hits}


def match(ad_path, facts_path):
    fb = FactBase(facts_path)
    rows = []
    for req, nice in requirements(Path(ad_path).read_text(encoding="utf-8")):
        rows.append({**grade(req, fb), "nice_to_have": nice})
    must = [r for r in rows if not r["nice_to_have"]] or rows
    n = len(must) or 1
    ev = sum(r["verdict"] == "evidence" for r in must)
    pa = sum(r["verdict"] == "partial" for r in must)
    coverage = round(100 * (ev + 0.5 * pa) / n)
    band = ("genuine match" if coverage >= 70 else "honest middle ground — say so" if coverage >= 50
            else "a stretch — lean towards skipping")
    keywords = sorted({t for r in rows for t in r["missing"] if len(t) > 2})
    warnings = [] if fb.gaps else ["the fact base has no '## Known gaps' section — gaps can't be flagged"]
    if not rows:
        warnings.append("no requirements found — is the first argument the job ad and --facts the fact base?")
    return {"coverage": coverage, "band": band, "must_haves": len(must), "requirements": rows,
            "missing_terms": keywords, "warnings": warnings}


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if not a or "--facts" not in a:
        sys.exit(__doc__)
    r = match(a[0], a[a.index("--facts") + 1])
    if "--json" in a:
        print(json.dumps(r, indent=2, ensure_ascii=False))
        return
    mark = {"evidence": "✓", "partial": "~", "gap": "✗"}
    for row in r["requirements"]:
        tag = " (nice to have)" if row["nice_to_have"] else ""
        print(f"{mark[row['verdict']]} {row['verdict']:<8} {row['score']:.2f}  {row['requirement'][:74]}{tag}")
        if row["verdict"] != "gap" and row["evidence"]:
            print(f"      ↳ {row['evidence'][:100]}")
        if row["known_gap"]:
            print(f"      ↳ known gap: {', '.join(row['known_gap'])}")
    print(f"\ncoverage: {r['coverage']}% of {r['must_haves']} must-have requirements — {r['band']}")
    for w in r["warnings"]:
        print("WARN", w)
    if r["missing_terms"]:
        print("terms the fact base never mentions:", ", ".join(r["missing_terms"][:25]))


if __name__ == "__main__":
    main()
