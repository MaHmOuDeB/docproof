#!/usr/bin/env python3
"""docproof add-entry — insert a whole new project/entry block (title ⇥ date, bullets, meta line).

`docproof edit` can't create tab-formatted title lines, so this clones existing paragraphs of the
same CV as formatting templates and fills in new text:

  docproof add-entry in.docx out.docx spec.json

spec.json (works on examples/resume.json built with `docproof build`):
  {"after": "Technologies: Python, scikit-learn",
   "like_title": "BSc Economics",
   "like_bullet": "Built an open-source churn",
   "like_meta": "Technologies: Python",
   "title": "Pricing Test Simulator — Personal Project", "date": "2025",
   "bullets": ["Simulated price tests on synthetic subscription data."],
   "meta": "Technologies: Python, NumPy."}
"after" = insert after the paragraph starting with this; "like_title" = an existing title ⇥ date
line WITHOUT links; "like_bullet" = an existing bullet; "like_meta" = an existing meta line (optional).

Every "like_*"/"after" prefix must match exactly one paragraph. Proves the only change to
document.xml is the inserted block, and that the new paragraphs read back as the spec's text.
"""
import html, json, re, sys
from pathlib import Path
from docproof.edit import read_xml, write_docx, rebuild, ensure  # noqa: E402

W_T = re.compile(r"<w:t(?:\s[^>]*)?>([^<]*)</w:t>")


def ptext(p):
    return html.unescape("".join(W_T.findall(p)))


def find(xml, prefix):
    hits = [m for m in re.finditer(r"<w:p[ >].*?</w:p>", xml, re.S) if ptext(m.group(0)).startswith(prefix)]
    if len(hits) != 1:
        sys.exit(f"ERROR: {len(hits)} paragraphs start with {prefix!r}; need exactly 1. Nothing written.")
    return hits[0]


def main():
    if len(sys.argv) != 4 or not (sys.argv[1].endswith(".docx") and sys.argv[2].endswith(".docx")
                                  and sys.argv[3].endswith(".json")):
        sys.exit(__doc__)
    src, dst, spec_path = sys.argv[1:4]
    if not (src.endswith(".docx") and dst.endswith(".docx")):
        sys.exit("usage: docproof add-entry in.docx out.docx spec.json")
    spec = json.loads(Path(spec_path).read_text())
    xml = read_xml(src)
    title_p = find(xml, spec["like_title"]).group(0)
    if "<w:hyperlink" in title_p or "<w:tab/>" not in title_p:
        sys.exit("ERROR: like_title must be a plain 'title ⇥ date' line without hyperlinks.")
    ts = list(W_T.finditer(title_p))
    esc = lambda s: html.escape(s, quote=False)
    new_title = (title_p[:ts[0].start(1)] + esc(spec["title"]) + title_p[ts[0].end(1):ts[-1].start(1)]
                 + esc(spec["date"]) + title_p[ts[-1].end(1):])
    block = [new_title] + [rebuild(find(xml, spec["like_bullet"]).group(0), b) for b in spec["bullets"]]
    if spec.get("meta"):
        block.append(rebuild(find(xml, spec["like_meta"]).group(0), spec["meta"]))
    ins = find(xml, spec["after"]).end()
    new_xml = xml[:ins] + "".join(block) + xml[ins:]
    ensure(new_xml[:ins] + new_xml[ins + len("".join(block)):] == xml, "more than the block changed")
    want = [spec["title"] + "\t" + spec["date"]] + spec["bullets"] + ([spec["meta"]] if spec.get("meta") else [])
    got = [ptext(p.replace("<w:tab/>", "<w:t>\t</w:t>")) for p in block]
    ensure(got == want, f"read-back mismatch:\n{got}\n{want}")
    write_docx(src, dst, new_xml)
    print(f"OK — inserted '{spec['title']}' ({len(spec['bullets'])} bullets) after {spec['after']!r}; nothing else changed")


def run():
    main()


if __name__ == "__main__":
    main()
