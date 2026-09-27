"""docproof add-summary — insert a summary section (heading + one paragraph) before a body heading.

  docproof add-summary in.docx out.docx HEADING "summary text" BEFORE_HEADING

Example (German Kurzprofil before the experience section):
  docproof add-summary lebenslauf.docx out.docx KURZPROFIL "Product Analyst mit …" BERUFSERFAHRUNG

The new heading is a clone of BEFORE_HEADING (same formatting, keep-with-next); the paragraph gets
plain summary formatting (justified, no bullet). The renderer shows SUMMARY/PROFILE/KURZPROFIL as
the summary block. The tool proves that the only change is the two inserted paragraphs.
"""
import html, re, sys
from pathlib import Path
from docproof.edit import read_xml, write_docx  # noqa: E402

SUMMARY_PPR = ('<w:pPr><w:spacing w:after="40" w:line="276" w:lineRule="auto"/><w:jc w:val="both"/>'
               '<w:rPr><w:sz w:val="16"/><w:szCs w:val="16"/></w:rPr></w:pPr>')


def ptext(p):
    return html.unescape("".join(re.findall(r"<w:t(?:\s[^>]*)?>([^<]*)</w:t>", p)))


def main():
    if len(sys.argv) != 6 or not (sys.argv[1].endswith(".docx") and sys.argv[2].endswith(".docx")):
        sys.exit(__doc__)
    src, dst, heading, text, before = sys.argv[1:6]
    xml = read_xml(src)
    paras = list(re.finditer(r"<w:p[ >].*?</w:p>", xml, re.S))
    if any(ptext(m.group(0)).strip() == heading for m in paras):
        sys.exit(f"ERROR: a {heading} heading already exists. Nothing written.")
    hits = [m for m in paras if ptext(m.group(0)).strip() == before]
    if len(hits) != 1:
        sys.exit(f"ERROR: {len(hits)} paragraphs are exactly {before!r}; need 1. Nothing written.")
    h = hits[0].group(0)
    ids = set(re.findall(r'w14:paraId="([0-9A-F]+)"', xml))
    new_id = lambda n: next(f"{0x5A000000 + i:08X}" for i in range(n, 10**6) if f"{0x5A000000 + i:08X}" not in ids)
    new_h = re.sub(r'w14:paraId="[0-9A-F]+"', f'w14:paraId="{new_id(0)}"', h, count=1)
    new_h = new_h.replace(f">{html.escape(before, quote=False)}<", f">{html.escape(heading, quote=False)}<", 1)
    open_tag = re.sub(r'w14:paraId="[0-9A-F]+"', f'w14:paraId="{new_id(1)}"', re.match(r"<w:p\b[^>]*>", h).group(0))
    new_p = (open_tag + SUMMARY_PPR + '<w:r><w:rPr><w:rtl w:val="0"/></w:rPr><w:t xml:space="preserve">'
             + html.escape(text, quote=False) + "</w:t></w:r></w:p>")
    assert ptext(new_h).strip() == heading and ptext(new_p) == text
    out = xml[:hits[0].start()] + new_h + new_p + xml[hits[0].start():]
    assert out.replace(new_h + new_p, "", 1) == xml, "something besides the insert changed"
    write_docx(src, dst, out)
    print(f"OK — inserted {heading} + summary ({len(text)} chars) before {before}; nothing else changed")


def run():
    main()


if __name__ == "__main__":
    main()
