.PHONY: install lint format type test qa bump release docs docs-open smoke dependabot protect-main help

export UV_MALWARE_CHECK := 1

DOCS_SOURCE := docs
DOCS_BUILD := $(DOCS_SOURCE)/_build

install: ## Install project dependencies with uv
	@uv sync

dependabot: ## Enable GitHub Dependabot alerts and security updates (idempotent)
	@sh .github/configure-dependabot.sh

protect-main: ## Require pull requests and block force pushes and deletion on main (idempotent)
	@sh .github/configure-main-protection.sh

lint: ## Run Ruff checks on this repository
	@uv run --group lint ruff check .

format: ## Format code with Ruff
	@uv run --group lint ruff format .

type: ## Run ty checks on this repository
	@uv run --group qa ty check

test: ## Run repository tests
	@uv run pytest -q

docs: ## Build package documentation as HTML
	@uv run --group docs sphinx-build $(DOCS_SOURCE) $(DOCS_BUILD)/html -b html -W

docs-open: docs ## Build docs and open them in the browser
	@uv run -m webbrowser $(DOCS_BUILD)/html/index.html

qa: lint type test docs ## Run local quality checks

BUMP ?= minor

.PHONY: bump
bump: ## Bump the project version
	@uv version --bump $(BUMP)

.PHONY: release-pr release
release-pr: ## Open a version and release-notes PR; merging publishes it
	@set -eu; \
	bump="$(BUMP)"; \
	case "$$bump" in patch|minor|major) ;; *) echo "BUMP must be patch, minor, or major" >&2; exit 2 ;; esac; \
	test "$$(git branch --show-current)" = main || { echo "Switch to main to prepare a release" >&2; exit 1; }; \
	test -z "$$(git status --porcelain)" || { echo "The working tree must be clean" >&2; exit 1; }; \
	git pull --ff-only origin main; \
	version=$$(uv version --bump "$$bump" --dry-run --short); \
	branch="release/$$version"; \
	if git show-ref --verify --quiet "refs/heads/$$branch"; then echo "Local branch $$branch already exists; resolve it before retrying" >&2; exit 1; fi; \
	remote_branch=$$(git ls-remote --heads origin "refs/heads/$$branch"); \
	if [ -n "$$remote_branch" ]; then echo "Remote branch $$branch already exists; resolve it before retrying" >&2; exit 1; fi; \
	uv version --bump "$$bump"; \
	git switch -c "$$branch"; \
	git add pyproject.toml uv.lock; \
	git commit -m "chore: bump version to $$version"; \
	git push --set-upstream origin "$$branch"; \
	notes_file=$$(mktemp); \
	trap 'rm -f "$$notes_file"' EXIT; \
	gh api repos/{owner}/{repo}/releases/generate-notes -f tag_name="$$version" -f target_commitish="$$(git rev-parse HEAD)" --jq .body > "$$notes_file"; \
	gh pr create --base main --head "$$branch" --title "chore: bump version to $$version" --body-file "$$notes_file"

release: release-pr ## Prepare a version bump PR (alias for release-pr)

smoke: ## Generate a project from template defaults and run generated QA
	@tmp_dir=$$(mktemp -d); \
	echo "Using $$tmp_dir"; \
	uv run copier copy --trust --vcs-ref=HEAD . "$$tmp_dir/test-project" --defaults; \
	$(MAKE) -C "$$tmp_dir/test-project" qa

help: ## Show available targets
	@uv run python -c "import re; \
	[[print(f'\033[36m{m[0]:<20}\033[0m {m[1]}') for m in re.findall(r'^([a-zA-Z_.-]+):.*?## (.*)$$', open(makefile).read(), re.M)] for makefile in ('$(MAKEFILE_LIST)').strip().split()]"

.DEFAULT_GOAL := help
