"""docproof init — set up a private workspace for your own documents.

  docproof init [DIR]        (default: the current folder)

Creates DIR/profile/fact-base.md and DIR/profile/resume.json from templates, plus DIR/applications/
for tailored output. Never overwrites an existing file. Keep DIR private — if it is inside a clone of
this repository, profile/ and applications/ are already git-ignored.
"""
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if a and a[0] in ("-h", "--help"):
        sys.exit(__doc__)
    root = Path(a[0] if a else ".").resolve()
    (root / "profile").mkdir(parents=True, exist_ok=True)
    (root / "applications").mkdir(exist_ok=True)
    for name in ("fact-base.md", "resume.json"):
        dst = root / "profile" / name
        if dst.exists():
            print(f"exists, kept: {dst}")
        else:
            shutil.copy(HERE / "templates" / name, dst)
            print(f"created:      {dst}")
    print(f"""
Next:
  1. Fill in {root / 'profile' / 'fact-base.md'} — every fact you may ever claim, plus your Known gaps.
  2. Fill in {root / 'profile' / 'resume.json'}, then:
       docproof build {root / 'profile' / 'resume.json'} {root / 'profile' / 'base.docx'}
       docproof check {root / 'profile' / 'base.docx'} --png {root / 'profile' / 'png'}
       docproof verify {root / 'profile' / 'base.docx'} --facts {root / 'profile' / 'fact-base.md'}
  3. For a job ad: docproof match ad.txt --facts profile/fact-base.md
     then tailor with Claude Code (/tailor) or any assistant (docproof prompt tailor …).""")


if __name__ == "__main__":
    main()
