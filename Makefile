.PHONY: install lint format test qa docs docs-open smoke task-start task-list task-find task-clean help

DOCS_SOURCE := docs
DOCS_BUILD := $(DOCS_SOURCE)/_build
WORKTREES_DIR ?= .worktrees
TASK ?=
BRANCH ?=
BASE ?= origin/main
ISSUE ?=

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

task-start: ## Create an isolated branch+worktree for a task. Usage: make task-start TASK=my-task [ISSUE=123] [BRANCH=chore/my-task] [BASE=origin/main]
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
	issue_value="$(ISSUE)"; \
	{ \
		echo "# Agent Task Context"; \
		echo; \
		echo "- task: $$task_slug"; \
		echo "- branch: $$branch_name"; \
		echo "- issue: $$issue_value"; \
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

task-find: ## Find task context by ISSUE, TASK, or BRANCH. Usage: make task-find ISSUE=123
	@set -eu; \
	if [ -z "$(ISSUE)" ] && [ -z "$(TASK)" ] && [ -z "$(BRANCH)" ]; then \
		echo "Set one selector: ISSUE=<id> or TASK=<task-name> or BRANCH=<branch-name>"; \
		exit 1; \
	fi; \
	if [ ! -d "$(WORKTREES_DIR)" ]; then \
		echo "No worktrees directory: $(WORKTREES_DIR)"; \
		exit 0; \
	fi; \
	context_files=$$(find "$(WORKTREES_DIR)" -maxdepth 2 -name .agent-task-context.md -print | sort); \
	if [ -z "$$context_files" ]; then \
		echo "No task context files found."; \
		exit 0; \
	fi; \
	if [ -n "$(ISSUE)" ]; then \
		matches=$$(printf '%s\n' $$context_files | xargs -r grep -l -- "^- issue: $(ISSUE)$$" || true); \
	elif [ -n "$(TASK)" ]; then \
		matches=$$(printf '%s\n' $$context_files | xargs -r grep -l -- "^- task: $(TASK)$$" || true); \
	else \
		matches=$$(printf '%s\n' $$context_files | xargs -r grep -l -- "^- branch: $(BRANCH)$$" || true); \
	fi; \
	if [ -z "$$matches" ]; then \
		echo "No matching task contexts found."; \
		exit 0; \
	fi; \
	for file in $$matches; do \
		echo "$$file"; \
		sed -n '1,12p' "$$file"; \
		echo ""; \
	done

task-clean: ## Remove a finished task worktree and local branch. Usage: make task-clean TASK=my-task
	@set -eu; \
	if [ -z "$(TASK)" ] && [ -z "$(BRANCH)" ]; then \
		echo "Set TASK=<task-name> or BRANCH=<branch-name>"; \
		exit 1; \
	fi; \
	if [ -n "$(TASK)" ]; then \
		context_file="$(WORKTREES_DIR)/$(TASK)/.agent-task-context.md"; \
	else \
		context_file=$$(find "$(WORKTREES_DIR)" -maxdepth 2 -name .agent-task-context.md -print | xargs -r grep -l -- "^- branch: $(BRANCH)$$" | head -n 1); \
	fi; \
	if [ -z "$$context_file" ] || [ ! -f "$$context_file" ]; then \
		echo "Task context not found."; \
		exit 1; \
	fi; \
	branch_name=$$(sed -n 's/^- branch: //p' "$$context_file" | head -n 1); \
	worktree_path=$$(sed -n 's/^- worktree: //p' "$$context_file" | head -n 1); \
	if [ -z "$$worktree_path" ]; then \
		worktree_path=$$(dirname "$$context_file"); \
	fi; \
	if [ -d "$$worktree_path" ]; then \
		git worktree remove "$$worktree_path"; \
	fi; \
	if [ -n "$$branch_name" ] && git show-ref --verify --quiet "refs/heads/$$branch_name"; then \
		git branch -d "$$branch_name"; \
	fi; \
	git worktree prune; \
	echo "Cleaned task context for branch '$$branch_name'."

help: ## Show available targets
	@uv run python -c "import re; \
	[[print(f'\033[36m{m[0]:<20}\033[0m {m[1]}') for m in re.findall(r'^([a-zA-Z_.-]+):.*?## (.*)$$', open(makefile).read(), re.M)] for makefile in ('$(MAKEFILE_LIST)').strip().split()]"

.DEFAULT_GOAL := help
