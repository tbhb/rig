"""Personal development environment tools."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("rig")
except PackageNotFoundError:
    __version__ = "unknown"
