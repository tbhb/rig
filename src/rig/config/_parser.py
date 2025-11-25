"""TOML parsing and validation for configuration files.

This module handles reading TOML config files, validating their structure
against the schema, and constructing ConfigSchema objects from the parsed
data.
"""

from __future__ import annotations

import re
import tomllib
from typing import TYPE_CHECKING, cast

from rig.config._errors import (
    ConfigFileAccessError,
    ConfigParseError,
    ConfigValidationError,
)
from rig.config._schema import (
    ConfigSchema,
    HooksConfig,
    PathPatterns,
    SyncConfig,
    WorktreeConfig,
)

if TYPE_CHECKING:
    from pathlib import Path

# Constants for suggestion algorithm
_MIN_PREFIX_LENGTH = 2
_MIN_SUGGESTION_SCORE = 3
_JACCARD_THRESHOLD = 0.5

# Valid keys at each level, derived from schema dataclasses
# Keys use TOML convention (kebab-case)
_SCHEMA_KEYS: dict[str, set[str]] = {
    "": {"worktree"},  # Root level
    "worktree": {
        "default-location",
        "delete-branch",
        "protected",
        "paths",
        "sync",
        "hooks",
    },
    "worktree.paths": {"sibling", "local", "pr"},
    "worktree.sync": {
        "link",
        "copy",
        "extend-link",
        "extend-copy",
        "exclude-link",
        "exclude-copy",
    },
    "worktree.hooks": {
        "post-add",
        "pre-remove",
        "extend-post-add",
        "extend-pre-remove",
        "exclude-post-add",
        "exclude-pre-remove",
    },
}

# Type expectations for leaf values
_FIELD_TYPES: dict[str, type] = {
    "worktree.default-location": str,
    "worktree.delete-branch": bool,
    "worktree.protected": bool,
    "worktree.paths.sibling": str,
    "worktree.paths.local": str,
    "worktree.paths.pr": str,
    "worktree.sync.link": list,
    "worktree.sync.copy": list,
    "worktree.sync.extend-link": list,
    "worktree.sync.extend-copy": list,
    "worktree.sync.exclude-link": list,
    "worktree.sync.exclude-copy": list,
    "worktree.hooks.post-add": list,
    "worktree.hooks.pre-remove": list,
    "worktree.hooks.extend-post-add": list,
    "worktree.hooks.extend-pre-remove": list,
    "worktree.hooks.exclude-post-add": list,
    "worktree.hooks.exclude-pre-remove": list,
}

# Fields that are base lists (cannot coexist with extend/exclude)
_BASE_LIST_FIELDS: dict[str, tuple[str, str]] = {
    "worktree.sync.link": (
        "worktree.sync.extend-link",
        "worktree.sync.exclude-link",
    ),
    "worktree.sync.copy": (
        "worktree.sync.extend-copy",
        "worktree.sync.exclude-copy",
    ),
    "worktree.hooks.post-add": (
        "worktree.hooks.extend-post-add",
        "worktree.hooks.exclude-post-add",
    ),
    "worktree.hooks.pre-remove": (
        "worktree.hooks.extend-pre-remove",
        "worktree.hooks.exclude-pre-remove",
    ),
}

# Valid values for location strategy
_VALID_LOCATION_STRATEGIES = frozenset({"sibling", "local"})


