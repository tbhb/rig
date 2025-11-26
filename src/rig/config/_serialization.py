"""Serialization utilities for configuration objects.

This module provides functions to serialize ConfigSchema objects
to various formats: dictionary, TOML, and JSON.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from rig.config._parser import python_to_toml_key

if TYPE_CHECKING:
    from rig.config._schema import (
        ConfigSchema,
        HooksConfig,
        PathPatterns,
        SyncConfig,
        WorktreeConfig,
    )


# Type aliases for serialized data
# Serialized values are JSON-compatible primitive types
# Using type statement for recursive types (Python 3.12+)
type SerializedScalar = str | bool | int | float
type SerializedDict = dict[str, SerializedValue]
type SerializedValue = SerializedScalar | list[SerializedValue] | SerializedDict


def to_dict(config: ConfigSchema) -> SerializedDict:
    """Convert a ConfigSchema to a dictionary.

    Recursively converts the configuration schema and all nested dataclasses
    to dictionaries. Omits fields with None values and empty tuples to
    produce clean output. Tuples are converted to lists for JSON compatibility.
    Keys are converted to kebab-case for TOML/JSON compatibility.

    Args:
        config: The configuration schema to serialize.

    Returns:
        Dictionary representation of the configuration with kebab-case keys.

    Example:
        >>> resolved = resolve_config()
        >>> data = to_dict(resolved.config)
        >>> print(data["worktree"]["default-location"])
        sibling
    """
    # Use type-safe conversion instead of dataclasses.asdict
    raw_dict = _config_to_raw_dict(config)
    cleaned = _clean_dict(raw_dict)
    return _convert_keys_to_toml(cleaned)


def to_toml(config: ConfigSchema) -> str:
    """Convert a ConfigSchema to TOML format.

    Serializes the configuration schema to a TOML string suitable for
    writing to a .rig.toml file. The output uses standard TOML formatting
    with proper section headers and indentation.

    Args:
        config: The configuration schema to serialize.

    Returns:
        TOML-formatted string representation.

    Example:
        >>> resolved = resolve_config()
        >>> toml_str = to_toml(resolved.config)
        >>> print(toml_str)
        [worktree]
        default-location = "sibling"
        delete-branch = true
        ...
    """
    # to_dict already converts to kebab-case
    data = to_dict(config)
    return _serialize_toml(data)


def to_json(config: ConfigSchema, *, indent: int = 2) -> str:
    """Convert a ConfigSchema to JSON format.

    Serializes the configuration schema to a JSON string. Useful for
    integration with tools that prefer JSON over TOML.

    Args:
        config: The configuration schema to serialize.
        indent: Number of spaces for indentation (default: 2).

    Returns:
        JSON-formatted string representation.

    Example:
        >>> resolved = resolve_config()
        >>> json_str = to_json(resolved.config)
        >>> print(json_str)
        {
          "worktree": {
            "default_location": "sibling",
            "delete_branch": true,
            ...
          }
        }
    """
    data = to_dict(config)
    return json.dumps(data, indent=indent)


# Type alias for raw dict before cleaning (includes tuples from config)
type RawDict = dict[str, RawValue]
type RawValue = str | bool | int | float | tuple[str, ...] | RawDict


def _config_to_raw_dict(config: ConfigSchema) -> RawDict:
    """Convert a ConfigSchema to a raw dictionary.

    Type-safe conversion that explicitly accesses config attributes
    instead of using dataclasses.asdict which returns Any.

    Args:
        config: The configuration schema to convert.

    Returns:
        Raw dictionary representation with snake_case keys.
    """
    return {
        "worktree": _worktree_to_raw_dict(config.worktree),
    }


def _worktree_to_raw_dict(worktree: WorktreeConfig) -> RawDict:
    """Convert a WorktreeConfig to a raw dictionary."""
    return {
        "default_location": worktree.default_location,
        "delete_branch": worktree.delete_branch,
        "protected": worktree.protected,
        "paths": _path_patterns_to_raw_dict(worktree.paths),
        "sync": _sync_config_to_raw_dict(worktree.sync),
        "hooks": _hooks_config_to_raw_dict(worktree.hooks),
    }


def _path_patterns_to_raw_dict(paths: PathPatterns) -> RawDict:
    """Convert a PathPatterns to a raw dictionary."""
    return {
        "sibling": paths.sibling,
        "local": paths.local,
        "pr": paths.pr,
    }


def _sync_config_to_raw_dict(sync: SyncConfig) -> RawDict:
    """Convert a SyncConfig to a raw dictionary."""
    return {
        "link": sync.link,
        "copy": sync.copy,
        "extend_link": sync.extend_link,
        "extend_copy": sync.extend_copy,
        "exclude_link": sync.exclude_link,
        "exclude_copy": sync.exclude_copy,
    }


def _hooks_config_to_raw_dict(hooks: HooksConfig) -> RawDict:
    """Convert a HooksConfig to a raw dictionary."""
    return {
        "post_add": hooks.post_add,
        "pre_remove": hooks.pre_remove,
        "extend_post_add": hooks.extend_post_add,
        "extend_pre_remove": hooks.extend_pre_remove,
        "exclude_post_add": hooks.exclude_post_add,
        "exclude_pre_remove": hooks.exclude_pre_remove,
    }


def _clean_dict(d: RawDict) -> SerializedDict:
    """Recursively clean a dictionary by removing None and empty values.

    Also converts tuples to lists for JSON compatibility.

    Args:
        d: Dictionary to clean.

    Returns:
        Cleaned dictionary.
    """
    result: SerializedDict = {}

    for key, value in d.items():
        # Skip empty tuples
        if isinstance(value, tuple) and len(value) == 0:
            continue

        # Recursively clean nested dicts
        if isinstance(value, dict):
            cleaned = _clean_dict(value)
            # Only include non-empty dicts
            if cleaned:
                result[key] = cleaned
        # Convert tuples to lists
        elif isinstance(value, tuple):
            result[key] = list(value)
        else:
            result[key] = value

    return result


def _convert_keys_to_toml(d: SerializedDict) -> SerializedDict:
    """Recursively convert dictionary keys to TOML format (kebab-case).

    Args:
        d: Dictionary with snake_case keys.

    Returns:
        Dictionary with kebab-case keys.
    """
    result: SerializedDict = {}

    for key, value in d.items():
        toml_key = python_to_toml_key(key)

        if isinstance(value, dict):
            result[toml_key] = _convert_keys_to_toml(value)
        else:
            result[toml_key] = value

    return result


# Type alias for non-dict serialized values (scalars and arrays)
TomlScalarValue = str | bool | int | float | list[SerializedValue]


def _serialize_toml(data: SerializedDict, prefix: str = "") -> str:
    """Manually serialize a dictionary to TOML format.

    Python's tomllib is read-only, so we need a manual serializer.
    This handles nested tables with [section.subsection] headers.

    Args:
        data: Dictionary to serialize.
        prefix: Current section prefix for nested tables.

    Returns:
        TOML-formatted string.
    """
    lines: list[str] = []

    # Separate scalar values from nested tables
    scalars: dict[str, TomlScalarValue] = {}
    tables: dict[str, SerializedDict] = {}

    for key, value in data.items():
        if isinstance(value, dict):
            tables[key] = value
        else:
            scalars[key] = value

    # Write section header if we have a prefix and there are scalars
    if prefix and scalars:
        lines.append(f"[{prefix}]")

    # Write scalar values
    for key, value in scalars.items():
        toml_value = _serialize_toml_value(value)
        lines.append(f"{key} = {toml_value}")

    # Add blank line after scalars if there are tables
    if scalars and tables:
        lines.append("")

    # Process nested tables
    for key, table in tables.items():
        nested_prefix = f"{prefix}.{key}" if prefix else key
        nested_content = _serialize_toml(table, nested_prefix)
        if nested_content:
            lines.append(nested_content)

    return "\n".join(lines)


def _serialize_toml_value(value: TomlScalarValue) -> str:
    """Serialize a single value to TOML format.

    Args:
        value: Value to serialize.

    Returns:
        TOML-formatted value string.
    """
    if isinstance(value, bool):
        # Booleans must be lowercase in TOML
        return "true" if value else "false"
    if isinstance(value, str):
        return _serialize_toml_string(value)
    if isinstance(value, int | float):
        return str(value)
    # Must be list at this point (exhaustive check)
    return _serialize_toml_array(value)


def _serialize_toml_string(s: str) -> str:
    """Serialize a string to TOML format with proper escaping.

    Args:
        s: String to serialize.

    Returns:
        TOML-formatted quoted string.
    """
    # Escape backslashes and double quotes
    escaped = s.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _serialize_toml_array(arr: list[SerializedValue]) -> str:
    """Serialize an array to TOML format.

    Args:
        arr: Array to serialize.

    Returns:
        TOML-formatted array string.
    """
    if not arr:
        return "[]"

    # For short arrays with simple values, use inline format
    items = [_serialize_toml_scalar(item) for item in arr]
    return "[" + ", ".join(items) + "]"


def _serialize_toml_scalar(value: SerializedValue) -> str:
    """Serialize a scalar value in an array to TOML format.

    Arrays in TOML can contain scalars or nested arrays but not tables.
    This handles the recursive case for nested arrays.

    Args:
        value: Value to serialize (must be a scalar or array, not dict).

    Returns:
        TOML-formatted value string.
    """
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return _serialize_toml_string(value)
    if isinstance(value, int | float):
        return str(value)
    if isinstance(value, list):
        return _serialize_toml_array(value)
    # Dict in array - should not happen with valid data, return empty
    return "{}"
