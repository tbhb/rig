"""Query utilities for configuration access.

This module provides utilities for querying configuration values,
tracking provenance, and filtering configuration layers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, final

from rig.config._parser import python_to_toml_key, toml_to_python_key
from rig.config._schema import (
    ConfigSchema,
    HooksConfig,
    PathPatterns,
    SyncConfig,
    WorktreeConfig,
)

if TYPE_CHECKING:
    from rig.config._discovery import ConfigFile
    from rig.config._resolver import ResolvedConfig
    from rig.config._types import ConfigLayer


# Union of all possible config value types returned by get_value_by_key
ConfigValue = (
    ConfigSchema
    | WorktreeConfig
    | PathPatterns
    | SyncConfig
    | HooksConfig
    | str
    | bool
    | tuple[str, ...]
    | None
)


def get_value_by_key(config: ConfigSchema, key: str) -> ConfigValue:
    """Get a configuration value by dot-notation key path.

    Traverses the configuration structure using the provided key path
    and returns the value at that location. Returns None if the key
    path doesn't exist or any intermediate value is None.

    Keys can be in either snake_case (Python) or kebab-case (TOML) format;
    they are normalized to snake_case for attribute access.

    Args:
        config: The configuration schema to query.
        key: Dot-notation key path (e.g., "worktree.default_location",
            "worktree.sync.link", "worktree.hooks.post_add").

    Returns:
        The value at the specified key path, or None if not found.

    Example:
        >>> resolved = resolve_config()
        >>> location = get_value_by_key(resolved.config, "worktree.default_location")
        >>> print(location)
        sibling
        >>> links = get_value_by_key(resolved.config, "worktree.sync.link")
        >>> print(links)
        ('.envrc', 'CLAUDE.md')
    """
    # Handle empty string: return the config itself
    if not key:
        return config

    # Normalize key: strip leading/trailing dots
    normalized_key = key.strip(".")

    # Handle edge case: key becomes empty after stripping
    if not normalized_key:
        return config

    # Split into parts
    parts = normalized_key.split(".")

    # Check for consecutive dots (empty parts in the middle)
    # Leading/trailing dots were stripped, so any empty part means consecutive dots
    if "" in parts:
        return None

    # If no valid parts, return None
    if not parts:
        return None

    # Traverse the structure - use object instead of Any for type safety
    # All config types are dataclasses with attribute access
    current: ConfigValue = config
    for part in parts:
        # Convert kebab-case to snake_case for attribute access
        python_key = toml_to_python_key(part)

        # Get the next value based on the current type
        # Only dataclass config types support attribute traversal
        next_value = _get_config_attr(current, python_key)
        if isinstance(next_value, _NotFound):
            return None
        current = next_value

    return current


# Sentinel for attribute not found (distinct from None which is a valid return)
@final
class _NotFound:
    """Sentinel type indicating an attribute was not found."""

    __slots__: tuple[str, ...] = ()


_NOT_FOUND: Final = _NotFound()


def _get_config_attr(  # noqa: PLR0911, PLR0912
    obj: ConfigValue,
    key: str,
) -> ConfigValue | _NotFound:
    """Get an attribute from a config object by key.

    Only dataclass config types support attribute access. Primitive types
    (str, bool, tuple) return _NOT_FOUND.

    Args:
        obj: The config object to get the attribute from.
        key: The attribute name (snake_case).

    Returns:
        The attribute value if found, or _NOT_FOUND sentinel.
    """
    # Handle None - no attributes
    if obj is None:
        return _NOT_FOUND

    # Handle primitive types - no attribute traversal
    if isinstance(obj, str | bool | tuple):
        return _NOT_FOUND

    # Handle config dataclass types - use specific attribute access
    if isinstance(obj, ConfigSchema):
        if key == "worktree":
            return obj.worktree
        return _NOT_FOUND

    if isinstance(obj, WorktreeConfig):
        if key == "default_location":
            return obj.default_location
        if key == "delete_branch":
            return obj.delete_branch
        if key == "protected":
            return obj.protected
        if key == "paths":
            return obj.paths
        if key == "sync":
            return obj.sync
        if key == "hooks":
            return obj.hooks
        return _NOT_FOUND

    if isinstance(obj, PathPatterns):
        if key == "sibling":
            return obj.sibling
        if key == "local":
            return obj.local
        if key == "pr":
            return obj.pr
        return _NOT_FOUND

    if isinstance(obj, SyncConfig):
        if key == "link":
            return obj.link
        if key == "copy":
            return obj.copy
        if key == "extend_link":
            return obj.extend_link
        if key == "extend_copy":
            return obj.extend_copy
        if key == "exclude_link":
            return obj.exclude_link
        if key == "exclude_copy":
            return obj.exclude_copy
        return _NOT_FOUND

    # At this point, obj must be HooksConfig (exhaustive check)
    # All other types have been handled above; type narrowing complete
    if key == "post_add":
        return obj.post_add
    if key == "pre_remove":
        return obj.pre_remove
    if key == "extend_post_add":
        return obj.extend_post_add
    if key == "extend_pre_remove":
        return obj.extend_pre_remove
    if key == "exclude_post_add":
        return obj.exclude_post_add
    if key == "exclude_pre_remove":
        return obj.exclude_pre_remove
    return _NOT_FOUND


def get_value_provenance(
    resolved: ResolvedConfig,
    key: str,
) -> tuple[ConfigValue, ConfigFile | None]:
    """Get a value and identify which layer provided it.

    Searches through the resolved configuration to find which config file
    provided the effective value for the given key. This is useful for
    understanding configuration precedence and debugging.

    Args:
        resolved: The resolved configuration with all layers.
        key: Dot-notation key path to query.

    Returns:
        A tuple of (value, file) where value is the configuration value
        and file is the ConfigFile that provided it. If the key doesn't
        exist in any layer or is only set by defaults, returns (value, None).

    Example:
        >>> resolved = resolve_config()
        >>> value, source = get_value_provenance(resolved, "worktree.default_location")
        >>> if source:
        ...     print(f"{value} from {source.layer.value}: {source.path}")
        sibling from project: /home/user/projects/myrepo/.rig.toml
    """
    # Get the current value from resolved config
    value = get_value_by_key(resolved.config, key)

    # Normalize the key to TOML format (kebab-case) for provenance lookup
    normalized_key = _normalize_key_to_toml(key)

    # Check the provenance dict (uses kebab-case keys)
    # The provenance dict only contains keys that were explicitly set
    if normalized_key in resolved.provenance:
        return value, resolved.provenance[normalized_key]

    # If not in provenance, no layer explicitly set this value
    # Return the value with None source (indicates default)
    return value, None


def filter_layers(
    resolved: ResolvedConfig,
    *,
    layers: set[ConfigLayer] | None = None,
    include_missing: bool = False,
) -> tuple[ConfigFile, ...]:
    """Filter config files by layer.

    Returns a subset of config files matching the specified criteria.
    Useful for inspecting specific layers or filtering out non-existent files.

    Args:
        resolved: The resolved configuration with all layers.
        layers: Set of layers to include. If None, includes all layers.
        include_missing: Whether to include files that don't exist.
            Default is False (only existing files).

    Returns:
        Tuple of ConfigFile objects matching the criteria, in resolution order.

    Example:
        >>> resolved = resolve_config()
        >>> # Get only existing files
        >>> existing = filter_layers(resolved)
        >>> for f in existing:
        ...     print(f"{f.layer.value}: {f.path}")

        >>> # Get only ancestor configs
        >>> ancestors = filter_layers(
        ...     resolved,
        ...     layers={ConfigLayer.ANCESTOR},
        ... )

        >>> # Get all local and worktree files, even if missing
        >>> local_files = filter_layers(
        ...     resolved,
        ...     layers={ConfigLayer.LOCAL, ConfigLayer.WORKTREE},
        ...     include_missing=True,
        ... )
    """
    result: list[ConfigFile] = []

    for config_file in resolved.layers:
        # Filter by layer if specified
        if layers is not None and config_file.layer not in layers:
            continue

        # Filter by existence unless include_missing is True
        if not include_missing and not config_file.exists:
            continue

        result.append(config_file)

    return tuple(result)


def _normalize_key_to_toml(key: str) -> str:
    """Normalize a key to TOML format (kebab-case).

    Handles keys that might be in snake_case (Python) format and
    converts them to kebab-case (TOML) format.

    Args:
        key: Key in either format.

    Returns:
        Key in kebab-case format.
    """
    # Strip leading/trailing dots and split
    normalized = key.strip(".")
    if not normalized:
        return ""

    parts = normalized.split(".")
    # Convert each part to kebab-case and rejoin
    return ".".join(python_to_toml_key(part) for part in parts if part)
