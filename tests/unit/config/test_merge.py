"""Unit tests for configuration merging algorithms.

Tests cover merge_lists function, all config merge functions (sync, hooks,
paths, worktree, schema), and warning generation for invalid excludes.
"""

from __future__ import annotations

from pathlib import Path

from rig.config import (
    ConfigLayer,
    ConfigSchema,
    HooksConfig,
    PathPatterns,
    SyncConfig,
    WorktreeConfig,
)
from rig.config._merge import (
    MergeWarning,
    merge_config_schemas,
    merge_hooks_configs,
    merge_lists,
    merge_path_patterns,
    merge_sync_configs,
    merge_worktree_configs,
)


class TestMergeLists:
    def test_empty_base_non_empty_extend_returns_extend(self) -> None:
        result = merge_lists(
            base=(),
            extend=("a", "b", "c"),
            exclude=frozenset(),
        )

        assert result == ("a", "b", "c")

    def test_non_empty_base_empty_extend_returns_base(self) -> None:
        result = merge_lists(
            base=("a", "b", "c"),
            extend=(),
            exclude=frozenset(),
        )

        assert result == ("a", "b", "c")

    def test_both_empty_returns_empty(self) -> None:
        result = merge_lists(
            base=(),
            extend=(),
            exclude=frozenset(),
        )

        assert result == ()

    def test_exclude_single_item_removes_from_base(self) -> None:
        result = merge_lists(
            base=("a", "b", "c"),
            extend=(),
            exclude=frozenset({"b"}),
        )

        assert result == ("a", "c")

    def test_exclude_multiple_items_removes_all_from_base(self) -> None:
        result = merge_lists(
            base=("a", "b", "c", "d"),
            extend=(),
            exclude=frozenset({"b", "d"}),
        )

        assert result == ("a", "c")

    def test_exclude_all_items_returns_empty(self) -> None:
        result = merge_lists(
            base=("a", "b", "c"),
            extend=(),
            exclude=frozenset({"a", "b", "c"}),
        )

        assert result == ()

    def test_exclude_non_existent_item_is_noop(self) -> None:
        result = merge_lists(
            base=("a", "b", "c"),
            extend=(),
            exclude=frozenset({"nonexistent"}),
        )

        assert result == ("a", "b", "c")

    def test_extend_appends_to_filtered_base(self) -> None:
        result = merge_lists(
            base=("a", "b", "c"),
            extend=("d", "e"),
            exclude=frozenset({"b"}),
        )

        assert result == ("a", "c", "d", "e")

    def test_base_order_preserved_after_exclusions(self) -> None:
        result = merge_lists(
            base=("z", "y", "x", "w"),
            extend=(),
            exclude=frozenset({"y"}),
        )

        assert result == ("z", "x", "w")

    def test_extend_order_preserved(self) -> None:
        result = merge_lists(
            base=(),
            extend=("z", "y", "x"),
            exclude=frozenset(),
        )

        assert result == ("z", "y", "x")

    def test_duplicate_in_base_not_deduplicated(self) -> None:
        result = merge_lists(
            base=("a", "b", "a", "c"),
            extend=(),
            exclude=frozenset(),
        )

        assert result == ("a", "b", "a", "c")

    def test_exclude_removes_all_matching_duplicates(self) -> None:
        result = merge_lists(
            base=("a", "b", "a", "c", "a"),
            extend=(),
            exclude=frozenset({"a"}),
        )

        assert result == ("b", "c")

    def test_spec_example_merge(self) -> None:
        # From spec: base=[".envrc", "CLAUDE.md", ".gemini/"]
        # exclude=[".envrc"], extend=[".my-tool-config"]
        # Result: ["CLAUDE.md", ".gemini/", ".my-tool-config"]
        result = merge_lists(
            base=(".envrc", "CLAUDE.md", ".gemini/"),
            extend=(".my-tool-config",),
            exclude=frozenset({".envrc"}),
        )

        assert result == ("CLAUDE.md", ".gemini/", ".my-tool-config")


