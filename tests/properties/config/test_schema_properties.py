"""Property-based tests for configuration schema.

Tests order preservation for sync/hooks (which matters for execution order).
Strategies are defined in conftest.py and shared across test modules.
"""

from hypothesis import given, strategies as st

from rig.config import (
    HooksConfig,
    SyncConfig,
)

# Import strategies from conftest
from tests.properties.config.conftest import file_path_text, hook_command_text

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
