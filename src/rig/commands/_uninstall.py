"""Uninstall command for rig."""

from rich.console import Console

from rig.commands._install import SHIM_SENTINEL, get_shim_path

_console = Console()


def _is_rig_managed_shim_content(content: str) -> bool:
    """Check if file content contains the rig shim sentinel."""
    return SHIM_SENTINEL in content


def uninstall() -> None:
    """Uninstall rig shim from ~/.local/bin.

    Removes the rig shim script if it exists and was created by rig.
    The command will refuse to remove files that don't contain the
    rig shim sentinel marker.

    Raises:
        SystemExit: If the file exists but was not created by rig install.
    """
    shim_path = get_shim_path()

    if not shim_path.exists():
        _console.print(f"[dim]No shim found at {shim_path}[/dim]")
        _console.print("[green]Nothing to uninstall.[/green]")
        return

    # Read and check if it's our shim
    content = shim_path.read_text()
    if not _is_rig_managed_shim_content(content):
        _console.print(f"[yellow]Warning:[/yellow] {shim_path} not created by rig.")
        _console.print("[red]Refusing to remove.[/red] Remove manually if needed.")
        raise SystemExit(1)

    # Remove the shim
    shim_path.unlink()
    _console.print(f"[green]Removed[/green] rig shim from {shim_path}")
