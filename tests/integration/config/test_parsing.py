from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from rig.config import (
    ConfigParseError,
    ConfigValidationError,
    parse_config_file,
)

if TYPE_CHECKING:
    from pathlib import Path


class TestConfigFileParsing:
    def test_parses_valid_toml(self, project_config_file: Path) -> None:
        config = parse_config_file(project_config_file)

        assert config.worktree.default_location == "local"
        assert config.worktree.sync.link == (".env", "node_modules")
        assert config.worktree.sync.copy == ("config.local.json",)
        assert config.worktree.hooks.post_add == ("npm install", "make setup")

    def test_raises_on_invalid_toml_syntax(self, invalid_toml_config: Path) -> None:
        with pytest.raises(ConfigParseError) as exc_info:
            parse_config_file(invalid_toml_config)

        error = exc_info.value
        assert error.path == invalid_toml_config
        # Error message should describe the syntax problem
        assert len(error.detail) > 0
        # Should include line number information
        assert error.line is not None or "line" in error.detail.lower()

    def test_raises_on_invalid_schema(self, invalid_schema_config: Path) -> None:
        with pytest.raises(ConfigValidationError) as exc_info:
            parse_config_file(invalid_schema_config)

        error = exc_info.value
        assert error.path == invalid_schema_config
        # Should report unknown key or invalid value
        assert "unknown" in error.detail.lower() or "invalid" in error.detail.lower()

    def test_handles_empty_config_file(self, project_dir: Path) -> None:
        config_file = project_dir / ".rig.toml"
        config_file.write_text("")

        config = parse_config_file(config_file)

        # Should return defaults for empty file
        assert config.worktree.default_location == "sibling"
        assert config.worktree.delete_branch is True
        assert config.worktree.protected is False
        assert config.worktree.sync.link == ()
        assert config.worktree.sync.copy == ()

    def test_handles_partial_config(self, project_dir: Path) -> None:
        config_file = project_dir / ".rig.toml"
        config_file.write_text("""
[worktree]
protected = true
""")

        config = parse_config_file(config_file)

        # Specified value should be set
        assert config.worktree.protected is True
        # Unspecified values should be defaults
        assert config.worktree.default_location == "sibling"
        assert config.worktree.delete_branch is True
        assert config.worktree.sync.link == ()

    def test_parses_all_sync_fields(self, project_dir: Path) -> None:
        config_file = project_dir / ".rig.toml"
        config_file.write_text("""
[worktree.sync]
link = ["a", "b"]
copy = ["c", "d"]
""")

        config = parse_config_file(config_file)

        assert config.worktree.sync.link == ("a", "b")
        assert config.worktree.sync.copy == ("c", "d")

    def test_parses_all_hooks_fields(self, project_dir: Path) -> None:
        config_file = project_dir / ".rig.toml"
        config_file.write_text("""
[worktree.hooks]
post-add = ["setup.sh"]
pre-remove = ["cleanup.sh"]
""")

        config = parse_config_file(config_file)

        assert config.worktree.hooks.post_add == ("setup.sh",)
        assert config.worktree.hooks.pre_remove == ("cleanup.sh",)

    def test_parses_path_patterns(self, project_dir: Path) -> None:
        config_file = project_dir / ".rig.toml"
        config_file.write_text("""
[worktree.paths]
sibling = "../{repo}-{branch}"
local = ".worktrees/{branch}"
pr = "../pr-{number}"
""")

        config = parse_config_file(config_file)

        assert config.worktree.paths.sibling == "../{repo}-{branch}"
        assert config.worktree.paths.local == ".worktrees/{branch}"
        assert config.worktree.paths.pr == "../pr-{number}"


