"""Type definitions and enums for the configuration system.

This module defines the core type aliases and enumerations used throughout
the configuration system. All types are designed to be immutable and
suitable for use in frozen dataclasses.
"""

from enum import Enum
from typing import Literal


class ConfigLayer(Enum):
    """Configuration layer identifier.

    Configuration layers are processed in order from lowest to highest
    precedence: GLOBAL -> ANCESTOR -> PROJECT -> LOCAL. Each layer can
    override or extend values from previous layers.

    Attributes:
        GLOBAL: User-wide defaults in ~/.local/rig/config.toml
        ANCESTOR: Directory-based configs in parent directories (.rig.toml)
        PROJECT: Project-specific config in the repository root (.rig.toml)
        LOCAL: Personal overrides gitignored in the project (.rig.local.toml)
    """

    GLOBAL = "global"
    ANCESTOR = "ancestor"
    PROJECT = "project"
    LOCAL = "local"


LocationStrategy = Literal["sibling", "local"]
"""Strategy for worktree placement.

- "sibling": Place worktrees alongside the main repository
- "local": Place worktrees inside the repository in a hidden directory
"""

PathPlaceholder = Literal["{repo}", "{branch}", "{number}"]
"""Valid placeholders for path pattern templates.

- {repo}: Repository name
- {branch}: Branch name with slashes converted to dashes
- {number}: Pull request number
"""

OutputFormat = Literal["toml", "json"]
"""Output format for configuration display commands."""

LayerSpec = ConfigLayer | str
"""Layer specification for CLI commands.

Can be a ConfigLayer enum value or a string for special cases like
"ancestor:/path/to/.rig.toml" to specify a particular ancestor config.
"""
