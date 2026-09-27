"""docproof edit / dump / text — safe, verifiable edits to a .docx document.

Works on raw word/document.xml text (never re-serialises through a library), so everything not
explicitly edited stays byte-identical. Matching uses each paragraph's *concatenated* text, so it
does not matter how Word split the text into runs.

Zones
  header : everything before the first body heading (SUMMARY, PROFESSIONAL EXPERIENCE, KURZPROFIL,
           BERUFSERFAHRUNG …). Protected. The ONLY editable header paragraph is the title line,
           via ops with "zone": "title".
  body   : everything from that heading onwards.

Commands (as `docproof <cmd>`)
  inspect <doc.docx>                         real Word file? which language/anchor?
  dump    <doc.docx> [--anchor X] [--runs]   list paragraphs with index, zone, flags, text
                                             (--runs: run indices + formatting for set_segments)
  edit    <doc.docx> <ops.json> <out.docx> [--anchor X]
  header-diff <original.docx> <edited.docx>  header byte-identity (title line excepted)
  text    <doc.docx>                         plain text of every paragraph

ops.json — a list of operations, applied in order. Every "match" must hit exactly one paragraph in
its zone or the whole run aborts (a silent no-op is worse than an error).

  {"op": "set_text", "match": "Ran 40+ A/B", "text": "Designed and analysed 40+ A/B tests ..."}
  {"op": "replace",  "match": "Ran 40+ A/B", "old": "Ran", "new": "Designed"}
  {"op": "delete",   "match": "Supported quarterly planning"}
  {"op": "set_segments", "match": "Tools:", "segments": [
        {"text": "Tools: ", "style_of": 0},
        {"text": "SQL, dbt, Python, Looker", "style_of": 1}]}
  {"op": "set_segments", "match": "Northwind Apps", "segments": [
        {"text": "Northwind Apps, Lisbon, PT", "style_of": 0},
        {"tab": true, "style_of": 1}, {"text": "Mar 2022 – Aug 2025", "style_of": 1}]}
  {"op": "insert_after", "anchor": "Automated the weekly", "like": "Automated the weekly",
                         "text": "New bullet text ..."}
  {"op": "set_text", "zone": "title", "match": "Product Analyst",
                     "text": "Product Analyst | Experimentation | SQL, Python"}

"replace" edits inside the single run that contains "old" — keeps all formatting, needs no force;
prefer it for small changes on formatted lines. "set_segments" rewrites a formatted line run by run.

Safety refusals for set_text / insert_after (override with "force": true only after inspecting):
  - the paragraph contains a drawing, hyperlink, field, or tab (tabs carry right-aligned dates)
  - the paragraph has runs with different formatting (e.g. a bold keyword inside a bullet)
After a forced set_text, re-apply keyword bold with `docproof keywords`.

Not this tool's job (use the dedicated, self-verifying commands): a new title⇥date line or entry
block → add-entry; a hyperlink → add-link; a summary section → add-summary; moving sections or
lines → reorder. If the same step fails twice, stop and report the exact op and error.

When checking whether a paragraph is empty, match text runs with the regex <w:t[ >] — a plain
"<w:t" also matches <w:tab/> and <w:tabs>.
"""
import json
import re
import sys
import zipfile
from html import unescape
from xml.sax.saxutils import escape

# First body section heading: boundary() takes the first paragraph whose text matches ANY of these.
from docproof.headings import ANCHORS  # noqa: E402

# ---------------------------------------------------------------- io


def read_xml(path):
    with zipfile.ZipFile(path) as z:
        return z.read("word/document.xml").decode("utf-8")


def ensure(cond, msg="post-check failed"):
    """A real check (unlike assert, it survives python -O). Nothing is written when it fails."""
    if not cond:
        raise SystemExit(f"ERROR: {msg}. Nothing was written.")


def write_docx(src, dst, new_xml):
    """Write via a temp file in the target folder, then replace atomically — so src == dst is safe
    and a crash never leaves a half-written document."""
    import os
    import tempfile
    from pathlib import Path
    dst = Path(dst)
    fd, tmp = tempfile.mkstemp(suffix=".docx", dir=dst.resolve().parent)
    os.close(fd)
    try:
        with zipfile.ZipFile(src) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == "word/document.xml":
                    data = new_xml.encode("utf-8")
                zout.writestr(item, data)
        os.replace(tmp, dst)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def is_real_docx(path):
    try:
        with zipfile.ZipFile(path) as z:
            return "word/document.xml" in z.namelist()
    except zipfile.BadZipFile:
        return False

