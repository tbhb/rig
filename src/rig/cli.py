"""CLI entry point for rig."""

from cyclopts import App
from rich.console import Console

from rig.commands import install, uninstall
from rig.paths import rig_prefix

console = Console()

app = App("rig", "Personal development environment tools.")


@app.command(name="--prefix")
def prefix() -> None:
    """Print the installation prefix for rig."""
    console.out(str(rig_prefix()))


_ = app.command(install)
_ = app.command(uninstall)


def main() -> None:
    """Run the CLI application."""
    app()


if __name__ == "__main__":
    main()
