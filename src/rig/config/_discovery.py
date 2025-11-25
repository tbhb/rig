"""File discovery logic for the configuration system.

This module implements the algorithm for discovering configuration files
in the layered configuration hierarchy. It handles ancestor directory
traversal with appropriate boundary conditions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from rig.config._errors import ConfigFileAccessError
from rig.config._paths import (
    get_global_config_path,
    get_home_directory,
    get_local_config_path,
    get_project_config_path,
    resolve_path_safely,
)
from rig.config._types import ConfigLayer

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from rig.config._schema import ConfigSchema


@dataclass(slots=True, frozen=True)
class ConfigFile:
    """Represents a discovered configuration file.

    A ConfigFile captures metadata about a config file location,
    whether it exists, and optionally its parsed content.

    Attributes:
        path: Absolute path to the config file.
        layer: Which configuration layer this file belongs to.
        exists: Whether the file exists on disk.
        content: Parsed ConfigSchema if file was loaded, None otherwise.
    """

    path: Path
    layer: ConfigLayer
    exists: bool
    content: ConfigSchema | None = None


def discover_config_files(
    project_root: Path,
    *,
    home_dir: Path | None = None,
) -> tuple[ConfigFile, ...]:
    """Discover all config files in resolution order.

    Searches for config files in the following order:
    1. Global config (~/.local/rig/config.toml)
    2. Ancestor .rig.toml files (farthest to nearest)
    3. Project .rig.toml
    4. Project .rig.local.toml

    The search for ancestors stops at the home directory or
    filesystem root, whichever is reached first.

    Args:
        project_root: Absolute path to the project root directory.
        home_dir: Home directory for boundary (defaults to Path.home()).
            Provided for testing.

    Returns:
        Tuple of ConfigFile objects in resolution order.
        Files that don't exist are included with exists=False.

    Raises:
        ConfigFileAccessError: If a directory cannot be accessed.
    """
    if home_dir is None:
        home_dir = get_home_directory()

    result: list[ConfigFile] = []

    # 1. Global config
    global_path = get_global_config_path()
    result.append(
        ConfigFile(
            path=global_path,
            layer=ConfigLayer.GLOBAL,
            exists=_safe_exists(global_path),
        )
    )

    # 2. Ancestor configs (farthest to nearest)
    ancestor_paths = find_ancestor_configs(project_root, home_dir=home_dir)
    result.extend(
        ConfigFile(
            path=ancestor_path,
            layer=ConfigLayer.ANCESTOR,
            exists=_safe_exists(ancestor_path),
        )
        for ancestor_path in ancestor_paths
    )

    # 3. Project config
    project_path = get_project_config_path(project_root)
    result.append(
        ConfigFile(
            path=project_path,
            layer=ConfigLayer.PROJECT,
            exists=_safe_exists(project_path),
        )
    )

    # 4. Local config
    local_path = get_local_config_path(project_root)
    result.append(
        ConfigFile(
            path=local_path,
            layer=ConfigLayer.LOCAL,
            exists=_safe_exists(local_path),
        )
    )

    return tuple(result)


def find_ancestor_configs(
    start: Path,
    *,
    home_dir: Path | None = None,
) -> tuple[Path, ...]:
    """Find .rig.toml files in ancestor directories.

    Walks up from the start directory, collecting paths to any
    .rig.toml files found. Stops at home_dir or filesystem root.

    The returned paths are in "farthest to nearest" order - the
    first path is the most distant ancestor, the last is the
    immediate parent.

    Args:
        start: Directory to start searching from (typically project root).
        home_dir: Stop searching when reaching this directory.
            Defaults to Path.home().

    Returns:
        Tuple of paths to ancestor .rig.toml files, farthest first.

    Note:
        Does not include .rig.toml in the start directory itself -
        that's handled separately as the project config.
    """
    if home_dir is None:
        home_dir = get_home_directory()

    # Resolve paths for consistent comparison
    resolved_start = resolve_path_safely(start)
    resolved_home = resolve_path_safely(home_dir)

    # Collect ancestors in nearest-to-farthest order, then reverse
    ancestors: list[Path] = []

    for ancestor_dir in _walk_ancestors(resolved_start, resolved_home):
        config_path = ancestor_dir / ".rig.toml"
        if _safe_exists(config_path):
            ancestors.append(config_path)

    # Reverse to get farthest-to-nearest order
    ancestors.reverse()
    return tuple(ancestors)


def _walk_ancestors(
    start: Path,
    stop_at: Path,
) -> Iterator[Path]:
    """Yield ancestor directories from start up to (but not including) stop_at.

    Internal helper that handles the upward directory traversal.

    Args:
        start: Starting directory.
        stop_at: Directory to stop at (not yielded).

    Yields:
        Parent directories from immediate parent up to stop_at.
    """
    current = start.parent

    while current != stop_at:
        # Check for filesystem root (parent == self)
        if current == current.parent:
            break
        yield current
        current = current.parent


def _safe_exists(path: Path) -> bool:
    """Check if a path exists, handling permission errors gracefully.

    Args:
        path: Path to check.

    Returns:
        True if the path exists and is accessible, False otherwise.

    Raises:
        ConfigFileAccessError: If access is denied due to permissions.
    """
    try:
        return path.exists()
    except PermissionError as e:
        raise ConfigFileAccessError(
            path=path,
            detail="permission denied",
        ) from e
    except OSError:
        # Other OS errors (e.g., broken symlinks) are treated as non-existent
        return False