# ---------------------------------------------------------------- paragraph scanning

P_TAG = re.compile(r"<w:p\b[^>]*/>|<w:p\b[^>]*>|</w:p>")


def paragraphs(xml):
    """Outermost <w:p> spans as (start, end). Handles nesting (text boxes) and <w:p/>."""
    spans, depth, start = [], 0, None
    for m in P_TAG.finditer(xml):
        tag = m.group(0)
        if tag.endswith("/>"):
            if depth == 0:
                spans.append((m.start(), m.end()))
        elif tag.startswith("</"):
            depth -= 1
            if depth == 0:
                spans.append((start, m.end()))
        else:
            if depth == 0:
                start = m.start()
            depth += 1
    return spans


def p_text(pxml):
    out = []
    for m in re.finditer(r"<w:t(?:\s[^>]*)?>(.*?)</w:t>|<w:tab/>|<w:br/>", pxml, re.S):
        if m.group(0) == "<w:tab/>":
            out.append("\t")
        elif m.group(0) == "<w:br/>":
            out.append("\n")
        else:
            out.append(unescape(m.group(1)))
    return "".join(out)


def run_rprs(pxml):
    body = re.sub(r"<w:pPr>.*?</w:pPr>", "", pxml, count=1, flags=re.S)
    rprs = []
    for m in re.finditer(r"<w:r(?:\s[^>]*)?>(.*?)</w:r>", body, re.S):
        if "<w:t" not in m.group(1):
            continue
        rp = re.search(r"<w:rPr>.*?</w:rPr>", m.group(1), re.S)
        rprs.append(rp.group(0) if rp else "")
    return rprs


def flags(pxml):
    f = []
    if "<w:drawing" in pxml or "<w:pict" in pxml:
        f.append("drawing")
    if "<w:hyperlink" in pxml:
        f.append("hyperlink")
    if "<w:fldChar" in pxml or "<w:instrText" in pxml or "<w:fldSimple" in pxml:
        f.append("field")
    if "<w:tab/>" in pxml or "\t" in p_text(pxml):
        f.append("tab")
    if len(set(run_rprs(pxml))) > 1:
        f.append("mixed-format")
    return f


def boundary(xml, anchor=None):
    """Start offset of the anchor heading paragraph (first paragraph whose text is the anchor)."""
    anchors = (anchor,) if anchor else ANCHORS
    for s, e in paragraphs(xml):
        t = p_text(xml[s:e]).strip().upper()
        if t in anchors:
            return s, t
    raise SystemExit(f"ERROR: anchor heading {anchors} not found — cannot locate header boundary.")

def text_runs(pxml):
    """[(run_start, run_end, rPr, text)] for runs that carry text or a tab, in order (offsets within pxml)."""
    ppr = re.search(r"<w:pPr>.*?</w:pPr>", pxml, re.S)
    off = ppr.end() if ppr else 0
    out = []
    for m in re.finditer(r"<w:r(?:\s[^>]*)?>(.*?)</w:r>", pxml[off:], re.S):
        inner = m.group(1)
        if "<w:t" not in inner and "<w:tab/>" not in inner:
            continue
        rp = re.search(r"<w:rPr>.*?</w:rPr>", inner, re.S)
        out.append((off + m.start(), off + m.end(), rp.group(0) if rp else "", p_text(m.group(0))))
    return out


def describe_rpr(rpr):
    tags = [n for n, t in (("bold", "<w:b/>"), ("italic", "<w:i/>"), ("underline", "<w:u "))
            if t in rpr]
    col = re.search(r'<w:color w:val="([0-9A-Fa-f]{6})"', rpr)
    if col:
        tags.append("#" + col.group(1))
    return ",".join(tags) or "plain"


