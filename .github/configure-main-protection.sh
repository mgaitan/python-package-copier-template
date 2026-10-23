#!/bin/sh
set -eu

if ! command -v gh >/dev/null 2>&1; then
    echo "Error: install and authenticate gh before configuring main protection." >&2
    exit 1
fi

github_api() {
    gh api -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2026-03-10" "$@"
}

repo="${1:-}"
if [ -z "$repo" ]; then
    repo=$(gh repo view --json nameWithOwner --jq .nameWithOwner)
fi

if ! github_api "repos/${repo}/branches/main" >/dev/null; then
    echo "Error: could not find main for ${repo}. Check gh authentication and push the initial main branch before retrying." >&2
    exit 1
fi

endpoint="repos/${repo}/rulesets"
if ! ruleset_id=$(github_api --paginate "${endpoint}?includes_parents=false&per_page=100" \
    --jq '.[] | select(.name == "python-package-template-main" and .source_type == "Repository") | .id'); then
    echo "Error: could not read rulesets for ${repo}. Check gh authentication and repository permissions." >&2
    exit 1
fi

case "$ruleset_id" in
    "") method=POST ;;
    *[!0-9]*)
        echo "Error: multiple python-package-template-main rulesets found for ${repo}. Resolve duplicates before retrying." >&2
        exit 1
        ;;
    *) method=PUT; endpoint="${endpoint}/${ruleset_id}" ;;
esac

if ! github_api --method "$method" "$endpoint" --input - >/dev/null <<'JSON'
{
  "name": "python-package-template-main",
  "target": "branch",
  "enforcement": "active",
  "bypass_actors": [],
  "conditions": {
    "ref_name": {"include": ["refs/heads/main"], "exclude": []}
  },
  "rules": [
    {"type": "deletion"},
    {"type": "non_fast_forward"},
    {
      "type": "pull_request",
      "parameters": {
        "dismiss_stale_reviews_on_push": true,
        "require_code_owner_review": false,
        "require_last_push_approval": false,
        "required_approving_review_count": 0,
        "required_review_thread_resolution": true
      }
    }
  ]
}
JSON
then
    echo "Error: could not protect main for ${repo}. Check Administration: write permission, organization policies, and GitHub plan support for rulesets; retry with make protect-main." >&2
    exit 1
fi

echo "Main protection enabled for ${repo}: pull requests required; force pushes and deletion blocked."
