"""Configuration merging algorithms.

This module implements the layer merging algorithms for the configuration
system. It handles merging configuration layers according to the extend/exclude
semantics defined in the specification.

The core merge algorithm:
1. Start with base items
2. Remove items matching exclude set
3. Append items from extend list

This produces deterministic ordering: base items (minus exclusions) followed
by extensions in declaration order.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ._schema import (
    ConfigSchema,
    HooksConfig,
    PathPatterns,
    SyncConfig,
    WorktreeConfig,
)

if TYPE_CHECKING:
    from pathlib import Path

    from ._types import ConfigLayer


@dataclass(slots=True, frozen=True)
class MergeWarning:
    """Warning generated during configuration merge.

    Warnings are non-fatal issues detected during merging, such as attempting
    to exclude an item that doesn't exist in the base list. These often
    indicate typos or stale configuration.

    Attributes:
        key: Dot-notation key path where the warning occurred (e.g.,
            "worktree.sync.link").
        excluded_item: The item that was in the exclude list but not in the
            base list.
        layer: Configuration layer that contained the problematic exclude.
        source_path: Absolute path to the config file that generated the
            warning, or None for programmatically constructed configs.
    """

    key: str
    excluded_item: str
    layer: ConfigLayer
    source_path: Path | None


def merge_lists(
    base: tuple[str, ...],
    extend: tuple[str, ...],
    exclude: frozenset[str],
) -> tuple[str, ...]:
    """Merge list with extend/exclude modifiers.

    This is the core merge algorithm that implements the extend/exclude
    semantics. It processes lists deterministically to produce consistent
    output regardless of layer complexity.

    The algorithm:
    1. Filter base items, removing any that match the exclude set
    2. Append all items from extend
    3. Return the merged result

    This preserves ordering: filtered base items first, then extensions in
    the order they were declared.

    Args:
        base: Base list of items from upstream layers.
        extend: Additional items to append after filtering.
        exclude: Set of items to remove from base before extending.

    Returns:
        Merged tuple with deterministic ordering.

    Examples:
        >>> merge_lists(
        ...     base=("a", "b", "c"),
        ...     extend=("d", "e"),
        ...     exclude=frozenset({"b"}),
        ... )
        ('a', 'c', 'd', 'e')

        >>> merge_lists(
        ...     base=(".envrc", "CLAUDE.md", ".gemini/"),
        ...     extend=(".my-tool-config",),
        ...     exclude=frozenset({".envrc"}),
        ... )
        ('CLAUDE.md', '.gemini/', '.my-tool-config')

        >>> merge_lists(
        ...     base=(),
        ...     extend=("a", "b"),
        ...     exclude=frozenset(),
        ... )
        ('a', 'b')
    """
    # Filter base items, removing excludes
    filtered = tuple(item for item in base if item not in exclude)

    # Append extensions
    return filtered + extend


@dataclass(slots=True, frozen=True)
class _ListFieldMergeContext:
    """Context for merging a list field with extend/exclude modifiers.

    This dataclass bundles parameters for the list field merge operation,
    reducing the parameter count and improving type safety.

    Attributes:
        base: Base list from upstream layer.
        extend: Items to append from downstream layer.
        exclude: Items to remove from base before extending.
        key: Dot-notation key path for warning messages.
        layer: Configuration layer being merged.
        source_path: Path to config file for provenance tracking.
        base_explicitly_set: Whether downstream layer explicitly set the base
            field (triggering full replacement instead of extend/exclude).
    """

    base: tuple[str, ...]
    extend: tuple[str, ...]
    exclude: tuple[str, ...]
    key: str
    layer: ConfigLayer
    source_path: Path | None
    base_explicitly_set: bool


def _merge_list_field(
    ctx: _ListFieldMergeContext,
) -> tuple[tuple[str, ...], tuple[MergeWarning, ...]]:
    """Merge a single list field with extend/exclude modifiers.

    This helper handles the logic for merging a list field between two config
    layers. It checks whether the base was explicitly set (full replacement)
    or should be extended, generates warnings for non-existent excludes, and
    applies the merge algorithm.

    Args:
        ctx: Context containing all merge parameters.

    Returns:
        Tuple of (merged_list, warnings). The merged list is the result of
        applying extend/exclude semantics. Warnings are generated for each
        item in exclude that wasn't found in base.
    """
    # If downstream sets base explicitly, it's a full replacement
    # Ignore extend/exclude from downstream (they shouldn't be set anyway)
    if ctx.base_explicitly_set:
        return (ctx.base, ())

    # Generate warnings for non-existent excludes
    base_set_for_lookup = set(ctx.base)
    warnings = [
        MergeWarning(
            key=ctx.key,
            excluded_item=excluded_item,
            layer=ctx.layer,
            source_path=ctx.source_path,
        )
        for excluded_item in ctx.exclude
        if excluded_item not in base_set_for_lookup
    ]

    # Apply merge algorithm
    exclude_set = frozenset(ctx.exclude)
    merged = merge_lists(ctx.base, ctx.extend, exclude_set)

    return (merged, tuple(warnings))


def merge_sync_configs(
    upstream: SyncConfig,
    downstream: SyncConfig,
    layer: ConfigLayer,
    source_path: Path | None = None,
) -> tuple[SyncConfig, tuple[MergeWarning, ...]]:
    """Merge two SyncConfig layers.

    Merges sync configuration following extend/exclude semantics. Each list
    field (link, copy) can be either fully replaced if set explicitly in
    downstream, or extended/filtered using the extend_*/exclude_* fields.

    Args:
        upstream: Base sync configuration from lower-precedence layers.
        downstream: Override sync configuration from higher-precedence layer.
        layer: Configuration layer for the downstream config.
        source_path: Path to downstream config file for warning provenance.

    Returns:
        Tuple of (merged_config, warnings). The merged config has all list
        fields resolved. Warnings are generated for non-existent excludes.

    Examples:
        >>> upstream = SyncConfig(link=("a", "b", "c"))
        >>> downstream = SyncConfig(
        ...     extend_link=("d",),
        ...     exclude_link=("b",),
        ... )
        >>> merged, warnings = merge_sync_configs(
        ...     upstream, downstream, ConfigLayer.LOCAL
        ... )
        >>> merged.link
        ('a', 'c', 'd')
    """
    all_warnings: list[MergeWarning] = []

    # Merge link field
    link_base = downstream.link if downstream.link else upstream.link
    link_set = bool(downstream.link)
    link, link_warnings = _merge_list_field(
        _ListFieldMergeContext(
            base=link_base,
            extend=downstream.extend_link,
            exclude=downstream.exclude_link,
            key="worktree.sync.link",
            layer=layer,
            source_path=source_path,
            base_explicitly_set=link_set,
        )
    )
    all_warnings.extend(link_warnings)

    # Merge copy field
    copy_base = downstream.copy if downstream.copy else upstream.copy
    copy_set = bool(downstream.copy)
    copy, copy_warnings = _merge_list_field(
        _ListFieldMergeContext(
            base=copy_base,
            extend=downstream.extend_copy,
            exclude=downstream.exclude_copy,
            key="worktree.sync.copy",
            layer=layer,
            source_path=source_path,
            base_explicitly_set=copy_set,
        )
    )
    all_warnings.extend(copy_warnings)

    return (
        SyncConfig(
            link=link,
            copy=copy,
            extend_link=(),
            extend_copy=(),
            exclude_link=(),
            exclude_copy=(),
        ),
        tuple(all_warnings),
    )


def merge_hooks_configs(
    upstream: HooksConfig,
    downstream: HooksConfig,
    layer: ConfigLayer,
    source_path: Path | None = None,
) -> tuple[HooksConfig, tuple[MergeWarning, ...]]:
    """Merge two HooksConfig layers.

    Merges hook configuration following extend/exclude semantics. Each list
    field (post_add, pre_remove) can be either fully replaced if set
    explicitly in downstream, or extended/filtered using the extend_*/exclude_*
    fields.

    Args:
        upstream: Base hooks configuration from lower-precedence layers.
        downstream: Override hooks configuration from higher-precedence layer.
        layer: Configuration layer for the downstream config.
        source_path: Path to downstream config file for warning provenance.

    Returns:
        Tuple of (merged_config, warnings). The merged config has all list
        fields resolved. Warnings are generated for non-existent excludes.

    Examples:
        >>> upstream = HooksConfig(post_add=("uv sync",))
        >>> downstream = HooksConfig(extend_post_add=("direnv allow",))
        >>> merged, warnings = merge_hooks_configs(
        ...     upstream, downstream, ConfigLayer.LOCAL
        ... )
        >>> merged.post_add
        ('uv sync', 'direnv allow')
    """
    all_warnings: list[MergeWarning] = []

    # Merge post_add field
    post_add_base = downstream.post_add if downstream.post_add else upstream.post_add
    post_add_set = bool(downstream.post_add)
    post_add, post_add_warnings = _merge_list_field(
        _ListFieldMergeContext(
            base=post_add_base,
            extend=downstream.extend_post_add,
            exclude=downstream.exclude_post_add,
            key="worktree.hooks.post-add",
            layer=layer,
            source_path=source_path,
            base_explicitly_set=post_add_set,
        )
    )
    all_warnings.extend(post_add_warnings)

    # Merge pre_remove field
    pre_remove_base = (
        downstream.pre_remove if downstream.pre_remove else upstream.pre_remove
    )
    pre_remove_set = bool(downstream.pre_remove)
    pre_remove, pre_remove_warnings = _merge_list_field(
        _ListFieldMergeContext(
            base=pre_remove_base,
            extend=downstream.extend_pre_remove,
            exclude=downstream.exclude_pre_remove,
            key="worktree.hooks.pre-remove",
            layer=layer,
            source_path=source_path,
            base_explicitly_set=pre_remove_set,
        )
    )
    all_warnings.extend(pre_remove_warnings)

    return (
        HooksConfig(
            post_add=post_add,
            pre_remove=pre_remove,
            extend_post_add=(),
            extend_pre_remove=(),
            exclude_post_add=(),
            exclude_pre_remove=(),
        ),
        tuple(all_warnings),
    )


def merge_path_patterns(
    upstream: PathPatterns,
    downstream: PathPatterns,
) -> PathPatterns:
    """Merge PathPatterns with simple override semantics.

    PathPatterns fields are scalar strings, so merging uses simple override
    logic: any non-default downstream value replaces the upstream value.

    Args:
        upstream: Base path patterns from lower-precedence layers.
        downstream: Override path patterns from higher-precedence layer.

    Returns:
        Merged PathPatterns where downstream non-default values override
        upstream values.

    Examples:
        >>> default = PathPatterns()
        >>> upstream = PathPatterns(sibling="../{repo}-{branch}")
        >>> downstream = PathPatterns(local=".worktrees/{branch}")
        >>> merged = merge_path_patterns(upstream, downstream)
        >>> merged.sibling
        '../{repo}-{branch}'
        >>> merged.local
        '.worktrees/{branch}'
    """
    default = PathPatterns()

    return PathPatterns(
        sibling=(
            downstream.sibling
            if downstream.sibling != default.sibling
            else upstream.sibling
        ),
        local=(
            downstream.local if downstream.local != default.local else upstream.local
        ),
        pr=(downstream.pr if downstream.pr != default.pr else upstream.pr),
    )


def merge_worktree_configs(
    upstream: WorktreeConfig,
    downstream: WorktreeConfig,
    layer: ConfigLayer,
    source_path: Path | None = None,
) -> tuple[WorktreeConfig, tuple[MergeWarning, ...]]:
    """Merge two WorktreeConfig layers.

    Merges worktree configuration using a combination of override semantics
    for scalar fields and extend/exclude semantics for list fields in nested
    configs.

    Scalar fields (default_location, delete_branch, protected) use simple
    override: downstream non-default values replace upstream values.

    Nested configs (paths, sync, hooks) are merged recursively using their
    respective merge functions.

    Args:
        upstream: Base worktree configuration from lower-precedence layers.
        downstream: Override worktree configuration from higher-precedence
            layer.
        layer: Configuration layer for the downstream config.
        source_path: Path to downstream config file for warning provenance.

    Returns:
        Tuple of (merged_config, warnings). The merged config has all fields
        resolved. Warnings are collected from nested sync and hooks merging.

    Examples:
        >>> upstream = WorktreeConfig(
        ...     default_location="sibling",
        ...     sync=SyncConfig(link=("a", "b")),
        ... )
        >>> downstream = WorktreeConfig(
        ...     delete_branch=False,
        ...     sync=SyncConfig(extend_link=("c",)),
        ... )
        >>> merged, warnings = merge_worktree_configs(
        ...     upstream, downstream, ConfigLayer.LOCAL
        ... )
        >>> merged.default_location
        'sibling'
        >>> merged.delete_branch
        False
        >>> merged.sync.link
        ('a', 'b', 'c')
    """
    default = WorktreeConfig()
    all_warnings: list[MergeWarning] = []

    # Merge scalar fields with override semantics
    default_location = (
        downstream.default_location
        if downstream.default_location != default.default_location
        else upstream.default_location
    )
    delete_branch = (
        downstream.delete_branch
        if downstream.delete_branch != default.delete_branch
        else upstream.delete_branch
    )
    protected = (
        downstream.protected
        if downstream.protected != default.protected
        else upstream.protected
    )

    # Merge nested configs
    paths = merge_path_patterns(upstream.paths, downstream.paths)

    sync, sync_warnings = merge_sync_configs(
        upstream.sync, downstream.sync, layer, source_path
    )
    all_warnings.extend(sync_warnings)

    hooks, hooks_warnings = merge_hooks_configs(
        upstream.hooks, downstream.hooks, layer, source_path
    )
    all_warnings.extend(hooks_warnings)

    return (
        WorktreeConfig(
            default_location=default_location,
            delete_branch=delete_branch,
            protected=protected,
            paths=paths,
            sync=sync,
            hooks=hooks,
        ),
        tuple(all_warnings),
    )


def merge_config_schemas(
    upstream: ConfigSchema,
    downstream: ConfigSchema,
    layer: ConfigLayer,
    source_path: Path | None = None,
) -> tuple[ConfigSchema, tuple[MergeWarning, ...]]:
    """Merge two ConfigSchema layers.

    Merges complete configuration schemas by delegating to worktree config
    merging. This is the top-level merge function that should be used when
    combining configuration layers.

    Args:
        upstream: Base configuration schema from lower-precedence layers.
        downstream: Override configuration schema from higher-precedence layer.
        layer: Configuration layer for the downstream config.
        source_path: Path to downstream config file for warning provenance.

    Returns:
        Tuple of (merged_schema, warnings). The merged schema has all fields
        resolved through recursive merging. Warnings are propagated from
        nested merges.

    Examples:
        >>> upstream = ConfigSchema(
        ...     worktree=WorktreeConfig(sync=SyncConfig(link=(".envrc", "CLAUDE.md")))
        ... )
        >>> downstream = ConfigSchema(
        ...     worktree=WorktreeConfig(
        ...         sync=SyncConfig(
        ...             extend_link=(".my-config",),
        ...             exclude_link=(".envrc",),
        ...         )
        ...     )
        ... )
        >>> merged, warnings = merge_config_schemas(
        ...     upstream, downstream, ConfigLayer.LOCAL
        ... )
        >>> merged.worktree.sync.link
        ('CLAUDE.md', '.my-config')
    """
    worktree, warnings = merge_worktree_configs(
        upstream.worktree, downstream.worktree, layer, source_path
    )

    return (
        ConfigSchema(worktree=worktree),
        warnings,
    )