class TestMergeSyncConfigs:
    def test_base_replacement_when_downstream_sets_link(self) -> None:
        upstream = SyncConfig(link=("a", "b", "c"))
        downstream = SyncConfig(link=("x", "y"))

        merged, warnings = merge_sync_configs(upstream, downstream, ConfigLayer.LOCAL)

        assert merged.link == ("x", "y")
        assert warnings == ()

    def test_extend_link_adds_to_upstream(self) -> None:
        upstream = SyncConfig(link=("a", "b"))
        downstream = SyncConfig(extend_link=("c", "d"))

        merged, warnings = merge_sync_configs(upstream, downstream, ConfigLayer.LOCAL)

        assert merged.link == ("a", "b", "c", "d")
        assert warnings == ()

    def test_exclude_link_removes_from_upstream(self) -> None:
        upstream = SyncConfig(link=("a", "b", "c"))
        downstream = SyncConfig(exclude_link=("b",))

        merged, warnings = merge_sync_configs(upstream, downstream, ConfigLayer.LOCAL)

        assert merged.link == ("a", "c")
        assert warnings == ()

    def test_combined_extend_exclude_link(self) -> None:
        upstream = SyncConfig(link=("a", "b", "c"))
        downstream = SyncConfig(
            extend_link=("d", "e"),
            exclude_link=("b",),
        )

        merged, warnings = merge_sync_configs(upstream, downstream, ConfigLayer.LOCAL)

        assert merged.link == ("a", "c", "d", "e")
        assert warnings == ()

    def test_warning_for_non_existent_exclude_link(self) -> None:
        upstream = SyncConfig(link=("a", "b"))
        downstream = SyncConfig(exclude_link=("nonexistent",))

        merged, warnings = merge_sync_configs(
            upstream, downstream, ConfigLayer.LOCAL, Path("/test/config.toml")
        )

        assert merged.link == ("a", "b")
        assert len(warnings) == 1
        assert warnings[0].key == "worktree.sync.link"
        assert warnings[0].excluded_item == "nonexistent"
        assert warnings[0].layer == ConfigLayer.LOCAL
        assert warnings[0].source_path == Path("/test/config.toml")

    def test_extend_copy_adds_to_upstream(self) -> None:
        upstream = SyncConfig(copy=("file1", "file2"))
        downstream = SyncConfig(extend_copy=("file3",))

        merged, warnings = merge_sync_configs(upstream, downstream, ConfigLayer.PROJECT)

        assert merged.copy == ("file1", "file2", "file3")
        assert warnings == ()

    def test_exclude_copy_removes_from_upstream(self) -> None:
        upstream = SyncConfig(copy=("file1", "file2", "file3"))
        downstream = SyncConfig(exclude_copy=("file2",))

        merged, warnings = merge_sync_configs(upstream, downstream, ConfigLayer.PROJECT)

        assert merged.copy == ("file1", "file3")
        assert warnings == ()

    def test_combined_extend_exclude_copy(self) -> None:
        upstream = SyncConfig(copy=("file1", "file2"))
        downstream = SyncConfig(
            extend_copy=("file3",),
            exclude_copy=("file1",),
        )

        merged, warnings = merge_sync_configs(upstream, downstream, ConfigLayer.LOCAL)

        assert merged.copy == ("file2", "file3")
        assert warnings == ()

    def test_all_six_fields_processed_correctly(self) -> None:
        upstream = SyncConfig(
            link=("link1", "link2"),
            copy=("copy1", "copy2"),
        )
        downstream = SyncConfig(
            extend_link=("link3",),
            exclude_link=("link1",),
            extend_copy=("copy3",),
            exclude_copy=("copy1",),
        )

        merged, warnings = merge_sync_configs(upstream, downstream, ConfigLayer.LOCAL)

        assert merged.link == ("link2", "link3")
        assert merged.copy == ("copy2", "copy3")
        assert merged.extend_link == ()
        assert merged.extend_copy == ()
        assert merged.exclude_link == ()
        assert merged.exclude_copy == ()
        assert warnings == ()

    def test_multiple_warnings_for_multiple_invalid_excludes(self) -> None:
        upstream = SyncConfig(link=("a",), copy=("b",))
        downstream = SyncConfig(
            exclude_link=("x", "y"),
            exclude_copy=("z",),
        )

        _merged, warnings = merge_sync_configs(upstream, downstream, ConfigLayer.LOCAL)

        assert len(warnings) == 3
        warning_items = {w.excluded_item for w in warnings}
        assert warning_items == {"x", "y", "z"}

    def test_empty_upstream_with_extend(self) -> None:
        upstream = SyncConfig()
        downstream = SyncConfig(extend_link=("a", "b"))

        merged, warnings = merge_sync_configs(upstream, downstream, ConfigLayer.LOCAL)

        assert merged.link == ("a", "b")
        assert warnings == ()