def parse_config_file(path: Path) -> ConfigSchema:
    """Parse a config file into a ConfigSchema.

    Reads the file, parses TOML, validates structure, and constructs
    the appropriate schema objects.

    Args:
        path: Absolute path to the config file.

    Returns:
        Parsed and validated ConfigSchema.

    Raises:
        ConfigFileAccessError: If file cannot be read.
        ConfigParseError: If file contains invalid TOML syntax.
        ConfigValidationError: If structure or values are invalid.
    """
    # Read file content
    try:
        content = path.read_text(encoding="utf-8")
    except PermissionError as e:
        raise ConfigFileAccessError(
            path=path,
            detail="permission denied",
        ) from e
    except IsADirectoryError as e:
        raise ConfigFileAccessError(
            path=path,
            detail="is a directory",
        ) from e
    except OSError as e:
        raise ConfigFileAccessError(
            path=path,
            detail=str(e),
        ) from e

    # Handle empty files
    if not content.strip():
        return ConfigSchema()

    # Parse TOML
    try:
        data = tomllib.loads(content)
    except tomllib.TOMLDecodeError as e:
        # Extract line/column from error message if available
        line, column = _extract_error_location(str(e))
        raise ConfigParseError(
            path=path,
            line=line,
            column=column,
            detail=str(e),
        ) from e

    # Handle empty parsed result
    if not data:
        return ConfigSchema()

    # Validate structure
    validate_config_structure(data, path)

    # Build and return schema
    return _build_config_schema(data)


def validate_config_structure(
    data: dict[str, object],
    path: Path,
) -> None:
    """Validate config structure against the schema.

    Checks for:
    - Unknown top-level keys
    - Unknown nested keys at each level
    - Invalid type for field values
    - Invalid combinations (base + extend/exclude)

    Args:
        data: Parsed TOML data as a dictionary.
        path: Path to config file (for error messages).

    Raises:
        ConfigValidationError: If validation fails.
    """
    # Validate keys recursively
    _validate_keys_recursive(data, "", path)

    # Validate base/extend exclusivity
    _validate_base_extend_exclusivity(data, path)


def _validate_keys_recursive(
    data: dict[str, object],
    prefix: str,
    path: Path,
) -> None:
    """Recursively validate keys at each level.

    Args:
        data: Dictionary to validate.
        prefix: Dot-notation prefix for current level.
        path: Path to config file (for error messages).

    Raises:
        ConfigValidationError: If an unknown key or invalid type is found.
    """
    valid_keys = _SCHEMA_KEYS.get(prefix, set())

    for key, value in data.items():
        # Build full key path
        full_key = f"{prefix}.{key}" if prefix else key

        # Check if key is valid at this level
        if key not in valid_keys:
            suggestion = _suggest_similar_key(key, valid_keys)
            detail = f"unknown key '{key}'"
            if suggestion:
                detail += f" (did you mean '{suggestion}'?)"
            raise ConfigValidationError(
                path=path,
                key=prefix if prefix else "root",
                detail=detail,
            )

        # If value is a dict, recurse
        if isinstance(value, dict):
            # Type narrowing: value is dict, but keys/values are unknown.
            # Use cast to assert proper type after isinstance check.
            nested_dict = cast("dict[str, object]", value)
            _validate_keys_recursive(
                nested_dict,
                full_key,
                path,
            )
        else:
            # Validate type
            _validate_field_type(full_key, value, path)


def _validate_field_type(
    full_key: str,
    value: object,
    path: Path,
) -> None:
    """Validate that a field value has the expected type.

    Args:
        full_key: Dot-notation key path.
        value: The value to validate.
        path: Path to config file (for error messages).

    Raises:
        ConfigValidationError: If the type is invalid.
    """
    expected_type = _FIELD_TYPES.get(full_key)
    if expected_type is None:
        # This shouldn't happen if _SCHEMA_KEYS is properly maintained
        return

    if not isinstance(value, expected_type):
        expected_name = _get_type_name(expected_type)
        actual_name = _get_type_name(type(value))

        raise ConfigValidationError(
            path=path,
            key=full_key,
            detail=f"expected {expected_name}, got {actual_name}",
        )

    # Special validation for lists: all items must be strings
    if isinstance(value, list):
        # Type narrowing: value is list, but item type is unknown.
        # Use cast to assert proper type after isinstance check.
        list_value = cast("list[object]", value)
        _validate_list_items(full_key, list_value, path)

    # Special validation for location strategy
    if (
        full_key == "worktree.default-location"
        and value not in _VALID_LOCATION_STRATEGIES
    ):
        valid_options = ", ".join(sorted(_VALID_LOCATION_STRATEGIES))
        raise ConfigValidationError(
            path=path,
            key=full_key,
            detail=f"invalid value '{value}' (must be one of: {valid_options})",
        )