def replace_in_run(pxml, old, new):
    """Replace `old` inside the single <w:t> that contains it. Keeps all formatting.
    Returns new pxml, or None if `old` is not wholly inside exactly one <w:t>."""
    hits = [m for m in re.finditer(r"(<w:t(?:\s[^>]*)?>)(.*?)(</w:t>)", pxml, re.S)
            if old in unescape(m.group(2))]
    if len(hits) != 1 or unescape(hits[0].group(2)).count(old) != 1:
        return None
    m = hits[0]
    open_t = m.group(1) if "xml:space" in m.group(1) else '<w:t xml:space="preserve">'
    new_inner = escape(unescape(m.group(2)).replace(old, new))
    return pxml[:m.start()] + open_t + new_inner + m.group(3) + pxml[m.end():]


def rebuild_segments(pxml, segments):
    """Rebuild a paragraph from segments, each borrowing the formatting of an original run:
       {"text": "...", "style_of": i}  or  {"tab": true, "style_of": i}"""
    runs = text_runs(pxml)
    open_tag = re.match(r"<w:p\b[^>]*>", pxml).group(0)
    ppr = re.search(r"<w:pPr>.*?</w:pPr>", pxml, re.S)
    parts = []
    for seg in segments:
        i = seg.get("style_of", 0)
        if not 0 <= i < len(runs):
            raise SystemExit(f"ERROR: style_of {i} out of range (paragraph has {len(runs)} runs; see dump --runs).")
        rpr = runs[i][2]
        if seg.get("tab"):
            parts.append(f"<w:r>{rpr}<w:tab/></w:r>")
        else:
            parts.append(f'<w:r>{rpr}<w:t xml:space="preserve">{escape(seg["text"])}</w:t></w:r>')
    return f"{open_tag}{ppr.group(0) if ppr else ''}{''.join(parts)}</w:p>"


# ---------------------------------------------------------------- paragraph rebuild


def rebuild(pxml, new_text):
    open_tag = re.match(r"<w:p\b[^>]*>", pxml).group(0)
    ppr = re.search(r"<w:pPr>.*?</w:pPr>", pxml, re.S)
    rprs = run_rprs(pxml)
    rpr = rprs[0] if rprs else ""
    run = f'<w:r>{rpr}<w:t xml:space="preserve">{escape(new_text)}</w:t></w:r>'
    return f"{open_tag}{ppr.group(0) if ppr else ''}{run}</w:p>"


PHONE = re.compile(r"\+?\d[\d\s()/-]{7,}\d")


def title_eligible(xml, bnd, span):
    """The title line is a header paragraph that is not the name (first text paragraph),
    not contact info, and has no image or link."""
    s, e = span
    px = xml[s:e]
    text_paras = [(a, b) for a, b in paragraphs(xml[:bnd]) if p_text(xml[a:b]).strip()]
    if text_paras and (s, e) == text_paras[0]:
        return False, "it is the name line"
    t = p_text(px)
    if "@" in t or "linkedin" in t.lower() or PHONE.search(t):
        return False, "it contains contact details"
    if "<w:drawing" in px or "<w:hyperlink" in px:
        return False, "it contains an image or link"
    return True, ""


def locate(xml, bnd, match, zone):
    hits = []
    for s, e in paragraphs(xml):
        in_header = s < bnd
        if zone == "body" and in_header:
            continue
        if zone == "title" and not in_header:
            continue
        if match in p_text(xml[s:e]):
            hits.append((s, e))
    if len(hits) != 1:
        raise SystemExit(f'ERROR: "{match}" matched {len(hits)} paragraphs in zone "{zone}" '
                         f"(need exactly 1). Nothing was written.")
    return hits[0]


def guard(pxml, op):
    bad = [f for f in flags(pxml) if f in ("drawing", "hyperlink", "field", "tab", "mixed-format")]
    if bad and not op.get("force"):
        raise SystemExit(f'ERROR: refusing {op["op"]} on "{op.get("match") or op.get("anchor")}" — '
                         f"paragraph has {bad}. Inspect with `dump`; pass \"force\": true only if "
                         f"collapsing to one run is acceptable. Nothing was written.")

# ---------------------------------------------------------------- commands