class TestMergeHooksConfigs:
    def test_extend_post_add_adds_to_upstream(self) -> None:
        upstream = HooksConfig(post_add=("npm install",))
        downstream = HooksConfig(extend_post_add=("direnv allow",))

        merged, warnings = merge_hooks_configs(upstream, downstream, ConfigLayer.LOCAL)

        assert merged.post_add == ("npm install", "direnv allow")
        assert warnings == ()

    def test_exclude_post_add_removes_from_upstream(self) -> None:
        upstream = HooksConfig(post_add=("npm install", "setup.sh"))
        downstream = HooksConfig(exclude_post_add=("setup.sh",))

        merged, warnings = merge_hooks_configs(upstream, downstream, ConfigLayer.LOCAL)

        assert merged.post_add == ("npm install",)
        assert warnings == ()

    def test_extend_pre_remove_adds_to_upstream(self) -> None:
        upstream = HooksConfig(pre_remove=("cleanup.sh",))
        downstream = HooksConfig(extend_pre_remove=("backup.sh",))

        merged, warnings = merge_hooks_configs(upstream, downstream, ConfigLayer.LOCAL)

        assert merged.pre_remove == ("cleanup.sh", "backup.sh")
        assert warnings == ()

    def test_exclude_pre_remove_removes_from_upstream(self) -> None:
        upstream = HooksConfig(pre_remove=("cleanup.sh", "backup.sh"))
        downstream = HooksConfig(exclude_pre_remove=("backup.sh",))

        merged, warnings = merge_hooks_configs(upstream, downstream, ConfigLayer.LOCAL)

        assert merged.pre_remove == ("cleanup.sh",)
        assert warnings == ()

    def test_warning_for_non_existent_exclude_post_add(self) -> None:
        upstream = HooksConfig(post_add=("npm install",))
        downstream = HooksConfig(exclude_post_add=("nonexistent",))

        _merged, warnings = merge_hooks_configs(
            upstream, downstream, ConfigLayer.LOCAL, Path("/test/config.toml")
        )

        assert len(warnings) == 1
        assert warnings[0].key == "worktree.hooks.post-add"
        assert warnings[0].excluded_item == "nonexistent"

    def test_warning_for_non_existent_exclude_pre_remove(self) -> None:
        upstream = HooksConfig(pre_remove=("cleanup.sh",))
        downstream = HooksConfig(exclude_pre_remove=("nonexistent",))

        _merged, warnings = merge_hooks_configs(
            upstream, downstream, ConfigLayer.LOCAL, Path("/test/config.toml")
        )

        assert len(warnings) == 1
        assert warnings[0].key == "worktree.hooks.pre-remove"
        assert warnings[0].excluded_item == "nonexistent"

    def test_base_replacement_when_downstream_sets_post_add(self) -> None:
        upstream = HooksConfig(post_add=("old.sh",))
        downstream = HooksConfig(post_add=("new.sh",))

        merged, warnings = merge_hooks_configs(
            upstream, downstream, ConfigLayer.PROJECT
        )

        assert merged.post_add == ("new.sh",)
        assert warnings == ()

    def test_all_four_fields_cleared_in_result(self) -> None:
        upstream = HooksConfig(post_add=("a",), pre_remove=("b",))
        downstream = HooksConfig(
            extend_post_add=("c",),
            extend_pre_remove=("d",),
        )

        merged, _warnings = merge_hooks_configs(upstream, downstream, ConfigLayer.LOCAL)

        assert merged.extend_post_add == ()
        assert merged.extend_pre_remove == ()
        assert merged.exclude_post_add == ()
        assert merged.exclude_pre_remove == ()


