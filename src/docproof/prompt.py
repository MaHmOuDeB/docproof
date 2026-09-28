"""docproof prompt — build a ready-to-paste prompt for ChatGPT, Gemini, Claude or any other LLM.

  docproof prompt tailor --facts fact-base.md --ad job-ad.txt --doc base.docx [--out prompt.txt]
  docproof prompt audit  --facts fact-base.md --doc tailored.docx
  docproof prompt review --doc tailored.docx [--ad job-ad.txt] [--persona "hiring manager"]
  docproof prompt write  --facts fact-base.md --kind letter|email|about|headline|bio|pitch
                         [--ad job-ad.txt] [--notes company-notes.txt]

`write` asks for a cover letter, LinkedIn About/headline, bio or pitch; save the answer as a .md
file and check it with `docproof prose <file.md> --kind … --facts … [--ad …]`.

The prompt bundles the fact base, the job ad, the `match` report and the document text with the
house rules, and asks the model for a machine-readable answer. For `tailor`, save the model's JSON
reply and apply it safely with:

  docproof apply base.docx reply.json tailored.docx --facts fact-base.md --ad job-ad.txt

which runs the edits, bolds the keywords, checks the story (title ↔ summary, scope, echo, relevance)
and verifies every figure against the fact base.
The model proposes; the tools check.
"""
import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

from docproof.facts import docx_paragraphs

HERE = Path(__file__).resolve().parent


def doc_lines(docx):
    """Header paragraphs + body paragraphs, one per line, as the model should reference them."""
    import html
    import re
    import zipfile
    with zipfile.ZipFile(docx) as z:
        x = z.read("word/document.xml").decode("utf-8")
    head = x[:x.find("</w:tbl>")] if "</w:tbl>" in x else ""
    hl = [html.unescape("".join(re.findall(r"<w:t(?:\s[^>]*)?>([^<]*)</w:t>", p))).strip()
          for p in re.findall(r"<w:p[ >].*?</w:p>", head, re.S)]
    return "\n".join([l for l in hl if l] + docx_paragraphs(docx))


def _capture(fn, *args):
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            fn(*args)
    except SystemExit:
        pass
    return buf.getvalue().strip()


def build_prompt(kind, opt):
    tpl = (HERE / "prompts" / f"{kind}.md").read_text(encoding="utf-8")
    if kind == "tailor":
        from docproof.match import main as match_main
        return tpl.format(facts=Path(opt["--facts"]).read_text(encoding="utf-8"),
                          ad=Path(opt["--ad"]).read_text(encoding="utf-8"),
                          match=_capture(match_main, [opt["--ad"], "--facts", opt["--facts"]]),
                          doc=doc_lines(opt["--doc"]))
    if kind == "audit":
        from docproof.verify import main as verify_main
        return tpl.format(facts=Path(opt["--facts"]).read_text(encoding="utf-8"), doc=doc_lines(opt["--doc"]),
                          verify=_capture(verify_main, [opt["--doc"], "--facts", opt["--facts"]]))
    if kind == "review":
        ad = opt.get("--ad")
        return tpl.format(persona=opt.get("--persona", "senior tech recruiter"), doc=doc_lines(opt["--doc"]),
                          ad_clause=", for the job ad below" if ad else "",
                          ad_block=f"\n=== JOB AD ===\n{Path(ad).read_text(encoding='utf-8')}\n" if ad else "")
    if kind == "write":
        k = opt["--kind"]
        ad, notes = opt.get("--ad"), opt.get("--notes")
        return tpl.format(
            kind_label=WRITE_KINDS[k][0], length=WRITE_KINDS[k][1], kind_rules=WRITE_KINDS[k][2],
            facts=Path(opt["--facts"]).read_text(encoding="utf-8"),
            ad_clause=", for the job ad below" if ad else "",
            ad_block=f"\n=== JOB AD ===\n{Path(ad).read_text(encoding='utf-8')}\n" if ad else "",
            notes_block=(f"\n=== NOTES ON THE EMPLOYER (from their own site) ===\n"
                         f"{Path(notes).read_text(encoding='utf-8')}\n" if notes else ""))
    raise KeyError(kind)


