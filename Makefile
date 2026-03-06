.PHONY: install lint format test qa docs docs-open smoke task-start task-list help

DOCS_SOURCE := docs
DOCS_BUILD := $(DOCS_SOURCE)/_build
WORKTREES_DIR ?= .worktrees
TASK ?=
BRANCH ?=
BASE ?= origin/main

install: ## Install project dependencies with uv
	@uv sync

lint: ## Run Ruff checks on this repository
	@uv run ruff check .

format: ## Format code with Ruff
	@uv run ruff format .

test: ## Run repository tests
	@uv run pytest -q

docs: ## Build package documentation as HTML
	@uv run --group docs sphinx-build $(DOCS_SOURCE) $(DOCS_BUILD)/html -b html -W

docs-open: docs ## Build docs and open them in the browser
	@uv run -m webbrowser $(DOCS_BUILD)/html/index.html

qa: lint test docs ## Run local quality checks

smoke: ## Generate a project from template defaults and run generated QA
	@tmp_dir=$$(mktemp -d); \
	echo "Using $$tmp_dir"; \
	uv run copier copy --trust --vcs-ref=HEAD . "$$tmp_dir/test-project" --defaults; \
	$(MAKE) -C "$$tmp_dir/test-project" qa

task-start: ## Create an isolated branch+worktree for a task. Usage: make task-start TASK=my-task [BRANCH=chore/my-task] [BASE=origin/main]
	@set -eu; \
	if [ -z "$(TASK)" ]; then \
		echo "TASK is required. Example: make task-start TASK=improve-docs"; \
		exit 1; \
	fi; \
	task_slug=$$(printf '%s' "$(TASK)" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9._-]+/-/g; s/^-+//; s/-+$$//'); \
	if [ -z "$$task_slug" ]; then \
		echo "TASK produced an empty slug. Choose a different TASK value."; \
		exit 1; \
	fi; \
	branch_name="$(BRANCH)"; \
	if [ -z "$$branch_name" ]; then \
		branch_name="chore/$$task_slug"; \
	fi; \
	worktree_path="$(WORKTREES_DIR)/$$task_slug"; \
	if [ -e "$$worktree_path" ]; then \
		echo "Worktree path already exists: $$worktree_path"; \
		exit 1; \
	fi; \
	if git show-ref --verify --quiet "refs/heads/$$branch_name"; then \
		echo "Local branch already exists: $$branch_name"; \
		exit 1; \
	fi; \
	git fetch origin; \
	mkdir -p "$(WORKTREES_DIR)"; \
	git worktree add "$$worktree_path" -b "$$branch_name" "$(BASE)"; \
	created_at=$$(date -u '+%Y-%m-%dT%H:%M:%SZ'); \
	{ \
		echo "# Agent Task Context"; \
		echo; \
		echo "- task: $$task_slug"; \
		echo "- branch: $$branch_name"; \
		echo "- base: $(BASE)"; \
		echo "- created_at_utc: $$created_at"; \
		echo "- worktree: $$worktree_path"; \
		echo "- source_repo: $$(pwd)"; \
	} > "$$worktree_path/.agent-task-context.md"; \
	echo "Created worktree: $$worktree_path"; \
	echo "Branch: $$branch_name"; \
	echo "Next step: cd $$worktree_path"

task-list: ## List registered git worktrees and saved task context files
	@echo "Git worktrees:"; \
	git worktree list; \
	echo ""; \
	echo "Task context files:"; \
	if [ -d "$(WORKTREES_DIR)" ]; then \
		find "$(WORKTREES_DIR)" -maxdepth 2 -name .agent-task-context.md -print | sort; \
	else \
		echo "(none)"; \
	fi

help: ## Show available targets
	@uv run python -c "import re; \
	[[print(f'\033[36m{m[0]:<20}\033[0m {m[1]}') for m in re.findall(r'^([a-zA-Z_.-]+):.*?## (.*)$$', open(makefile).read(), re.M)] for makefile in ('$(MAKEFILE_LIST)').strip().split()]"

.DEFAULT_GOAL := help
