"""docproof render — typeset a .docx document as a designed PDF.

The .docx stays the single source of truth (edit it with `docproof edit`). This tool only READS it,
builds a self-contained HTML page (Inter embedded; photo embedded) and prints it to PDF with headless
Chrome/Chromium. One column, real selectable text, clickable links — ATS-safe.

Usage
  docproof render <doc.docx> [--out out.pdf] [--html out.html] [--png DIR] [--dump]

  --dump   print the parsed structure (sections / entries / bullets) and exit — use it to check
           the classification after unusual edits.

Classification (from the docx structure, no guessing on text):
  heading   bold, ALL CAPS, no tab, not a list item          → section (shown in Title Case)
  entry     bold with a tab (title ⇥ date)                   → project / education head
  role      bold, no tab, no "Label:" start                  → job title; the next tab line
            (company ⇥ date) is folded in: the date moves up onto the role line
  label row bold "Label:" start (Skills / Kenntnisse)         → two-column definition row
  bullet    list item (numPr)                                 → bullet of the current entry
  meta      line starting "Technologies:" etc.                → small grey line, no bullet
  plain     anything else: summary paragraph, or "a | b | c"  → paragraph / inline list

Self-check after printing: every word of the docx appears in the PDF text, and the page count is
reported. Exit code 1 if words are missing. Chrome: set DOCPROOF_CHROME to override discovery.
"""
import base64, html, os, re, subprocess, sys, tempfile, time, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
FONTS = HERE / "assets" / "fonts"
META_PREFIXES = ("Technologies:", "Technologien:", "Skills used:", "Methoden & Tools:")
from docproof.headings import GERMAN_MARKERS, SUMMARY_KEYS  # noqa: E402
from docproof.pdftools import pdf_text, pdf_pages, fonts_in  # noqa: E402

TITLE_CASE = {}  # headings not listed are shown with str.title() ("PROFESSIONAL EXPERIENCE" → "Professional Experience")


def find_chrome():
    """Chrome/Chromium/Edge on macOS, Linux or Windows; DOCPROOF_CHROME overrides."""
    import shutil
    env = os.environ.get("DOCPROOF_CHROME")
    if env:
        return env
    for c in ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              "/Applications/Chromium.app/Contents/MacOS/Chromium",
              "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
              r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"):
        if os.path.exists(c):
            return c
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome", "msedge"):
        path = shutil.which(name)
        if path:
            return path
    sys.exit("No Chrome/Chromium found. Install one or set DOCPROOF_CHROME=/path/to/chrome.")

W_T = re.compile(r"<w:t(?:\s[^>]*)?>([^<]*)</w:t>")


# ───────────────────────────── docx parsing ─────────────────────────────
def runs_of(p, rels):
    """[(text, href, bold)] for a paragraph, tabs as '\t', hyperlinks resolved."""
    out = []
    for m in re.finditer(r'<w:hyperlink\b([^>]*)>(.*?)</w:hyperlink>|<w:r[ >].*?</w:r>', p, re.S):
        if m.group(1) is not None:
            rid = re.search(r'r:id="([^"]+)"', m.group(1))
            href = rels.get(rid.group(1)) if rid else None
            for r in re.findall(r"<w:r[ >].*?</w:r>", m.group(2), re.S):
                out.append((run_text(r), href, is_bold(r)))
        else:
            out.append((run_text(m.group(0)), None, is_bold(m.group(0))))
    return [(t, h, b) for t, h, b in out if t]


def run_text(r):
    parts = re.findall(r"<w:t(?:\s[^>]*)?>([^<]*)</w:t>|<w:tab/>", r)
    s = ""
    for m in re.finditer(r"<w:t(?:\s[^>]*)?>([^<]*)</w:t>|<w:tab/>", r):
        s += "\t" if m.group(0) == "<w:tab/>" else html.unescape(m.group(1))
    return s


def is_bold(r):
    return bool(re.search(r'<w:b(?: w:val="(?:1|true)")?/>', r))


