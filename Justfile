set unstable

# List available recipes
default:
  @just --list

# Install all dependencies (Python + Node.js)
install:
  uv sync --frozen
  pnpm install --frozen-lockfile

# Run tests
test *args: install
  uv run --frozen pytest "$@"

# Run tests with coverage
test-coverage *args: install
  uv run --frozen pytest --cov=rig --cov-report=term-missing --cov-branch "$@"

# Format code
format: install
  uv run --frozen codespell -w
  uv run --frozen ruff format .

fix: install
  uv run --frozen ruff format .
  uv run --frozen ruff check --fix .

fix-unsafe: install
  uv run --frozen ruff format .
  uv run --frozen ruff check --fix --unsafe-fixes .

# Lint code
lint: install
  uv run --frozen codespell
  uv run --frozen yamllint --strict .
  uv run --frozen ruff check .
  uv run --frozen basedpyright
  pnpm exec markdownlint-cli2 "**/*.md"

# Lint Markdown files
lint-markdown: install
  pnpm exec markdownlint-cli2 "**/*.md"

# Lint Python code
lint-python: install
  uv run --frozen ruff check .
  uv run --frozen ruff format --check .
  uv run --frozen basedpyright

# Check spelling
lint-spelling: install
  uv run --frozen codespell

# Run pre-commit hooks on changed files
prek: install
  uv run --frozen prek

# Run pre-commit hooks on all files
prek-all: install
  uv run --frozen prek run --all-files

# Clean build artifacts
clean:
  rm -rf build/
  rm -rf dist/
  rm -rf site/
  find . -type d -name __pycache__ -exec rm -rf {} +
  find . -type d -name .pytest_cache -exec rm -rf {} +
  find . -type d -name .ruff_cache -exec rm -rf {} +

# Convert Mermaid diagrams
mermaid *args:
  pnpm exec mmdc "$@"
