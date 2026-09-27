"""Shared helpers: read a fact base (Markdown) and the text of a .docx."""
import html
import re
import zipfile
from pathlib import Path

W_T = re.compile(r"<w:t(?:\s[^>]*)?>([^<]*)</w:t>")
STOP = set("""a an and are as at be by for from has have in into is it its of on or our the their this to
we will with you your who what can able across per via within using use used etc e g i ie also
plus more most other own new well strong good great excellent experience experienced years year
nice similar including include such like least ideally proven solid hands on based both""".split())
# light synonym folding so "experimentation" meets "a/b tests", "visualisation" meets "visualization"
SYN = {"experimentation": "experiment", "experiments": "experiment", "experimental": "experiment",
       "ab": "experiment", "a/b": "experiment", "split": "experiment",
       "visualisation": "visualization", "visualise": "visualization", "visualize": "visualization",
       "analyse": "analysis", "analyze": "analysis", "analysed": "analysis", "analyzed": "analysis",
       "analysing": "analysis", "analyzing": "analysis", "analytics": "analysis", "analytical": "analysis",
       "dashboards": "dashboard", "reporting": "report", "reports": "report",
       "stakeholders": "stakeholder", "modelling": "model", "modeling": "model", "models": "model"}


IRREGULAR = {"built": "build", "wrote": "write", "ran": "run", "led": "lead", "made": "make",
             "drove": "drive", "grew": "grow", "taught": "teach", "won": "win"}


def stem(tok):
    tok = IRREGULAR.get(tok, SYN.get(tok, tok))
    for suf in ("ations", "ation", "ings", "ing", "ied", "ies", "ed", "es", "s"):
        if len(tok) > len(suf) + (2 if suf == "s" else 3) and tok.endswith(suf):
            tok = tok[: -len(suf)] + ("y" if suf in ("ies", "ied") else "")
            break
    if len(tok) > 4 and tok.endswith("e"):
        tok = tok[:-1]
    if len(tok) > 5 and tok.endswith("at"):
        tok = tok[:-2]
    return SYN.get(tok, tok)


def surface_tokens(text):
    """[(original word, stem)] — for showing readable words in reports."""
    raw = re.findall(r"a/b|[a-z0-9][a-z0-9+#.]*[a-z0-9+#]|[a-z0-9]", text.lower())
    return [(t, stem(t)) for t in raw if t not in STOP and not re.fullmatch(r"\d+", t)]


def tokens(text):
    raw = re.findall(r"a/b|[a-z0-9][a-z0-9+#.]*[a-z0-9+#]|[a-z0-9]", text.lower())
    return [stem(t) for t in raw if t not in STOP and not re.fullmatch(r"\d+", t)]


class FactBase:
    def __init__(self, path):
        self.path = Path(path)
        self.text = self.path.read_text(encoding="utf-8")
        self.gaps = self._section_items("Known gaps")
        # evidence = everything except the Identity and Known gaps sections (a gap is not evidence)
        evidence = re.sub(r"^##\s+(Known gaps|Identity)\s*$.*?(?=^##\s|\Z)", "", self.text,
                          flags=re.M | re.S | re.I)
        clean = re.sub(r"\*\*|`", "", evidence)
        self.lines = [ln.strip(" -*\t") for ln in clean.splitlines()
                      if ln.strip(" -*#\t") and not ln.lstrip().startswith("#")]
        self.tokens = set(tokens(clean))

    def _section_items(self, title):
        m = re.search(rf"^##\s+{re.escape(title)}\s*$(.*?)(?=^##\s|\Z)", self.text, re.M | re.S | re.I)
        if not m:
            return []
        return [re.sub(r"\*\*|`", "", ln.strip()[2:]).strip() for ln in m.group(1).splitlines()
                if ln.strip().startswith(("- ", "* "))]

    def has_number(self, num):
        """num like '40+', '0.84', '6' — present in the fact base as a number token."""
        core = num.replace(",", ".").rstrip("+%")
        pat = rf"(?<![\d.]){re.escape(core)}(?![\d])"
        return re.search(pat, self.text.replace(",", ".")) is not None


def docx_paragraphs(path):
    """Plain text of every body paragraph (after the header table), in order."""
    with zipfile.ZipFile(path) as z:
        x = z.read("word/document.xml").decode("utf-8")
    body = x[x.find("</w:tbl>"):] if "</w:tbl>" in x else x
    out = []
    for p in re.findall(r"<w:p[ >].*?</w:p>", body, re.S):
        p = p.replace("<w:tab/>", "<w:t>\t</w:t>")      # keep "title ⇥ date" apart
        t = html.unescape("".join(W_T.findall(p)))
        if t.strip():
            out.append(t.strip())
    return out
