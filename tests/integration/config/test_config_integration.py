from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from rig.config import resolve_config

if TYPE_CHECKING:
    from pathlib import Path

# xfail markers reference stage files in plans/rig-config/
_STAGE_1 = "Stage 1: loading"
_STAGE_2 = "Stage 2: merging"
_STAGE_3 = "Stage 3: read commands"
_STAGE_4 = "Stage 4: write commands"
_STAGE_5 = "Stage 5: edit command"
_STAGE_6 = "Stage 6: diagnostic commands"


class TestConfigFileDiscovery:
    @pytest.mark.xfail(reason=_STAGE_1, strict=True)
    def test_discovers_global_config(self, global_config_file: Path) -> None:
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason=_STAGE_1, strict=True)
    def test_discovers_project_config(self, project_config_file: Path) -> None:
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason=_STAGE_1, strict=True)
    def test_discovers_local_config(self, local_config_file: Path) -> None:
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason=_STAGE_1, strict=True)
    def test_discovers_ancestor_configs(
        self, ancestor_config_file: Path, project_dir: Path
    ) -> None:
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason=_STAGE_1, strict=True)
    def test_discovers_multiple_ancestor_configs(
        self, multi_ancestor_hierarchy: dict[str, Path]
    ) -> None:
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason=_STAGE_1, strict=True)
    def test_returns_empty_for_no_config(self, empty_project_dir: Path) -> None:
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason=_STAGE_1, strict=True)
    def test_stops_at_filesystem_root(self, project_dir: Path) -> None:
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason=_STAGE_1, strict=True)
    def test_stops_at_home_directory(self, temp_home: Path, project_dir: Path) -> None:
        pytest.fail("Not implemented")


class TestConfigFileParsing:
    @pytest.mark.xfail(reason=_STAGE_1, strict=True)
    def test_parses_valid_toml(self, project_config_file: Path) -> None:
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason=_STAGE_1, strict=True)
    def test_raises_on_invalid_toml_syntax(self, invalid_toml_config: Path) -> None:
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason=_STAGE_1, strict=True)
    def test_raises_on_invalid_schema(self, invalid_schema_config: Path) -> None:
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason=_STAGE_1, strict=True)
    def test_handles_empty_config_file(self, project_dir: Path) -> None:
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason=_STAGE_1, strict=True)
    def test_handles_partial_config(self, project_dir: Path) -> None:
        pytest.fail("Not implemented")


