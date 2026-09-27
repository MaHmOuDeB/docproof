import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EX = ROOT / "examples"
FACTS = EX / "profile" / "fact-base.md"
ENV = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
sys.path.insert(0, str(ROOT / "src"))


def dp(*args, check=True):
    r = subprocess.run([sys.executable, "-m", "docproof", *map(str, args)], capture_output=True, text=True, env=ENV)
    if check and r.returncode:
        raise AssertionError(f"docproof {' '.join(map(str, args))} failed:\n{r.stdout}\n{r.stderr}")
    return r


def have_chrome():
    try:
        from docproof.render import find_chrome
        find_chrome()
        return shutil.which("pdftotext") is not None
    except SystemExit:
        return False


def xml(docx):
    with zipfile.ZipFile(docx) as z:
        return z.read("word/document.xml").decode()


class Workdir:
    def __enter__(self):
        self.d = Path(tempfile.mkdtemp(prefix="docproof-test-"))
        self.cv = self.d / "cv.docx"
        dp("build", EX / "resume.json", self.cv)
        return self

    def __exit__(self, *exc):
        shutil.rmtree(self.d, ignore_errors=True)

    def p(self, name):
        return self.d / name
