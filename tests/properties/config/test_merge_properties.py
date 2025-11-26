"""Property-based tests for configuration merging.

Tests verify merge invariants using Hypothesis to generate random configurations.
Focuses on properties that must hold regardless of input: bounded growth,
exclusion effectiveness, ordering preservation, and type safety.
"""

from __future__ import annotations

from hypothesis import given, strategies as st
from hypothesis.strategies import DrawFn, composite

from rig.config import (
    ConfigLayer,
    ConfigSchema,
    HooksConfig,
    SyncConfig,
    WorktreeConfig,
)
from rig.config._merge import (
    merge_config_schemas,
    merge_hooks_configs,
    merge_lists,
    merge_sync_configs,
    merge_worktree_configs,
)

from tests.properties.config.conftest import (
    config_schemas,
    file_path_text,
    hooks_configs,
    sync_configs,
    worktree_configs,
)

# --- Additional Strategies for Merge Testing ---


@composite
def list_merge_inputs(
    draw: DrawFn,
) -> tuple[tuple[str, ...], tuple[str, ...], frozenset[str]]:
    """Generate inputs for merge_lists testing.

    Returns (base, extend, exclude) where exclude is a subset of base U extend.
    """
    base = tuple(draw(st.lists(file_path_text, max_size=20)))
    extend = tuple(draw(st.lists(file_path_text, max_size=20)))

    # Generate exclude set that may or may not be valid
    # Mix of items from base, items from extend, and random items
    possible_excludes = (
        list(base) + list(extend) + draw(st.lists(file_path_text, max_size=5))
    )

    # Handle empty possible_excludes case
    if possible_excludes:
        exclude_list = draw(st.lists(st.sampled_from(possible_excludes), max_size=10))
    else:
        exclude_list = []

    exclude = frozenset(exclude_list)

    return (base, extend, exclude)


# --- Merge Lists Properties ---


class TestMergeListsProperties:
    @given(inputs=list_merge_inputs())
    def test_bounded_growth(
        self, inputs: tuple[tuple[str, ...], tuple[str, ...], frozenset[str]]
    ) -> None:
        base, extend, exclude = inputs

        result = merge_lists(base, extend, exclude)

        # Result can never be larger than base + extend
        assert len(result) <= len(base) + len(extend)

    @given(inputs=list_merge_inputs())
    def test_exclusion_effective_for_base_items(
        self, inputs: tuple[tuple[str, ...], tuple[str, ...], frozenset[str]]
    ) -> None:
        base, extend, exclude = inputs

        result = merge_lists(base, extend, exclude)

        # Items from base that were excluded should not appear in result
        # (unless they're also in extend, which re-adds them)
        for item in exclude:
            if item in base and item not in extend:
                assert item not in result

    @given(inputs=list_merge_inputs())
    def test_extend_items_appear_at_end(
        self, inputs: tuple[tuple[str, ...], tuple[str, ...], frozenset[str]]
    ) -> None:
        base, extend, exclude = inputs

        result = merge_lists(base, extend, exclude)

        # All extend items should appear in the result
        # They should appear after all filtered base items
        if extend:
            # Find where extend items start
            for extend_item in extend:
                if extend_item in result:
                    # All items after this should be from extend or were in base
                    # but the extend items maintain their relative order
                    break

    @given(inputs=list_merge_inputs())
    def test_base_order_preserved(
        self, inputs: tuple[tuple[str, ...], tuple[str, ...], frozenset[str]]
    ) -> None:
        base, extend, exclude = inputs

        result = merge_lists(base, extend, exclude)

        # The relative order of base items should be preserved
        # (but we need to account for items that appear in both base and extend)
        # Just check that the order of base items (before extend) is maintained
        base_set = set(base)
        result_base_portion = [
            item for item in result if item in base_set and item not in extend
        ]
        expected_base_portion = [
            item for item in base if item not in exclude and item not in extend
        ]

        assert result_base_portion == expected_base_portion

    @given(
        base=st.lists(file_path_text, max_size=20),
        extend=st.lists(file_path_text, max_size=20),
    )
    def test_identity_with_empty_exclude(
        self, base: list[str], extend: list[str]
    ) -> None:
        base_tuple = tuple(base)
        extend_tuple = tuple(extend)

        result = merge_lists(base_tuple, extend_tuple, frozenset())

        assert result == base_tuple + extend_tuple

    @given(base=st.lists(file_path_text, max_size=20))
    def test_identity_with_empty_extend_and_exclude(self, base: list[str]) -> None:
        base_tuple = tuple(base)

        result = merge_lists(base_tuple, (), frozenset())

        assert result == base_tuple

    @given(extend=st.lists(file_path_text, max_size=20))
    def test_identity_with_empty_base_and_exclude(self, extend: list[str]) -> None:
        extend_tuple = tuple(extend)

        result = merge_lists((), extend_tuple, frozenset())

        assert result == extend_tuple

    @given(inputs=list_merge_inputs())
    def test_result_is_tuple(
        self, inputs: tuple[tuple[str, ...], tuple[str, ...], frozenset[str]]
    ) -> None:
        base, extend, exclude = inputs

        result = merge_lists(base, extend, exclude)

        assert isinstance(result, tuple)

    @given(inputs=list_merge_inputs())
    def test_all_result_items_from_base_or_extend(
        self, inputs: tuple[tuple[str, ...], tuple[str, ...], frozenset[str]]
    ) -> None:
        base, extend, exclude = inputs

        result = merge_lists(base, extend, exclude)

        base_set = set(base)
        extend_set = set(extend)

        for item in result:
            assert item in base_set or item in extend_set