class TestMultiLayerMerging:
    def test_project_overrides_global(
        self, global_config_file: Path, project_config_file: Path, temp_home: Path
    ) -> None:
        assert global_config_file.exists()  # Fixture creates the file
        project_dir = project_config_file.parent

        resolved = resolve_config(project_dir, home_dir=temp_home)

        # Project sets default-location to "local", overriding global's "sibling"
        assert resolved.config.worktree.default_location == "local"

    def test_local_overrides_project(
        self, project_config_file: Path, local_config_file: Path, temp_home: Path
    ) -> None:
        assert local_config_file.exists()  # Fixture creates the file
        project_dir = project_config_file.parent

        resolved = resolve_config(project_dir, home_dir=temp_home)

        # Local sets protected to true, overriding project's implicit false
        assert resolved.config.worktree.protected is True

    def test_full_precedence_order(
        self,
        global_config_file: Path,
        ancestor_config_file: Path,
        project_config_file: Path,
        local_config_file: Path,
        temp_home: Path,
    ) -> None:
        # Fixtures create the files
        assert global_config_file.exists()
        assert ancestor_config_file.exists()
        assert local_config_file.exists()

        project_dir = project_config_file.parent

        resolved = resolve_config(project_dir, home_dir=temp_home)

        # Global: default-location = "sibling", delete-branch = true
        # Ancestor: delete-branch = false, paths.sibling = "../wt/{branch}"
        # Project: default-location = "local"
        # Local: protected = true
        assert resolved.config.worktree.default_location == "local"  # from project
        assert resolved.config.worktree.delete_branch is False  # from ancestor
        assert resolved.config.worktree.protected is True  # from local
        # from ancestor
        assert resolved.config.worktree.paths.sibling == "../wt/{branch}"

    def test_ancestor_configs_merge_in_order(
        self, multi_ancestor_hierarchy: dict[str, Path], temp_home: Path
    ) -> None:
        project_dir = multi_ancestor_hierarchy["project"]

        resolved = resolve_config(project_dir, home_dir=temp_home)

        # Root: link = [".env"]
        # Org: extend-link = [".secrets"]
        # Project: extend-link = ["node_modules"], exclude-link = [".secrets"]
        # Result: [".env", "node_modules"]
        assert resolved.config.worktree.sync.link == (".env", "node_modules")

        # Root: default-location = "sibling"
        # Org: delete-branch = false
        # Team: paths.sibling = "../{repo}-wt-{branch}"
        # Project: protected = true
        assert resolved.config.worktree.default_location == "sibling"
        assert resolved.config.worktree.delete_branch is False
        assert resolved.config.worktree.protected is True
        assert resolved.config.worktree.paths.sibling == "../{repo}-wt-{branch}"

        # Hooks: Team adds ["team-setup.sh"], Project extends
        assert resolved.config.worktree.hooks.post_add == (
            "team-setup.sh",
            "npm install",
        )

    def test_defaults_used_when_no_config(
        self, empty_project_dir: Path, temp_home: Path
    ) -> None:
        resolved = resolve_config(empty_project_dir, home_dir=temp_home)

        # Should have all default values
        assert resolved.config.worktree.default_location == "sibling"
        assert resolved.config.worktree.delete_branch is True
        assert resolved.config.worktree.protected is False
        assert resolved.config.worktree.sync.link == ()
        assert resolved.config.worktree.sync.copy == ()
        assert resolved.config.worktree.hooks.post_add == ()
        assert resolved.config.worktree.hooks.pre_remove == ()


