#!/usr/bin/env bash
set -euo pipefail

if [ ! -d .git ]; then
  echo "Run this from the BatLLM repository root." >&2
  exit 1
fi

git checkout -b chore/audit-ci-security-state-docs
cp -R .github docs SECURITY.md PR_TITLE.txt PR_BODY.md .
git add .
git commit -m "chore: add audit-driven CI security and state documentation"

echo "Branch created: chore/audit-ci-security-state-docs"
echo "Open the PR with:"
echo "gh pr create --title \"$(cat PR_TITLE.txt)\" --body-file PR_BODY.md"
