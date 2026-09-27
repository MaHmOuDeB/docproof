"""docproof build — turn a résumé JSON file into a .docx in the house template.

  docproof build resume.json out.docx
  docproof build --example > resume.json      (print the fictional example to start from)

No dependencies: the Word XML is written directly, in exactly the structure the other tools expect
(a header table with name / title / contact line and optional photo, ALL-CAPS section headings,
real list-numbered bullets, "Label: items" skill rows, title ⇥ date lines). Edit the result with
`docproof edit`, render it with `docproof render`.

resume.json (see examples/resume.json):
  language      "en" | "de"                      (switches the default headings)
  name, title   strings; title uses "  |  " between parts
  photo         optional path to a PNG/JPEG (relative to the JSON file)
  contact       ["City, Country", "you@example.com", "+00 …", "linkedin.com/in/you", "github.com/you"]
  summary       paragraph (German: shown under KURZPROFIL)
  experience    [{title, company, location, dates, bullets: [...]}]
  skills        [{label, items}]
  education     [{degree, school, dates, details: [...]}]
  languages     [["English", "Native"], ["Spanish", "C1"]]
  projects      [{name, context, dates, links: [{label, url}], bullets: [...], tech}]
  certifications, interests   optional
  sections      optional order, e.g. ["summary", "experience", "skills", "education", "languages",
                "projects", "certifications", "interests"]
"""
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

HEADINGS = {
    "en": {"summary": "SUMMARY", "experience": "PROFESSIONAL EXPERIENCE", "skills": "SKILLS",
           "education": "EDUCATION", "languages": "LANGUAGES", "projects": "PROJECTS",
           "certifications": "CERTIFICATIONS", "interests": "INTERESTS", "tech": "Technologies:"},
    "de": {"summary": "KURZPROFIL", "experience": "BERUFSERFAHRUNG", "skills": "KENNTNISSE",
           "education": "AUSBILDUNG", "languages": "SPRACHEN", "projects": "PROJEKTE",
           "certifications": "ZERTIFIKATE", "interests": "INTERESSEN", "tech": "Technologien:"},
}
ORDER = ["summary", "experience", "skills", "education", "languages", "projects", "certifications", "interests"]

PAGE_W, MARGIN = 11906, 1077          # A4 width and 19 mm margins, in twips
TEXT_W = PAGE_W - 2 * MARGIN
GREY, DARK, ACCENT = "595959", "1D1D1F", "1F3864"

NS = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
      'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
      'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
      'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"')
HL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink"


class Doc:
    def __init__(self):
        self.rels = []            # (id, type, target, external)
        self.media = {}           # name -> bytes

    def rel(self, type_, target, external=False):
        rid = f"rId{len(self.rels) + 10}"
        self.rels.append((rid, type_, target, external))
        return rid

    def link(self, text, url, color=GREY):
        rid = self.rel(HL, url, external=True)
        return f'<w:hyperlink r:id="{rid}">{run(text, color=color)}</w:hyperlink>'


def run(text, bold=False, size=None, color=None, italic=False):
    rpr = ""
    if bold:
        rpr += '<w:b w:val="1"/><w:bCs w:val="1"/>'
    if italic:
        rpr += '<w:i w:val="1"/>'
    if color:
        rpr += f'<w:color w:val="{color}"/>'
    if size:
        rpr += f'<w:sz w:val="{int(size * 2)}"/><w:szCs w:val="{int(size * 2)}"/>'
    parts = text.split("\t")
    body = '<w:tab/>'.join(f'<w:t xml:space="preserve">{escape(p)}</w:t>' if p else "" for p in parts)
    return f"<w:r><w:rPr>{rpr}</w:rPr>{body}</w:r>"


def para(content, after=40, before=0, keep_next=False, bullet=False, tab=False, border=False, jc=None):
    ppr = ""
    if keep_next:
        ppr += "<w:keepNext/>"
    if bullet:
        ppr += '<w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr>'
    if border:
        ppr += f'<w:pBdr><w:bottom w:val="single" w:sz="6" w:space="2" w:color="{ACCENT}"/></w:pBdr>'
    if tab:
        ppr += f'<w:tabs><w:tab w:val="right" w:pos="{TEXT_W}"/></w:tabs>'
    ppr += f'<w:spacing w:before="{before}" w:after="{after}"/>'
    if bullet:
        ppr += '<w:ind w:left="360" w:hanging="200"/>'
    if jc:
        ppr += f'<w:jc w:val="{jc}"/>'
    return f"<w:p><w:pPr>{ppr}</w:pPr>{content}</w:p>"


