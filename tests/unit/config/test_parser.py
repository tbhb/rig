from __future__ import annotations

import stat
from typing import TYPE_CHECKING

import pytest

from rig.config import (
    ConfigFileAccessError,
    ConfigParseError,
    ConfigSchema,
    ConfigValidationError,
    HooksConfig,
    PathPatterns,
    SyncConfig,
    WorktreeConfig,
    parse_config_file,
)
from rig.config._parser import (
    _extract_error_location,
    _suggest_similar_key,
    python_to_toml_key,
    toml_to_python_key,
    validate_config_structure,
)

if TYPE_CHECKING:
    from pathlib import Path


class TestParseConfigFile:
    def test_empty_file_returns_defaults(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text("")

        result = parse_config_file(config_file)

        assert result == ConfigSchema()

    def test_whitespace_only_file_returns_defaults(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text("   \n\t\n   ")

        result = parse_config_file(config_file)

        assert result == ConfigSchema()

    def test_minimal_config_sets_field(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text('[worktree]\ndefault-location = "local"')

        result = parse_config_file(config_file)

        assert result.worktree.default_location == "local"

    def test_full_config_with_all_fields(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text("""
[worktree]
default-location = "local"
delete-branch = false
protected = true

[worktree.paths]
sibling = "../custom-{branch}"
local = ".wt/{branch}"
pr = "../pr-{number}"

[worktree.sync]
link = [".env", ".venv"]
copy = ["node_modules"]

[worktree.hooks]
post-add = ["npm install"]
pre-remove = ["npm run clean"]
""")

        result = parse_config_file(config_file)

        assert result.worktree.default_location == "local"
        assert result.worktree.delete_branch is False
        assert result.worktree.protected is True
        assert result.worktree.paths.sibling == "../custom-{branch}"
        assert result.worktree.paths.local == ".wt/{branch}"
        assert result.worktree.paths.pr == "../pr-{number}"
        assert result.worktree.sync.link == (".env", ".venv")
        assert result.worktree.sync.copy == ("node_modules",)
        assert result.worktree.hooks.post_add == ("npm install",)
        assert result.worktree.hooks.pre_remove == ("npm run clean",)

    def test_partial_config_uses_defaults(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text("[worktree]\nprotected = true")

        result = parse_config_file(config_file)

        assert result.worktree.protected is True
        assert result.worktree.default_location == "sibling"
        assert result.worktree.delete_branch is True
        assert result.worktree.paths == PathPatterns()
        assert result.worktree.sync == SyncConfig()
        assert result.worktree.hooks == HooksConfig()

    def test_raises_config_parse_error_on_invalid_toml(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text("[worktree\ninvalid toml")

        with pytest.raises(ConfigParseError) as exc_info:
            parse_config_file(config_file)

        assert exc_info.value.path == config_file
        assert exc_info.value.detail is not None

    def test_raises_config_file_access_error_on_file_not_found(
        self, tmp_path: Path
    ) -> None:
        nonexistent = tmp_path / "nonexistent.toml"

        with pytest.raises(ConfigFileAccessError) as exc_info:
            parse_config_file(nonexistent)

        assert exc_info.value.path == nonexistent

    def test_raises_config_file_access_error_on_permission_denied(
        self, tmp_path: Path
    ) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text("[worktree]\nprotected = true")
        config_file.chmod(0o000)

        try:
            with pytest.raises(ConfigFileAccessError, match="permission denied"):
                parse_config_file(config_file)
        finally:
            config_file.chmod(stat.S_IRUSR | stat.S_IWUSR)

    def test_raises_config_file_access_error_on_directory(self, tmp_path: Path) -> None:
        directory = tmp_path / "config_dir"
        directory.mkdir()

        with pytest.raises(ConfigFileAccessError, match="is a directory"):
            parse_config_file(directory)


class TestValidateConfigStructure:
    def test_rejects_unknown_top_level_key(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text('[unknown_section]\nfoo = "bar"')

        with pytest.raises(ConfigValidationError, match="unknown key"):
            parse_config_file(config_file)

    def test_rejects_unknown_worktree_key(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text('[worktree]\nunknown-field = "value"')

        with pytest.raises(ConfigValidationError, match="unknown key"):
            parse_config_file(config_file)

    def test_rejects_unknown_nested_key(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text('[worktree.sync]\nunknown = ["file"]')

        with pytest.raises(ConfigValidationError, match="unknown key"):
            parse_config_file(config_file)

    def test_suggests_similar_key_on_typo(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text('[worktree]\ndefault-locaton = "sibling"')

        with pytest.raises(ConfigValidationError, match="did you mean"):
            parse_config_file(config_file)

    def test_accepts_valid_structure(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text("""
[worktree]
default-location = "sibling"
delete-branch = true
protected = false

[worktree.paths]
sibling = "../{repo}-{branch}"
local = ".worktrees/{branch}"
pr = "../{repo}-pr-{number}"

[worktree.sync]
link = [".env"]
copy = ["data"]

[worktree.hooks]
post-add = ["setup.sh"]
pre-remove = ["cleanup.sh"]
""")

        result = parse_config_file(config_file)

        assert result.worktree.default_location == "sibling"

    def test_validates_at_correct_path_level(self, tmp_path: Path) -> None:
        data: dict[str, object] = {"worktree": {"unknown": "value"}}
        config_file = tmp_path / "config.toml"
        config_file.touch()

        with pytest.raises(ConfigValidationError) as exc_info:
            validate_config_structure(data, config_file)

        assert exc_info.value.key == "worktree"


class TestTypeValidation:
    def test_rejects_wrong_type_for_string_field(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text("[worktree]\ndefault-location = 123")

        with pytest.raises(ConfigValidationError, match="expected string, got integer"):
            parse_config_file(config_file)

    def test_rejects_wrong_type_for_boolean_field(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text('[worktree]\ndelete-branch = "yes"')

        with pytest.raises(ConfigValidationError, match="expected boolean, got string"):
            parse_config_file(config_file)

    def test_rejects_wrong_type_for_list_field(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text('[worktree.sync]\nlink = ".env"')

        with pytest.raises(ConfigValidationError, match="expected array, got string"):
            parse_config_file(config_file)

    def test_rejects_non_string_list_items(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text("[worktree.sync]\nlink = [123, 456]")

        with pytest.raises(
            ConfigValidationError, match="array item 0 must be a string"
        ):
            parse_config_file(config_file)

    def test_rejects_invalid_location_strategy(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text('[worktree]\ndefault-location = "invalid"')

        with pytest.raises(ConfigValidationError, match="invalid value 'invalid'"):
            parse_config_file(config_file)

    def test_accepts_valid_location_strategy_sibling(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text('[worktree]\ndefault-location = "sibling"')

        result = parse_config_file(config_file)

        assert result.worktree.default_location == "sibling"

    def test_accepts_valid_location_strategy_local(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text('[worktree]\ndefault-location = "local"')

        result = parse_config_file(config_file)

        assert result.worktree.default_location == "local"


class TestBaseExtendExclusivity:
    def test_rejects_link_with_extend_link(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text("""
[worktree.sync]
link = [".env"]
extend-link = [".env.local"]
""")

        with pytest.raises(
            ConfigValidationError,
            match="cannot specify both 'link' and 'extend-link'",
        ):
            parse_config_file(config_file)

    def test_rejects_link_with_exclude_link(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text("""
[worktree.sync]
link = [".env"]
exclude-link = [".env.local"]
""")

        with pytest.raises(
            ConfigValidationError,
            match="cannot specify both 'link' and 'exclude-link'",
        ):
            parse_config_file(config_file)

    def test_rejects_copy_with_extend_copy(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text("""
[worktree.sync]
copy = ["data"]
extend-copy = ["more_data"]
""")

        with pytest.raises(
            ConfigValidationError,
            match="cannot specify both 'copy' and 'extend-copy'",
        ):
            parse_config_file(config_file)

    def test_rejects_post_add_with_extend_post_add(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text("""
[worktree.hooks]
post-add = ["setup.sh"]
extend-post-add = ["extra.sh"]
""")

        with pytest.raises(
            ConfigValidationError,
            match="cannot specify both 'post-add' and 'extend-post-add'",
        ):
            parse_config_file(config_file)

    def test_accepts_only_extend_without_base(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text("""
[worktree.sync]
extend-link = [".env.local"]
extend-copy = ["extra_data"]

[worktree.hooks]
extend-post-add = ["extra.sh"]
""")

        result = parse_config_file(config_file)

        assert result.worktree.sync.extend_link == (".env.local",)
        assert result.worktree.sync.extend_copy == ("extra_data",)
        assert result.worktree.hooks.extend_post_add == ("extra.sh",)

    def test_accepts_extend_and_exclude_together(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text("""
[worktree.sync]
extend-link = [".env.local"]
exclude-link = [".env.production"]
""")

        result = parse_config_file(config_file)

        assert result.worktree.sync.extend_link == (".env.local",)
        assert result.worktree.sync.exclude_link == (".env.production",)


class TestKeyConversion:
    def test_toml_to_python_key_converts_single_hyphen(self) -> None:
        assert toml_to_python_key("default-location") == "default_location"

    def test_toml_to_python_key_converts_multiple_hyphens(self) -> None:
        assert toml_to_python_key("extend-post-add") == "extend_post_add"

    def test_toml_to_python_key_preserves_no_hyphens(self) -> None:
        assert toml_to_python_key("sibling") == "sibling"

    def test_python_to_toml_key_converts_single_underscore(self) -> None:
        assert python_to_toml_key("default_location") == "default-location"

    def test_python_to_toml_key_converts_multiple_underscores(self) -> None:
        assert python_to_toml_key("extend_post_add") == "extend-post-add"

    def test_key_conversion_roundtrip(self) -> None:
        toml_keys = [
            "default-location",
            "delete-branch",
            "extend-link",
            "extend-post-add",
            "exclude-pre-remove",
        ]
        for toml_key in toml_keys:
            python_key = toml_to_python_key(toml_key)
            roundtrip = python_to_toml_key(python_key)
            assert roundtrip == toml_key


class TestSchemaBuilding:
    def test_build_creates_config_schema_with_worktree(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text('[worktree]\ndefault-location = "local"')

        result = parse_config_file(config_file)

        assert isinstance(result, ConfigSchema)
        assert isinstance(result.worktree, WorktreeConfig)
        assert result.worktree.default_location == "local"

    def test_build_creates_path_patterns(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text("""
[worktree.paths]
sibling = "../custom-{branch}"
local = ".custom/{branch}"
pr = "../custom-pr-{number}"
""")

        result = parse_config_file(config_file)

        assert isinstance(result.worktree.paths, PathPatterns)
        assert result.worktree.paths.sibling == "../custom-{branch}"
        assert result.worktree.paths.local == ".custom/{branch}"
        assert result.worktree.paths.pr == "../custom-pr-{number}"

    def test_build_creates_sync_config_with_tuples(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text("""
[worktree.sync]
link = [".env", ".venv", "node_modules"]
copy = ["data", "cache"]
""")

        result = parse_config_file(config_file)

        assert isinstance(result.worktree.sync, SyncConfig)
        assert result.worktree.sync.link == (".env", ".venv", "node_modules")
        assert result.worktree.sync.copy == ("data", "cache")
        assert isinstance(result.worktree.sync.link, tuple)
        assert isinstance(result.worktree.sync.copy, tuple)

    def test_build_creates_hooks_config_with_tuples(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text("""
[worktree.hooks]
post-add = ["npm install", "pip install -e ."]
pre-remove = ["npm run clean"]
""")

        result = parse_config_file(config_file)

        assert isinstance(result.worktree.hooks, HooksConfig)
        assert result.worktree.hooks.post_add == (
            "npm install",
            "pip install -e .",
        )
        assert result.worktree.hooks.pre_remove == ("npm run clean",)
        assert isinstance(result.worktree.hooks.post_add, tuple)
        assert isinstance(result.worktree.hooks.pre_remove, tuple)


class TestErrorMessages:
    def test_parse_error_includes_file_path(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text("[invalid")

        with pytest.raises(ConfigParseError) as exc_info:
            parse_config_file(config_file)

        error_str = str(exc_info.value)
        assert str(config_file) in error_str

    def test_validation_error_includes_key_path(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text("[worktree]\nunknown = 123")

        with pytest.raises(ConfigValidationError) as exc_info:
            parse_config_file(config_file)

        error_str = str(exc_info.value)
        assert "worktree" in error_str

    def test_access_error_includes_file_path(self, tmp_path: Path) -> None:
        nonexistent = tmp_path / "missing.toml"

        with pytest.raises(ConfigFileAccessError) as exc_info:
            parse_config_file(nonexistent)

        error_str = str(exc_info.value)
        assert str(nonexistent) in error_str


class TestEdgeCases:
    def test_handles_empty_arrays(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text("""
[worktree.sync]
link = []
copy = []
""")

        result = parse_config_file(config_file)

        assert result.worktree.sync.link == ()
        assert result.worktree.sync.copy == ()

    def test_handles_nested_section_without_parent(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text("""
[worktree.sync]
link = [".env"]
""")

        result = parse_config_file(config_file)

        assert result.worktree.sync.link == (".env",)
        assert result.worktree.default_location == "sibling"

    def test_handles_unicode_content(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text("""
[worktree.hooks]
post-add = ["echo 'Hello, World!'"]
""")

        result = parse_config_file(config_file)

        assert result.worktree.hooks.post_add == ("echo 'Hello, World!'",)

    def test_handles_special_characters_in_paths(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text("""
[worktree.sync]
link = [".env", "path/with spaces", "file-with-dashes"]
""")

        result = parse_config_file(config_file)

        assert result.worktree.sync.link == (
            ".env",
            "path/with spaces",
            "file-with-dashes",
        )

    def test_comments_are_ignored(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text("""
# This is a comment
[worktree]
# Another comment
default-location = "local"  # Inline comment
""")

        result = parse_config_file(config_file)

        assert result.worktree.default_location == "local"

    def test_empty_toml_dict_returns_defaults(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text("# just a comment, nothing else")

        result = parse_config_file(config_file)

        assert result == ConfigSchema()


class TestSuggestSimilarKey:
    def test_returns_none_for_empty_valid_keys(self) -> None:
        result = _suggest_similar_key("anything", set())

        assert result is None

    def test_suggests_key_with_common_prefix(self) -> None:
        valid_keys = {"default-location", "delete-branch", "protected"}

        result = _suggest_similar_key("default-locaton", valid_keys)

        assert result == "default-location"

    def test_suggests_key_with_similar_characters(self) -> None:
        valid_keys = {"link", "copy", "extend-link"}

        result = _suggest_similar_key("lnik", valid_keys)

        assert result == "link"

    def test_returns_none_for_very_different_key(self) -> None:
        valid_keys = {"default-location", "delete-branch"}

        result = _suggest_similar_key("xyz", valid_keys)

        assert result is None


class TestExtractErrorLocation:
    def test_extracts_line_and_column(self) -> None:
        error_msg = "Invalid value at line 5 column 10"

        line, column = _extract_error_location(error_msg)

        assert line == 5
        assert column == 10

    def test_extracts_line_only(self) -> None:
        error_msg = "Error on line 42"

        line, column = _extract_error_location(error_msg)

        assert line == 42
        assert column is None

    def test_returns_none_for_no_location(self) -> None:
        error_msg = "Some generic error"

        line, column = _extract_error_location(error_msg)

        assert line is None
        assert column is None

    def test_extracts_column_with_col_abbreviation(self) -> None:
        error_msg = "Error at col 15"

        line, column = _extract_error_location(error_msg)

        assert line is None
        assert column == 15


class TestPartialPathPatterns:
    def test_partial_paths_use_defaults_for_missing(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text("""
[worktree.paths]
sibling = "../custom-{branch}"
""")

        result = parse_config_file(config_file)

        assert result.worktree.paths.sibling == "../custom-{branch}"
        assert result.worktree.paths.local == ".worktrees/{branch}"
        assert result.worktree.paths.pr == "../{repo}-pr-{number}"

    def test_only_local_path_set(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text("""
[worktree.paths]
local = ".wt/{branch}"
""")

        result = parse_config_file(config_file)

        assert result.worktree.paths.sibling == "../{repo}-{branch}"
        assert result.worktree.paths.local == ".wt/{branch}"
        assert result.worktree.paths.pr == "../{repo}-pr-{number}"

    def test_only_pr_path_set(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text("""
[worktree.paths]
pr = "../pr-{number}"
""")

        result = parse_config_file(config_file)

        assert result.worktree.paths.sibling == "../{repo}-{branch}"
        assert result.worktree.paths.local == ".worktrees/{branch}"
        assert result.worktree.paths.pr == "../pr-{number}"


class TestPreRemoveHooks:
    def test_pre_remove_with_extend_raises_error(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text("""
[worktree.hooks]
pre-remove = ["cleanup.sh"]
extend-pre-remove = ["extra.sh"]
""")

        with pytest.raises(
            ConfigValidationError,
            match="cannot specify both 'pre-remove' and 'extend-pre-remove'",
        ):
            parse_config_file(config_file)

    def test_copy_with_exclude_raises_error(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text("""
[worktree.sync]
copy = ["data"]
exclude-copy = ["temp"]
""")

        with pytest.raises(
            ConfigValidationError,
            match="cannot specify both 'copy' and 'exclude-copy'",
        ):
            parse_config_file(config_file)