class TestExtendExcludeResolution:
    def test_extend_link_adds_to_base(self, project_dir: Path, temp_home: Path) -> None:
        # Set up base and extend
        project_config = project_dir / ".rig.toml"
        project_config.write_text("""
[worktree.sync]
link = ["base-link"]
""")
        local_config = project_dir / ".rig.local.toml"
        local_config.write_text("""
[worktree.sync]
extend-link = ["extra-link"]
""")

        resolved = resolve_config(project_dir, home_dir=temp_home)

        assert resolved.config.worktree.sync.link == ("base-link", "extra-link")

    def test_extend_copy_adds_to_base(self, project_dir: Path, temp_home: Path) -> None:
        project_config = project_dir / ".rig.toml"
        project_config.write_text("""
[worktree.sync]
copy = ["base-copy"]
""")
        local_config = project_dir / ".rig.local.toml"
        local_config.write_text("""
[worktree.sync]
extend-copy = ["extra-copy"]
""")

        resolved = resolve_config(project_dir, home_dir=temp_home)

        assert resolved.config.worktree.sync.copy == ("base-copy", "extra-copy")

    def test_exclude_link_removes_from_base(
        self, project_dir: Path, temp_home: Path
    ) -> None:
        project_config = project_dir / ".rig.toml"
        project_config.write_text("""
[worktree.sync]
link = ["keep", "remove", "also-keep"]
""")
        local_config = project_dir / ".rig.local.toml"
        local_config.write_text("""
[worktree.sync]
exclude-link = ["remove"]
""")

        resolved = resolve_config(project_dir, home_dir=temp_home)

        assert resolved.config.worktree.sync.link == ("keep", "also-keep")

    def test_exclude_copy_removes_from_base(
        self, project_dir: Path, temp_home: Path
    ) -> None:
        project_config = project_dir / ".rig.toml"
        project_config.write_text("""
[worktree.sync]
copy = ["data/", "temp/", "cache/"]
""")
        local_config = project_dir / ".rig.local.toml"
        local_config.write_text("""
[worktree.sync]
exclude-copy = ["temp/"]
""")

        resolved = resolve_config(project_dir, home_dir=temp_home)

        assert resolved.config.worktree.sync.copy == ("data/", "cache/")

    def test_extend_post_add_adds_to_base(
        self, project_dir: Path, temp_home: Path
    ) -> None:
        project_config = project_dir / ".rig.toml"
        project_config.write_text("""
[worktree.hooks]
post-add = ["npm install"]
""")
        local_config = project_dir / ".rig.local.toml"
        local_config.write_text("""
[worktree.hooks]
extend-post-add = ["direnv allow"]
""")

        resolved = resolve_config(project_dir, home_dir=temp_home)

        assert resolved.config.worktree.hooks.post_add == (
            "npm install",
            "direnv allow",
        )

    def test_extend_pre_remove_adds_to_base(
        self, project_dir: Path, temp_home: Path
    ) -> None:
        project_config = project_dir / ".rig.toml"
        project_config.write_text("""
[worktree.hooks]
pre-remove = ["cleanup.sh"]
""")
        local_config = project_dir / ".rig.local.toml"
        local_config.write_text("""
[worktree.hooks]
extend-pre-remove = ["backup.sh"]
""")

        resolved = resolve_config(project_dir, home_dir=temp_home)

        assert resolved.config.worktree.hooks.pre_remove == (
            "cleanup.sh",
            "backup.sh",
        )

    def test_exclude_post_add_removes_from_base(
        self, project_dir: Path, temp_home: Path
    ) -> None:
        project_config = project_dir / ".rig.toml"
        project_config.write_text("""
[worktree.hooks]
post-add = ["setup.sh", "old.sh", "init.sh"]
""")
        local_config = project_dir / ".rig.local.toml"
        local_config.write_text("""
[worktree.hooks]
exclude-post-add = ["old.sh"]
""")

        resolved = resolve_config(project_dir, home_dir=temp_home)

        assert resolved.config.worktree.hooks.post_add == ("setup.sh", "init.sh")

    def test_exclude_pre_remove_removes_from_base(
        self, project_dir: Path, temp_home: Path
    ) -> None:
        project_config = project_dir / ".rig.toml"
        project_config.write_text("""
[worktree.hooks]
pre-remove = ["cleanup.sh", "skip.sh"]
""")
        local_config = project_dir / ".rig.local.toml"
        local_config.write_text("""
[worktree.hooks]
exclude-pre-remove = ["skip.sh"]
""")

        resolved = resolve_config(project_dir, home_dir=temp_home)

        assert resolved.config.worktree.hooks.pre_remove == ("cleanup.sh",)

    def test_extend_exclude_across_layers(
        self, multi_ancestor_hierarchy: dict[str, Path], temp_home: Path
    ) -> None:
        project_dir = multi_ancestor_hierarchy["project"]

        resolved = resolve_config(project_dir, home_dir=temp_home)

        # Verify the multi-layer extend/exclude from fixtures works
        # Root: link = [".env"]
        # Org: extend-link = [".secrets"]
        # Project: extend-link = ["node_modules"], exclude-link = [".secrets"]
        assert resolved.config.worktree.sync.link == (".env", "node_modules")

    def test_exclude_nonexistent_item_is_noop(
        self, project_dir: Path, temp_home: Path
    ) -> None:
        project_config = project_dir / ".rig.toml"
        project_config.write_text("""
[worktree.sync]
link = ["a", "b", "c"]
""")
        local_config = project_dir / ".rig.local.toml"
        local_config.write_text("""
[worktree.sync]
exclude-link = ["nonexistent"]
""")

        resolved = resolve_config(project_dir, home_dir=temp_home)

        # Items are unchanged
        assert resolved.config.worktree.sync.link == ("a", "b", "c")
        # But we should have a warning
        assert len(resolved.warnings) == 1
        assert resolved.warnings[0].excluded_item == "nonexistent"


