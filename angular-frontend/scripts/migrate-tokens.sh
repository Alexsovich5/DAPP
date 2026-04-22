#!/usr/bin/env bash
# One-shot migration: rename legacy CSS custom properties to new --color-* tokens.
# Run from repo root: bash angular-frontend/scripts/migrate-tokens.sh

set -euo pipefail

ROOT="angular-frontend/src"

FILES=$(grep -rl --include='*.scss' --include='*.ts' --include='*.html' \
  -e '--emotional-primary' \
  -e '--emotional-accent' \
  -e '--emotional-danger' \
  -e '--emotional-warning' \
  -e '--df-primary' \
  -e '--df-accent' \
  -e '--df-bg' \
  -e '--df-surface' \
  -e '--df-text' \
  -e '--text-primary' \
  -e '--text-secondary' \
  -e '--surface-primary' \
  -e '--surface-secondary' \
  "$ROOT" || true)

if [ -z "$FILES" ]; then
  echo "No files to migrate."
  exit 0
fi

echo "Migrating:"
echo "$FILES"

for f in $FILES; do
  # Order matters: longer names first so prefixes don't swallow suffixes.
  sed -i.bak \
    -e 's/--emotional-primary-hover/--color-primary-hover/g' \
    -e 's/--emotional-primary/--color-primary/g' \
    -e 's/--emotional-accent-soft/--color-accent-soft/g' \
    -e 's/--emotional-accent/--color-accent/g' \
    -e 's/--emotional-danger/--color-danger/g' \
    -e 's/--emotional-warning/--color-warning/g' \
    -e 's/--df-primary/--color-primary/g' \
    -e 's/--df-accent/--color-accent/g' \
    -e 's/--df-bg/--color-bg/g' \
    -e 's/--df-surface/--color-surface/g' \
    -e 's/--df-text-muted/--color-text-muted/g' \
    -e 's/--df-text/--color-text/g' \
    -e 's/--text-primary/--color-text/g' \
    -e 's/--text-secondary/--color-text-muted/g' \
    -e 's/--surface-primary/--color-surface/g' \
    -e 's/--surface-secondary/--color-surface-alt/g' \
    "$f"
  rm -f "${f}.bak"
done

echo "Done. Review with: git diff"
