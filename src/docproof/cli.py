"""docproof — fact-grounded documents with automated verification.

Usage: docproof <command> [args]   (docproof <command> with no args prints its help)

Build and render
  build        <resume.json> <out.docx>             JSON → .docx in the house template
  render       <doc.docx> [--out out.pdf] [--png DIR]   designed PDF (Inter, headless Chrome)
  check        <doc.docx> [--orig base.docx] [--png DIR]  full layout/integrity verification

Verify against the facts
  verify       <doc.docx> --facts fact-base.md       every figure traces to the fact base; no known gap claimed
  match        <job-ad.txt> --facts fact-base.md     requirement → evidence map, coverage %, gaps

Edit safely (every command proves that only the intended part changed)
  dump         <doc.docx> [--runs]                   list paragraphs — always dump before writing ops
  edit         <doc.docx> <ops.json> <out.docx>      set_text / replace / delete / set_segments / insert_after
  keywords     <in.docx> <out.docx> <spec.json>      bold 1–2 key phrases per bullet
  reorder      <in.docx> <out.docx> sections "A,B,…" | move "<para>" "<before>"
  add-entry    <in.docx> <out.docx> <entry.json>     new title ⇥ date line + bullets + meta line
  add-link     <in.docx> <out.docx> "<prefix>" "Label" <url>
  add-summary  <in.docx> <out.docx> HEADING "text" BEFORE_HEADING
  set-metadata <in.docx> <out.docx> "Title" "Author"
  text | inspect | header-diff                        plain text / sanity check / header byte-identity

Maintenance
  lint         <paths…> --rules rules.json          stale-phrase linter for your own skill files
  doctor                                            check Chrome, poppler and fonts
  demo         [--out DIR]                          build → check → verify → match on the example
"""
import importlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

# command → (module, entry function, argv prefix passed to the module)
COMMANDS = {
    "build": ("build", "main", []),
    "render": ("render", "run", []),
    "check": ("check", "run_cli", []),
    "verify": ("verify", "main", []),
    "match": ("match", "main", []),
    "dump": ("edit", "run", ["dump"]),
    "edit": ("edit", "run", ["apply"]),
    "text": ("edit", "run", ["text"]),
    "inspect": ("edit", "run", ["check"]),
    "header-diff": ("edit", "run", ["verify"]),
    "keywords": ("keywords", "run", []),
    "reorder": ("reorder", "run", []),
    "add-entry": ("add_entry", "run", []),
    "add-link": ("add_link", "main", []),
    "add-summary": ("add_summary", "run", []),
    "set-metadata": ("metadata", "main", []),
    "lint": ("lint", "main", []),
}
HERE = Path(__file__).resolve().parent


def doctor():
    ok = True
    from docproof.render import find_chrome
    try:
        print("chrome   :", find_chrome())
    except SystemExit as e:
        ok = False
        print("chrome   : MISSING —", e)
    for tool in ("pdftotext", "pdfinfo", "pdftoppm"):
        path = shutil.which(tool)
        print(f"{tool:<9}:", path or "missing (install poppler; pypdf fallback covers text, not PNG previews)")
    try:
        import pypdf  # noqa: F401
        print("pypdf    : installed")
    except ImportError:
        print("pypdf    : not installed (only needed without poppler)")
    fonts = sorted(p.name for p in (HERE / "assets" / "fonts").glob("*.woff2"))
    print("fonts    :", ", ".join(fonts) or "MISSING")
    ok = ok and bool(fonts) and (shutil.which("pdftotext") is not None or _has("pypdf"))
    print("\nREADY" if ok else "\nNOT READY — fix the lines above")
    return 0 if ok else 1


def _has(mod):
    try:
        importlib.import_module(mod)
        return True
    except ImportError:
        return False


def examples_dir():
    for p in (HERE / "examples", HERE.parents[1] / "examples", Path.cwd() / "examples"):
        if (p / "resume.json").exists():
            return p
    sys.exit("examples/ not found — run the demo from a clone of the repository")


def demo(argv):
    ex = examples_dir()
    out = Path(argv[argv.index("--out") + 1] if "--out" in argv else "docproof-demo").resolve()
    out.mkdir(parents=True, exist_ok=True)
    dp = [sys.executable, "-m", "docproof"]
    docx = out / "resume.docx"
    steps = [
        ("build", dp + ["build", str(ex / "resume.json"), str(docx)]),
        ("check", dp + ["check", str(docx), "--png", str(out)]),
        ("verify", dp + ["verify", str(docx), "--facts", str(ex / "profile" / "fact-base.md")]),
        ("match", dp + ["match", str(ex / "jobs" / "experimentation-analyst.txt"),
                        "--facts", str(ex / "profile" / "fact-base.md")]),
    ]
    failed = []
    for name, cmd in steps:
        print(f"\n━━ {name} ━━", flush=True)
        code = subprocess.run(cmd, env={**os.environ, "PYTHONPATH": str(HERE.parent)}).returncode
        if code:
            failed.append(name)
    print(f"\nDemo output in {out}" + (f" — FAILED: {', '.join(failed)}" if failed else " — all steps passed"))
    return 1 if failed else 0


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if not a or a[0] in ("-h", "--help", "help"):
        print(__doc__)
        return
    if a[0] in ("-V", "--version"):
        from docproof import __version__
        print(__version__)
        return
    cmd, rest = a[0], a[1:]
    if cmd == "doctor":
        sys.exit(doctor())
    if cmd == "demo":
        sys.exit(demo(rest))
    if cmd not in COMMANDS:
        sys.exit(f"unknown command {cmd!r}\n\n{__doc__}")
    mod, fn, prefix = COMMANDS[cmd]
    module = importlib.import_module(f"docproof.{mod}")
    sys.argv = [f"docproof {cmd}"] + prefix + rest
    getattr(module, fn)()


if __name__ == "__main__":
    main()