class TestShowCommand:
    @pytest.mark.xfail(reason=_STAGE_3, strict=True)
    def test_show_outputs_merged_config(self, project_config_file: Path) -> None:
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason=_STAGE_3, strict=True)
    def test_show_outputs_toml_format(self, project_config_file: Path) -> None:
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason=_STAGE_3, strict=True)
    def test_show_outputs_json_format(self, project_config_file: Path) -> None:
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason=_STAGE_3, strict=True)
    def test_show_with_layer_filter(
        self, global_config_file: Path, project_config_file: Path
    ) -> None:
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason=_STAGE_3, strict=True)
    def test_show_with_section_filter(self, project_config_file: Path) -> None:
        pytest.fail("Not implemented")


class TestGetCommand:
    @pytest.mark.xfail(reason=_STAGE_3, strict=True)
    def test_get_scalar_value(self, project_config_file: Path) -> None:
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason=_STAGE_3, strict=True)
    def test_get_nested_value(self, project_config_file: Path) -> None:
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason=_STAGE_3, strict=True)
    def test_get_array_value(self, project_config_file: Path) -> None:
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason=_STAGE_3, strict=True)
    def test_get_nonexistent_key_returns_empty(self, project_config_file: Path) -> None:
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason=_STAGE_3, strict=True)
    def test_get_with_default_value(self, project_config_file: Path) -> None:
        pytest.fail("Not implemented")


class TestSetCommand:
    @pytest.mark.xfail(reason=_STAGE_4, strict=True)
    def test_set_creates_config_file(self, empty_project_dir: Path) -> None:
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason=_STAGE_4, strict=True)
    def test_set_scalar_value(self, project_config_file: Path) -> None:
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason=_STAGE_4, strict=True)
    def test_set_nested_value(self, project_config_file: Path) -> None:
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason=_STAGE_4, strict=True)
    def test_set_array_value(self, project_config_file: Path) -> None:
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason=_STAGE_4, strict=True)
    def test_set_to_global_layer(self, global_config_file: Path) -> None:
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason=_STAGE_4, strict=True)
    def test_set_to_local_layer(self, local_config_file: Path) -> None:
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason=_STAGE_4, strict=True)
    def test_set_validates_value_type(self, project_config_file: Path) -> None:
        pytest.fail("Not implemented")


class TestUnsetCommand:
    @pytest.mark.xfail(reason=_STAGE_4, strict=True)
    def test_unset_removes_key(self, project_config_file: Path) -> None:
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason=_STAGE_4, strict=True)
    def test_unset_nested_key(self, project_config_file: Path) -> None:
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason=_STAGE_4, strict=True)
    def test_unset_nonexistent_key_is_noop(self, project_config_file: Path) -> None:
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason=_STAGE_4, strict=True)
    def test_unset_from_specific_layer(
        self, project_config_file: Path, local_config_file: Path
    ) -> None:
        pytest.fail("Not implemented")


class TestEditCommand:
    @pytest.mark.xfail(reason=_STAGE_5, strict=True)
    def test_edit_opens_editor(self, project_config_file: Path) -> None:
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason=_STAGE_5, strict=True)
    def test_edit_uses_visual_env(self, project_config_file: Path) -> None:
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason=_STAGE_5, strict=True)
    def test_edit_uses_editor_env(self, project_config_file: Path) -> None:
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason=_STAGE_5, strict=True)
    def test_edit_falls_back_to_vi(self, project_config_file: Path) -> None:
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason=_STAGE_5, strict=True)
    def test_edit_creates_config_if_missing(self, empty_project_dir: Path) -> None:
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason=_STAGE_5, strict=True)
    def test_edit_validates_after_save(self, project_config_file: Path) -> None:
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason=_STAGE_5, strict=True)
    def test_edit_specific_layer(
        self, global_config_file: Path, project_config_file: Path
    ) -> None:
        pytest.fail("Not implemented")


