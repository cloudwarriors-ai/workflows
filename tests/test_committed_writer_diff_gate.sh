#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKFLOW="$ROOT/.github/workflows/reusable-claude-autofix-rlm.yml"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

git -C "$TMP" init -q
git -C "$TMP" config user.name "Regression Test"
git -C "$TMP" config user.email "regression@example.invalid"
printf 'base\n' > "$TMP/base.txt"
git -C "$TMP" add base.txt
git -C "$TMP" commit -qm "base"
BASE_SHA="$(git -C "$TMP" rev-parse HEAD)"

# Reproduce the live failure: the writer commits its product change, leaving a
# clean worktree. `git status --porcelain` is empty, but the base-relative diff
# must still classify the result as reviewable.
printf 'Praxis channel conversation verified.\n' > "$TMP/canary.md"
git -C "$TMP" add canary.md
git -C "$TMP" commit -qm "writer commits before returning"

test -z "$(git -C "$TMP" status --porcelain)"
if git -C "$TMP" diff --quiet "$BASE_SHA" --; then
  echo "committed writer diff was not detected" >&2
  exit 1
fi

grep -Fq 'base_sha=$BASE_SHA' "$WORKFLOW"
grep -Fq 'git diff --quiet "$BASE_SHA" --' "$WORKFLOW"
grep -Fq 'BASE_SHA: ${{ steps.branch.outputs.base_sha }}' "$WORKFLOW"

echo "committed writer diff gate: PASS"