def heading(text):
    return para(run(text, bold=True, size=11, color=ACCENT), before=240, after=100, keep_next=True, border=True)


def is_url(item):
    return bool(re.match(r"^(https?://)?[\w.-]+\.[a-z]{2,}(/\S*)?$", item, re.I)) and "@" not in item


def contact_line(doc, items):
    out = []
    for i, it in enumerate(items):
        if i:
            out.append(run("      ", color=GREY))
        if "@" in it:
            out.append(doc.link(it, "mailto:" + it))
        elif re.match(r"^\+?[\d\s()/-]{7,}$", it):
            out.append(doc.link(it, "tel:" + re.sub(r"[^\d+]", "", it)))
        elif is_url(it):
            out.append(doc.link(it, it if it.startswith("http") else "https://" + it))
        else:
            out.append(run(it, color=GREY))
    return para("".join(out), after=0, before=60)


def photo_drawing(doc, path, emu=720000):
    data = Path(path).read_bytes()
    ext = "png" if data[:4] == b"\x89PNG" else "jpeg"
    name = f"photo.{ext}"
    doc.media[name] = data
    rid = doc.rel("http://schemas.openxmlformats.org/officeDocument/2006/relationships/image", f"media/{name}")
    return (f'<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0">'
            f'<wp:extent cx="{emu}" cy="{emu}"/><wp:docPr id="1" name="Photo"/>'
            f'<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            f'<pic:pic><pic:nvPicPr><pic:cNvPr id="0" name="{name}"/><pic:cNvPicPr/></pic:nvPicPr>'
            f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
            f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{emu}" cy="{emu}"/></a:xfrm>'
            f'<a:prstGeom prst="ellipse"><a:avLst/></a:prstGeom></pic:spPr></pic:pic>'
            f'</a:graphicData></a:graphic></wp:inline></w:drawing></w:r>')


def header_table(doc, spec, base):
    name = spec["name"].upper() if spec.get("name_caps", True) else spec["name"]
    text = (para(run(name, bold=True, size=20, color=DARK), after=40)
            + (para(run(spec["title"], bold=True, size=11, color=DARK), after=0) if spec.get("title") else "")
            + contact_line(doc, spec.get("contact", [])))
    cells, widths = [], []
    if spec.get("photo"):
        cells.append(para(photo_drawing(doc, base / spec["photo"]), after=0))
        widths.append(1500)
    cells.append(text)
    widths.append(TEXT_W - sum(widths))
    grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    tcs = "".join(f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/><w:vAlign w:val="center"/></w:tcPr>{c}</w:tc>'
                  for w, c in zip(widths, cells))
    return (f'<w:tbl><w:tblPr><w:tblW w:w="{TEXT_W}" w:type="dxa"/><w:tblLayout w:type="fixed"/>'
            f'<w:tblBorders><w:top w:val="nil"/><w:left w:val="nil"/><w:bottom w:val="nil"/><w:right w:val="nil"/>'
            f'<w:insideH w:val="nil"/><w:insideV w:val="nil"/></w:tblBorders></w:tblPr>'
            f'<w:tblGrid>{grid}</w:tblGrid><w:tr>{tcs}</w:tr></w:tbl>')


def dated(left_runs, date, keep_next=True):
    return para(left_runs + (run("\t" + date, color=GREY) if date else ""), after=20, before=100,
                keep_next=keep_next, tab=True)


