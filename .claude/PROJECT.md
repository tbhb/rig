# Rig project instructions

These instructions are for discussing the Rig project in conversational contexts (Claude Web, Desktop, or Mobile). For Claude Code usage, see `CLAUDE.md` in the repository root.

## Project overview

Rig is my personal toolkit for managing local development environments and AI coding agent configurations (Claude Code, Gemini CLI). It provides a CLI for managing dotfiles, project templates, and development utilities.

### Architecture

```text
src/rig/
├── __init__.py       # Package exports
├── cli.py            # Entry point using cyclopts
├── paths.py          # Path utilities for locating installation
└── commands/
    ├── __init__.py
    ├── install.py    # Install shim to ~/.local/bin/rig
    └── uninstall.py  # Remove the shim
```

### Key commands

- `rig install` - Install shim to `~/.local/bin/rig` for global access
- `rig uninstall` - Remove the shim
- `rig --prefix` - Print the repository path

## Design philosophy

### Minimal dependencies

Standard library first. Before adding any dependency:

1. Can stdlib solve it? Use stdlib.
2. Is it critical? If no, don't add.
3. Does value justify maintenance burden?

### Core principles

- **SOLID, DRY, YAGNI, KISS**: Apply rigorously; KISS takes precedence when complexity doesn't demand sophistication
- **Secure by default**: Require explicit opt-in for less secure behavior
- **Defense in depth**: Multiple validation layers
- **Measure, don't guess**: Profile before optimizing
- **Pay for what you use**: No runtime overhead for unused features

## Technical standards

### Python

- Target Python 3.14
- Modern features: pattern matching, type parameter syntax, dataclasses with slots
- Comprehensive type hints using basedpyright
- typing-extensions for advanced patterns (ReadOnly, TypeIs, Doc)

### Code organization

- Private modules: leading underscore (`_module.py`)
- Public API: export through `__init__.py`
- Immutability: `@dataclass(slots=True, frozen=True)`
- Import order: stdlib, third-party, local

### Naming conventions

- Classes: PascalCase
- Functions: snake_case
- Constants: UPPER_SNAKE_CASE
- Private: leading underscore

## Testing approach

- Unit tests for command logic and path utilities
- Property-based tests with Hypothesis for complex input domains
- Target >95% code coverage
- Test naming: `test_<scenario>_<expected_result>`

## Dependencies

**Runtime:** cyclopts (CLI), rich (terminal output)

**Development:** pytest, hypothesis, ruff, basedpyright, codespell

**Tools:** uv (package manager), just (task runner)

## Security considerations

The install command writes executable shims. Key concerns:

- Path traversal in `generate_shim_content()`
- Shell injection in generated scripts
- Safe handling of existing files (sentinel checking)

## Git workflow

GitHub Flow with conventional commits:

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `refactor`: Code restructuring
- `test`: Test changes
- `ci`: CI/CD changes

## How to help

When discussing this project, you can help with:

- Explaining architecture decisions and trade-offs
- Discussing Python patterns and best practices
- Reviewing code snippets for standards compliance
- Suggesting approaches for new features
- Explaining type safety patterns
- Discussing testing strategies

When I share code, apply these project standards in your feedback. Prioritize security, type safety, and simplicity.
