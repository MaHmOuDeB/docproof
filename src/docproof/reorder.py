#!/usr/bin/env python3
"""docproof reorder — move whole document sections, or single paragraphs, without changing any content.

  docproof reorder in.docx out.docx sections "PROFESSIONAL EXPERIENCE,SKILLS,EDUCATION,..."
  docproof reorder in.docx out.docx move "<text prefix of paragraph to move>" "<text prefix of paragraph to put it before>"

sections: a section = its heading paragraph plus everything up to the next section heading. The list
          must name every body section exactly once (the header before the first heading never moves).
move:     moves one paragraph (e.g. reorder skill lines inside Skills). Both prefixes must be unique.
Safety:   refuses to run if it would add, drop or alter any paragraph. After writing, it checks that the
          output contains exactly the same paragraphs byte for byte (only their order changed) and that
          the header zone is byte-identical. Run `docproof inspect` afterwards.
"""
import re, sys, zipfile, collections
from html import unescape

from docproof.headings import ALL as HEADINGS  # noqa: E402
from docproof.edit import ensure, write_docx  # noqa: E402

def text(p): return "".join(unescape(t) for t in re.findall(r"<w:t(?:\s[^>]*)?>(.*?)</w:t>", p, re.S)).strip()

def body_paras(xml):
    body_open = xml.find("<w:body>") + len("<w:body>")
    sect = xml.rfind("<w:sectPr")
    paras = [(m.start(), m.end()) for m in re.finditer(r"<w:p\b.*?</w:p>", xml[:sect], re.S) if m.start() >= body_open]
    return paras, sect

def main(src, dst, mode, *a):
    if mode == "sections" and a:
        a = (a[0].upper(),) + a[1:]
    z = zipfile.ZipFile(src); xml = z.read("word/document.xml").decode()
    paras, sect = body_paras(xml)
    first = next(i for i, (s, e) in enumerate(paras) if text(xml[s:e]) in HEADINGS)
    head_end = paras[first][0]
    region_start, region_end = head_end, paras[-1][1]
    body = [xml[s:e] for s, e in paras[first:]]
    # anything between paragraphs inside the region (should be nothing) must be preserved -> refuse otherwise
    gaps = "".join(xml[paras[i][1]:paras[i + 1][0]] for i in range(first, len(paras) - 1))
    if gaps.strip():
        sys.exit("ERROR: non-paragraph content between body paragraphs (tables/bookmarks?) — refusing to reorder.")
    if any("<w:sectPr" in p for p in body):
        sys.exit("ERROR: a section break lives inside a body paragraph — refusing to reorder.")
    if mode == "sections":
        order = [h.strip() for h in a[0].split(",")]
        blocks, cur = collections.OrderedDict(), None
        for p in body:
            t = text(p)
            if t in HEADINGS: cur = t; blocks[cur] = []
            blocks[cur].append(p)
        if sorted(order) != sorted(blocks):
            sys.exit(f"ERROR: order must list every section exactly once. Document has: {list(blocks)}")
        new_body = [p for h in order for p in blocks[h]]
    elif mode == "move":
        what, before = a
        idx = lambda pre: [i for i, p in enumerate(body) if text(p).startswith(pre)]
        w, b = idx(what), idx(before)
        if len(w) != 1 or len(b) != 1: sys.exit(f"ERROR: prefixes must each match exactly one paragraph (got {len(w)}, {len(b)}).")
        p = body[w[0]]; rest = body[:w[0]] + body[w[0] + 1:]
        j = next(i for i, q in enumerate(rest) if text(q).startswith(before))
        new_body = rest[:j] + [p] + rest[j:]
    else:
        sys.exit(__doc__)
    ensure(collections.Counter(new_body) == collections.Counter(body), "paragraph multiset changed")
    new_xml = xml[:region_start] + "".join(new_body) + xml[region_end:]
    ensure(new_xml[:region_start] == xml[:region_start], "header changed")
    z.close()
    write_docx(src, dst, new_xml)
    order_now = [text(p) for p in new_body if text(p) in HEADINGS]
    print("OK — content identical, order now:", " → ".join(order_now))

def run():
    if len(sys.argv) < 5:
        sys.exit(__doc__)
    main(*sys.argv[1:])


if __name__ == "__main__":
    run()
