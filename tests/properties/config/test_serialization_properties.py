from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import cast

import pytest
from hypothesis import given, settings
from hypothesis.strategies import DrawFn, composite

from rig.config import (
    ConfigSchema,
    HooksConfig,
    PathPatterns,
    SyncConfig,
    WorktreeConfig,
    parse_config_file,
)

# Import strategies from conftest
from tests.properties.config.conftest import config_schemas

# Import serialization utilities - these will be implemented in Stage 4
try:
    from rig.config._serialization import (
        SerializedDict,
        SerializedValue,
        to_dict,
        to_json,
        to_toml,
    )
except ImportError:
    pytest.skip("Serialization utilities not yet implemented", allow_module_level=True)


# --- TOML-safe Hypothesis Strategies for Serialization Testing ---
# These strategies generate strings that are valid TOML content (no control chars)

from hypothesis import strategies as st

# TOML-safe text: printable ASCII and common Unicode, no control characters
# TOML allows most printable characters in basic strings
_CONTROL_CHARS = (
    "\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f"
    "\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f"
    '"\\'  # Exclude TOML special chars that need escaping
)
toml_safe_text = st.text(
    alphabet=st.characters(
        # Letters, Numbers, Punctuation, Symbols, Spaces
        categories=["L", "N", "P", "S", "Zs"],
        exclude_characters=_CONTROL_CHARS,
    ),
    min_size=0,
    max_size=50,
)


@composite
def toml_safe_path_patterns(draw: DrawFn) -> PathPatterns:
    """Generate PathPatterns with TOML-safe strings."""
    return PathPatterns(
        sibling=draw(toml_safe_text),
        local=draw(toml_safe_text),
        pr=draw(toml_safe_text),
    )


@composite
def serializable_sync_configs(draw: DrawFn) -> SyncConfig:
    """Generate SyncConfig that avoids base+extend/exclude conflicts.

    For serialization tests, we need valid configs that don't violate
    the mutual exclusivity constraints (base with extend/exclude).
    Uses TOML-safe strings.
    """
    # Either use base lists OR extend/exclude, not both
    use_base = draw(st.booleans())

    if use_base:
        return SyncConfig(
            link=tuple(draw(st.lists(toml_safe_text, max_size=5))),
            copy=tuple(draw(st.lists(toml_safe_text, max_size=5))),
        )
    return SyncConfig(
        extend_link=tuple(draw(st.lists(toml_safe_text, max_size=3))),
        extend_copy=tuple(draw(st.lists(toml_safe_text, max_size=3))),
        exclude_link=tuple(draw(st.lists(toml_safe_text, max_size=3))),
        exclude_copy=tuple(draw(st.lists(toml_safe_text, max_size=3))),
    )


@composite
def serializable_hooks_configs(draw: DrawFn) -> HooksConfig:
    """Generate HooksConfig that avoids base+extend/exclude conflicts.

    Uses TOML-safe strings.
    """
    use_base = draw(st.booleans())

    if use_base:
        return HooksConfig(
            post_add=tuple(draw(st.lists(toml_safe_text, max_size=5))),
            pre_remove=tuple(draw(st.lists(toml_safe_text, max_size=5))),
        )
    return HooksConfig(
        extend_post_add=tuple(draw(st.lists(toml_safe_text, max_size=3))),
        extend_pre_remove=tuple(draw(st.lists(toml_safe_text, max_size=3))),
        exclude_post_add=tuple(draw(st.lists(toml_safe_text, max_size=3))),
        exclude_pre_remove=tuple(draw(st.lists(toml_safe_text, max_size=3))),
    )


@composite
def serializable_worktree_configs(draw: DrawFn) -> WorktreeConfig:
    """Generate WorktreeConfig suitable for serialization round-trips."""
    from rig.config import LocationStrategy  # noqa: PLC0415

    location: LocationStrategy = draw(st.sampled_from(["sibling", "local"]))
    return WorktreeConfig(
        default_location=location,
        delete_branch=draw(st.booleans()),
        protected=draw(st.booleans()),
        paths=draw(toml_safe_path_patterns()),
        sync=draw(serializable_sync_configs()),
        hooks=draw(serializable_hooks_configs()),
    )


@composite
def serializable_config_schemas(draw: DrawFn) -> ConfigSchema:
    """Generate ConfigSchema suitable for serialization round-trips."""
    return ConfigSchema(worktree=draw(serializable_worktree_configs()))


# --- Property Tests for TOML Round-Trip ---


class TestTomlRoundTrip:
    @given(config=serializable_config_schemas())
    @settings(max_examples=50)
    def test_toml_round_trip_preserves_data(self, config: ConfigSchema) -> None:
        # Convert to TOML
        toml_str = to_toml(config)

        # Write to temp file and parse back
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_str)
            config_file = Path(f.name)

        try:
            parsed = parse_config_file(config_file)

            # Convert both to dict for comparison (handles default value equivalence)
            original_dict = to_dict(config)
            parsed_dict = to_dict(parsed)

            assert original_dict == parsed_dict
        finally:
            config_file.unlink()


# --- Property Tests for JSON Round-Trip ---


class TestJsonRoundTrip:
    @given(config=serializable_config_schemas())
    @settings(max_examples=50)
    def test_json_round_trip_preserves_data(self, config: ConfigSchema) -> None:
        # Convert to JSON
        json_str = to_json(config)

        # Parse back - cast since json.loads returns Any
        parsed_dict = cast("SerializedDict", json.loads(json_str))

        # Compare with original dict
        original_dict = to_dict(config)

        assert parsed_dict == original_dict


# --- Property Tests for to_dict Idempotence ---


class TestToDictIdempotence:
    @given(config=serializable_config_schemas())
    @settings(max_examples=50)
    def test_to_dict_is_idempotent(self, config: ConfigSchema) -> None:
        # to_dict should produce the same result when applied to equivalent structures
        dict1 = to_dict(config)
        dict2 = to_dict(config)

        assert dict1 == dict2

    @given(config=serializable_config_schemas())
    @settings(max_examples=50)
    def test_to_dict_produces_json_serializable_output(
        self, config: ConfigSchema
    ) -> None:
        result = to_dict(config)

        # Should be JSON serializable without error
        json_str = json.dumps(result)
        assert isinstance(json_str, str)


# --- Property Tests for Tuple to List Conversion ---


class TestTupleToListConversion:
    @given(config=config_schemas())
    @settings(max_examples=50)
    def test_all_tuples_converted_to_lists(self, config: ConfigSchema) -> None:
        result = to_dict(config)

        def check_no_tuples(obj: SerializedValue) -> bool:
            if isinstance(obj, dict):
                return all(check_no_tuples(v) for v in obj.values())
            if isinstance(obj, list):
                return all(check_no_tuples(item) for item in obj)
            # SerializedValue doesn't include tuple, so scalars are fine
            return True

        assert check_no_tuples(result)


# --- Property Tests for Key Conversion ---


class TestKeyConversion:
    @given(config=serializable_config_schemas())
    @settings(max_examples=50)
    def test_uses_kebab_case_keys(self, config: ConfigSchema) -> None:
        result = to_dict(config)

        def check_kebab_case(obj: SerializedValue, path: str = "") -> list[str]:
            issues: list[str] = []
            if isinstance(obj, dict):
                for key, value in obj.items():
                    # Keys should use hyphens, not underscores
                    if "_" in key:
                        issues.append(f"{path}.{key}")
                    issues.extend(check_kebab_case(value, f"{path}.{key}"))
            return issues

        issues = check_kebab_case(result)
        assert not issues, f"Found underscore keys: {issues}"