def parse(docx):
    z = zipfile.ZipFile(docx)
    x = z.read("word/document.xml").decode("utf8")
    rels = dict(re.findall(r'Id="([^"]+)"[^>]*Target="([^"]+)"',
                           z.read("word/_rels/document.xml.rels").decode("utf8")))
    rels.update({k: v for v, k in re.findall(r'Target="([^"]+)"[^>]*Id="([^"]+)"',
                                              z.read("word/_rels/document.xml.rels").decode("utf8"))})
    tbl_end = x.find("</w:tbl>")
    head_xml, body_xml = x[:tbl_end], x[tbl_end:]

    # header: name, title line, contact line, photo (largest embedded image)
    hparas = [p for p in re.findall(r"<w:p[ >].*?</w:p>", head_xml, re.S)
              if "".join(W_T.findall(p)).strip()]
    htexts = [html.unescape("".join(W_T.findall(p))).strip() for p in hparas]
    contact_p = next((p for p in hparas if "<w:hyperlink" in p), hparas[2] if len(hparas) > 2 else "")
    links = {}
    for m in re.finditer(r'<w:hyperlink\b[^>]*r:id="([^"]+)"[^>]*>(.*?)</w:hyperlink>', contact_p, re.S):
        links[html.unescape("".join(W_T.findall(m.group(2)))).strip()] = rels.get(m.group(1))
    contact_text = html.unescape("".join(W_T.findall(contact_p)))
    contacts = []
    for item in [s.strip() for s in re.split(r"\s{2,}", contact_text) if s.strip()]:
        href = links.get(item)
        kind = ("email" if "@" in item else "phone" if re.match(r"^\+?[\d\s()/-]{7,}$", item) else
                "linkedin" if "linkedin" in (href or item).lower() else "web" if href or "." in item.split()[0]
                else "location")
        contacts.append({"text": item, "href": href, "kind": kind})
    embeds = re.findall(r'r:embed="([^"]+)"', head_xml)
    photo = None
    if embeds:
        best = max(embeds, key=lambda r: len(z.read("word/" + rels[r])))
        photo = z.read("word/" + rels[best])
    header = {"name": htexts[0], "title": htexts[1], "contacts": contacts, "photo": photo}

    # body
    sections, cur, entry, lang = [], None, None, "en"
    paras = re.findall(r"<w:p[ >].*?</w:p>", body_xml, re.S)
    for p in paras:
        runs = runs_of(p, rels)
        text = "".join(t for t, _, _ in runs)
        if not text.strip():
            continue
        li = "<w:numPr>" in p
        bold = bool(runs) and runs[0][2]
        tab = "\t" in text
        stripped = text.strip()
        if bold and not tab and not li and stripped.isupper():
            if stripped in GERMAN_MARKERS:
                lang = "de"
            cur = {"title": TITLE_CASE.get(stripped, stripped.title()), "key": stripped, "blocks": []}
            sections.append(cur)
            entry = None
            continue
        if cur is None:
            raise SystemExit(f"text before first heading: {stripped[:60]}")
        if stripped.startswith(META_PREFIXES):
            label, _, rest = stripped.partition(":")
            (entry or {"meta": []}).setdefault("meta", []).append((label, rest.strip()))
            if entry is None:
                cur["blocks"].append({"type": "plain", "text": stripped})
            continue
        if li:
            if entry is None:
                entry = {"type": "entry", "title_runs": [], "date": "", "sub": "", "bullets": [], "meta": []}
                cur["blocks"].append(entry)
            entry["bullets"].append(runs)
            continue
        if tab:
            left, _, right = text.partition("\t")
            if entry is not None and entry.get("await_sub"):
                entry.update(sub=left.strip(), date=right.strip(), await_sub=False)
                continue
            # title runs = runs up to the tab
            tr, acc = [], ""
            for t, h, b in runs:
                if "\t" in t:
                    tr.append((t.split("\t")[0], h, b))
                    break
                tr.append((t, h, b))
            entry = {"type": "entry", "title_runs": tr, "date": right.strip(), "sub": "",
                     "bullets": [], "meta": [], "role": False}
            cur["blocks"].append(entry)
            continue
        if bold and runs[0][0].rstrip().endswith(":"):
            cur["blocks"].append({"type": "label", "label": runs[0][0].strip().rstrip(":"),
                                  "text": "".join(t for t, _, _ in runs[1:]).strip()})
            entry = None
            continue
        if bold:
            entry = {"type": "entry", "title_runs": [(stripped, None, True)], "date": "", "sub": "",
                     "bullets": [], "meta": [], "role": True, "await_sub": True}
            cur["blocks"].append(entry)
            continue
        cur["blocks"].append({"type": "plain", "text": stripped})
        entry = None
    return header, sections, lang, x