class TestUnicodeAndSpecialContent:
    def test_handles_unicode_in_config(
        self, project_dir: Path, temp_home: Path
    ) -> None:
        config_file = project_dir / ".rig.toml"
        config_file.write_text("""
[worktree.sync]
link = ["fichier-accentue.txt", "archivo-espanol.txt", "fichier-francais.txt"]
copy = ["data-kanjis.json"]

[worktree.hooks]
post-add = ["echo 'Installation terminee'"]
""")

        config = parse_config_file(config_file)

        assert "fichier-accentue.txt" in config.worktree.sync.link
        assert "archivo-espanol.txt" in config.worktree.sync.link
        assert "fichier-francais.txt" in config.worktree.sync.link
        assert "data-kanjis.json" in config.worktree.sync.copy

    def test_handles_very_long_arrays(self, project_dir: Path, temp_home: Path) -> None:
        items = [f"item-{i}" for i in range(100)]
        items_toml = ", ".join(f'"{item}"' for item in items)

        config_file = project_dir / ".rig.toml"
        config_file.write_text(f"""
[worktree.sync]
link = [{items_toml}]
""")

        config = parse_config_file(config_file)

        assert len(config.worktree.sync.link) == 100
        assert config.worktree.sync.link[0] == "item-0"
        assert config.worktree.sync.link[99] == "item-99"

    def test_handles_special_characters_in_paths(self, tmp_path: Path) -> None:
        special_dir = tmp_path / "project with spaces"
        special_dir.mkdir()
        (special_dir / ".git").mkdir()

        config_file = special_dir / ".rig.toml"
        config_file.write_text("""
[worktree]
default-location = "local"

[worktree.sync]
link = ["path with spaces/file.txt", "special@chars#file.txt"]
""")

        config = parse_config_file(config_file)

        assert config.worktree.default_location == "local"
        assert "path with spaces/file.txt" in config.worktree.sync.link
        assert "special@chars#file.txt" in config.worktree.sync.link


class TestEmptyAndWhitespaceContent:
    def test_handles_empty_arrays(self, project_dir: Path, temp_home: Path) -> None:
        config_file = project_dir / ".rig.toml"
        config_file.write_text("""
[worktree.sync]
link = []
copy = []

[worktree.hooks]
post-add = []
pre-remove = []
""")

        config = parse_config_file(config_file)

        assert config.worktree.sync.link == ()
        assert config.worktree.sync.copy == ()
        assert config.worktree.hooks.post_add == ()
        assert config.worktree.hooks.pre_remove == ()

    def test_handles_whitespace_only_file(
        self, project_dir: Path, temp_home: Path
    ) -> None:
        config_file = project_dir / ".rig.toml"
        config_file.write_text("   \n\n   \t\t\n   ")

        config = parse_config_file(config_file)

        assert config.worktree.default_location == "sibling"
        assert config.worktree.delete_branch is True


class TestErrorReporting:
    def test_reports_toml_syntax_error_with_line_number(
        self, invalid_toml_config: Path
    ) -> None:
        with pytest.raises(ConfigParseError) as exc_info:
            parse_config_file(invalid_toml_config)

        error = exc_info.value
        assert error.path == invalid_toml_config
        assert error.line is not None or "line" in error.detail.lower()
        assert len(error.detail) > 0

    def test_reports_schema_validation_error(self, invalid_schema_config: Path) -> None:
        with pytest.raises(ConfigValidationError) as exc_info:
            parse_config_file(invalid_schema_config)

        error = exc_info.value
        assert error.path == invalid_schema_config
        assert (
            "unknown" in error.detail.lower()
            or "invalid" in error.detail.lower()
            or error.key != ""
        )

    def test_reports_type_mismatch_in_validation(self, project_dir: Path) -> None:
        config_file = project_dir / ".rig.toml"
        config_file.write_text("""
[worktree]
protected = "yes"
""")

        with pytest.raises(ConfigValidationError) as exc_info:
            parse_config_file(config_file)

        error = exc_info.value
        assert "boolean" in error.detail.lower() or "expected" in error.detail.lower()

    def test_reports_invalid_location_strategy(self, project_dir: Path) -> None:
        config_file = project_dir / ".rig.toml"
        config_file.write_text("""
[worktree]
default-location = "invalid_value"
""")

        with pytest.raises(ConfigValidationError) as exc_info:
            parse_config_file(config_file)

        error = exc_info.value
        assert "invalid" in error.detail.lower()
        assert "worktree.default-location" in error.key

    def test_reports_array_item_type_error(self, project_dir: Path) -> None:
        config_file = project_dir / ".rig.toml"
        config_file.write_text("""
[worktree.sync]
link = ["valid", 123, "also-valid"]
""")

        with pytest.raises(ConfigValidationError) as exc_info:
            parse_config_file(config_file)

        error = exc_info.value
        assert "string" in error.detail.lower() or "array item" in error.detail.lower()
