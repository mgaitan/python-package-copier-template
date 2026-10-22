#!/bin/sh
set -eu

if ! command -v gh >/dev/null 2>&1; then
    echo "Error: install and authenticate gh before configuring Dependabot." >&2
    exit 1
fi

repo="${1:-}"
if [ -z "$repo" ]; then
    repo=$(gh repo view --json nameWithOwner --jq .nameWithOwner)
fi

for feature in vulnerability-alerts automated-security-fixes; do
    if ! gh api --method PUT \
        -H "Accept: application/vnd.github+json" \
        -H "X-GitHub-Api-Version: 2026-03-10" \
        "repos/${repo}/${feature}" >/dev/null; then
        echo "Error: could not enable ${feature} for ${repo}. Check gh authentication, repository administration permissions, and organization policies; retry with make dependabot." >&2
        exit 1
    fi
done

echo "Dependabot alerts, dependency graph, and security updates enabled for ${repo}."