# ───────────────────────────── HTML ─────────────────────────────
def e(s):
    s = html.escape(s, quote=False)
    # never break hyphenated compounds ("k-NN", "save-offer", "churn-prediction") at the hyphen
    return re.sub(r"(?<![\w-])(\w{1,12}-\w{1,14})(?![\w-])", r'<span class="nw">\1</span>', s)


# Key metrics get a slightly heavier weight so the eye has anchors when scanning. Only numbers that
# carry a result or scope — never dates or years.
METRIC = re.compile(
    r"(?:~|ca\.\s)?\d+(?:[.,]\d+)?\s?(?:to|auf|–)\s(?:~|ca\.\s)?\d+(?:[.,]\d+)?\s(?:minutes|Minuten)"  # ~20 to ~3 minutes
    r"|\(?(?:~|ca\.\s)?\d+(?:[.,]\d+)?(?:–\d+)?\s?%\)?"                                                   # ~85%, 50–70%, 78 %
    r"|\d+(?:[.,]\d+)?\+"                                                                                     # 25+, 3+
    r"|\büber \d+(?:[.,]\d+)?\b"                                                                                # DE: über 25
    r"|\b\d+/100\b"                                                                                            # 83/100 (x/5 ratings stay plain)
    r"|\b\d+\s(?:markets|marketplaces|countries|teams|Märkten|Ländern|Teams)\b"
    r"|(?:~|ca\.\s)?\d+(?:[.,]\d+)?\s?(?:hours|hrs|h)\s(?:to|auf|–)\s(?:~|ca\.\s)?\d+(?:[.,]\d+)?\s(?:minutes|min|Minuten)"
)


def emph(h, cap=3):
    """Wrap up to `cap` metric tokens in <span class="m"> — text outside tags only. More than two
    bold items in one bullet turns anchors into noise."""
    parts, n = re.split(r"(<[^>]+>)", h), [0]

    def sub(m):
        n[0] += 1
        return f'<span class="m">{m.group(0)}</span>' if n[0] <= cap else m.group(0)
    out, in_b = [], False
    for p in parts:
        if p.startswith("<"):
            in_b = p.startswith("<b") or (in_b and not p.startswith("</b"))
            out.append(p)
        else:
            out.append(p if in_b else METRIC.sub(sub, p))
    return "".join(out)

def bullet_html(runs):
    """Bullet text: bold runs from the .docx become key-phrase emphasis (`docproof keywords`); figures
    fill the remaining emphasis budget so a bullet never carries more than 2 bold items."""
    parts, n_kw = [], 0
    for t, hr, b in runs:
        if b and not hr and t.strip():
            n_kw += 1
            parts.append(f'<b class="k">{e(t)}</b>')
        else:
            parts.append(link(t, hr, "ext"))
    return no_widow(emph("".join(parts), cap=max(0, 2 - n_kw)))

def no_widow(h):
    """Tie the last two words together (non-breaking space outside tags) so a bullet can never end
    on a single stranded word."""
    depth, i = 0, len(h) - 1
    while i >= 0:
        c = h[i]
        if c == ">":
            depth += 1
        elif c == "<":
            depth -= 1
        elif c == " " and depth == 0:
            tail = h[i + 1:]
            if "-" in tail and "<" not in tail and ">" not in tail:   # "Event-Tracking" must not split
                return h[:i] + '&nbsp;<span class="nw">' + tail + "</span>"
            return h[:i] + "&nbsp;" + tail
        i -= 1
    return h


def link(text, href, cls=""):
    c = f' class="{cls}"' if cls else ""
    return f'<a href="{html.escape(href)}"{c}>{e(text)}</a>' if href else e(text)


def inline_list(text):
    """'a  |  b  |  c' → items separated by a quiet dot."""
    parts = [s.strip() for s in text.split("|")]
    return '<span class="sep" aria-hidden="true"> · </span>'.join(
        f'<span class="item">{e(p)}</span>' for p in parts if p)


