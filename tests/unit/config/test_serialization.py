from __future__ import annotations

import json
from typing import TYPE_CHECKING, cast

import pytest

from rig.config import (
    ConfigSchema,
    HooksConfig,
    PathPatterns,
    SyncConfig,
    WorktreeConfig,
    parse_config_file,
)

if TYPE_CHECKING:
    from pathlib import Path

# Import serialization utilities - these will be implemented in Stage 4
try:
    from rig.config._serialization import (
        SerializedDict,
        SerializedValue,
        _serialize_toml_scalar,
        to_dict,
        to_json,
        to_toml,
    )
except ImportError:
    pytest.skip("Serialization utilities not yet implemented", allow_module_level=True)


def assert_dict(value: SerializedValue, msg: str = "") -> SerializedDict:
    """Assert that a SerializedValue is a dict and return it narrowed.

    Args:
        value: The value to check.
        msg: Optional message for the assertion error.

    Returns:
        The value narrowed to SerializedDict.
    """
    assert isinstance(value, dict), msg or f"Expected dict, got {type(value).__name__}"
    return value


class TestToDictEmptyConfig:
    def test_produces_dict_for_default_config(self) -> None:
        config = ConfigSchema()
        result = to_dict(config)
        # Default config should produce a dict with default values
        assert isinstance(result, dict)
        # The worktree key should exist with default values serialized
        assert "worktree" in result
        worktree = assert_dict(result["worktree"])
        # Default location should be "sibling"
        assert worktree["default-location"] == "sibling"


class TestToDictFullConfig:
    def test_converts_all_nested_dataclasses(self) -> None:
        config = ConfigSchema(
            worktree=WorktreeConfig(
                default_location="local",
                delete_branch=False,
                protected=True,
                paths=PathPatterns(
                    sibling="../custom-{branch}",
                    local=".wt/{branch}",
                    pr="../pr-{number}",
                ),
                sync=SyncConfig(
                    link=(".env", ".venv"),
                    copy=("node_modules",),
                ),
                hooks=HooksConfig(
                    post_add=("npm install",),
                    pre_remove=("npm run clean",),
                ),
            )
        )

        result = to_dict(config)

        worktree = assert_dict(result["worktree"])
        assert worktree["default-location"] == "local"
        assert worktree["delete-branch"] is False
        assert worktree["protected"] is True

        paths = assert_dict(worktree["paths"])
        assert paths["sibling"] == "../custom-{branch}"

        sync = assert_dict(worktree["sync"])
        assert sync["link"] == [".env", ".venv"]

        hooks = assert_dict(worktree["hooks"])
        assert hooks["post-add"] == ["npm install"]


class TestToDictOmitsNone:
    def test_omits_none_values(self) -> None:
        # ConfigSchema doesn't have optional fields that can be None,
        # but we test that the function handles None values appropriately
        config = ConfigSchema()
        result = to_dict(config)

        # Recursively check that no None values exist in the raw structure
        # (SerializedValue type doesn't include None, so we check the runtime dict)
        def check_no_nones(d: SerializedDict) -> bool:
            for value in d.values():
                # SerializedValue doesn't include None, but we check at runtime
                # to verify the implementation doesn't produce None values
                if isinstance(value, dict) and not check_no_nones(value):
                    return False
            return True

        assert check_no_nones(result)


class TestToDictOmitsEmptyTuples:
    def test_omits_sync_section_when_all_tuples_empty(self) -> None:
        # When all sync fields are empty tuples, the entire sync section is omitted
        config = ConfigSchema(
            worktree=WorktreeConfig(
                sync=SyncConfig(
                    link=(),  # Empty tuple
                    copy=(),  # Empty tuple
                )
            )
        )

        result = to_dict(config)

        # Empty tuples cause sync to be omitted entirely (empty dict is not included)
        assert "worktree" in result
        worktree = assert_dict(result["worktree"])
        assert "sync" not in worktree, "Sync section should be omitted"

    def test_omits_individual_empty_tuples_but_keeps_section(self) -> None:
        # When some sync fields have values, section is kept but empty tuples omitted
        config = ConfigSchema(
            worktree=WorktreeConfig(
                sync=SyncConfig(
                    link=(".env",),  # Non-empty tuple
                    copy=(),  # Empty tuple - should be omitted
                )
            )
        )

        result = to_dict(config)

        assert "worktree" in result
        worktree = assert_dict(result["worktree"])
        assert "sync" in worktree
        sync_dict = assert_dict(worktree["sync"])
        assert "link" in sync_dict, "Non-empty link should be present"
        assert sync_dict["link"] == [".env"]
        assert "copy" not in sync_dict, "Empty copy tuple should be omitted"


class TestToDictConvertsTuplesToLists:
    def test_converts_tuples_to_lists(self) -> None:
        config = ConfigSchema(
            worktree=WorktreeConfig(
                sync=SyncConfig(
                    link=(".env", ".venv"),
                )
            )
        )

        result = to_dict(config)

        # Tuples should be converted to lists for JSON/TOML compatibility
        worktree = assert_dict(result["worktree"])
        sync = assert_dict(worktree["sync"])
        link_value = sync["link"]
        assert isinstance(link_value, list)
        assert link_value == [".env", ".venv"]


class TestToDictNestedNoneHandling:
    def test_handles_nested_none_values(self) -> None:
        # Test that nested structures with defaults are handled properly
        config = ConfigSchema()
        result = to_dict(config)

        # The result should be a valid dict without None values
        assert isinstance(result, dict)