def _get_type_name(t: type) -> str:
    """Get human-readable name for a type.

    Args:
        t: The type to get a name for.

    Returns:
        Human-readable type name.
    """
    type_names: dict[type, str] = {
        list: "array",
        str: "string",
        bool: "boolean",
        int: "integer",
    }
    return type_names.get(t, t.__name__)


def _validate_list_items(
    full_key: str,
    value: list[object],
    path: Path,
) -> None:
    """Validate that all list items are strings.

    Args:
        full_key: Dot-notation key path.
        value: The list to validate.
        path: Path to config file (for error messages).

    Raises:
        ConfigValidationError: If any item is not a string.
    """
    for i, item in enumerate(value):
        if not isinstance(item, str):
            raise ConfigValidationError(
                path=path,
                key=full_key,
                detail=(
                    f"array item {i} must be a string, "
                    f"got {type(item).__name__}"
                ),
            )


def _validate_base_extend_exclusivity(
    data: dict[str, object],
    path: Path,
) -> None:
    """Validate that base lists don't coexist with extend/exclude in same file.

    Args:
        data: Parsed TOML data.
        path: Path to config file (for error messages).

    Raises:
        ConfigValidationError: If both base and extend/exclude exist.
    """
    for base_field, (extend_field, exclude_field) in _BASE_LIST_FIELDS.items():
        base_exists = _key_exists_in_data(base_field, data)
        extend_exists = _key_exists_in_data(extend_field, data)
        exclude_exists = _key_exists_in_data(exclude_field, data)

        if base_exists and extend_exists:
            base_name = base_field.split(".")[-1]
            extend_name = extend_field.split(".")[-1]
            parent_key = ".".join(base_field.split(".")[:-1])
            raise ConfigValidationError(
                path=path,
                key=parent_key,
                detail=(
                    f"cannot specify both '{base_name}' and "
                    f"'{extend_name}' in the same file"
                ),
            )

        if base_exists and exclude_exists:
            base_name = base_field.split(".")[-1]
            exclude_name = exclude_field.split(".")[-1]
            parent_key = ".".join(base_field.split(".")[:-1])
            raise ConfigValidationError(
                path=path,
                key=parent_key,
                detail=(
                    f"cannot specify both '{base_name}' and "
                    f"'{exclude_name}' in the same file"
                ),
            )


def _key_exists_in_data(key_path: str, data: dict[str, object]) -> bool:
    """Check if a dot-notation key path exists in nested data.

    Args:
        key_path: Dot-notation key path (e.g., "worktree.sync.link").
        data: Nested dictionary to search.

    Returns:
        True if the key exists, False otherwise.
    """
    parts = key_path.split(".")
    # Use dict[str, object] | None to avoid Unknown type accumulation in loop
    current_dict: dict[str, object] | None = data

    for part in parts:
        if current_dict is None or part not in current_dict:
            return False
        value = current_dict[part]
        # Next iteration: if value is a dict, continue; otherwise mark as terminal.
        # Cast needed because isinstance(value, dict) narrows to dict[Unknown, Unknown].
        if isinstance(value, dict):
            current_dict = cast("dict[str, object]", value)
        else:
            current_dict = None

    return True


def _build_config_schema(data: dict[str, object]) -> ConfigSchema:
    """Build a ConfigSchema from validated TOML data.

    Assumes data has already been validated. Handles key conversion
    from kebab-case to snake_case and constructs nested dataclasses.

    Args:
        data: Validated TOML data.

    Returns:
        Constructed ConfigSchema.
    """
    worktree_raw = data.get("worktree")
    # Use cast to assert proper type after isinstance check
    worktree_data: dict[str, object] = (
        cast("dict[str, object]", worktree_raw)
        if isinstance(worktree_raw, dict)
        else {}
    )

    return ConfigSchema(
        worktree=_build_worktree_config(worktree_data),
    )


