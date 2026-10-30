#!/usr/bin/env bash
# PostToolUse (Write|Edit): lint the frontend file the agent just edited — oxlint and the
# UI-literals rule (CLAUDE.md "UI"), both on that file only. Exit 2 + stderr is the only
# combination Claude sees. Whole-project checks (tsc, tests, backend) run in end-of-turn.sh.
export NO_COLOR=1 FORCE_COLOR=0
command -v jq >/dev/null || { echo "Hook lint-edited-file.sh needs jq: install it or port the hook to Node." >&2; exit 2; }

INPUT=$(cat)
FILE=$(printf '%s' "$INPUT" | jq -r '.tool_input.file_path // .tool_input.notebook_path // empty' 2>/dev/null)
CWD=$(printf '%s' "$INPUT" | jq -r '.cwd // empty' 2>/dev/null)
[ -n "$FILE" ] || exit 0
case "$FILE" in /*) ;; *) FILE="${CWD:-$PWD}/$FILE" ;; esac
[ -f "$FILE" ] || exit 0

# Checkout of the edited file, not $CLAUDE_PROJECT_DIR (stale after EnterWorktree, wrong for a
# sibling worktree). Files of other repositories (~/.claude, other projects) are skipped.
ROOT=$(git -C "$(dirname "$FILE")" rev-parse --show-toplevel 2>/dev/null) || exit 0
REPO=$(git -C "$ROOT" rev-parse --path-format=absolute --git-common-dir 2>/dev/null)
SESSION_REPO=$(git -C "${CWD:-$PWD}" rev-parse --path-format=absolute --git-common-dir 2>/dev/null)
[ -n "$REPO" ] && [ "$REPO" = "$SESSION_REPO" ] || exit 0

# Register the checkout so the Stop hook sweeps it too, even when it is not the session cwd.
SID=$(printf '%s' "$INPUT" | jq -r '.session_id // empty' 2>/dev/null | tr -cd 'A-Za-z0-9_-')
if [ -n "$SID" ] && mkdir -p "${TMPDIR:-/tmp}/claude-hooks"; then
  printf '%s\n' "$ROOT" >>"${TMPDIR:-/tmp}/claude-hooks/$SID.roots"
fi

# Only the frontend has per-edit checks; backend Java is compiled at end of turn.
REL=${FILE#"$ROOT"/frontend/}
[ "$REL" != "$FILE" ] || exit 0
case "$REL" in node_modules/*|dist/*) exit 0 ;; esac
cd "$ROOT/frontend" || exit 0

REPORT=""
case "$REL" in
  *.ts|*.tsx|*.mts|*.cts|*.js|*.jsx|*.mjs|*.cjs)
    # Local binary, no npx: an uninstalled linter fails here (exit 2) instead of passing.
    # --deny-warnings: oxlint reports its default rules (no-debugger, no-unused-vars, use-isnan)
    # as warnings with exit 0; the tree has none, so any warning here is new.
    OUT=$(node_modules/.bin/oxlint --deny-warnings "$REL" 2>&1 </dev/null) || REPORT="$REPORT
oxlint:
$OUT
"
    ;;
esac

# The UI-literals rule reads its own file list in a few ms; keep only the edited file's lines.
# A failure without any "path:line:" line is the script itself breaking (e.g. a listed file
# was renamed): report it whole.
case "$REL" in
  src/*.ts|src/*.tsx|src/*.css)
    if ! OUT=$(node scripts/check-ui-literals.mjs 2>&1 </dev/null); then
      MINE=$(printf '%s\n' "$OUT" | grep --color=never -F "$REL:")
      if [ -n "$MINE" ]; then
        REPORT="$REPORT
check-ui-literals (use a colour role or theme.other from src/theme.ts):
$MINE
"
      elif ! printf '%s\n' "$OUT" | grep -qE '^[^ ]+:[0-9]+: '; then
        REPORT="$REPORT
check-ui-literals could not run:
$OUT
"
      fi
    fi
    ;;
esac

if [ -n "$REPORT" ]; then
  echo "Lint errors in frontend/$REL:$REPORT" >&2
  exit 2
fi
exit 0
