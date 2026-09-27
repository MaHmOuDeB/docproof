"""docproof set-metadata — set the Word document's Title and Author (they carry over into exported PDFs).

  docproof set-metadata in.docx out.docx "CV – Jordan Rivera" "Jordan Rivera"

Some exports (e.g. Google Docs) have no docProps/core.xml at all; in that case the part is created
and registered in [Content_Types].xml and _rels/.rels (both are required, or Word ignores it).
"""
import datetime
import sys
import zipfile
from xml.sax.saxutils import escape


def set_metadata(src, dst, title, author):
    with zipfile.ZipFile(src) as z:
        names = z.namelist()
        files = {n: z.read(n) for n in names}
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    files["docProps/core.xml"] = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
        'xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        f'<dc:title>{escape(title)}</dc:title><dc:creator>{escape(author)}</dc:creator>'
        f'<cp:lastModifiedBy>{escape(author)}</cp:lastModifiedBy>'
        f'<dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>'
        f'<dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>'
        '</cp:coreProperties>').encode()
    ct = files["[Content_Types].xml"].decode()
    if "/docProps/core.xml" not in ct:
        files["[Content_Types].xml"] = ct.replace(
            "</Types>", '<Override PartName="/docProps/core.xml" '
            'ContentType="application/vnd.openxmlformats-package.core-properties+xml"/></Types>').encode()
    rels = files["_rels/.rels"].decode()
    if "docProps/core.xml" not in rels:
        files["_rels/.rels"] = rels.replace(
            "</Relationships>", '<Relationship Id="rIdCoreProps" '
            'Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" '
            'Target="docProps/core.xml"/></Relationships>').encode()
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zo:
        for n in names + [n for n in files if n not in names]:
            zo.writestr(n, files[n])
    print(f"metadata: title={title!r} author={author!r}")


def main(argv=None):
    a = sys.argv[1:] if argv is None else argv
    if len(a) != 4 or not (a[0].endswith(".docx") and a[1].endswith(".docx")):
        sys.exit(__doc__)
    set_metadata(*a)


if __name__ == "__main__":
    main()