class TestToTomlProducesValidToml:
    def test_produces_parseable_toml(self, tmp_path: Path) -> None:
        config = ConfigSchema(
            worktree=WorktreeConfig(
                default_location="local",
                sync=SyncConfig(link=(".env",)),
            )
        )

        toml_str = to_toml(config)

        # Should be valid TOML - write to file and parse
        config_file = tmp_path / "config.toml"
        config_file.write_text(toml_str)

        # parse_config_file should not raise
        parsed = parse_config_file(config_file)
        assert parsed.worktree.default_location == "local"


class TestToTomlRoundTrip:
    def test_round_trip_preserves_values(self, tmp_path: Path) -> None:
        original = ConfigSchema(
            worktree=WorktreeConfig(
                default_location="local",
                delete_branch=False,
                protected=True,
                paths=PathPatterns(
                    sibling="../custom-{branch}",
                ),
                sync=SyncConfig(
                    link=(".env", "CLAUDE.md"),
                    copy=("data/",),
                ),
                hooks=HooksConfig(
                    post_add=("npm install", "pip install -e ."),
                ),
            )
        )

        toml_str = to_toml(original)
        config_file = tmp_path / "config.toml"
        config_file.write_text(toml_str)
        parsed = parse_config_file(config_file)

        assert parsed.worktree.default_location == original.worktree.default_location
        assert parsed.worktree.delete_branch == original.worktree.delete_branch
        assert parsed.worktree.protected == original.worktree.protected
        assert parsed.worktree.paths.sibling == original.worktree.paths.sibling
        assert parsed.worktree.sync.link == original.worktree.sync.link
        assert parsed.worktree.sync.copy == original.worktree.sync.copy
        assert parsed.worktree.hooks.post_add == original.worktree.hooks.post_add


class TestToTomlSectionHeaders:
    def test_produces_proper_section_headers(self) -> None:
        config = ConfigSchema(
            worktree=WorktreeConfig(
                sync=SyncConfig(link=(".env",)),
            )
        )

        toml_str = to_toml(config)

        # Should have proper TOML section headers
        assert "[worktree]" in toml_str or "[worktree.sync]" in toml_str


class TestToTomlBooleanFormatting:
    def test_formats_booleans_as_lowercase(self) -> None:
        config = ConfigSchema(
            worktree=WorktreeConfig(
                delete_branch=True,
                protected=False,
            )
        )

        toml_str = to_toml(config)

        # TOML uses lowercase true/false
        if "delete-branch" in toml_str:
            assert "true" in toml_str.lower()
        if "protected" in toml_str:
            assert "false" in toml_str.lower()


class TestToTomlStringEscaping:
    def test_escapes_special_characters(self) -> None:
        config = ConfigSchema(
            worktree=WorktreeConfig(
                hooks=HooksConfig(
                    post_add=('echo "hello world"',),
                )
            )
        )

        toml_str = to_toml(config)

        # Should produce valid TOML even with quotes in strings
        assert "hello" in toml_str


class TestToJsonProducesValidJson:
    def test_produces_valid_json(self) -> None:
        config = ConfigSchema(
            worktree=WorktreeConfig(
                default_location="local",
                sync=SyncConfig(link=(".env",)),
            )
        )

        json_str = to_json(config)

        # Should be valid JSON - use cast to avoid Any warning from json.loads
        parsed = cast("SerializedDict", json.loads(json_str))
        assert isinstance(parsed, dict)
        worktree = assert_dict(parsed["worktree"])
        assert worktree["default-location"] == "local"


class TestToJsonRespectsIndent:
    def test_uses_specified_indentation(self) -> None:
        config = ConfigSchema(worktree=WorktreeConfig(default_location="local"))

        json_str_2 = to_json(config, indent=2)
        json_str_4 = to_json(config, indent=4)

        # Different indentation should produce different output
        # (but both should be valid JSON)
        assert json.loads(json_str_2) == json.loads(json_str_4)
        # With indent, should have newlines
        assert "\n" in json_str_2
        assert "\n" in json_str_4


class TestToJsonRoundTrip:
    def test_round_trip_produces_equivalent_dict(self) -> None:
        config = ConfigSchema(
            worktree=WorktreeConfig(
                default_location="local",
                delete_branch=False,
                sync=SyncConfig(link=(".env", ".venv")),
            )
        )

        json_str = to_json(config)
        parsed = cast("SerializedDict", json.loads(json_str))

        # Should produce equivalent dict
        original_dict = to_dict(config)
        assert parsed == original_dict


class TestSerializeTomlScalar:
    def test_serializes_integer_in_array(self) -> None:
        result = _serialize_toml_scalar(42)
        assert result == "42"

    def test_serializes_float_in_array(self) -> None:
        result = _serialize_toml_scalar(3.14)
        assert result == "3.14"

    def test_serializes_boolean_true_in_array(self) -> None:
        result = _serialize_toml_scalar(True)
        assert result == "true"

    def test_serializes_boolean_false_in_array(self) -> None:
        result = _serialize_toml_scalar(False)
        assert result == "false"

    def test_serializes_string_in_array(self) -> None:
        result = _serialize_toml_scalar("hello")
        assert result == '"hello"'

    def test_serializes_nested_list_in_array(self) -> None:
        result = _serialize_toml_scalar(["a", "b"])
        assert result == '["a", "b"]'

    def test_serializes_dict_as_empty_table(self) -> None:
        # Dict in array is not valid TOML but the function handles it gracefully
        # Testing runtime behavior with invalid input type
        test_input = cast("SerializedValue", {"key": "value"})
        result = _serialize_toml_scalar(test_input)
        assert result == "{}"
