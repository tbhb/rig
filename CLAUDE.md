# CLAUDE.md

## Table of contents

- [Project overview](#project-overview)
- [Core principles](#core-principles)
- [Claude Code behavior](#claude-code-behavior)
- [Development workflow](#development-workflow)
- [Testing strategy](#testing-strategy)
- [Code quality](#code-quality)
- [Code standards](#code-standards)
- [Git workflow](#git-workflow)
- [CI/CD](#cicd)
- [Dependencies](#dependencies)
- [Documentation](#documentation)
- [Available skills and agents](#available-skills-and-agents)

## Project overview

Rig is a personal toolkit for managing local development environments and AI coding agent configurations (Claude Code, Gemini CLI). It provides a CLI for managing dotfiles, project templates, and development utilities.

**Architecture:**

- `src/rig/cli.py` - Entry point using cyclopts for command parsing
- `src/rig/commands/` - Command implementations (install, uninstall)
- `src/rig/paths.py` - Path utilities for locating the rig installation

**Key commands:**

- `rig install` - Install shim to `~/.local/bin/rig` for global access
- `rig uninstall` - Remove the shim
- `rig --prefix` - Print the repository path

## Core principles

### Minimal dependencies

Standard library first. Before adding any dependency:

1. Can stdlib solve it? Use stdlib.
2. Is it critical? If no, don't add.
3. Does value justify maintenance burden?

### Design principles

- **SOLID, DRY, YAGNI, KISS**: Apply rigorously; KISS takes precedence when complexity doesn't demand sophistication
- **Secure by Default**: Require explicit opt-in for less secure behavior
- **Defense in Depth**: Multiple validation layers
- **Measure, Don't Guess**: Profile before optimizing
- **Pay for What You Use**: No runtime overhead for unused features

## Claude Code behavior

Be concise and direct. Work incrementally on a few tasks at a time. Clarify before acting when instructions are ambiguous. Prefer prose over excessive bullet lists when explaining concepts.

### Task execution

- Plan first for substantial changes
- Validate incrementally (type checking, tests after each logical unit)
- Track completed vs pending work
- Verify quality gates before marking tasks complete

### Tool usage

Validate tool results before proceeding. Make parallel tool calls when operations are independent. Reference specific line numbers (e.g., `src/rig/commands/install.py:42`). Never compromise type safety or test coverage.

## Development workflow

```bash
just install          # Install Python and Node.js dependencies
just test             # Run all tests
just lint             # Run all linters (codespell, yamllint, ruff, basedpyright, markdownlint)
just format           # Format code (codespell -w, ruff format)
just clean            # Clean build artifacts and caches
just prek             # Run pre-commit hooks on staged files
just prek-all         # Run pre-commit hooks on all files
```

### Targeted commands

```bash
just lint-python      # Python only (ruff check, ruff format --check, basedpyright)
just lint-markdown    # Markdown only
just lint-spelling    # Spell check only
just test <args>      # Pass args to pytest (e.g., just test -k install)
```

Use `uv run python` for all Python execution.

## Testing strategy

Tests organized under `tests/`: `unit/` for isolated tests, `properties/` for Hypothesis property-based tests.

Organize tests by module (e.g., `test_install.py` for `commands/install.py`), never by task.

**Requirements:**

- Property-based tests with Hypothesis for functions with complex input domains
- Unit tests for command logic and path utilities
- Maintain >95% coverage

### Security considerations

The install command writes executable shims. Review for:

- Path traversal in `generate_shim_content()`
- Shell injection in generated scripts
- Safe handling of existing files (sentinel checking)

## Code quality

Before completing changes, all must pass:

1. Type checking: `uv run basedpyright` with zero errors
2. Linting: `uv run ruff check .` all checks
3. Tests: >95% coverage
4. Documentation: Google-style docstrings for public APIs

Never add type ignore or lint suppressions without explicit user confirmation. Use code-reviewer agent for comprehensive review.

### Architectural decisions

Document rationale, consider alternatives, analyze impact. Standard library first.

## Code standards

**Python:** Target 3.14. Use modern features: pattern matching, type parameter syntax, dataclasses with slots.

**Type checking:** Comprehensive type hints required. Use basedpyright, TYPE_CHECKING blocks, typing-extensions (ReadOnly, TypeIs, Doc). See type-safety skill for patterns.

**Organization:**

- Private modules: leading underscore (`_module.py`)
- Public API: export through `__init__.py`
- Immutability: @dataclass(slots=True, frozen=True)
- Import order: stdlib, third-party, local

**Naming:** Classes PascalCase, functions snake_case, constants UPPER_SNAKE_CASE, private `_underscore`.

**Class ordering:** State, lifecycle (`__init__`), magic methods, public interface, private methods.

**Tests:** No docstrings. Names must be self-explanatory: test_<scenario>_<expected_result>.

## Git workflow

GitHub Flow with branch protection. Never commit directly to main.

```bash
git checkout -b feat/my-feature
git commit -m "feat(module): add functionality"
git push -u origin feat/my-feature
gh pr create --title "feat(module): add functionality"
```

**Conventional Commits:** feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert.

Never bypass pre-commit hooks. Fix issues flagged by hooks.

## CI/CD

GitHub Actions on PRs and main pushes (`.github/workflows/ci.yml`):

- **Lint**: codespell, yamllint, ruff, basedpyright, markdownlint, actionlint
- **Test**: Ubuntu, Python 3.14 (runs after lint passes)

See actions-cicd-practices skill for workflow patterns.

## Dependencies

**Runtime:** cyclopts (CLI framework), rich (terminal output)

**Dev:** pytest, pytest-cov, pytest-mock, hypothesis, ruff, basedpyright, codespell, yamllint, prek (pre-commit)

**Tools:** uv (package manager), just (command runner), pnpm (Node.js for markdownlint)

## Documentation

Headlines: sentence case only. Diagrams: Mermaid.js only, no ASCII art.

## Available skills and agents

Skills and agents provide specialized guidance, activating automatically based on context.

### Skills

| Skill | Trigger context |
|-------|-----------------|
| type-safety | Type hints, basedpyright, TypedDict |
| testing-practices | pytest, Hypothesis, Atheris, coverage |
| hypothesis-strategies | Custom Hypothesis strategies, property tests |
| benchmarking | pytest-benchmark, performance regression |
| profiling-practices | py-spy, flame graphs, optimization |
| security-practices | Security, input validation |
| error-handling | Exception design, error messages |
| dataclass-patterns | Frozen dataclasses, slots, immutability |
| python-dev-practices | Modern Python patterns, tooling |
| shell-dev-practices | POSIX scripts, bash, shellcheck |
| just-automation-practices | Justfile recipes, task automation |
| actions-cicd-practices | GitHub Actions, workflows |
| skill-developer | Creating/managing skills |

### Agents

| Agent | Purpose |
|-------|---------|
| code-architect | Design architecture, plan implementations |
| code-reviewer | Review code for standards compliance |
| refactoring-architect | Plan safe refactoring strategies |
| test-architect | Design test strategies, Hypothesis/Atheris |
| api-designer | Design ergonomic, type-safe APIs |
| documentation-architect | Plan documentation using Diataxis |
| documentation-reviewer | Review documentation scope and quality |
| mutation-test-analyst | Analyze mutation testing survivors |
| performance-architect | Profile and optimize critical paths |
| specification-architect | Create RFC 2119 specifications |
| web-research-specialist | Research external documentation |
