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
"""

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
    "ConfigLayer",
    "ConfigSchema",
    "HooksConfig",
    "LayerSpec",
    "LocationStrategy",
    "OutputFormat",
    "PathPatterns",
    "PathPlaceholder",
    "SyncConfig",
    "WorktreeConfig",
]
