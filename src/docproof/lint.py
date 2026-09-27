"""docproof lint — catch stale facts and rules in your own skill, agent and prompt files.

  docproof lint <path> [<path> …] --rules rules.json

Every time you correct a fact or a rule, older files tend to keep contradicting it. Put each
correction in a rules file and run this after every edit; exit code 1 on any hit.

rules.json: [{"pattern": "<regex>", "fix": "<what is correct now>"}, …]
A line containing the marker `lint-ok` (or quoting the old value on purpose, e.g. "old: …",
"never …", "→") is ignored, so a rules/conflicts table can quote stale phrasing.
"""
import json
import re
import sys
from pathlib import Path

IGNORE = re.compile(r"lint-ok|\bnever\b|→|superseded|instead of|\bold\b|\bwas\b|\bwere\b", re.I)
SUFFIXES = {".md", ".py", ".txt", ".json", ".yaml", ".yml"}


def load_rules(path):
    rules = json.loads(Path(path).read_text(encoding="utf-8"))
    return [(re.compile(r["pattern"], re.I), r["fix"]) for r in rules]


def scan(roots, rules, skip=()):
    hits = []
    for root in map(Path, roots):
        files = [root] if root.is_file() else sorted(p for p in root.rglob("*") if p.is_file())
        for f in files:
            if f.suffix not in SUFFIXES or f.resolve() in skip:
                continue
            for n, line in enumerate(f.read_text(errors="ignore").splitlines(), 1):
                if IGNORE.search(line):
                    continue
                for pat, fix in rules:
                    if pat.search(line):
                        hits.append((f, n, line.strip(), fix))
    return hits


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if "--rules" not in a or a.index("--rules") + 1 >= len(a):
        sys.exit(__doc__)
    i = a.index("--rules")
    rules_path = a[i + 1]
    del a[i:i + 2]
    if not a:
        sys.exit(__doc__)
    hits = scan(a, load_rules(rules_path), skip={Path(rules_path).resolve()})
    for f, n, line, fix in hits:
        print(f"{f}:{n}: {line[:110]}\n    → {fix}")
    print(f"\n{len(hits)} stale hit(s)" if hits else "LINT CLEAN: no stale phrases found")
    sys.exit(1 if hits else 0)


if __name__ == "__main__":
    main()
