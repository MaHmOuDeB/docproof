"""docproof add-link — append a grey "  ·  <label>" hyperlink to a document line.

  docproof add-link in.docx out.docx "<paragraph text prefix>" "<label>" <url> [<rel-id>]
  e.g.  docproof add-link cv.docx out.docx "Churn Radar" "Live demo" https://example.com/demo

If the line already has a hyperlink, the new one clones its formatting and the "  ·  " separator
before it; otherwise a separator and a plain hyperlink run are appended. Refuses unless exactly one
paragraph starts with the prefix, and proves that only that paragraph (and the relationships part)
changed. Idempotent: if the rel-id already exists, nothing is written.
"""
import re
import sys
import zipfile
from xml.sax.saxutils import escape

W_T = re.compile(r"<w:t(?:\s[^>]*)?>([^<]*)</w:t>")
HL_TYPE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink"


def add_link(src, dst, prefix, label, url, rid=None):
    with zipfile.ZipFile(src) as z:
        items = [(it, z.read(it.filename)) for it in z.infolist()]
    files = {it.filename: d for it, d in items}
    xml, rels = files["word/document.xml"].decode(), files["word/_rels/document.xml.rels"].decode()
    if rid is None:
        used = set(re.findall(r'Id="([^"]+)"', rels))
        rid = next(f"rIdLink{i}" for i in range(1, 10_000) if f"rIdLink{i}" not in used)
    elif f'Id="{rid}"' in rels:
        print(f"{rid} already present — nothing to do")
        return
    paras = [m for m in re.finditer(r"<w:p[ >].*?</w:p>", xml, re.S)
             if "".join(W_T.findall(m.group(0))).startswith(escape(prefix))]
    if len(paras) != 1:
        sys.exit(f"ERROR: {len(paras)} paragraphs start with {prefix!r}; need exactly 1. Nothing written.")
    p = orig = paras[0].group(0)
    links = list(re.finditer(r"<w:hyperlink\b.*?</w:hyperlink>", p, re.S))
    sep_run = ('<w:r><w:rPr><w:color w:val="7A7A7F"/></w:rPr>'
               '<w:t xml:space="preserve">  ·  </w:t></w:r>')
    if links:
        last = links[-1]
        seps = [m for m in re.finditer(r"<w:r>(?:(?!</w:r>).)*?<w:t[^>]*>\s+·\s+</w:t></w:r>",
                                       p[:last.start()], re.S)]
        new_link = re.sub(r'r:id="[^"]+"', f'r:id="{rid}"', last.group(0), count=1)
        new_link = re.sub(r"(<w:t[^>]*>)[^<]*(</w:t>)", lambda m: m.group(1) + escape(label) + m.group(2),
                          new_link, count=1)
        insert_at, block = last.end(), (seps[-1].group(0) if seps else sep_run) + new_link
    else:
        new_link = (f'<w:hyperlink r:id="{rid}"><w:r><w:rPr><w:color w:val="505055"/><w:u w:val="single"/>'
                    f'</w:rPr><w:t xml:space="preserve">{escape(label)}</w:t></w:r></w:hyperlink>')
        block = sep_run + new_link
        tab = p.find("<w:tab/>")
        run_start = max(p.rfind("<w:r>", 0, tab), p.rfind("<w:r ", 0, tab)) if tab != -1 else -1
        if run_start == -1:                       # no date column: append at the end of the line
            insert_at = p.rfind("</w:p>")
        elif "<w:t" in p[run_start:tab]:          # text and tab share a run: split it at the tab
            rpr = re.match(r"<w:r[^>]*>(<w:rPr>.*?</w:rPr>)?", p[run_start:], re.S).group(1) or ""
            p_split = p[:tab] + "</w:r>" + "\x00" + "<w:r>" + rpr + p[tab:]
            insert_at = p_split.index("\x00")
            p = p_split.replace("\x00", "")
        else:                                     # the tab starts its own run: link goes before it
            insert_at = run_start
    new_p = p[:insert_at] + block + p[insert_at:]
    new_xml = xml[:paras[0].start()] + new_p + xml[paras[0].end():]
    assert new_xml.replace(new_p, orig, 1) == xml
    new_text, old_text = "".join(W_T.findall(new_p)), "".join(W_T.findall(orig))
    assert new_text.startswith(old_text.split("\t")[0][:20]) and escape(label) in new_text, "link text check failed"
    files["word/document.xml"] = new_xml.encode()
    files["word/_rels/document.xml.rels"] = rels.replace(
        "</Relationships>", f'<Relationship Id="{rid}" Type="{HL_TYPE}" '
        f'Target="{escape(url)}" TargetMode="External"/></Relationships>').encode()
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zo:
        for it, _ in items:
            zo.writestr(it, files[it.filename])
    print(f"OK — added '{label}' → {url} to the line starting {prefix!r}; nothing else changed")


def main(argv=None):
    a = sys.argv[1:] if argv is None else argv
    if len(a) not in (5, 6) or not (a[0].endswith(".docx") and a[1].endswith(".docx")):
        sys.exit(__doc__)
    add_link(*a)


if __name__ == "__main__":
    main()
