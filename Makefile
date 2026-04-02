.PHONY: install lint format test qa bump release docs docs-open smoke help

DOCS_SOURCE := docs
DOCS_BUILD := $(DOCS_SOURCE)/_build

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

bump: ## Bump the project minor version
	@uv version --bump minor

release: ## Create a GitHub release for the current version
	@version=$$(uv version --short); \
	git commit -am "Bump $$version"; \
	git push origin main; \
	gh release create "$$version" --generate-notes

smoke: ## Generate a project from template defaults and run generated QA
	@tmp_dir=$$(mktemp -d); \
	echo "Using $$tmp_dir"; \
	uv run copier copy --trust --vcs-ref=HEAD . "$$tmp_dir/test-project" --defaults; \
	$(MAKE) -C "$$tmp_dir/test-project" qa

help: ## Show available targets
	@uv run python -c "import re; \
	[[print(f'\033[36m{m[0]:<20}\033[0m {m[1]}') for m in re.findall(r'^([a-zA-Z_.-]+):.*?## (.*)$$', open(makefile).read(), re.M)] for makefile in ('$(MAKEFILE_LIST)').strip().split()]"

.DEFAULT_GOAL := help
