#!/usr/bin/env bash
# Fails the build if emoji characters appear in non-messaging source files.
# Spec success criterion: "Zero unintentional emoji in code
# (grep yields only angular-frontend/src/app/features/messaging/ matches)."

set -euo pipefail

# Emoji Unicode ranges covered by this pattern (ripgrep Unicode):
#   \p{Emoji} covers all Unicode emoji codepoints
# We use ripgrep (rg) for portable Unicode support on macOS and Linux.
PATTERN='[\x{1F300}-\x{1FAFF}\x{2600}-\x{27BF}\x{FE0F}]'

# Search the frontend sources, excluding the messaging feature (reactions are intentional).
MATCHES=$(rg \
  --glob '*.ts' \
  --glob '*.html' \
  --glob '*.scss' \
  --glob '!**/messaging/**' \
  -e "$PATTERN" \
  angular-frontend/src 2>&1 || true)

if [ -n "$MATCHES" ]; then
  echo "ERROR: Emoji found outside messaging feature:"
  echo "$MATCHES"
  exit 1
fi

echo "OK: no emoji outside messaging feature."