def cmd_check(path):
    if not is_real_docx(path):
        print(f"NOT A REAL WORD FILE: {path}\nIt is not a valid .docx zip (often a text/markdown export "
              f"saved with a .docx name). Stop and ask for a direct upload of the real file.")
        sys.exit(2)
    xml = read_xml(path)
    _, a = boundary(xml)
    print(f"OK: real .docx | anchor heading: {a} | language: {'English' if a in ('SUMMARY', 'PROFESSIONAL EXPERIENCE') else 'German'} "
          f"| paragraphs: {len(paragraphs(xml))}")


def cmd_dump(path, anchor=None, runs=False):
    xml = read_xml(path)
    bnd, a = boundary(xml, anchor)
    print(f"# anchor = {a}   (header = before it; only the title line is editable there)")
    for i, (s, e) in enumerate(paragraphs(xml)):
        px = xml[s:e]
        t = p_text(px).replace("\n", " ⏎ ").replace("\t", " ⇥ ")
        if not t.strip():
            continue
        z = "HDR " if s < bnd else "BODY"
        f = ",".join(flags(px))
        print(f"[{i:03d}] {z} {('{'+f+'}') if f else ''} {t}")
        if runs and ("mixed-format" in f or "tab" in f):
            for k, (_, _, rp, rt) in enumerate(text_runs(px)):
                print(f"        run {k}: ({describe_rpr(rp)}) {rt!r}")


def cmd_apply(path, ops_path, out, anchor=None):
    if not is_real_docx(path):
        cmd_check(path)
    xml = read_xml(path)
    ops = json.load(open(ops_path, encoding="utf-8"))
    title_ops = [o for o in ops if o.get("zone") == "title"]
    if len(title_ops) > 1:
        raise SystemExit("ERROR: only one title-line op is allowed.")
    for n, op in enumerate(ops, 1):
        bnd, _ = boundary(xml, anchor)
        zone = op.get("zone", "body")
        kind = op["op"]
        if zone not in ("body", "title"):
            raise SystemExit(f'ERROR: op {n}: zone must be "body" or "title".')
        if zone == "title" and kind not in ("set_text", "replace"):
            raise SystemExit(f"ERROR: op {n}: only set_text/replace are allowed on the title line.")

        if kind in ("set_text", "replace", "delete"):
            s, e = locate(xml, bnd, op["match"], zone)
            px = xml[s:e]
            if zone == "title":
                ok, why = title_eligible(xml, bnd, (s, e))
                if not ok:
                    raise SystemExit(f"ERROR: op {n}: that header paragraph is not the title line — {why}. "
                                     f"Only the title line may be edited in the header. Nothing was written.")
            if kind == "delete":
                xml = xml[:s] + xml[e:]
            else:
                if kind == "replace":
                    cur = p_text(px)
                    if cur.count(op["old"]) != 1:
                        raise SystemExit(f'ERROR: op {n}: "{op["old"]}" occurs {cur.count(op["old"])}x '
                                         f"in the matched paragraph (need 1).")
                    in_run = replace_in_run(px, op["old"], op["new"])
                    if in_run is not None:          # formatting fully preserved
                        xml = xml[:s] + in_run + xml[e:]
                    else:                           # spans runs: only safe if paragraph is uniform
                        if flags(px) and not op.get("force"):
                            raise SystemExit(f'ERROR: op {n}: "{op["old"]}" spans several runs in a formatted '
                                             f"paragraph. Use a shorter \"old\" that sits inside one run, or "
                                             f"set_segments. Nothing was written.")
                        xml = xml[:s] + rebuild(px, cur.replace(op["old"], op["new"])) + xml[e:]
                else:
                    guard(px, op)
                    xml = xml[:s] + rebuild(px, op["text"]) + xml[e:]
        elif kind == "set_segments":
            s, e = locate(xml, bnd, op["match"], zone)
            px = xml[s:e]
            if "<w:drawing" in px or "<w:hyperlink" in px:
                raise SystemExit(f"ERROR: op {n}: set_segments refused — paragraph has an image or link.")
            xml = xml[:s] + rebuild_segments(px, op["segments"]) + xml[e:]
            op["text"] = "".join("\t" if g.get("tab") else g["text"] for g in op["segments"])
        elif kind == "insert_after":
            s_like, e_like = locate(xml, bnd, op["like"], "body")
            like = xml[s_like:e_like]
            guard(like, {"op": kind, "anchor": op["like"], "force": op.get("force")})
            _, e_anchor = locate(xml, bnd, op["anchor"], "body")
            xml = xml[:e_anchor] + rebuild(like, op["text"]) + xml[e_anchor:]
        else:
            raise SystemExit(f'ERROR: op {n}: unknown op "{kind}".')
        print(f"  ✓ op {n}: {kind} [{zone}] {op.get('match') or op.get('anchor')}")

    # post-condition, checked in memory BEFORE anything is written: every new text is present
    texts = [p_text(xml[s:e]) for s, e in paragraphs(xml)]
    for op in ops:
        if op["op"] in ("set_text", "insert_after", "set_segments"):
            ensure(op["text"] in texts, f'post-check failed: "{op["text"][:60]}…" not found as a paragraph')
        if op["op"] == "delete":
            ensure(not any(op["match"] in t for t in texts), f'post-check failed: "{op["match"]}" still present')
    write_docx(path, out, xml)
    print(f"Wrote {out} — all post-checks passed.")


