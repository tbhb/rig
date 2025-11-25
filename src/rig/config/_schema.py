"""Configuration schema dataclasses.

This module defines the frozen dataclass hierarchy for the configuration
schema. All dataclasses use slots for memory efficiency and are frozen
for immutability.

The schema follows a nested structure:
    ConfigSchema
    └── WorktreeConfig
        ├── PathPatterns
        ├── SyncConfig
        └── HooksConfig
"""

from dataclasses import dataclass, field
from typing import Literal


@dataclass(slots=True, frozen=True)
class PathPatterns:
    """Path pattern templates for worktree locations.

    Patterns support placeholders: {repo}, {branch}, {number}.
    The {branch} placeholder converts slashes to dashes for filesystem safety.

    Attributes:
        sibling: Template for sibling worktrees (alongside main repo).
        local: Template for local worktrees (inside repo).
        pr: Template for pull request worktrees.
    """

    sibling: str = "../{repo}-{branch}"
    local: str = ".worktrees/{branch}"
    pr: str = "../{repo}-pr-{number}"


@dataclass(slots=True, frozen=True)
class SyncConfig:
    """Configuration for syncing paths between worktrees.

    Base lists (link, copy) are set in upstream configs. Downstream configs
    use extend_* and exclude_* to modify without full replacement.

    Attributes:
        link: Paths to symlink from the main worktree.
        copy: Paths to copy from the main worktree.
        extend_link: Additional paths to add to the link list.
        extend_copy: Additional paths to add to the copy list.
        exclude_link: Paths to remove from the link list.
        exclude_copy: Paths to remove from the copy list.
    """

    link: tuple[str, ...] = ()
    copy: tuple[str, ...] = ()
    extend_link: tuple[str, ...] = ()
    extend_copy: tuple[str, ...] = ()
    exclude_link: tuple[str, ...] = ()
    exclude_copy: tuple[str, ...] = ()


@dataclass(slots=True, frozen=True)
class HooksConfig:
    """Configuration for worktree lifecycle hooks.

    Hooks are shell commands executed during worktree operations.
    Commands receive worktree context via environment variables.

    Base lists (post_add, pre_remove) are set in upstream configs.
    Downstream configs use extend_* and exclude_* to modify.

    Attributes:
        post_add: Commands to run after creating a worktree.
        pre_remove: Commands to run before removing a worktree.
        extend_post_add: Additional commands to add to post_add.
        extend_pre_remove: Additional commands to add to pre_remove.
        exclude_post_add: Commands to remove from post_add.
        exclude_pre_remove: Commands to remove from pre_remove.
    """

    post_add: tuple[str, ...] = ()
    pre_remove: tuple[str, ...] = ()
    extend_post_add: tuple[str, ...] = ()
    extend_pre_remove: tuple[str, ...] = ()
    exclude_post_add: tuple[str, ...] = ()
    exclude_pre_remove: tuple[str, ...] = ()


@dataclass(slots=True, frozen=True)
class WorktreeConfig:
    """Configuration for worktree management.

    Contains all settings related to worktree creation, sync behavior,
    and lifecycle hooks.

    Attributes:
        default_location: Default placement strategy ("sibling" or "local").
        delete_branch: Whether to delete the branch when removing a worktree.
        protected: Whether the worktree is protected from accidental removal.
        paths: Path pattern templates for worktree locations.
        sync: Configuration for syncing paths between worktrees.
        hooks: Configuration for lifecycle hooks.
    """

    default_location: Literal["sibling", "local"] = "sibling"
    delete_branch: bool = True
    protected: bool = False
    paths: PathPatterns = field(default_factory=PathPatterns)
    sync: SyncConfig = field(default_factory=SyncConfig)
    hooks: HooksConfig = field(default_factory=HooksConfig)


@dataclass(slots=True, frozen=True)
class ConfigSchema:
    """Root configuration schema.

    This is the top-level container for all configuration sections.
    Currently only contains worktree configuration, but structured
    to allow future expansion.

    Attributes:
        worktree: Worktree management configuration.
    """

    worktree: WorktreeConfig = field(default_factory=WorktreeConfig)
