"""PDF helpers: text, page count, fonts and PNG previews.

Uses poppler (pdftotext / pdfinfo / pdffonts / pdftoppm) when it is installed, and falls back to
pypdf for text and page count. PNG previews need poppler's pdftoppm.
"""
import re
import shutil
import subprocess


def _run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True).stdout


def have_poppler():
    return shutil.which("pdftotext") is not None


def pdf_text(pdf, page=None, layout=False):
    if have_poppler():
        cmd = ["pdftotext"] + (["-layout"] if layout else [])
        if page:
            cmd += ["-f", str(page), "-l", str(page)]
        return _run(cmd + [str(pdf), "-"])
    from pypdf import PdfReader
    pages = PdfReader(str(pdf)).pages
    chosen = [pages[page - 1]] if page else pages
    return "\n".join((p.extract_text(extraction_mode="layout" if layout else "plain") or "") for p in chosen)


def pdf_pages(pdf):
    if shutil.which("pdfinfo"):
        m = re.search(r"Pages:\s+(\d+)", _run(["pdfinfo", str(pdf)]))
        if m:
            return int(m.group(1))
    from pypdf import PdfReader
    return len(PdfReader(str(pdf)).pages)


def fonts_in(pdf):
    if shutil.which("pdffonts"):
        return sorted(set(re.findall(r"\+(Inter[-\w]*)", _run(["pdffonts", str(pdf)]))))
    return []


def to_pngs(pdf, out_prefix, dpi=80):
    """Write <out_prefix>-1.png … ; returns False if pdftoppm is unavailable."""
    if not shutil.which("pdftoppm"):
        return False
    subprocess.run(["pdftoppm", "-r", str(dpi), "-png", str(pdf), str(out_prefix)], capture_output=True)
    return True
