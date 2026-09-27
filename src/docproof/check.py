"""docproof check — one command for the whole "is this document ready to send?" verification.

  docproof check <doc.docx> [--pdf out.pdf] [--orig original.docx] [--png DIR]

Runs, in order, and stops at the first hard failure:
  1. inspect           real Word file? language/anchor
  2. header-diff       header byte-identical to the original (skipped without --orig)
  3. render            designed PDF (default: next to the .docx) + its own every-word text check
  4. page report       page count and the first line of every page (a page must not start mid-entry)
  5. widow report      a bullet whose last line is a single word (the renderer ties the last two
                       words, so this should never fire — if it does, investigate)
  6. reader check      phrases that show the document was tailored ("job ad", "ATS", "tailored my
                       CV" …) — the person reading it wrote the ad
     links             every URL in the PDF
  7. previews          PNG per page with --png DIR (then LOOK at them)

Hard failures exit 1; soft findings print as "WARN" so they can't be missed.
"""
import re, subprocess, sys
from pathlib import Path

from docproof.headings import ALL  # noqa: E402
from docproof.pdftools import pdf_pages, pdf_text, to_pngs  # noqa: E402

HEADINGS = tuple(h.title() for h in ALL) + tuple(ALL)
DP = [sys.executable, "-m", "docproof"]


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def main():
    a = sys.argv[1:]
    if not a or not a[0].endswith(".docx"):
        sys.exit(__doc__)
    docx = Path(a[0]).resolve()
    opt = lambda k: a[a.index(k) + 1] if k in a else None
    pdf = Path(opt("--pdf") or docx.with_suffix(".pdf")).resolve()
    fails = []

    code, out = run(DP + ["inspect", str(docx)])
    print("1 check   :", out.splitlines()[-1] if out else code)
    if code:
        sys.exit("FAILED: not a usable .docx — nothing else was checked")
    if opt("--orig"):
        code, out = run(DP + ["header-diff", opt("--orig"), str(docx)])
        print("2 header  :", " | ".join(out.splitlines()) if out else code)
        if code or "PASSED" not in out: fails.append("header")
    code, out = run(DP + ["render", str(docx), "--out", str(pdf)])
    print("3 render  :", out.splitlines()[-1] if out else code)
    if code: fails.append("render/text")
    if not pdf.exists():
        sys.exit("FAILED: no PDF")

    pages = pdf_pages(pdf)
    print(f"4 pages   : {pages}")
    for n in range(1, pages + 1):
        lines = [l for l in pdf_text(pdf, page=n, layout=True).splitlines() if l.strip()]
        if not lines:
            continue
        first = lines[0].strip()
        if n > 1:
            ok = first.startswith(HEADINGS) or not lines[0].startswith("  ")
            print(f"  page {n} starts: {first[:70]}" + ("" if ok else "   WARN: starts mid-entry"))
        # 5. short last lines: an indented continuation line with ≤ 2 words that ends a bullet
        for i, l in enumerate(lines[1:], 1):
            s = l.strip()
            prev = lines[i - 1]
            if (l.startswith("  ") and len(s.split()) <= 1 and len(prev.strip()) > 60
                    and not re.search(r"\d{4}$", s) and not s.startswith(("Technologies", "Technologien"))):
                print(f"  WARN short last line p{n}: '{s}'  (after: …{prev.strip()[-40:]})")
    # reader-perspective guard: the person reading this document wrote the job ad
    full = pdf_text(pdf)
    for pat in (r"job[- ]?(ads?|descriptions?|postings?)", r"scrap\w* (?:\d+ )?(?:job|posting)", r"tailor\w* (?:my |the )?CVs?",
                r"Stellenanzeigen", r"Bewerbungsprozess", r"\bATS\b"):
        for m in re.finditer(pat, full, re.I):
            print(f"  WARN reader-perspective: '{full[max(0, m.start()-40):m.end()+30].strip()}' — reads as gaming recruiters")
    d = pdf.read_bytes()
    urls = sorted(set(u.decode() for u in re.findall(rb"/URI \((.*?)\)", d)))
    print("6 links   :", ", ".join(urls) or "none")
    if opt("--png"):
        out_dir = Path(opt("--png")); out_dir.mkdir(parents=True, exist_ok=True)
        for old in out_dir.glob(pdf.stem + "-*.png"):
            old.unlink()
        if to_pngs(pdf, out_dir / pdf.stem):
            print("7 images  :", ", ".join(sorted(p.name for p in out_dir.glob(pdf.stem + "-*.png"))), "→ LOOK at them")
        else:
            print("7 images  : skipped — install poppler (pdftoppm) for PNG previews")
    if fails:
        sys.exit("FAILED: " + ", ".join(fails))
    print("ALL HARD CHECKS PASSED")


def run_cli():
    main()


if __name__ == "__main__":
    main()