def title_html(runs):
    """Entry head: 'Name — qualifier  ·  GitHub' / 'Degree  |  School' → weighted spans."""
    out = []
    for i, (t, href, _) in enumerate(runs):
        if href:
            out.append(f'<a class="ext" href="{html.escape(href)}">{e(t.strip())}</a>')
            continue
        if t.strip() == "·":
            out.append('<span class="sep"> · </span>')
            continue
        if i == 0:
            if " — " in t:
                a, b = t.split(" — ", 1)
                out.append(f'<span class="t">{e(a.strip())}</span>'
                           f'<span class="q"> — {e(b.strip())}</span>')
            elif "|" in t:
                a, b = t.split("|", 1)
                out.append(f'<span class="t">{e(a.strip())}</span>'
                           f'<span class="q"><span class="sep"> · </span>{e(b.strip())}</span>')
            else:
                out.append(f'<span class="t">{e(t.strip())}</span>')
        else:
            out.append(f'<span class="q">{e(t)}</span>')
    return "".join(out)


ICONS = {
    "location": '<svg viewBox="0 0 16 16"><path d="M8 1.5a4.5 4.5 0 0 0-4.5 4.5c0 3.2 4.5 8.5 4.5 8.5s4.5-5.3 4.5-8.5A4.5 4.5 0 0 0 8 1.5Zm0 6.2a1.7 1.7 0 1 1 0-3.4 1.7 1.7 0 0 1 0 3.4Z"/></svg>',
    "email": '<svg viewBox="0 0 16 16"><path d="M2 3.5h12a.5.5 0 0 1 .5.5v8a.5.5 0 0 1-.5.5H2a.5.5 0 0 1-.5-.5V4a.5.5 0 0 1 .5-.5Zm.6 1.2v.2L8 8.6l5.4-3.7v-.2H2.6Zm10.8 1.6L8 10 2.6 6.3v5h10.8v-5Z"/></svg>',
    "phone": '<svg viewBox="0 0 16 16"><path d="M4.6 1.8 6.4 4a1 1 0 0 1 0 1.3l-.9 1a8.6 8.6 0 0 0 4.2 4.2l1-.9a1 1 0 0 1 1.3 0l2.2 1.8a1 1 0 0 1 .1 1.4l-1 1.1c-.6.6-1.5.8-2.3.5A13 13 0 0 1 2.6 5.9c-.3-.8-.1-1.7.5-2.3l1-1a1 1 0 0 1 1.5.1Z"/></svg>',
    "web": '<svg viewBox="0 0 16 16"><path d="M8 1.5a6.5 6.5 0 1 0 0 13 6.5 6.5 0 0 0 0-13Zm4.9 6H10.8a10 10 0 0 0-.8-3.9 5.3 5.3 0 0 1 2.9 3.9ZM8 2.8c.6.8 1.4 2.4 1.6 4.7H6.4C6.6 5.2 7.4 3.6 8 2.8ZM6 3.6a10 10 0 0 0-.8 3.9H3.1A5.3 5.3 0 0 1 6 3.6ZM3.1 8.5h2.1c.1 1.5.4 2.8.8 3.9a5.3 5.3 0 0 1-2.9-3.9ZM8 13.2c-.6-.8-1.4-2.4-1.6-4.7h3.2c-.2 2.3-1 3.9-1.6 4.7Zm2-.8c.4-1.1.7-2.4.8-3.9h2.1A5.3 5.3 0 0 1 10 12.4Z"/></svg>',
    "linkedin": '<svg viewBox="0 0 16 16"><path d="M13.5 1.5h-11a1 1 0 0 0-1 1v11a1 1 0 0 0 1 1h11a1 1 0 0 0 1-1v-11a1 1 0 0 0-1-1ZM5.4 12.6H3.5V6.5h1.9v6.1ZM4.4 5.7a1.1 1.1 0 1 1 0-2.2 1.1 1.1 0 0 1 0 2.2Zm8.2 6.9h-1.9v-3c0-.7 0-1.6-1-1.6s-1.1.8-1.1 1.6v3H6.7V6.5h1.8v.8c.3-.5.9-1 1.9-1 2 0 2.3 1.3 2.3 3v3.3Z"/></svg>',
}