class TestInspectCommand:
    @pytest.mark.xfail(reason=_STAGE_6, strict=True)
    def test_inspect_shows_all_layers(
        self,
        global_config_file: Path,
        ancestor_config_file: Path,
        project_config_file: Path,
        local_config_file: Path,
    ) -> None:
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason=_STAGE_6, strict=True)
    def test_inspect_shows_value_sources(
        self, global_config_file: Path, project_config_file: Path
    ) -> None:
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason=_STAGE_6, strict=True)
    def test_inspect_shows_override_chain(
        self, multi_ancestor_hierarchy: dict[str, Path]
    ) -> None:
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason=_STAGE_6, strict=True)
    def test_inspect_specific_key(self, project_config_file: Path) -> None:
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason=_STAGE_6, strict=True)
    def test_inspect_shows_extend_exclude_resolution(
        self, config_with_all_extend_exclude: Path
    ) -> None:
        pytest.fail("Not implemented")


class TestWhereCommand:
    @pytest.mark.xfail(reason=_STAGE_6, strict=True)
    def test_where_lists_all_config_files(
        self,
        global_config_file: Path,
        ancestor_config_file: Path,
        project_config_file: Path,
        local_config_file: Path,
    ) -> None:
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason=_STAGE_6, strict=True)
    def test_where_shows_paths_in_precedence_order(
        self, multi_ancestor_hierarchy: dict[str, Path]
    ) -> None:
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason=_STAGE_6, strict=True)
    def test_where_indicates_missing_files(self, empty_project_dir: Path) -> None:
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason=_STAGE_6, strict=True)
    def test_where_for_specific_layer(
        self, global_config_file: Path, project_config_file: Path
    ) -> None:
        pytest.fail("Not implemented")


class TestErrorHandling:
    @pytest.mark.xfail(reason=_STAGE_1, strict=True)
    def test_reports_toml_syntax_error_with_line_number(
        self, invalid_toml_config: Path
    ) -> None:
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason=_STAGE_1, strict=True)
    def test_reports_schema_validation_error(self, invalid_schema_config: Path) -> None:
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason=_STAGE_4, strict=True)
    def test_reports_permission_error(self, project_config_file: Path) -> None:
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason=_STAGE_3, strict=True)
    def test_reports_missing_key_error(self, project_config_file: Path) -> None:
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason=_STAGE_4, strict=True)
    def test_reports_type_mismatch_error(self, project_config_file: Path) -> None:
        pytest.fail("Not implemented")


class TestEdgeCases:
    def test_handles_circular_extends(self, project_dir: Path, temp_home: Path) -> None:
        # This isn't really circular in the traditional sense, but tests
        # that extend/exclude operations work correctly even when the same
        # items appear in multiple layers
        project_config = project_dir / ".rig.toml"
        project_config.write_text("""
[worktree.sync]
link = ["a", "b", "c"]
""")
        local_config = project_dir / ".rig.local.toml"
        local_config.write_text("""
[worktree.sync]
extend-link = ["b", "d"]
exclude-link = ["c"]
""")

        resolved = resolve_config(project_dir, home_dir=temp_home)

        # Should handle duplicates and exclusions correctly
        # Result: ["a", "b", "b", "d"] (duplicates not removed)
        assert resolved.config.worktree.sync.link == ("a", "b", "b", "d")

    @pytest.mark.xfail(reason=_STAGE_1, strict=True)
    def test_handles_unicode_in_config(self, project_dir: Path) -> None:
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason=_STAGE_1, strict=True)
    def test_handles_very_deep_nesting(self, project_dir: Path) -> None:
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason=_STAGE_1, strict=True)
    def test_handles_very_long_arrays(self, project_dir: Path) -> None:
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason=_STAGE_1, strict=True)
    def test_handles_special_characters_in_paths(self, tmp_path: Path) -> None:
        pytest.fail("Not implemented")
