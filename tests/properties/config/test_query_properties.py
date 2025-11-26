from __future__ import annotations

from pathlib import Path

import pytest
from hypothesis import given, settings, strategies as st
from hypothesis.strategies import DrawFn, composite

from rig.config import (
    ConfigLayer,
    ConfigSchema,
    WorktreeConfig,
)
from rig.config._discovery import ConfigFile
from rig.config._resolver import ResolvedConfig

from tests.properties.config.conftest import config_schemas

# Import query utilities - these will be implemented in Stage 4
try:
    from rig.config._query import (
        filter_layers,
        get_value_by_key,
        get_value_provenance,
    )
except ImportError:
    pytest.skip("Query utilities not yet implemented", allow_module_level=True)


# --- Hypothesis Strategies for Key Paths ---


# Valid first-level keys
FIRST_LEVEL_KEYS = ["worktree"]

# Valid second-level keys under worktree
WORKTREE_KEYS = [
    "default_location",
    "delete_branch",
    "protected",
    "paths",
    "sync",
    "hooks",
]

# Valid third-level keys
PATHS_KEYS = ["sibling", "local", "pr"]
SYNC_KEYS = [
    "link",
    "copy",
    "extend_link",
    "extend_copy",
    "exclude_link",
    "exclude_copy",
]
HOOKS_KEYS = [
    "post_add",
    "pre_remove",
    "extend_post_add",
    "extend_pre_remove",
    "exclude_post_add",
    "exclude_pre_remove",
]


@composite
def valid_key_paths(draw: DrawFn) -> str:
    """Generate valid dot-notation key paths for ConfigSchema."""
    # Decide depth (1, 2, or 3 levels)
    depth = draw(st.integers(min_value=1, max_value=3))

    if depth == 1:
        return "worktree"

    second_level = draw(st.sampled_from(WORKTREE_KEYS))

    if depth == 2:
        return f"worktree.{second_level}"

    # Depth 3: need to pick appropriate third-level key
    if second_level == "paths":
        third_level = draw(st.sampled_from(PATHS_KEYS))
    elif second_level == "sync":
        third_level = draw(st.sampled_from(SYNC_KEYS))
    elif second_level == "hooks":
        third_level = draw(st.sampled_from(HOOKS_KEYS))
    else:
        # Scalar fields don't have third level, return depth 2
        return f"worktree.{second_level}"

    return f"worktree.{second_level}.{third_level}"


@composite
def invalid_key_paths(draw: DrawFn) -> str:
    """Generate invalid dot-notation key paths that should return None."""
    # Note: Patterns like "..." and "a..b" contain consecutive dots
    # which get filtered to empty segments - these may behave differently
    invalid_patterns = [
        "nonexistent",
        "worktree.nonexistent",
        "worktree.sync.nonexistent",
        "foo.bar.baz",
    ]
    return draw(st.sampled_from(invalid_patterns))


@composite
def malformed_key_paths(draw: DrawFn) -> str:
    """Generate malformed but handleable key paths."""
    malformed_patterns = [
        "",  # Empty string
        ".",  # Just a dot
        ".worktree",  # Leading dot
        "worktree.",  # Trailing dot
        "worktree..sync",  # Consecutive dots
        "...worktree...",  # Multiple issues
    ]
    return draw(st.sampled_from(malformed_patterns))


@composite
def config_layers_set(draw: DrawFn) -> set[ConfigLayer]:
    """Generate a non-empty set of ConfigLayer values."""
    layers = [ConfigLayer.GLOBAL, ConfigLayer.PROJECT, ConfigLayer.LOCAL]
    selected = draw(st.lists(st.sampled_from(layers), min_size=1, max_size=3))
    return set(selected)