def font_face():
    css = []
    for w, f in ((400, "Regular"), (500, "Medium"), (600, "SemiBold"), (700, "Bold")):
        b64 = base64.b64encode((FONTS / f"Inter-{f}.woff2").read_bytes()).decode()
        css.append(f"@font-face{{font-family:'Inter';font-weight:{w};font-style:normal;"
                   f"src:url(data:font/woff2;base64,{b64}) format('woff2');}}")
    return "\n".join(css)


CSS = """
@page { size: A4; margin: 13mm 18mm 13mm 18mm; }
:root {
  --text: #1d1d1f; --second: #505055; --third: #7a7a7f; --hair: #c7c7cc;  /* greys dark enough to survive printing */
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body {
  font-family: 'Inter', -apple-system, 'Helvetica Neue', Arial, sans-serif;
  font-size: 8.9pt; line-height: 1.45; color: var(--text); background: #fff;
  font-feature-settings: 'cv11' 1, 'ss03' 1; -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility; hyphens: manual;
}
a { color: inherit; text-decoration: none; }

/* header */
header { display: flex; align-items: center; gap: 15pt; margin-bottom: 4pt; }
header .ph { width: 60pt; height: 60pt; border-radius: 50%; overflow: hidden; flex: none; }
header .ph img { width: 100%; height: 100%; object-fit: cover; transform: scale(1.06); transform-origin: 50% 0%; }  /* zoom anchored at the top: never crops the top of the head */
header h1 { font-size: 20pt; font-weight: 600; letter-spacing: 0.045em; line-height: 1.1; }
header .role { font-size: 10pt; font-weight: 500; color: var(--text); margin-top: 3pt;
               letter-spacing: -0.005em; }
header .role .sep { color: var(--third); font-weight: 400; }
header .contact { display: flex; flex-wrap: wrap; column-gap: 10pt; row-gap: 2pt; margin-top: 5pt;
                  font-size: 7.6pt; color: var(--second); }
header .contact span { display: inline-flex; align-items: center; gap: 3.5pt; white-space: nowrap; }
header svg { width: 7.8pt; height: 7.8pt; fill: var(--third); flex: none; }

/* sections */
section { margin-top: 14pt; }
section.keep { break-inside: avoid; }
h2 { font-size: 12.5pt; font-weight: 600; letter-spacing: -0.015em; line-height: 1.2;
     margin-bottom: 6pt; break-after: avoid; }
.summary { font-size: 9.2pt; line-height: 1.5; }
.m, .k { font-weight: 600; }

.entry + .entry { margin-top: 8pt; }
.head { display: flex; justify-content: space-between; align-items: baseline; gap: 12pt;
        break-after: avoid; }
.head .title { font-size: 9.6pt; line-height: 1.35; }
.head .t { font-weight: 600; letter-spacing: -0.005em; }
.head .q { color: var(--second); font-weight: 400; }
.head .date { font-size: 8.3pt; color: var(--second); white-space: nowrap;
              font-variant-numeric: tabular-nums; }
.sub { font-size: 8.5pt; color: var(--second); margin-top: 0.5pt; break-after: avoid; }
.sep { color: var(--third); }
a.ext { color: var(--second); text-decoration: underline; text-decoration-color: var(--hair);
        text-decoration-thickness: 0.6pt; text-underline-offset: 2pt; }

ul { list-style: none; margin-top: 3pt; }
li { position: relative; padding-left: 10pt; break-inside: avoid; }
li + li { margin-top: 1.6pt; }
li::before { content: ""; position: absolute; left: 1.5pt; top: 0.62em; width: 3pt; height: 3pt;
             border-radius: 50%; background: var(--third); }
.meta { font-size: 8.1pt; color: var(--second); margin-top: 3pt; padding-left: 10pt; break-before: avoid; }
.entry.keep { break-inside: avoid; }
li:first-child:not(:last-child), li:nth-last-child(2) { break-after: avoid; }
.meta b { font-weight: 500; color: var(--text); }

/* skills: definition grid */
.grid { display: grid; grid-template-columns: 33mm 1fr; column-gap: 10pt; break-inside: avoid; }
.grid + .grid { margin-top: 4pt; }
h2 + .grid-block .grid:first-child { break-before: avoid; }
.grid dt { font-weight: 600; font-size: 9pt; }
.grid dd { }

.inline .item { white-space: normal; }
.nw { white-space: nowrap; }
.pairs { display: flex; flex-wrap: wrap; column-gap: 16pt; row-gap: 2pt; }
.pair .k { font-weight: 500; }
.pair .v { color: var(--second); }
.plain + .plain { margin-top: 3pt; }
"""


