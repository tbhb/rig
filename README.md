# rig

![Python 3.14+](https://img.shields.io/badge/python-3.14+-blue.svg)
![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)

Rig is my personal toolkit for managing my local development environment and working with AI coding agents, specifically Claude Code and Gemini CLI. Currently it provides a CLI for installing itself globally, with planned features for dotfile management, project templates, and development utilities.

> [!WARNING]
> This is my personal development setup. I'm sharing it because others might find it useful as a reference or starting point, but it reflects my opinions, preferences, and workflows. Your mileage may vary.
>
> I make no guarantees about stability, backwards compatibility, or whether any of this will work for you. Feel free to fork it and make it your own.

## What's in here

Currently, rig provides:

- **CLI tool** with install/uninstall commands for global access via a shim script
- **Claude Code configurations** including custom agents, skills, commands, and standards
- **Project standards** for Python development, testing, documentation, and CI/CD

### Roadmap

Planned features include:

- Dotfile management and syncing
- Project template application
- Git worktree utilities for agent tasks
- Gemini CLI configuration equivalents

## Installation

### Requirements

- [uv](https://docs.astral.sh/uv/) - Python package manager
- [just](https://just.systems/) - Command runner (for development)
- [pnpm](https://pnpm.io/) - Node.js package manager (for development)

### Setup

Clone the repository and install the CLI globally:

```bash
git clone https://github.com/tbhb/rig.git ~/Code/github.com/tbhb/rig
cd ~/Code/github.com/tbhb/rig
uv run rig install
```

This creates a shim in `~/.local/bin/rig` that allows you to run `rig` from anywhere on your system.

> [!NOTE]
> Ensure `~/.local/bin` is in your PATH. If not, add to your shell config:
>
> ```bash
> export PATH="$HOME/.local/bin:$PATH"
> ```

## Usage

### Commands

```bash
rig install     # Install the rig shim to ~/.local/bin for global access
rig uninstall   # Remove the rig shim from ~/.local/bin
rig --prefix    # Print the installation prefix (repository path)
```

## Development

Run `just` to see all available tasks, or use these common commands:

```bash
just install       # Install Python and Node.js dependencies
just test          # Run tests
just format        # Format code (codespell, ruff)
just lint          # Run all linters (codespell, yamllint, ruff, basedpyright, markdownlint)
just clean         # Remove build artifacts and caches
```

### Additional lint tasks

```bash
just lint-markdown   # Markdown linting only
just lint-python     # Python linting only (ruff, basedpyright)
just lint-spelling   # Spell checking only
```

### Pre-commit hooks

```bash
just prek        # Run pre-commit hooks on staged files
just prek-all    # Run pre-commit hooks on all files
```

## Acknowledgements

The skill activation hook design is ported from [claude-code-infrastructure-showcase](https://github.com/diet103/claude-code-infrastructure-showcase) by [@diet103](https://github.com/diet103).

## License

MIT License. See [LICENSE](LICENSE) for details.