def _build_worktree_config(data: dict[str, object]) -> WorktreeConfig:
    """Build WorktreeConfig from worktree section data.

    Args:
        data: Worktree section dictionary.

    Returns:
        Constructed WorktreeConfig.
    """
    kwargs: dict[str, str | bool | PathPatterns | SyncConfig | HooksConfig] = {}

    # Scalar fields
    default_location = data.get("default-location")
    if isinstance(default_location, str):
        kwargs["default_location"] = default_location

    delete_branch = data.get("delete-branch")
    if isinstance(delete_branch, bool):
        kwargs["delete_branch"] = delete_branch

    protected = data.get("protected")
    if isinstance(protected, bool):
        kwargs["protected"] = protected

    # Nested sections - use cast to assert proper types after isinstance checks
    paths_raw = data.get("paths")
    if isinstance(paths_raw, dict):
        paths_data = cast("dict[str, object]", paths_raw)
        kwargs["paths"] = _build_path_patterns(paths_data)

    sync_raw = data.get("sync")
    if isinstance(sync_raw, dict):
        sync_data = cast("dict[str, object]", sync_raw)
        kwargs["sync"] = _build_sync_config(sync_data)

    hooks_raw = data.get("hooks")
    if isinstance(hooks_raw, dict):
        hooks_data = cast("dict[str, object]", hooks_raw)
        kwargs["hooks"] = _build_hooks_config(hooks_data)

    # kwargs values are validated by isinstance checks above; ignore is necessary
    # because dynamically constructing dataclass kwargs loses type precision
    return WorktreeConfig(**kwargs)  # pyright: ignore[reportArgumentType]


def _build_path_patterns(data: dict[str, object]) -> PathPatterns:
    """Build PathPatterns from paths section data.

    Args:
        data: Paths section dictionary.

    Returns:
        Constructed PathPatterns.
    """
    kwargs: dict[str, str] = {}

    sibling = data.get("sibling")
    if isinstance(sibling, str):
        kwargs["sibling"] = sibling

    local = data.get("local")
    if isinstance(local, str):
        kwargs["local"] = local

    pr = data.get("pr")
    if isinstance(pr, str):
        kwargs["pr"] = pr

    return PathPatterns(**kwargs)


def _build_sync_config(data: dict[str, object]) -> SyncConfig:
    """Build SyncConfig from sync section data.

    Args:
        data: Sync section dictionary.

    Returns:
        Constructed SyncConfig.
    """
    kwargs: dict[str, tuple[str, ...]] = {}

    # Map TOML keys to Python attributes
    field_mapping = {
        "link": "link",
        "copy": "copy",
        "extend-link": "extend_link",
        "extend-copy": "extend_copy",
        "exclude-link": "exclude_link",
        "exclude-copy": "exclude_copy",
    }

    for toml_key, python_key in field_mapping.items():
        value = data.get(toml_key)
        if isinstance(value, list):
            # Convert list to tuple of strings.
            # Items are validated as strings by validate_config_structure.
            # Use cast to assert proper type after isinstance check.
            items = cast("list[str]", value)
            kwargs[python_key] = tuple(items)

    return SyncConfig(**kwargs)


def _build_hooks_config(data: dict[str, object]) -> HooksConfig:
    """Build HooksConfig from hooks section data.

    Args:
        data: Hooks section dictionary.

    Returns:
        Constructed HooksConfig.
    """
    kwargs: dict[str, tuple[str, ...]] = {}

    # Map TOML keys to Python attributes
    field_mapping = {
        "post-add": "post_add",
        "pre-remove": "pre_remove",
        "extend-post-add": "extend_post_add",
        "extend-pre-remove": "extend_pre_remove",
        "exclude-post-add": "exclude_post_add",
        "exclude-pre-remove": "exclude_pre_remove",
    }

    for toml_key, python_key in field_mapping.items():
        value = data.get(toml_key)
        if isinstance(value, list):
            # Convert list to tuple of strings.
            # Items are validated as strings by validate_config_structure.
            # Use cast to assert proper type after isinstance check.
            items = cast("list[str]", value)
            kwargs[python_key] = tuple(items)

    return HooksConfig(**kwargs)