def cmd_verify(orig, edited, anchor=None):
    ox, nx = read_xml(orig), read_xml(edited)
    ob, _ = boundary(ox, anchor)
    nb, _ = boundary(nx, anchor)
    oh, nh = ox[:ob], nx[:nb]
    if oh == nh:
        print("HEADER CHECK PASSED: byte-identical.")
        return
    # allow exactly one differing paragraph (the title line), text-only difference
    op, np_ = paragraphs(oh), paragraphs(nh)
    if len(op) != len(np_):
        raise SystemExit("HEADER CHECK FAILED: paragraph count in header changed.")
    diffs = [(a, b) for a, b in zip(op, np_) if oh[a[0]:a[1]] != nh[b[0]:b[1]]]
    if len(diffs) != 1:
        raise SystemExit(f"HEADER CHECK FAILED: {len(diffs)} header paragraphs differ (max 1: the title).")
    (a, b), = diffs
    restored = nh[:b[0]] + oh[a[0]:a[1]] + nh[b[1]:]
    if restored != oh:
        raise SystemExit("HEADER CHECK FAILED: differences outside the title paragraph.")
    old_px, new_px = oh[a[0]:a[1]], nh[b[0]:b[1]]
    ok, why = title_eligible(ox, ob, a)
    if not ok:
        raise SystemExit(f"HEADER CHECK FAILED: the changed header paragraph is not the title line — {why}.")
    print("HEADER CHECK PASSED: identical except the title line —")
    print(f"   before: {p_text(old_px)}\n   after : {p_text(new_px)}")


def cmd_text(path):
    xml = read_xml(path)
    for s, e in paragraphs(xml):
        t = p_text(xml[s:e])
        if t.strip():
            print(t)


def run():
    a = sys.argv[1:]
    anchor = None
    show_runs = "--runs" in a
    if show_runs:
        a.remove("--runs")
    if "--anchor" in a:
        i = a.index("--anchor")
        anchor = a[i + 1].upper()
        del a[i:i + 2]
    if not a:
        print(__doc__)
        sys.exit(0)
    cmd, args = a[0], a[1:]
    need = {"check": (1, (".docx",)), "dump": (1, (".docx",)), "text": (1, (".docx",)),
            "apply": (3, (".docx", ".json", ".docx")), "verify": (2, (".docx", ".docx"))}
    if cmd in need:
        n, exts = need[cmd]
        if len(args) != n or any(not str(x).lower().endswith(e) for x, e in zip(args, exts)):
            usage = {"check": "inspect <doc.docx>", "dump": "dump <doc.docx> [--runs]", "text": "text <doc.docx>",
                     "apply": "edit <doc.docx> <ops.json> <out.docx>",
                     "verify": "header-diff <original.docx> <edited.docx>"}[cmd]
            sys.exit(f"usage: docproof {usage}\n\n" + __doc__)
    {"check": lambda: cmd_check(*args),
     "dump": lambda: cmd_dump(*args, anchor=anchor, runs=show_runs),
     "apply": lambda: cmd_apply(*args, anchor=anchor),
     "verify": lambda: cmd_verify(*args, anchor=anchor),
     "text": lambda: cmd_text(*args)}.get(cmd, lambda: print(__doc__))()


if __name__ == "__main__":
    run()