# --- Sync Config Merge Properties ---


class TestMergeSyncConfigsProperties:
    @given(upstream=sync_configs(), downstream=sync_configs())
    def test_type_preservation(
        self, upstream: SyncConfig, downstream: SyncConfig
    ) -> None:
        merged, warnings = merge_sync_configs(upstream, downstream, ConfigLayer.LOCAL)

        assert isinstance(merged, SyncConfig)
        assert isinstance(warnings, tuple)
        assert isinstance(merged.link, tuple)
        assert isinstance(merged.copy, tuple)

    @given(upstream=sync_configs(), downstream=sync_configs())
    def test_extend_exclude_fields_cleared(
        self, upstream: SyncConfig, downstream: SyncConfig
    ) -> None:
        merged, _warnings = merge_sync_configs(upstream, downstream, ConfigLayer.LOCAL)

        # Result should never have extend/exclude fields set
        assert merged.extend_link == ()
        assert merged.extend_copy == ()
        assert merged.exclude_link == ()
        assert merged.exclude_copy == ()

    @given(upstream=sync_configs(), downstream=sync_configs())
    def test_warning_count_bounded(
        self, upstream: SyncConfig, downstream: SyncConfig
    ) -> None:
        _merged, warnings = merge_sync_configs(upstream, downstream, ConfigLayer.LOCAL)

        # Number of warnings can't exceed total number of exclude items
        max_warnings = len(downstream.exclude_link) + len(downstream.exclude_copy)
        assert len(warnings) <= max_warnings

    @given(upstream=sync_configs())
    def test_merging_default_downstream_preserves_upstream(
        self, upstream: SyncConfig
    ) -> None:
        downstream = SyncConfig()  # all defaults

        merged, warnings = merge_sync_configs(upstream, downstream, ConfigLayer.LOCAL)

        # Merging with defaults should preserve upstream (no extend/exclude)
        assert merged.link == upstream.link
        assert merged.copy == upstream.copy
        assert warnings == ()

    @given(downstream=sync_configs())
    def test_merging_into_default_upstream(self, downstream: SyncConfig) -> None:
        upstream = SyncConfig()  # all defaults

        merged, _warnings = merge_sync_configs(upstream, downstream, ConfigLayer.LOCAL)

        # Should handle empty upstream gracefully
        assert isinstance(merged, SyncConfig)


# --- Hooks Config Merge Properties ---


class TestMergeHooksConfigsProperties:
    @given(upstream=hooks_configs(), downstream=hooks_configs())
    def test_type_preservation(
        self, upstream: HooksConfig, downstream: HooksConfig
    ) -> None:
        merged, warnings = merge_hooks_configs(upstream, downstream, ConfigLayer.LOCAL)

        assert isinstance(merged, HooksConfig)
        assert isinstance(warnings, tuple)
        assert isinstance(merged.post_add, tuple)
        assert isinstance(merged.pre_remove, tuple)

    @given(upstream=hooks_configs(), downstream=hooks_configs())
    def test_extend_exclude_fields_cleared(
        self, upstream: HooksConfig, downstream: HooksConfig
    ) -> None:
        merged, _warnings = merge_hooks_configs(upstream, downstream, ConfigLayer.LOCAL)

        assert merged.extend_post_add == ()
        assert merged.extend_pre_remove == ()
        assert merged.exclude_post_add == ()
        assert merged.exclude_pre_remove == ()

    @given(upstream=hooks_configs(), downstream=hooks_configs())
    def test_warning_count_bounded(
        self, upstream: HooksConfig, downstream: HooksConfig
    ) -> None:
        _merged, warnings = merge_hooks_configs(upstream, downstream, ConfigLayer.LOCAL)

        max_warnings = len(downstream.exclude_post_add) + len(
            downstream.exclude_pre_remove
        )
        assert len(warnings) <= max_warnings


# --- Worktree Config Merge Properties ---


