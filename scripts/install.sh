#!/usr/bin/env bash
# Copy docproof's Claude Code skill, agents and command into ~/.claude (or ./.claude with --project).
# Existing files with the same name are left alone unless you pass --force.
set -euo pipefail
cd "$(dirname "$0")/.."
DEST="$HOME/.claude"; FORCE=0
for a in "$@"; do
  case "$a" in
    --project) DEST="$PWD/.claude" ;;
    --force)   FORCE=1 ;;
    *) echo "usage: scripts/install.sh [--project] [--force]"; exit 2 ;;
  esac
done
copy() {  # src dst
  if [ -e "$2" ] && [ "$FORCE" -eq 0 ]; then echo "skip (exists): $2   — re-run with --force to overwrite"; return; fi
  mkdir -p "$(dirname "$2")"; rm -rf "$2"; cp -R "$1" "$2"; echo "installed: $2"
}
copy claude/skills/doc-craft             "$DEST/skills/doc-craft"
copy claude/agents/document-tailor.md    "$DEST/agents/document-tailor.md"
copy claude/agents/claim-auditor.md      "$DEST/agents/claim-auditor.md"
copy claude/agents/fresh-eyes-reviewer.md "$DEST/agents/fresh-eyes-reviewer.md"
copy claude/commands/tailor.md           "$DEST/commands/tailor.md"
if ! command -v docproof >/dev/null 2>&1; then
  echo; echo "Next: install the CLI with  pip install -e .  (from this folder)"
fi
echo; echo "Point the agents at your fact base, e.g. add to ~/.claude/CLAUDE.md:"
echo "  docproof fact base: ~/career/fact-base.md"
echo "Agents load when a Claude Code session starts — open a new session to use them."