def toml_to_python_key(key: str) -> str:
    """Convert TOML key (kebab-case) to Python attribute (snake_case).

    Args:
        key: TOML key in kebab-case.

    Returns:
        Python attribute name in snake_case.

    Examples:
        >>> toml_to_python_key("default-location")
        'default_location'
        >>> toml_to_python_key("post-add")
        'post_add'
        >>> toml_to_python_key("extend-post-add")
        'extend_post_add'
    """
    return key.replace("-", "_")


def python_to_toml_key(key: str) -> str:
    """Convert Python attribute (snake_case) to TOML key (kebab-case).

    Args:
        key: Python attribute name in snake_case.

    Returns:
        TOML key in kebab-case.

    Examples:
        >>> python_to_toml_key("default_location")
        'default-location'
        >>> python_to_toml_key("post_add")
        'post-add'
    """
    return key.replace("_", "-")


def _suggest_similar_key(unknown: str, valid_keys: set[str]) -> str | None:
    """Find a similar valid key for error suggestions.

    Uses simple heuristics to find likely typos:
    - Same prefix (first 2+ characters)
    - Similar length (within 2 characters)
    - Common character transpositions

    Args:
        unknown: The unknown key that was used.
        valid_keys: Set of valid keys at this level.

    Returns:
        Suggestion string or None if no good match found.
    """
    if not valid_keys:
        return None

    unknown_lower = unknown.lower()
    best_match: str | None = None
    best_score = 0

    for valid in valid_keys:
        valid_lower = valid.lower()
        score = 0

        # Exact prefix match (most likely typo)
        if (
            len(unknown_lower) >= _MIN_PREFIX_LENGTH
            and len(valid_lower) >= _MIN_PREFIX_LENGTH
            and unknown_lower[:_MIN_PREFIX_LENGTH]
            == valid_lower[:_MIN_PREFIX_LENGTH]
        ):
            score += 3

        # Length similarity
        length_diff = abs(len(unknown) - len(valid))
        if length_diff == 0:
            score += 2
        elif length_diff == 1:
            score += 1

        # Character overlap (Jaccard-like)
        unknown_chars = set(unknown_lower)
        valid_chars = set(valid_lower)
        if unknown_chars and valid_chars:
            overlap = len(unknown_chars & valid_chars)
            union = len(unknown_chars | valid_chars)
            if union > 0 and overlap / union > _JACCARD_THRESHOLD:
                score += 2

        # Substring match
        if unknown_lower in valid_lower or valid_lower in unknown_lower:
            score += 2

        if score > best_score:
            best_score = score
            best_match = valid

    # Only suggest if we have a reasonable match
    if best_score >= _MIN_SUGGESTION_SCORE:
        return best_match

    return None


def _extract_error_location(error_msg: str) -> tuple[int | None, int | None]:
    """Extract line and column numbers from TOML error message.

    The tomllib error format typically includes "at line X column Y" or
    similar patterns.

    Args:
        error_msg: Error message from tomllib.TOMLDecodeError.

    Returns:
        Tuple of (line, column), with None for missing values.
    """
    line: int | None = None
    column: int | None = None

    # Try to match "at line X column Y" pattern
    line_col_match = re.search(r"at line (\d+) column (\d+)", error_msg)
    if line_col_match:
        line = int(line_col_match.group(1))
        column = int(line_col_match.group(2))
        return line, column

    # Try to match "line X" pattern
    line_match = re.search(r"line (\d+)", error_msg, re.IGNORECASE)
    if line_match:
        line = int(line_match.group(1))

    # Try to match "column X" or "col X" pattern
    col_match = re.search(r"col(?:umn)? (\d+)", error_msg, re.IGNORECASE)
    if col_match:
        column = int(col_match.group(1))

    return line, column