@composite
def resolved_configs_with_files(draw: DrawFn, tmp_path: Path) -> ResolvedConfig:
    """Generate ResolvedConfig with associated ConfigFile objects."""
    config = draw(config_schemas())

    # Generate config files
    files: list[ConfigFile] = []
    provenance: dict[str, ConfigFile] = {}

    # Global file (may or may not exist)
    global_exists = draw(st.booleans())
    global_file = ConfigFile(
        path=tmp_path / "global.toml",
        layer=ConfigLayer.GLOBAL,
        exists=global_exists,
        content=config if global_exists else None,
    )
    files.append(global_file)

    # Project file (may or may not exist)
    project_exists = draw(st.booleans())
    project_file = ConfigFile(
        path=tmp_path / ".rig.toml",
        layer=ConfigLayer.PROJECT,
        exists=project_exists,
        content=config if project_exists else None,
    )
    files.append(project_file)

    # Local file (may or may not exist)
    local_exists = draw(st.booleans())
    local_file = ConfigFile(
        path=tmp_path / ".rig.local.toml",
        layer=ConfigLayer.LOCAL,
        exists=local_exists,
        content=config if local_exists else None,
    )
    files.append(local_file)

    return ResolvedConfig(
        config=config,
        layers=tuple(files),
        provenance=provenance,
        warnings=(),
    )


# --- Property Tests for get_value_by_key ---


class TestGetValueByKeyProperties:
    @given(config=config_schemas(), key_path=valid_key_paths())
    @settings(max_examples=100)
    def test_valid_paths_return_non_none_values(
        self, config: ConfigSchema, key_path: str
    ) -> None:
        result = get_value_by_key(config, key_path)
        # Valid paths should always return something (not None)
        assert result is not None

    @given(config=config_schemas(), key_path=invalid_key_paths())
    @settings(max_examples=50)
    def test_invalid_paths_return_none(
        self, config: ConfigSchema, key_path: str
    ) -> None:
        result = get_value_by_key(config, key_path)
        # Invalid paths should return None
        assert result is None

    @given(config=config_schemas())
    @settings(max_examples=50)
    def test_empty_string_returns_entire_config(self, config: ConfigSchema) -> None:
        result = get_value_by_key(config, "")
        assert result == config

    @given(config=config_schemas())
    @settings(max_examples=50)
    def test_worktree_returns_worktree_config(self, config: ConfigSchema) -> None:
        result = get_value_by_key(config, "worktree")
        assert isinstance(result, WorktreeConfig)
        assert result == config.worktree


class TestGetValueByKeyTypeConsistency:
    @given(config=config_schemas())
    @settings(max_examples=50)
    def test_default_location_returns_string(self, config: ConfigSchema) -> None:
        result = get_value_by_key(config, "worktree.default_location")
        assert isinstance(result, str)
        assert result in ("sibling", "local")

    @given(config=config_schemas())
    @settings(max_examples=50)
    def test_delete_branch_returns_bool(self, config: ConfigSchema) -> None:
        result = get_value_by_key(config, "worktree.delete_branch")
        assert isinstance(result, bool)

    @given(config=config_schemas())
    @settings(max_examples=50)
    def test_sync_link_returns_tuple(self, config: ConfigSchema) -> None:
        result = get_value_by_key(config, "worktree.sync.link")
        assert isinstance(result, tuple)


class TestGetValueByKeyMalformedPaths:
    @given(config=config_schemas(), key_path=malformed_key_paths())
    @settings(max_examples=50)
    def test_malformed_paths_do_not_raise(
        self, config: ConfigSchema, key_path: str
    ) -> None:
        # Malformed paths should not raise exceptions
        # If this raises, the test itself will fail, which is what we want
        get_value_by_key(config, key_path)


# --- Property Tests for get_value_provenance ---


class TestGetValueProvenanceProperties:
    @given(config=config_schemas(), key_path=valid_key_paths())
    @settings(max_examples=50)
    def test_provenance_value_matches_get_value_by_key(
        self, config: ConfigSchema, key_path: str
    ) -> None:
        # Create a simple resolved config with synthetic path
        config_file = ConfigFile(
            path=Path("/test/.rig.toml"),
            layer=ConfigLayer.PROJECT,
            exists=True,
            content=config,
        )
        resolved = ResolvedConfig(
            config=config,
            layers=(config_file,),
            provenance={},  # Provenance would be populated by resolver
            warnings=(),
        )

        value, _source = get_value_provenance(resolved, key_path)
        direct_value = get_value_by_key(config, key_path)

        # Value from provenance should match direct query
        assert value == direct_value


