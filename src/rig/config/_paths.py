"""Path utilities for locating configuration files.

This module provides functions for determining the standard locations
of configuration files. Functions return paths without checking existence;
existence checks are performed by the discovery layer.
"""

from pathlib import Path

from rig.config._errors import ConfigFileAccessError


def get_global_config_path() -> Path:
    """Return the path to the global config file.

    The global config is always located at ~/.local/rig/config.toml.
    This function does not check whether the file exists.

    Returns:
        Absolute path to the global config file.
    """
    return get_home_directory() / ".local" / "rig" / "config.toml"


def get_project_config_path(project_root: Path) -> Path:
    """Return the path to the project config file.

    Args:
        project_root: Absolute path to the project root directory.

    Returns:
        Absolute path to .rig.toml in the project root.
    """
    return project_root / ".rig.toml"


def get_local_config_path(project_root: Path) -> Path:
    """Return the path to the local config file.

    Args:
        project_root: Absolute path to the project root directory.

    Returns:
        Absolute path to .rig.local.toml in the project root.
    """
    return project_root / ".rig.local.toml"


def get_worktree_config_path(worktree_path: Path) -> Path:
    """Return the path to the worktree config file.

    Args:
        worktree_path: Absolute path to the worktree directory.

    Returns:
        Absolute path to .rig.worktree.toml in the worktree.

    Example:
        >>> path = get_worktree_config_path(Path("/home/user/projects/myrepo-feature"))
        >>> print(path)
        /home/user/projects/myrepo-feature/.rig.worktree.toml
    """
    return worktree_path / ".rig.worktree.toml"


def get_home_directory() -> Path:
    """Return the user's home directory.

    Uses Path.home() which respects the HOME environment variable
    on Unix systems and USERPROFILE on Windows.

    Returns:
        Absolute path to the home directory.
    """
    return Path.home()


def resolve_path_safely(path: Path) -> Path:
    """Resolve a path without following symlinks beyond the target.

    This function normalizes the path by resolving . and .. components
    and following symlinks. It is used to ensure consistent path
    comparison during ancestor traversal.

    Note on security: While this function follows symlinks, the ancestor
    traversal algorithm only walks upward through parent directories.
    It never follows user-controlled path components that could escape
    intended boundaries.

    Args:
        path: Path to resolve.

    Returns:
        Normalized absolute path.

    Raises:
        ConfigFileAccessError: If path resolution fails due to
            permission errors or other OS-level issues.
    """
    try:
        return path.resolve()
    except OSError as e:
        raise ConfigFileAccessError(
            path=path,
            detail=str(e),
        ) from e