def body(doc, spec):
    lang = spec.get("language", "en")
    H = {**HEADINGS[lang], **spec.get("headings", {})}
    out = []
    for key in spec.get("sections", ORDER):
        val = spec.get(key)
        if not val:
            continue
        out.append(heading(H[key]))
        if key == "summary":
            out.append(para(run(val), after=40, jc="both"))
        elif key == "experience":
            for job in val:
                out.append(para(run(job["title"], bold=True, size=10.5, color=DARK), before=100, after=0,
                                keep_next=True))
                where = ", ".join(x for x in (job.get("company"), job.get("location")) if x)
                if job.get("note"):
                    where += " · " + job["note"]
                out.append(dated(run(where, color=GREY), job.get("dates", "")))
                out += [para(run(b), bullet=True, after=20) for b in job.get("bullets", [])]
        elif key == "skills":
            out += [para(run(g["label"] + ": ", bold=True) + run(g["items"]), after=40) for g in val]
        elif key == "education":
            for ed in val:
                head = ed["degree"] + (f"  |  {ed['school']}" if ed.get("school") else "")
                out.append(dated(run(head, bold=True, color=DARK), ed.get("dates", "")))
                out += [para(run(d), bullet=True, after=20) for d in ed.get("details", [])]
        elif key == "languages":
            pairs = val if isinstance(val, str) else "   |   ".join(f"{a} — {b}" for a, b in val)
            out.append(para(run(pairs), after=40))
        elif key == "projects":
            for pr in val:
                title = pr["name"] + (f" — {pr['context']}" if pr.get("context") else "")
                runs = run(title, bold=True, color=DARK)
                for ln in pr.get("links", []):
                    runs += run("  ·  ", color=GREY) + doc.link(ln["label"], ln["url"])
                out.append(dated(runs, pr.get("dates", "")))
                out += [para(run(b), bullet=True, after=20) for b in pr.get("bullets", [])]
                if pr.get("tech"):
                    out.append(para(run(H["tech"] + " ", bold=True, size=9, color=GREY)
                                    + run(pr["tech"], size=9, color=GREY), after=40))
        elif key == "certifications":
            out += [para(run(c), bullet=True, after=20) for c in val]
        elif key == "interests":
            out.append(para(run(val if isinstance(val, str) else ", ".join(val)), after=40))
    return "".join(out)


STYLES = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Calibri" w:eastAsia="Calibri"/>
<w:sz w:val="20"/><w:szCs w:val="20"/><w:color w:val="{DARK}"/></w:rPr></w:rPrDefault>
<w:pPrDefault><w:pPr><w:spacing w:after="40" w:line="264" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>
</w:styles>"""

NUMBERING = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:numbering xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:abstractNum w:abstractNumId="0"><w:multiLevelType w:val="singleLevel"/>
<w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="•"/><w:lvlJc w:val="left"/>
<w:pPr><w:ind w:left="360" w:hanging="200"/></w:pPr><w:rPr><w:color w:val="7A7A7F"/></w:rPr></w:lvl></w:abstractNum>
<w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num>
</w:numbering>"""


def build(spec, out, base=Path(".")):
    doc = Doc()
    head = header_table(doc, spec, base)
    main = body(doc, spec)
    sect = (f'<w:sectPr><w:pgSz w:w="{PAGE_W}" w:h="16838"/>'
            f'<w:pgMar w:top="900" w:right="{MARGIN}" w:bottom="900" w:left="{MARGIN}" '
            f'w:header="400" w:footer="400" w:gutter="0"/></w:sectPr>')
    document = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:document {NS}><w:body>'
                f'{head}{main}{sect}</w:body></w:document>')
    rels = ['<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/'
            'styles" Target="styles.xml"/>',
            '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/'
            'numbering" Target="numbering.xml"/>']
    rels += [f'<Relationship Id="{i}" Type="{t}" Target="{escape(g)}"' + (' TargetMode="External"' if x else "")
             + "/>" for i, t, g, x in doc.rels]
    ctypes = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
              '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
              '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
              '<Default Extension="xml" ContentType="application/xml"/>'
              '<Default Extension="png" ContentType="image/png"/><Default Extension="jpeg" ContentType="image/jpeg"/>'
              '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.'
              'wordprocessingml.document.main+xml"/>'
              '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.'
              'wordprocessingml.styles+xml"/>'
              '<Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.'
              'wordprocessingml.numbering+xml"/></Types>')
    root_rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                 '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                 '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
                 'relationships/officeDocument" Target="word/document.xml"/></Relationships>')
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ctypes)
        z.writestr("_rels/.rels", root_rels)
        z.writestr("word/document.xml", document)
        z.writestr("word/styles.xml", STYLES)
        z.writestr("word/numbering.xml", NUMBERING)
        z.writestr("word/_rels/document.xml.rels",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   + "".join(rels) + "</Relationships>")
        for name, data in doc.media.items():
            z.writestr(f"word/media/{name}", data)
    print(f"Wrote {out}")


def example_path():
    here = Path(__file__).resolve().parent
    for p in (here / "examples" / "resume.json", here.parents[1] / "examples" / "resume.json"):
        if p.exists():
            return p
    return None


def main(argv=None):
    a = sys.argv[1:] if argv is None else argv
    if a[:1] == ["--example"]:
        p = example_path()
        if not p:
            sys.exit("example not found")
        print(p.read_text(encoding="utf-8"))
        return
    if len(a) != 2 or not a[1].endswith(".docx"):
        sys.exit(__doc__)
    src = Path(a[0])
    build(json.loads(src.read_text(encoding="utf-8")), a[1], base=src.parent)


def run_cli():
    main()


if __name__ == "__main__":
    main()
