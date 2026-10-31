#!/usr/bin/env bash
# Stop: sweep everything this turn changed before the agent finishes, one retry.
#   frontend/ changed -> oxlint on the changed files, the UI-literals rule, tsc -b, the whole
#                        Vitest suite (~30 s, so it also catches a test of a module only imported)
#   backend/ changed  -> ./mvnw test-compile (the Testcontainers suite is the commit gate's job)
export NO_COLOR=1 FORCE_COLOR=0
command -v jq >/dev/null || { echo "Hook end-of-turn.sh needs jq: install it or port the hook to Node." >&2; exit 2; }

INPUT=$(cat)

# Already sent back once by this hook: let it finish. The commit gate catches the rest.
# (loop_count covers Cursor, which imports this hook from .claude/settings.json.)
ACTIVE=$(printf '%s' "$INPUT" | jq -r '.stop_hook_active // false' 2>/dev/null)
LOOPS=$(printf '%s' "$INPUT" | jq -r '.loop_count // 0' 2>/dev/null)
if [ "$ACTIVE" = "true" ] || [ "${LOOPS:-0}" != "0" ]; then
  exit 0
fi

# Checkouts to sweep: the session's (payload cwd follows EnterWorktree, $CLAUDE_PROJECT_DIR
# does not) plus every checkout lint-edited-file.sh registered for this session.
CWD=$(printf '%s' "$INPUT" | jq -r '.cwd // empty' 2>/dev/null)
SID=$(printf '%s' "$INPUT" | jq -r '.session_id // empty' 2>/dev/null | tr -cd 'A-Za-z0-9_-')
REGISTRY="${TMPDIR:-/tmp}/claude-hooks/${SID:-none}.roots"
ROOTS=()
while IFS= read -r r; do
  [ -n "$r" ] && [ -d "$r" ] && ROOTS+=("$r")
done <<EOF
$({ git -C "${CWD:-$PWD}" rev-parse --show-toplevel 2>/dev/null; [ -n "$SID" ] && cat "$REGISTRY" 2>/dev/null; } | sort -u)
EOF
if [ "${#ROOTS[@]}" -eq 0 ]; then
  # Not silent: the user sees why nothing was checked.
  jq -cn --arg m "end-of-turn.sh: no git checkout at ${CWD:-$PWD}, nothing checked." '{systemMessage: $m}'
  exit 0
fi

REPORT=""
for ROOT in "${ROOTS[@]}"; do
  cd "$ROOT" || continue

  # Changed and new files. Nothing changed (a Q&A turn): nothing to check here.
  # This also catches files rewritten through a shell command, which never reach a per-edit hook.
  CHANGED=$({ git diff --name-only HEAD; git ls-files -o --exclude-standard; } 2>/dev/null | sort -u)
  [ -n "$CHANGED" ] || continue

  if printf '%s\n' "$CHANGED" | grep -q '^frontend/'; then
    LINT=()
    while IFS= read -r f; do
      case "$f" in
        frontend/*.ts|frontend/*.tsx|frontend/*.mts|frontend/*.cts|frontend/*.js|frontend/*.jsx|frontend/*.mjs|frontend/*.cjs)
          [ -f "$f" ] && LINT+=("${f#frontend/}") ;;
      esac
    done <<EOF
$CHANGED
EOF
    cd "$ROOT/frontend" || continue
    if [ "${#LINT[@]}" -gt 0 ]; then
      OUT=$(node_modules/.bin/oxlint --deny-warnings "${LINT[@]}" 2>&1 </dev/null) || REPORT="$REPORT
oxlint errors in changed files ($ROOT/frontend):
$OUT
"
    fi
    OUT=$(node scripts/check-ui-literals.mjs 2>&1 </dev/null) || REPORT="$REPORT
check-ui-literals ($ROOT/frontend; use a colour role or theme.other from src/theme.ts):
$OUT
"
    OUT=$(node_modules/.bin/tsc -b --pretty false 2>&1 </dev/null) || REPORT="$REPORT
Typecheck fails ($ROOT/frontend, tsc -b):
$OUT
"
    # DEBUG_PRINT_LIMIT=0: Testing Library drops the DOM dump from a failed query's error.
    if ! OUT=$(DEBUG_PRINT_LIMIT=0 node_modules/.bin/vitest run 2>&1 </dev/null); then
      # The failures and the summary, not the whole log.
      SHORT=$(printf '%s\n' "$OUT" | grep --color=never -E -A12 'FAIL|Error|✗|×' | head -n 80)
      OUT=${SHORT:-$(printf '%s\n' "$OUT" | tail -n 40)}
      REPORT="$REPORT
Frontend tests fail ($ROOT/frontend, vitest run):
$OUT
"
    fi
    cd "$ROOT" || continue
  fi

  if printf '%s\n' "$CHANGED" | grep -qE '^backend/(src/|pom\.xml$)'; then
    cd "$ROOT/backend" || continue
    if ! OUT=$(./mvnw -B -q test-compile 2>&1 </dev/null); then
      OUT=$(printf '%s\n' "$OUT" | grep --color=never -E '^\[ERROR\]' | head -n 40)
      REPORT="$REPORT
Backend does not compile ($ROOT/backend, ./mvnw test-compile):
${OUT:-./mvnw failed without an [ERROR] line; run it to see why.}
"
    fi
    cd "$ROOT" || continue
  fi
done

if [ -n "$REPORT" ]; then
  echo "Fix these before you finish:$REPORT" >&2
  exit 2
fi
# Green: the registered checkouts are clean, start the next turn with an empty registry.
[ -n "$SID" ] && [ -f "$REGISTRY" ] && : >"$REGISTRY"
exit 0
