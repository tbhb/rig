"""Utilities for querying paths used by rig."""

import os
from pathlib import Path


def rig_prefix() -> Path:
    """Return the installation prefix for rig.

    The installation prefix is the root directory of the rig repository,
    used for locating configuration files and generating shim scripts.

    The path can be overridden by setting the RIG_PREFIX environment
    variable, primarily for testing purposes.

    Returns:
        Path to the rig repository root directory.

    Example:
        >>> prefix = rig_prefix()
        >>> (prefix / "pyproject.toml").exists()
        True
    """
    if env_path := os.environ.get("RIG_PREFIX"):
        return Path(env_path)
    return Path(__file__).resolve().parent.parent.parent
