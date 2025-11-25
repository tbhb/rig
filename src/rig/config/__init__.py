"""Configuration system for rig.

This module provides the layered configuration system for rig, supporting
multiple configuration files with precedence-based merging.

Public API:
    Types:
        ConfigLayer: Enum identifying configuration layers
        LocationStrategy: Literal type for worktree placement
        PathPlaceholder: Literal type for path template placeholders
        OutputFormat: Literal type for output formatting
        LayerSpec: Union type for layer specifications

    Schema:
        ConfigSchema: Root configuration container
        WorktreeConfig: Worktree management settings
        PathPatterns: Path pattern templates
        SyncConfig: Path sync configuration
        HooksConfig: Lifecycle hook configuration

    Errors:
        ConfigError: Base exception for configuration errors
        ConfigParseError: Raised when TOML parsing fails
        ConfigValidationError: Raised when validation fails
        ConfigFileAccessError: Raised when file access fails

    Discovery:
        ConfigFile: Represents a discovered config file
        discover_config_files: Find all config files in resolution order
        find_ancestor_configs: Find .rig.toml files in ancestor directories

    Parsing:
        parse_config_file: Parse a TOML config file into a ConfigSchema

    Resolution:
        ResolvedConfig: Fully resolved configuration with provenance
        ResolvedMergeWarning: Warning with file provenance
        resolve_config: Load and merge all configuration layers

    Paths:
        get_global_config_path: Path to ~/.local/rig/config.toml
        get_project_config_path: Path to .rig.toml in project root
        get_local_config_path: Path to .rig.local.toml in project root
"""

from rig.config._discovery import (
    ConfigFile,
    discover_config_files,
    find_ancestor_configs,
)
from rig.config._errors import (
    ConfigError,
    ConfigFileAccessError,
    ConfigParseError,
    ConfigValidationError,
)
from rig.config._parser import (
    parse_config_file,
)
from rig.config._paths import (
    get_global_config_path,
    get_local_config_path,
    get_project_config_path,
)
from rig.config._resolver import (
    ResolvedConfig,
    ResolvedMergeWarning,
    resolve_config,
)
from rig.config._schema import (
    ConfigSchema,
    HooksConfig,
    PathPatterns,
    SyncConfig,
    WorktreeConfig,
)
from rig.config._types import (
    ConfigLayer,
    LayerSpec,
    LocationStrategy,
    OutputFormat,
    PathPlaceholder,
)

__all__ = [
    "ConfigError",
    "ConfigFile",
    "ConfigFileAccessError",
    "ConfigLayer",
    "ConfigParseError",
    "ConfigSchema",
    "ConfigValidationError",
    "HooksConfig",
    "LayerSpec",
    "LocationStrategy",
    "OutputFormat",
    "PathPatterns",
    "PathPlaceholder",
    "ResolvedConfig",
    "ResolvedMergeWarning",
    "SyncConfig",
    "WorktreeConfig",
    "discover_config_files",
    "find_ancestor_configs",
    "get_global_config_path",
    "get_local_config_path",
    "get_project_config_path",
    "parse_config_file",
    "resolve_config",
]