def footer_css(name):
    """Name + page number on every page."""
    return ("@page { @bottom-right { content: \"" + name + " · \" counter(page) \"/\" counter(pages);"
            " font-family: 'Inter', sans-serif; font-size: 7pt; color: #86868b; } }"
            "")


def build_html(header, sections, lang):
    h = header
    photo = ""
    if h["photo"]:
        b = h["photo"]
        mime = ("image/png" if b[:8] == b"\x89PNG\r\n\x1a\n" else "image/jpeg" if b[:3] == b"\xff\xd8\xff"
                else "image/gif" if b[:4] == b"GIF8" else "image/webp" if b[8:12] == b"WEBP" else "image/png")
        photo = f'<div class="ph"><img alt="" src="data:{mime};base64,' + base64.b64encode(b).decode() + '"></div>'
    contacts = "".join(
        f'<span>{ICONS[c["kind"]]}{link(c["text"], c["href"])}</span>' for c in h["contacts"])
    out = [f'<header>{photo}<div><h1>{e(h["name"])}</h1>'
           f'<div class="role">{inline_list(h["title"])}</div>'
           f'<div class="contact">{contacts}</div></div></header>']
    for s in sections:
        entries = [b for b in s["blocks"] if b["type"] == "entry"]
        # short sections (≤2 entries, skills grid, languages, interests) never split across pages —
        # a split two-entry section is the most visible layout flaw a reader notices
        short = len(entries) <= 2
        out.append(f'<section class="{"keep" if short else ""}"><h2>{e(s["title"])}</h2>')
        labels = [b for b in s["blocks"] if b["type"] == "label"]
        if labels:
            # one small grid per row: rows never split, the block may break BETWEEN rows, and the
            # heading stays with the first row (the whole-block rule pushed Skills off page 1)
            out.append('<div class="grid-block">' + "".join(
                f'<dl class="grid row">'
                f'<dt>{e(b["label"])}</dt><dd>{no_widow(e(b["text"]))}</dd></dl>' for b in labels) + "</div>")
        for b in s["blocks"]:
            if b["type"] == "plain":
                if s["key"] in SUMMARY_KEYS:
                    out.append(f'<p class="summary">{no_widow(emph(e(b["text"]), cap=2))}</p>')
                elif "|" in b["text"] and all(" — " in x for x in b["text"].split("|")):
                    pairs = [x.strip().split(" — ", 1) for x in b["text"].split("|")]
                    out.append('<p class="plain pairs">' + "".join(
                        f'<span class="pair"><span class="k">{e(k)}</span> '
                        f'<span class="v">{e(v)}</span></span>' for k, v in pairs) + "</p>")
                elif "|" in b["text"]:
                    out.append(f'<p class="plain inline">{inline_list(b["text"])}</p>')
                else:
                    out.append(f'<p class="plain">{e(b["text"])}</p>')
            elif b["type"] == "entry":
                # short entries (≤4 bullets) never split across pages; long ones keep ≥2 bullets per side
                keep = " keep" if len(b["bullets"]) <= 4 else ""
                out.append(f'<div class="entry{keep}"><div class="head">'
                           f'<div class="title">{title_html(b["title_runs"])}</div>'
                           f'<div class="date">{e(b["date"])}</div></div>')
                if b["sub"]:
                    out.append(f'<div class="sub">{e(b["sub"])}</div>')
                if b["bullets"]:
                    out.append("<ul>" + "".join(
                        "<li>" + bullet_html(r) + "</li>"
                        for r in b["bullets"]) + "</ul>")
                for label, rest in b["meta"]:
                    out.append(f'<p class="meta"><b>{e(label)}</b>&ensp;{e(rest)}</p>')
                out.append("</div>")
        out.append("</section>")
    title = f'{h["name"].title()} — {"Lebenslauf" if lang == "de" else "CV"}'
    return (f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8">'
            f'<title>{e(title)}</title><meta name="author" content="{e(h["name"].title())}">'
            f"<style>{font_face()}{CSS}{footer_css(h['name'].title())}</style></head><body>{''.join(out)}</body></html>")