# kind → (label, length, extra rules)
WRITE_KINDS = {
    "letter": ("cover letter", "150–400 words, one page",
               "7. Structure: why this role (tied to something specific the employer said) → the evidence chains →\n"
               "   how the candidate works → a short, friendly close. Address a named person if one is known.\n"),
    "email": ("short application email (the letter and CV are attached)", "4–8 sentences, under 150 words",
              "7. Don't repeat the letter; give the reader one reason to open the attachments.\n"),
    "about": ("LinkedIn About section", "under 2,600 characters; the first two lines must work on their own",
              "7. Open with what the candidate does and one result — no \"I am a …-driven professional\".\n"
              "   Close with what they are looking for.\n"),
    "headline": ("LinkedIn headline", "under 220 characters",
                 "7. Role first, then 2–3 search terms recruiters use, then one proof point. Pipes as separators.\n"),
    "bio": ("short professional bio in the third person", "40–200 words", ""),
    "pitch": ("spoken elevator pitch", "under 90 words (about 30 seconds)",
              "7. Who they are → one thing they built or proved → what they're looking for now. Spoken rhythm.\n"),
}

NEEDS = {"tailor": ("--facts", "--ad", "--doc"), "audit": ("--facts", "--doc"), "review": ("--doc",),
         "write": ("--facts", "--kind")}


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if not a or a[0] not in NEEDS:
        sys.exit(__doc__)
    kind, rest = a[0], a[1:]
    opt = {rest[i]: rest[i + 1] for i in range(0, len(rest) - 1) if rest[i].startswith("--")}
    missing = [k for k in NEEDS[kind] if k not in opt]
    if kind == "write" and opt.get("--kind", "letter") not in WRITE_KINDS:
        sys.exit(f"docproof prompt write: --kind must be one of {', '.join(WRITE_KINDS)}")
    if missing:
        sys.exit(f"docproof prompt {kind}: missing {', '.join(missing)}\n\n{__doc__}")
    text = build_prompt(kind, opt)
    if "--out" in opt:
        Path(opt["--out"]).write_text(text, encoding="utf-8")
        print(f"Wrote {opt['--out']} ({len(text):,} characters) — paste it into your assistant.")
    else:
        print(text)


def apply_main(argv=None):
    """docproof apply <in.docx> <reply.json> <out.docx> [--facts fact-base.md] [--ad job-ad.txt]"""
    a = list(sys.argv[1:] if argv is None else argv)
    if len(a) < 3 or not (a[0].endswith(".docx") and a[1].endswith(".json") and a[2].endswith(".docx")):
        sys.exit("usage: docproof apply <in.docx> <reply.json> <out.docx> [--facts fact-base.md] [--ad job-ad.txt]\n\n"
                 "Applies an LLM's tailoring reply (from `docproof prompt tailor`): edits, then keyword bold,\n"
                 "then — with --facts — verifies every figure against the fact base.")
    src, reply_path, out = a[:3]
    raw = Path(reply_path).read_text(encoding="utf-8").strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
    reply = json.loads(raw)
    import tempfile
    from docproof import edit, keywords
    with tempfile.TemporaryDirectory() as td:
        ops_p, kw_p, mid = Path(td, "ops.json"), Path(td, "kw.json"), Path(td, "mid.docx")
        ops_p.write_text(json.dumps(reply.get("ops", [])), encoding="utf-8")
        sys.argv = ["docproof edit", "apply", src, str(ops_p), str(mid)]
        edit.run()
        kw = reply.get("keywords") or {}
        done = False
        if kw:
            kw_p.write_text(json.dumps(kw), encoding="utf-8")
            sys.argv = ["docproof keywords", str(mid), out, str(kw_p)]
            try:
                keywords.main()
                done = True
            except SystemExit as e:        # a stale bullet prefix shouldn't block the verification
                print(f"WARN keywords skipped — {e.code}")
        if not done:
            Path(out).write_bytes(mid.read_bytes())
            print(f"Wrote {out}")
    for n in reply.get("notes", []):
        print("note:", n)
    failed = False
    if "--ad" in a:
        from docproof.story import main as story_main

        try:
            facts = ["--facts", a[a.index("--facts") + 1]] if "--facts" in a else []
            story_main([out, "--ad", a[a.index("--ad") + 1]] + facts)
        except SystemExit as e:
            failed = bool(e.code)
    if "--facts" in a:
        from docproof.verify import main as verify_main

        try:
            verify_main([out, "--facts", a[a.index("--facts") + 1]])
        except SystemExit as e:
            failed = failed or bool(e.code)
    print(f"Next: docproof check {out} --orig {src} --png <dir>   (then look at the pages)")
    if failed:
        sys.exit(1)
