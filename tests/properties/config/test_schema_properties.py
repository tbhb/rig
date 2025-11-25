"""Property-based tests and Hypothesis strategies for configuration schema.

The strategies defined here are reusable for testing loading, merging, and
CLI commands in future stages. The tests exercise these strategies and
verify order preservation for sync/hooks (which matters for execution order).
"""

from hypothesis import given, strategies as st
from hypothesis.strategies import DrawFn, composite

from rig.config import (
    ConfigSchema,
    HooksConfig,
    LocationStrategy,
    PathPatterns,
    SyncConfig,
    WorktreeConfig,
)

# --- Reusable Hypothesis Strategies ---
# Export these for use in other test modules


path_pattern_text = st.text(
    alphabet=st.characters(categories=["L", "N", "P"], exclude_characters="\x00"),
    min_size=0,
    max_size=100,
)

file_path_text = st.text(
    alphabet=st.characters(categories=["L", "N", "P", "S"], exclude_characters="\x00"),
    min_size=0,
    max_size=100,
)

hook_command_text = st.text(
    alphabet=st.characters(exclude_characters="\x00", exclude_categories=["Cs"]),
    min_size=0,
    max_size=200,
)


@composite
def path_patterns(draw: DrawFn) -> PathPatterns:
    return PathPatterns(
        sibling=draw(path_pattern_text),
        local=draw(path_pattern_text),
        pr=draw(path_pattern_text),
    )


@composite
def sync_configs(draw: DrawFn) -> SyncConfig:
    return SyncConfig(
        link=tuple(draw(st.lists(file_path_text, max_size=10))),
        copy=tuple(draw(st.lists(file_path_text, max_size=10))),
        extend_link=tuple(draw(st.lists(file_path_text, max_size=5))),
        extend_copy=tuple(draw(st.lists(file_path_text, max_size=5))),
        exclude_link=tuple(draw(st.lists(file_path_text, max_size=5))),
        exclude_copy=tuple(draw(st.lists(file_path_text, max_size=5))),
    )


@composite
def hooks_configs(draw: DrawFn) -> HooksConfig:
    return HooksConfig(
        post_add=tuple(draw(st.lists(hook_command_text, max_size=10))),
        pre_remove=tuple(draw(st.lists(hook_command_text, max_size=10))),
        extend_post_add=tuple(draw(st.lists(hook_command_text, max_size=5))),
        extend_pre_remove=tuple(draw(st.lists(hook_command_text, max_size=5))),
        exclude_post_add=tuple(draw(st.lists(hook_command_text, max_size=5))),
        exclude_pre_remove=tuple(draw(st.lists(hook_command_text, max_size=5))),
    )


@composite
def worktree_configs(draw: DrawFn) -> WorktreeConfig:
    location: LocationStrategy = draw(st.sampled_from(["sibling", "local"]))
    return WorktreeConfig(
        default_location=location,
        delete_branch=draw(st.booleans()),
        protected=draw(st.booleans()),
        paths=draw(path_patterns()),
        sync=draw(sync_configs()),
        hooks=draw(hooks_configs()),
    )


@composite
def config_schemas(draw: DrawFn) -> ConfigSchema:
    return ConfigSchema(worktree=draw(worktree_configs()))


# --- Order Preservation Tests ---
# Order matters for sync paths (symlink before copy) and hooks (execution order)


class TestSyncOrderPreservation:
    @given(items=st.lists(file_path_text, min_size=2, max_size=20))
    def test_link_order_preserved(self, items: list[str]) -> None:
        sync = SyncConfig(link=tuple(items))
        assert list(sync.link) == items

    @given(items=st.lists(file_path_text, min_size=2, max_size=20))
    def test_copy_order_preserved(self, items: list[str]) -> None:
        sync = SyncConfig(copy=tuple(items))
        assert list(sync.copy) == items


class TestHooksOrderPreservation:
    @given(items=st.lists(hook_command_text, min_size=2, max_size=20))
    def test_post_add_order_preserved(self, items: list[str]) -> None:
        hooks = HooksConfig(post_add=tuple(items))
        assert list(hooks.post_add) == items

    @given(items=st.lists(hook_command_text, min_size=2, max_size=20))
    def test_pre_remove_order_preserved(self, items: list[str]) -> None:
        hooks = HooksConfig(pre_remove=tuple(items))
        assert list(hooks.pre_remove) == items