# ───────────────────────────── print + verify ─────────────────────────────
def words(s):
    return re.findall(r"[0-9A-Za-zÀ-ÿ]+", s)


def main():
    a = sys.argv[1:]
    if not a or not a[0].endswith(".docx"):
        sys.exit(__doc__)
    docx = Path(a[0])
    if "--out" in a:
        pdf = Path(a[a.index("--out") + 1]).resolve()
    elif len(a) > 1 and a[1].endswith(".pdf"):
        pdf = Path(a[1]).resolve()
    else:
        pdf = docx.with_suffix(".pdf").resolve()
    header, sections, lang, xml = parse(docx)
    if "--dump" in a:
        print("HEADER", {k: v for k, v in header.items() if k != "photo"})
        for s in sections:
            print(f"\n## {s['title']}")
            for b in s["blocks"]:
                if b["type"] == "entry":
                    print(f"  [{'role' if b.get('role') else 'entry'}] "
                          f"{''.join(t for t, _, _ in b['title_runs'])} | {b['sub']} | {b['date']}"
                          f"  ({len(b['bullets'])} bullets, {len(b['meta'])} meta)")
                else:
                    print(f"  [{b['type']}] {(b.get('label', '') + ': ') if b['type'] == 'label' else ''}"
                          f"{b['text'][:80]}")
        return
    page = build_html(header, sections, lang)
    html_path = Path(a[a.index("--html") + 1]).resolve() if "--html" in a else pdf.with_suffix(".html")
    html_path.write_text(page, encoding="utf8")
    # Chrome headless on macOS often writes the PDF and then never exits → poll for a stable file,
    # then terminate it ourselves (fonts/photo are data: URIs, so nothing loads late).
    if pdf.exists():
        pdf.unlink()
    with tempfile.TemporaryDirectory() as prof:
        proc = subprocess.Popen([find_chrome(), "--headless", "--no-sandbox", "--disable-gpu", "--no-first-run",
                                 "--no-default-browser-check", f"--user-data-dir={prof}",
                                 "--no-pdf-header-footer", f"--print-to-pdf={pdf}",
                                 html_path.as_uri()],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        last, stable = -1, 0
        for _ in range(240):                       # ≤ 60 s
            time.sleep(0.25)
            size = pdf.stat().st_size if pdf.exists() else -1
            stable = stable + 1 if size > 0 and size == last else 0
            last = size
            if stable >= 4 or (proc.poll() is not None and size > 0):
                break
        proc.terminate()
        try:
            proc.wait(5)
        except subprocess.TimeoutExpired:
            proc.kill()
    if not pdf.exists() or pdf.stat().st_size == 0:
        sys.exit("Chrome did not write the PDF")
    if "--html" not in a:
        html_path.unlink()
    # verify: every docx word is in the PDF text; fonts embedded; page count
    src = html.unescape(" ".join(W_T.findall(xml)))
    have = {w.lower() for w in words(pdf_text(pdf, layout=True))}
    missing = sorted({w for w in words(src) if w.lower() not in have})
    print(f"Wrote {pdf} — {pdf_pages(pdf)} page(s); fonts: " + (", ".join(fonts_in(pdf)) or "n/a"))
    if "--png" in a:
        from docproof.pdftools import to_pngs
        out_dir = Path(a[a.index("--png") + 1]); out_dir.mkdir(parents=True, exist_ok=True)
        print("previews:", "written to " + str(out_dir) if to_pngs(pdf, out_dir / pdf.stem)
              else "skipped (install poppler for pdftoppm)")
    if missing:
        print("MISSING WORDS in PDF text:", missing)
        sys.exit(1)
    print("TEXT CHECK PASSED: every word of the docx is in the PDF.")


def run():
    main()


if __name__ == "__main__":
    main()