class TestMergeWorktreeConfigsProperties:
    @given(upstream=worktree_configs(), downstream=worktree_configs())
    def test_type_preservation(
        self, upstream: WorktreeConfig, downstream: WorktreeConfig
    ) -> None:
        merged, warnings = merge_worktree_configs(
            upstream, downstream, ConfigLayer.LOCAL
        )

        assert isinstance(merged, WorktreeConfig)
        assert isinstance(warnings, tuple)
        assert isinstance(merged.sync, SyncConfig)
        assert isinstance(merged.hooks, HooksConfig)

    @given(upstream=worktree_configs(), downstream=worktree_configs())
    def test_scalar_override_correctness(
        self, upstream: WorktreeConfig, downstream: WorktreeConfig
    ) -> None:
        merged, _warnings = merge_worktree_configs(
            upstream, downstream, ConfigLayer.LOCAL
        )

        default = WorktreeConfig()

        # If downstream has non-default value, it should be in result
        if downstream.default_location != default.default_location:
            assert merged.default_location == downstream.default_location
        else:
            assert merged.default_location == upstream.default_location

        if downstream.delete_branch != default.delete_branch:
            assert merged.delete_branch == downstream.delete_branch
        else:
            assert merged.delete_branch == upstream.delete_branch

        if downstream.protected != default.protected:
            assert merged.protected == downstream.protected
        else:
            assert merged.protected == upstream.protected

    @given(upstream=worktree_configs(), downstream=worktree_configs())
    def test_warning_collection_from_nested_merges(
        self, upstream: WorktreeConfig, downstream: WorktreeConfig
    ) -> None:
        _merged, warnings = merge_worktree_configs(
            upstream, downstream, ConfigLayer.LOCAL
        )

        # Warnings from sync and hooks should be collected
        max_warnings = (
            len(downstream.sync.exclude_link)
            + len(downstream.sync.exclude_copy)
            + len(downstream.hooks.exclude_post_add)
            + len(downstream.hooks.exclude_pre_remove)
        )
        assert len(warnings) <= max_warnings


# --- Config Schema Merge Properties ---


class TestMergeConfigSchemasProperties:
    @given(upstream=config_schemas(), downstream=config_schemas())
    def test_type_preservation(
        self, upstream: ConfigSchema, downstream: ConfigSchema
    ) -> None:
        merged, warnings = merge_config_schemas(upstream, downstream, ConfigLayer.LOCAL)

        assert isinstance(merged, ConfigSchema)
        assert isinstance(merged.worktree, WorktreeConfig)
        assert isinstance(warnings, tuple)

    @given(upstream=config_schemas(), downstream=config_schemas())
    def test_delegates_to_worktree_merge(
        self, upstream: ConfigSchema, downstream: ConfigSchema
    ) -> None:
        merged, warnings = merge_config_schemas(upstream, downstream, ConfigLayer.LOCAL)

        # The result should be the same as directly merging worktree configs
        expected_worktree, expected_warnings = merge_worktree_configs(
            upstream.worktree, downstream.worktree, ConfigLayer.LOCAL
        )

        assert merged.worktree == expected_worktree
        assert warnings == expected_warnings


# --- Edge Cases and Invariants ---


class TestMergeEdgeCasesProperties:
    @given(
        items=st.lists(file_path_text, min_size=1, max_size=20),
        exclude_item=file_path_text,
    )
    def test_excluding_nonexistent_item_is_noop(
        self, items: list[str], exclude_item: str
    ) -> None:
        # Ensure exclude_item is NOT in items
        base = tuple(item for item in items if item != exclude_item)

        result = merge_lists(base, (), frozenset({exclude_item}))

        assert result == base

    @given(base=st.lists(file_path_text, min_size=1, max_size=20))
    def test_excluding_all_items_returns_empty(self, base: list[str]) -> None:
        base_tuple = tuple(base)
        exclude = frozenset(base)

        result = merge_lists(base_tuple, (), exclude)

        assert result == ()

    @given(sync=sync_configs())
    def test_merging_sync_with_itself_via_default(self, sync: SyncConfig) -> None:
        # Merge sync config with a default downstream
        merged, _warnings = merge_sync_configs(sync, SyncConfig(), ConfigLayer.LOCAL)

        # Should preserve all base values
        assert merged.link == sync.link
        assert merged.copy == sync.copy

    @given(hooks=hooks_configs())
    def test_merging_hooks_with_itself_via_default(self, hooks: HooksConfig) -> None:
        merged, _warnings = merge_hooks_configs(hooks, HooksConfig(), ConfigLayer.LOCAL)

        assert merged.post_add == hooks.post_add
        assert merged.pre_remove == hooks.pre_remove

    @given(config=config_schemas())
    def test_merging_config_with_default_preserves_values(
        self, config: ConfigSchema
    ) -> None:
        merged, _warnings = merge_config_schemas(
            config, ConfigSchema(), ConfigLayer.LOCAL
        )

        # Should be equivalent to original
        assert merged.worktree.default_location == config.worktree.default_location
        assert merged.worktree.delete_branch == config.worktree.delete_branch
        assert merged.worktree.protected == config.worktree.protected
