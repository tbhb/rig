"""Configuration resolution with multi-layer merging and provenance tracking.

This module implements the core resolution algorithm that discovers, parses,
and merges configuration files from multiple layers (global, ancestors, project,
local) to produce a single resolved configuration with full provenance tracking.

The resolver integrates discovery (_discovery.py), parsing (_parser.py), and
merging (_merge.py) to implement the complete resolution strategy described
in the specification.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from rig.config._discovery import ConfigFile, discover_config_files
from rig.config._parser import parse_config_file
from rig.config._schema import ConfigSchema

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(slots=True, frozen=True)
class ResolvedMergeWarning:
    """Warning from configuration resolution with enhanced context.

    This extends the MergeWarning from _merge.py with the ConfigFile
    that generated the warning, providing full resolution context.

    Attributes:
        key: Dot-notation key path where the warning occurred
            (e.g., "worktree.sync.link").
        excluded_item: The specific item that triggered the warning
            (e.g., an exclude that matched nothing).
        config_file: ConfigFile that caused the warning, providing
            path and layer information.
    """

    key: str
    excluded_item: str
    config_file: ConfigFile


@dataclass(slots=True, frozen=True)
class ResolvedConfig:
    """Fully resolved configuration with provenance and warnings.

    This is the result of the complete resolution process, containing
    the final merged configuration along with metadata about which
    layers contributed values and any warnings that were generated.

    Attributes:
        config: The final merged ConfigSchema after applying all layers.
        layers: All discovered config files in resolution order, including
            files that don't exist (exists=False). Order is: global,
            ancestors (farthest to nearest), project, local.
        provenance: Maps dot-notation keys to the ConfigFile that set their
            final value. Tracks both scalar and list fields. For list fields,
            tracks the file that set the base OR the most recent file that
            modified the list via extend/exclude.
        warnings: Tuple of warnings generated during merging. Warnings are
            non-fatal but indicate potential configuration issues such as
            attempting to exclude items that don't exist.

    Examples:
        >>> resolved = resolve_config(Path("/path/to/project"))
        >>> print(resolved.config.worktree.default_location)
        'sibling'
        >>> print(resolved.provenance.get("worktree.default-location"))
        ConfigFile(path=Path('.../.rig.toml'), layer=ConfigLayer.PROJECT, ...)
        >>> for warning in resolved.warnings:
        ...     file_path = warning.config_file.path
        ...     print(f"Warning in {file_path}: excluded {warning.excluded_item}")
    """

    config: ConfigSchema
    layers: tuple[ConfigFile, ...]
    provenance: dict[str, ConfigFile]
    warnings: tuple[ResolvedMergeWarning, ...]


def resolve_config(
    project_root: Path,
    *,
    home_dir: Path | None = None,
) -> ResolvedConfig:
    """Load and merge all configuration layers.

    This is the main entry point for configuration resolution. It discovers
    all config files in the resolution hierarchy, parses existing files,
    merges them in precedence order, and returns the resolved configuration
    with full provenance tracking.

    Resolution order (lowest to highest precedence):
    1. Global config (~/.local/rig/config.toml)
    2. Ancestor configs (farthest to nearest .rig.toml)
    3. Project config (.rig.toml in project root)
    4. Local config (.rig.local.toml in project root)

    The algorithm:
    1. Discover all config file locations using discover_config_files
    2. Parse existing files with parse_config_file
    3. Merge in resolution order using merge_config_schemas
    4. Collect all warnings generated during merge
    5. Build provenance map tracking which file set each key
    6. Return ResolvedConfig with merged config and metadata

    Args:
        project_root: Absolute path to the project root directory.
            This is typically the git repository root.
        home_dir: Home directory for boundary checking during ancestor
            discovery. Defaults to Path.home(). Provided primarily for
            testing with custom home directories.

    Returns:
        ResolvedConfig containing the merged configuration, all discovered
        layers, provenance mapping, and any merge warnings.

    Raises:
        ConfigFileAccessError: If a config file cannot be accessed due to
            permission errors or other I/O issues.
        ConfigParseError: If a config file contains invalid TOML syntax.
        ConfigValidationError: If a config file has invalid structure or
            values (unknown keys, wrong types, invalid combinations).

    Examples:
        >>> # Basic usage
        >>> resolved = resolve_config(Path("/home/user/projects/myapp"))
        >>> print(resolved.config.worktree.default_location)
        'sibling'

        >>> # Check provenance
        >>> location_source = resolved.provenance.get("worktree.default-location")
        >>> if location_source:
        ...     print(f"Set by: {location_source.path}")

        >>> # Handle warnings
        >>> for warning in resolved.warnings:
        ...     file_path = warning.config_file.path
        ...     print(f"Warning at {file_path}: excluded {warning.excluded_item}")
    """
    # Import here to avoid circular dependency with _merge module
    from rig.config._merge import merge_config_schemas  # noqa: PLC0415

    # 1. Discover all config file locations
    discovered_files = discover_config_files(project_root, home_dir=home_dir)

    # 2. Parse existing files and update ConfigFile objects with content
    layers_with_content: list[ConfigFile] = []
    for config_file in discovered_files:
        if config_file.exists:
            parsed_config = parse_config_file(config_file.path)
            layers_with_content.append(replace(config_file, content=parsed_config))
        else:
            layers_with_content.append(config_file)

    # 3. Merge configs in resolution order, collecting warnings
    merged_config = ConfigSchema()  # Start with default
    all_warnings: list[ResolvedMergeWarning] = []

    for layer_file in layers_with_content:
        if layer_file.content is not None:
            merged_config, merge_warnings = merge_config_schemas(
                upstream=merged_config,
                downstream=layer_file.content,
                layer=layer_file.layer,
                source_path=layer_file.path,
            )
            # Convert MergeWarnings to ResolvedMergeWarnings with ConfigFile
            all_warnings.extend(
                ResolvedMergeWarning(
                    key=merge_warning.key,
                    excluded_item=merge_warning.excluded_item,
                    config_file=layer_file,
                )
                for merge_warning in merge_warnings
            )

    # 4. Build provenance map
    provenance = _build_provenance_map(tuple(layers_with_content))

    return ResolvedConfig(
        config=merged_config,
        layers=tuple(layers_with_content),
        provenance=provenance,
        warnings=tuple(all_warnings),
    )


def _build_provenance_map(layers: tuple[ConfigFile, ...]) -> dict[str, ConfigFile]:
    """Build mapping of configuration keys to their source files.

    Tracks which configuration file provided each key's final value.
    Later layers override earlier layers, so we process in order and
    overwrite entries in the provenance map.

    For scalar fields (worktree.default-location, worktree.delete-branch),
    provenance tracks the last file that set the value.

    For list fields (sync.link, sync.copy, hooks.post-add, hooks.pre-remove),
    provenance tracks either:
    - The file that set the base list, OR
    - The most recent file that used extend-* or exclude-* to modify the list

    Args:
        layers: Tuple of ConfigFile objects in resolution order.
            Only layers with content (exists=True) contribute to provenance.

    Returns:
        Dictionary mapping dot-notation keys to the ConfigFile that set
        their final value. Keys use kebab-case (e.g., "worktree.default-location").

    Examples:
        >>> layers = (
        ...     ConfigFile(
        ...         path=global_path,
        ...         layer=ConfigLayer.GLOBAL,
        ...         exists=True,
        ...         content=global_config,
        ...     ),
        ...     ConfigFile(
        ...         path=project_path,
        ...         layer=ConfigLayer.PROJECT,
        ...         exists=True,
        ...         content=project_config,
        ...     ),
        ... )
        >>> provenance = _build_provenance_map(layers)
        >>> provenance.get("worktree.default-location")
        ConfigFile(path=project_path, ...)
    """
    provenance: dict[str, ConfigFile] = {}

    for layer in layers:
        if layer.content is None:
            continue

        # Extract all non-default keys from this layer
        keys_set = _extract_provenance_from_config(layer.content)

        # Update provenance map - later layers override earlier ones
        for key in keys_set:
            provenance[key] = layer

    return provenance


def _extract_provenance_from_config(config: ConfigSchema) -> set[str]:  # noqa: PLR0912
    """Extract all keys that differ from defaults in a configuration.

    Compares the given config against a default ConfigSchema to identify
    which keys have been explicitly set. Returns keys in dot-notation
    with kebab-case (matching TOML format).

    This function handles nested configuration structures:
    - Scalar fields: worktree.default-location, worktree.delete-branch
    - Nested tables: worktree.paths.sibling, worktree.sync.link
    - List fields: Both base lists and extend/exclude modifiers

    Args:
        config: ConfigSchema to extract provenance keys from.

    Returns:
        Set of dot-notation keys that differ from defaults.
        Keys use kebab-case format (e.g., "worktree.default-location").

    Examples:
        >>> config = ConfigSchema(
        ...     worktree=WorktreeConfig(
        ...         default_location="local", sync=SyncConfig(link=("CLAUDE.md",))
        ...     )
        ... )
        >>> keys = _extract_provenance_from_config(config)
        >>> "worktree.default-location" in keys
        True
        >>> "worktree.sync.link" in keys
        True
    """
    default_config = ConfigSchema()
    keys: set[str] = set()

    # Compare worktree level
    if config.worktree != default_config.worktree:
        # Scalar fields at worktree level
        if config.worktree.default_location != default_config.worktree.default_location:
            keys.add("worktree.default-location")
        if config.worktree.delete_branch != default_config.worktree.delete_branch:
            keys.add("worktree.delete-branch")
        if config.worktree.protected != default_config.worktree.protected:
            keys.add("worktree.protected")

        # Path patterns
        if config.worktree.paths != default_config.worktree.paths:
            if config.worktree.paths.sibling != default_config.worktree.paths.sibling:
                keys.add("worktree.paths.sibling")
            if config.worktree.paths.local != default_config.worktree.paths.local:
                keys.add("worktree.paths.local")
            if config.worktree.paths.pr != default_config.worktree.paths.pr:
                keys.add("worktree.paths.pr")

        # Sync configuration
        if config.worktree.sync != default_config.worktree.sync:
            # Base lists
            if config.worktree.sync.link != default_config.worktree.sync.link:
                keys.add("worktree.sync.link")
            if config.worktree.sync.copy != default_config.worktree.sync.copy:
                keys.add("worktree.sync.copy")

            # Extend/exclude modifiers
            if (
                config.worktree.sync.extend_link
                != default_config.worktree.sync.extend_link
            ):
                keys.add("worktree.sync.extend-link")
            if (
                config.worktree.sync.extend_copy
                != default_config.worktree.sync.extend_copy
            ):
                keys.add("worktree.sync.extend-copy")
            if (
                config.worktree.sync.exclude_link
                != default_config.worktree.sync.exclude_link
            ):
                keys.add("worktree.sync.exclude-link")
            if (
                config.worktree.sync.exclude_copy
                != default_config.worktree.sync.exclude_copy
            ):
                keys.add("worktree.sync.exclude-copy")

        # Hooks configuration
        if config.worktree.hooks != default_config.worktree.hooks:
            # Base lists
            if config.worktree.hooks.post_add != default_config.worktree.hooks.post_add:
                keys.add("worktree.hooks.post-add")
            if (
                config.worktree.hooks.pre_remove
                != default_config.worktree.hooks.pre_remove
            ):
                keys.add("worktree.hooks.pre-remove")

            # Extend/exclude modifiers
            if (
                config.worktree.hooks.extend_post_add
                != default_config.worktree.hooks.extend_post_add
            ):
                keys.add("worktree.hooks.extend-post-add")
            if (
                config.worktree.hooks.extend_pre_remove
                != default_config.worktree.hooks.extend_pre_remove
            ):
                keys.add("worktree.hooks.extend-pre-remove")
            if (
                config.worktree.hooks.exclude_post_add
                != default_config.worktree.hooks.exclude_post_add
            ):
                keys.add("worktree.hooks.exclude-post-add")
            if (
                config.worktree.hooks.exclude_pre_remove
                != default_config.worktree.hooks.exclude_pre_remove
            ):
                keys.add("worktree.hooks.exclude-pre-remove")

    return keys
