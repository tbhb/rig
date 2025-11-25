"""Install command for rig."""

import os
import stat
from pathlib import Path

from rich.console import Console
from rich.prompt import Confirm

from rig.paths import rig_prefix

SHIM_SENTINEL = "# rig-shim: managed by rig install"

_console = Console()


def get_shim_path() -> Path:
    """Return the path where the shim should be installed.

    The path can be overridden by setting the RIG_SHIM_PATH environment
    variable, primarily for testing purposes.

    Returns:
        Path to the shim location (default: ~/.local/bin/rig).
    """
    if env_path := os.environ.get("RIG_SHIM_PATH"):
        return Path(env_path)
    return Path.home() / ".local" / "bin" / "rig"


def is_in_path(directory: Path) -> bool:
    """Check if a directory is in the system PATH.

    Checks both the literal path and the resolved (symlink-expanded) path
    against entries in the PATH environment variable.

    Args:
        directory: The directory path to check.

    Returns:
        True if the directory (or its resolved form) is in PATH.
    """
    path_dirs = os.environ.get("PATH", "").split(os.pathsep)
    dir_str = str(directory)
    resolved_str = str(directory.resolve())
    return any(p in (dir_str, resolved_str) for p in path_dirs)


def is_rig_managed_shim(path: Path) -> bool:
    """Check if a file is a rig-managed shim.

    A rig-managed shim contains the SHIM_SENTINEL marker that identifies
    it as being created and managed by the rig install command.

    Args:
        path: Path to the file to check.

    Returns:
        True if the file exists and contains the rig shim sentinel.
    """
    if not path.exists():
        return False
    content = path.read_text()
    return SHIM_SENTINEL in content


def generate_shim_content(project_path: Path) -> str:
    """Generate the content for the shim script.

    Args:
        project_path: Path to the rig project directory.

    Returns:
        Shell script content with properly escaped path.
    """
    # Escape single quotes in path for safe shell embedding
    escaped_path = str(project_path).replace("'", "'\\''")
    return f"""#!/usr/bin/env bash
{SHIM_SENTINEL}
set -euo pipefail
exec uv run --project '{escaped_path}' rig "$@"
"""


def _print_path_instructions(bin_dir: Path) -> None:
    """Print instructions for adding the bin directory to PATH."""
    _console.print(f"\n[yellow]Warning:[/yellow] {bin_dir} is not in your PATH.\n")
    _console.print("Add it to your shell configuration:\n")
    _console.print("[bold]For bash[/bold] (~/.bashrc):")
    _console.print('  export PATH="$HOME/.local/bin:$PATH"\n')
    _console.print("[bold]For zsh[/bold] (~/.zshrc):")
    _console.print('  export PATH="$HOME/.local/bin:$PATH"\n')
    _console.print("Then restart your shell or run:")
    _console.print("  source ~/.bashrc  # or source ~/.zshrc\n")


def install() -> None:
    """Install rig shim to ~/.local/bin for global access.

    Creates a shell script shim at ~/.local/bin/rig that invokes rig via
    uv run from the project directory. The shim allows running rig from
    anywhere without activating a virtual environment.

    The command will:
    1. Create ~/.local/bin if it doesn't exist
    2. Check that ~/.local/bin is in PATH (exit with instructions if not)
    3. Prompt before overwriting files not created by rig
    4. Write an executable shim script with the rig sentinel marker

    Raises:
        SystemExit: If ~/.local/bin is not in PATH, or if user declines
            to overwrite an existing non-rig file.
    """
    project_path = rig_prefix()
    shim_path = get_shim_path()
    bin_dir = shim_path.parent

    # Create ~/.local/bin if it doesn't exist
    if not bin_dir.exists():
        bin_dir.mkdir(parents=True, exist_ok=True)
        _console.print(f"[green]Created[/green] {bin_dir}")

    # Check if bin_dir is in PATH
    if not is_in_path(bin_dir):
        _print_path_instructions(bin_dir)
        msg = f"{bin_dir} is not in PATH"
        raise SystemExit(msg)

    # Check if shim already exists
    if shim_path.exists():
        if not is_rig_managed_shim(shim_path):
            _console.print(f"[yellow]Warning:[/yellow] {shim_path} not created by rig.")
            if not Confirm.ask("Overwrite?", default=False):
                _console.print("[red]Aborted.[/red]")
                raise SystemExit(1)
        else:
            _console.print("[dim]Updating existing rig shim...[/dim]")

    # Write the shim
    shim_content = generate_shim_content(project_path)
    _ = shim_path.write_text(shim_content)

    # Make executable
    current_mode = shim_path.stat().st_mode
    shim_path.chmod(current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    _console.print(f"[green]Installed[/green] rig shim to {shim_path}")
    _console.print(f"[dim]Project path: {project_path}[/dim]")
