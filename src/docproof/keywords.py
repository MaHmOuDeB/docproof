"""docproof keywords — bold the key phrase(s) in bullets so a skimming reader spots them.

  docproof keywords in.docx out.docx spec.json

spec.json: {"<text prefix of the paragraph>": ["phrase to bold", "another phrase"], ...}
A spec REPLACES all bold in the paragraphs it lists (existing bold is cleared first); an empty
list [] just clears the bold. Paragraphs not listed are left untouched.

House rule: one key phrase per bullet (two at most) — the WHAT (skill/output), not filler — and
none on low-relevance entries. When tailoring, bold the job ad's own key terms. The renderer counts these
phrases toward a 2-item emphasis budget per bullet (auto-bolded figures fill the rest).

Each prefix must match exactly one body paragraph, each phrase must occur exactly once in it, and
the paragraph must be a simple one (no tab, link or drawing). The tool proves the paragraph text is
unchanged and that nothing outside the edited paragraphs changed.
"""
import html, json, re, sys
from pathlib import Path
from docproof.edit import read_xml, write_docx  # noqa: E402

BOLD = '<w:b w:val="1"/><w:bCs w:val="1"/>'


def runs(p):
    """[(rPr, text)] for a simple paragraph."""
    out = []
    for r in re.findall(r"<w:r>.*?</w:r>|<w:r [^>]*>.*?</w:r>", p, re.S):
        rpr = re.search(r"<w:rPr>.*?</w:rPr>", r, re.S)
        txt = "".join(html.unescape(t) for t in re.findall(r"<w:t(?:\s[^>]*)?>([^<]*)</w:t>", r))
        out.append((rpr.group(0) if rpr else "<w:rPr></w:rPr>", txt))
    return out


def ptext(p):
    return "".join(html.unescape(t) for t in re.findall(r"<w:t(?:\s[^>]*)?>([^<]*)</w:t>", p))


def unbold(rpr):
    body = re.sub(r"<w:b(?:Cs)?\b[^>]*/>", "", rpr[len("<w:rPr>"):-len("</w:rPr>")])
    return "<w:rPr>" + body + "</w:rPr>"


def embolden(rpr):
    if re.search(r'<w:b(?: w:val="(?:1|true)")?/>', rpr):
        return rpr
    body = re.sub(r"<w:b(?:Cs)?\b[^>]*/>", "", rpr[len("<w:rPr>"):-len("</w:rPr>")])
    return "<w:rPr>" + BOLD + body + "</w:rPr>"


def main():
    src, dst, spec_path = sys.argv[1:4]
    if not (src.endswith(".docx") and dst.endswith(".docx")):
        sys.exit("usage: docproof keywords in.docx out.docx spec.json")
    spec = json.loads(Path(spec_path).read_text())
    xml = read_xml(src)
    body_start = xml.find("</w:tbl>")
    new_xml, done = xml, 0
    for prefix, phrases in spec.items():
        hits = [m for m in re.finditer(r"<w:p[ >].*?</w:p>", new_xml, re.S)
                if m.start() > body_start and ptext(m.group(0)).startswith(prefix)]
        if len(hits) != 1:
            sys.exit(f"ERROR: {len(hits)} paragraphs start with {prefix!r}; need 1. Nothing written.")
        p = hits[0].group(0)
        if any(t in p for t in ("<w:tab/>", "<w:hyperlink", "<w:drawing")):
            sys.exit(f"ERROR: {prefix!r} is not a simple paragraph. Nothing written.")
        rs = runs(p)
        chars = [(c, unbold(rpr)) for rpr, t in rs for c in t]      # spec replaces existing bold
        text = "".join(c for c, _ in chars)
        bold = [False] * len(chars)
        for ph in phrases:
            if text.count(ph) != 1:
                sys.exit(f"ERROR: {ph!r} occurs {text.count(ph)}× in {prefix!r}; need exactly 1. Nothing written.")
            i = text.index(ph)
            for k in range(i, i + len(ph)):
                bold[k] = True
        # regroup consecutive chars with the same (rPr, bold) into runs
        groups = []
        for (c, rpr), b in zip(chars, bold):
            key = embolden(rpr) if b else rpr
            if groups and groups[-1][0] == key:
                groups[-1][1] += c
            else:
                groups.append([key, c])
        ppr = re.search(r"<w:pPr>.*?</w:pPr>", p, re.S)
        open_tag = re.match(r"<w:p\b[^>]*>", p).group(0)
        new_runs = "".join(f'<w:r>{k}<w:t xml:space="preserve">{html.escape(t, quote=False)}</w:t></w:r>'
                           for k, t in groups)
        new_p = open_tag + (ppr.group(0) if ppr else "") + new_runs + "</w:p>"
        assert ptext(new_p) == text, f"text changed in {prefix!r}"
        new_xml = new_xml[:hits[0].start()] + new_p + new_xml[hits[0].end():]
        done += 1
    # everything outside the edited paragraphs is identical
    strip = lambda x: re.sub(r"<w:p[ >].*?</w:p>", lambda m: ptext(m.group(0)), x, flags=re.S)
    assert strip(new_xml) == strip(xml), "text outside the edited paragraphs changed"
    write_docx(src, dst, new_xml)
    print(f"OK — bolded key phrases in {done} paragraph(s); text unchanged")


def run():
    main()


if __name__ == "__main__":
    main()
