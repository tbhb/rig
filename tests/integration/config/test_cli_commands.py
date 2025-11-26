from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

# xfail markers reference stage files in plans/rig-config/
_STAGE_3 = "Stage 3: read commands"
_STAGE_4 = "Stage 4: write commands"
_STAGE_5 = "Stage 5: edit command"
_STAGE_6 = "Stage 6: diagnostic commands"


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