class TestMergePathPatterns:
    def test_downstream_overrides_all_fields(self) -> None:
        upstream = PathPatterns(
            sibling="../{repo}-{branch}",
            local=".worktrees/{branch}",
            pr="../{repo}-pr-{number}",
        )
        downstream = PathPatterns(
            sibling="../custom-{branch}",
            local=".wt/{branch}",
            pr="../pr-{number}",
        )

        merged = merge_path_patterns(upstream, downstream)

        assert merged.sibling == "../custom-{branch}"
        assert merged.local == ".wt/{branch}"
        assert merged.pr == "../pr-{number}"

    def test_partial_override_preserves_upstream_defaults(self) -> None:
        upstream = PathPatterns(
            sibling="../custom-{branch}",
            local=".custom/{branch}",
        )
        downstream = PathPatterns(local=".override/{branch}")

        merged = merge_path_patterns(upstream, downstream)

        assert merged.sibling == "../custom-{branch}"
        assert merged.local == ".override/{branch}"
        assert merged.pr == "../{repo}-pr-{number}"  # default

    def test_default_downstream_values_ignored(self) -> None:
        upstream = PathPatterns(sibling="../custom-{branch}")
        downstream = PathPatterns()  # all defaults

        merged = merge_path_patterns(upstream, downstream)

        assert merged.sibling == "../custom-{branch}"
        assert merged.local == ".worktrees/{branch}"
        assert merged.pr == "../{repo}-pr-{number}"


class TestMergeWorktreeConfigs:
    def test_scalar_fields_override(self) -> None:
        upstream = WorktreeConfig(
            default_location="sibling",
            delete_branch=True,
            protected=False,
        )
        downstream = WorktreeConfig(
            default_location="local",
            delete_branch=False,
            protected=True,
        )

        merged, warnings = merge_worktree_configs(
            upstream, downstream, ConfigLayer.LOCAL
        )

        assert merged.default_location == "local"
        assert merged.delete_branch is False
        assert merged.protected is True
        assert warnings == ()

    def test_nested_sync_config_merged(self) -> None:
        upstream = WorktreeConfig(sync=SyncConfig(link=("a", "b")))
        downstream = WorktreeConfig(sync=SyncConfig(extend_link=("c",)))

        merged, warnings = merge_worktree_configs(
            upstream, downstream, ConfigLayer.LOCAL
        )

        assert merged.sync.link == ("a", "b", "c")
        assert warnings == ()

    def test_nested_hooks_config_merged(self) -> None:
        upstream = WorktreeConfig(hooks=HooksConfig(post_add=("setup.sh",)))
        downstream = WorktreeConfig(hooks=HooksConfig(extend_post_add=("init.sh",)))

        merged, warnings = merge_worktree_configs(
            upstream, downstream, ConfigLayer.LOCAL
        )

        assert merged.hooks.post_add == ("setup.sh", "init.sh")
        assert warnings == ()

    def test_nested_paths_merged(self) -> None:
        upstream = WorktreeConfig(paths=PathPatterns(sibling="../custom-{branch}"))
        downstream = WorktreeConfig(paths=PathPatterns(local=".wt/{branch}"))

        merged, _warnings = merge_worktree_configs(
            upstream, downstream, ConfigLayer.LOCAL
        )

        assert merged.paths.sibling == "../custom-{branch}"
        assert merged.paths.local == ".wt/{branch}"

    def test_warnings_collected_from_nested_merges(self) -> None:
        upstream = WorktreeConfig(
            sync=SyncConfig(link=("a",)),
            hooks=HooksConfig(post_add=("b",)),
        )
        downstream = WorktreeConfig(
            sync=SyncConfig(exclude_link=("nonexistent1",)),
            hooks=HooksConfig(exclude_post_add=("nonexistent2",)),
        )

        _merged, warnings = merge_worktree_configs(
            upstream, downstream, ConfigLayer.LOCAL, Path("/test/config.toml")
        )

        assert len(warnings) == 2
        warning_items = {w.excluded_item for w in warnings}
        assert warning_items == {"nonexistent1", "nonexistent2"}

    def test_default_values_not_overridden(self) -> None:
        upstream = WorktreeConfig(default_location="local")
        downstream = WorktreeConfig()  # all defaults

        merged, _warnings = merge_worktree_configs(
            upstream, downstream, ConfigLayer.LOCAL
        )

        assert merged.default_location == "local"
        assert merged.delete_branch is True  # default
        assert merged.protected is False  # default

    def test_complex_multi_field_merge(self) -> None:
        upstream = WorktreeConfig(
            default_location="sibling",
            delete_branch=True,
            paths=PathPatterns(sibling="../{repo}-{branch}"),
            sync=SyncConfig(link=("CLAUDE.md", ".envrc")),
            hooks=HooksConfig(post_add=("npm install",)),
        )
        downstream = WorktreeConfig(
            protected=True,
            paths=PathPatterns(local=".wt/{branch}"),
            sync=SyncConfig(
                extend_link=(".gemini/",),
                exclude_link=(".envrc",),
            ),
            hooks=HooksConfig(extend_post_add=("direnv allow",)),
        )

        merged, warnings = merge_worktree_configs(
            upstream, downstream, ConfigLayer.LOCAL
        )

        assert merged.default_location == "sibling"
        assert merged.delete_branch is True
        assert merged.protected is True
        assert merged.paths.sibling == "../{repo}-{branch}"
        assert merged.paths.local == ".wt/{branch}"
        assert merged.sync.link == ("CLAUDE.md", ".gemini/")
        assert merged.hooks.post_add == ("npm install", "direnv allow")
        assert warnings == ()