class TestGetValueProvenanceSourceConsistency:
    def test_source_is_config_file_or_none(self) -> None:
        config = ConfigSchema()
        config_file = ConfigFile(
            path=Path("/test/.rig.toml"),
            layer=ConfigLayer.PROJECT,
            exists=True,
            content=config,
        )
        resolved = ResolvedConfig(
            config=config,
            layers=(config_file,),
            provenance={},
            warnings=(),
        )

        _, source = get_value_provenance(resolved, "worktree.default_location")

        assert source is None or isinstance(source, ConfigFile)


# --- Property Tests for filter_layers ---


class TestFilterLayersProperties:
    @given(layers_set=config_layers_set())
    @settings(max_examples=50)
    def test_filter_returns_subset_of_layers(
        self, layers_set: set[ConfigLayer]
    ) -> None:
        # Create config files for all layer types with synthetic paths
        global_file = ConfigFile(
            path=Path("/test/global.toml"),
            layer=ConfigLayer.GLOBAL,
            exists=True,
            content=ConfigSchema(),
        )
        project_file = ConfigFile(
            path=Path("/test/.rig.toml"),
            layer=ConfigLayer.PROJECT,
            exists=True,
            content=ConfigSchema(),
        )
        local_file = ConfigFile(
            path=Path("/test/.rig.local.toml"),
            layer=ConfigLayer.LOCAL,
            exists=True,
            content=ConfigSchema(),
        )
        resolved = ResolvedConfig(
            config=ConfigSchema(),
            layers=(global_file, project_file, local_file),
            provenance={},
            warnings=(),
        )

        result = filter_layers(resolved, layers=layers_set)

        # Result should only contain layers from the filter set
        for config_file in result:
            assert config_file.layer in layers_set

    @given(include_missing=st.booleans())
    @settings(max_examples=20)
    def test_include_missing_parameter_respected(self, include_missing: bool) -> None:
        existing_file = ConfigFile(
            path=Path("/test/.rig.toml"),
            layer=ConfigLayer.PROJECT,
            exists=True,
            content=ConfigSchema(),
        )
        missing_file = ConfigFile(
            path=Path("/test/.rig.local.toml"),
            layer=ConfigLayer.LOCAL,
            exists=False,
            content=None,
        )
        resolved = ResolvedConfig(
            config=ConfigSchema(),
            layers=(existing_file, missing_file),
            provenance={},
            warnings=(),
        )

        result = filter_layers(resolved, include_missing=include_missing)

        if include_missing:
            assert len(result) == 2
        else:
            assert len(result) == 1
            assert all(f.exists for f in result)


class TestFilterLayersOrderPreservation:
    def test_order_is_subset_of_original_order(self) -> None:
        files = [
            ConfigFile(
                path=Path("/test/global.toml"),
                layer=ConfigLayer.GLOBAL,
                exists=True,
                content=ConfigSchema(),
            ),
            ConfigFile(
                path=Path("/test/.rig.toml"),
                layer=ConfigLayer.PROJECT,
                exists=True,
                content=ConfigSchema(),
            ),
            ConfigFile(
                path=Path("/test/.rig.local.toml"),
                layer=ConfigLayer.LOCAL,
                exists=True,
                content=ConfigSchema(),
            ),
        ]
        resolved = ResolvedConfig(
            config=ConfigSchema(),
            layers=tuple(files),
            provenance={},
            warnings=(),
        )

        # Filter for GLOBAL and LOCAL (skipping PROJECT)
        result = filter_layers(resolved, layers={ConfigLayer.GLOBAL, ConfigLayer.LOCAL})

        # Order should be preserved: GLOBAL before LOCAL
        assert len(result) == 2
        assert result[0].layer == ConfigLayer.GLOBAL
        assert result[1].layer == ConfigLayer.LOCAL
