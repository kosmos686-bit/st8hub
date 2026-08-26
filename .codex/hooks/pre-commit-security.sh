#!/bin/bash
# Blocks git commits containing hardcoded API tokens/secrets

# Parse tool input from Claude Code hook JSON
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('tool_input', {}).get('command', ''))
except:
    print('')
" 2>/dev/null)

# Only intercept git commit commands
if ! echo "$COMMAND" | grep -qE "git commit"; then
    exit 0
fi

# Get staged files content via git index
STAGED_FILES=$(git diff --cached --name-only 2>/dev/null)
if [ -z "$STAGED_FILES" ]; then
    exit 0
fi

VIOLATIONS=""

for FILE in $STAGED_FILES; do
    # Read staged content (from git index, not working tree)
    CONTENT=$(git show ":$FILE" 2>/dev/null) || continue

    # Anthropic API key: sk-ant-api03-...
    if echo "$CONTENT" | grep -qP 'sk-ant-api[0-9]+-[A-Za-z0-9_\-]{20,}'; then
        VIOLATIONS="$VIOLATIONS\n  ❌ Anthropic API key in $FILE"
    fi

    # Telegram bot token: 10digits:35chars
    if echo "$CONTENT" | grep -qP '\b[0-9]{8,10}:[A-Za-z0-9_\-]{35}\b'; then
        VIOLATIONS="$VIOLATIONS\n  ❌ Telegram bot token in $FILE"
    fi

    # GitHub token patterns (ghp_, gho_, github_pat_)
    if echo "$CONTENT" | grep -qP '(ghp_|gho_|ghu_|ghs_|github_pat_)[A-Za-z0-9_]{20,}'; then
        VIOLATIONS="$VIOLATIONS\n  ❌ GitHub token in $FILE"
    fi

    # Generic high-entropy AAAA-style base64 secrets (min 40 chars, mixed case+digits)
    if echo "$CONTENT" | grep -qP '"[A-Za-z0-9+/]{40,}={0,2}"'; then
        VIOLATIONS="$VIOLATIONS\n  ⚠️  Possible base64 secret in $FILE (review manually)"
    fi

    # Hardcoded password patterns
    if echo "$CONTENT" | grep -qiP '(password|passwd|secret)\s*=\s*"[^"]{6,}"'; then
        VIOLATIONS="$VIOLATIONS\n  ❌ Hardcoded password/secret in $FILE"
    fi
done

if [ -n "$VIOLATIONS" ]; then
    MSG="🚫 COMMIT BLOCKED — hardcoded secrets detected:$(echo -e "$VIOLATIONS")\n\nFix: move to .env and use os.getenv()"
    echo "$MSG" >&2
    # Output Claude Code block decision
    python3 -c "
import json, sys
msg = sys.argv[1]
print(json.dumps({'decision': 'block', 'reason': msg}))
" "$MSG"
    exit 1
fi

exit 0