class TestMergeConfigSchemas:
    def test_delegates_to_worktree_merge(self) -> None:
        upstream = ConfigSchema(
            worktree=WorktreeConfig(
                default_location="sibling",
                sync=SyncConfig(link=("a",)),
            )
        )
        downstream = ConfigSchema(
            worktree=WorktreeConfig(
                default_location="local",
                sync=SyncConfig(extend_link=("b",)),
            )
        )

        merged, warnings = merge_config_schemas(upstream, downstream, ConfigLayer.LOCAL)

        assert merged.worktree.default_location == "local"
        assert merged.worktree.sync.link == ("a", "b")
        assert warnings == ()

    def test_collects_warnings_from_worktree_merge(self) -> None:
        upstream = ConfigSchema(worktree=WorktreeConfig(sync=SyncConfig(link=("a",))))
        downstream = ConfigSchema(
            worktree=WorktreeConfig(sync=SyncConfig(exclude_link=("nonexistent",)))
        )

        _merged, warnings = merge_config_schemas(
            upstream, downstream, ConfigLayer.LOCAL, Path("/test/config.toml")
        )

        assert len(warnings) == 1
        assert warnings[0].excluded_item == "nonexistent"


class TestMergeWarning:
    def test_warning_contains_expected_fields(self) -> None:
        warning = MergeWarning(
            key="worktree.sync.link",
            excluded_item=".envrc",
            layer=ConfigLayer.LOCAL,
            source_path=Path("/test/.rig.local.toml"),
        )

        assert warning.key == "worktree.sync.link"
        assert warning.excluded_item == ".envrc"
        assert warning.layer == ConfigLayer.LOCAL
        assert warning.source_path == Path("/test/.rig.local.toml")

    def test_warning_with_none_source_path(self) -> None:
        warning = MergeWarning(
            key="worktree.sync.copy",
            excluded_item="data/",
            layer=ConfigLayer.PROJECT,
            source_path=None,
        )

        assert warning.source_path is None
