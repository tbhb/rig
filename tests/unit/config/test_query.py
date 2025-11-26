from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from rig.config import (
    ConfigLayer,
    ConfigSchema,
    HooksConfig,
    PathPatterns,
    SyncConfig,
    WorktreeConfig,
)
from rig.config._discovery import ConfigFile
from rig.config._resolver import ResolvedConfig

if TYPE_CHECKING:
    from pathlib import Path

# Import query utilities - these will be implemented in Stage 4
# For now, we define the expected API signatures for TDD
try:
    from rig.config._query import (
        filter_layers,
        get_value_by_key,
        get_value_provenance,
    )
except ImportError:
    pytest.skip("Query utilities not yet implemented", allow_module_level=True)


class TestGetValueByKeySimplePath:
    def test_returns_worktree_config_for_worktree_key(self) -> None:
        config = ConfigSchema()
        result = get_value_by_key(config, "worktree")
        assert isinstance(result, WorktreeConfig)

    def test_returns_string_for_default_location(self) -> None:
        config = ConfigSchema(worktree=WorktreeConfig(default_location="local"))
        result = get_value_by_key(config, "worktree.default_location")
        assert result == "local"

    def test_returns_boolean_for_protected(self) -> None:
        config = ConfigSchema(worktree=WorktreeConfig(protected=True))
        result = get_value_by_key(config, "worktree.protected")
        assert result is True


class TestGetValueByKeyNestedPath:
    def test_returns_default_location_nested(self) -> None:
        config = ConfigSchema(worktree=WorktreeConfig(default_location="sibling"))
        result = get_value_by_key(config, "worktree.default_location")
        assert result == "sibling"

    def test_returns_paths_sibling_pattern(self) -> None:
        config = ConfigSchema(
            worktree=WorktreeConfig(paths=PathPatterns(sibling="../custom-{branch}"))
        )
        result = get_value_by_key(config, "worktree.paths.sibling")
        assert result == "../custom-{branch}"


class TestGetValueByKeyDeepPath:
    def test_returns_sync_link_tuple(self) -> None:
        config = ConfigSchema(
            worktree=WorktreeConfig(sync=SyncConfig(link=(".env", ".venv")))
        )
        result = get_value_by_key(config, "worktree.sync.link")
        assert result == (".env", ".venv")

    def test_returns_hooks_post_add_tuple(self) -> None:
        config = ConfigSchema(
            worktree=WorktreeConfig(hooks=HooksConfig(post_add=("npm install",)))
        )
        result = get_value_by_key(config, "worktree.hooks.post_add")
        assert result == ("npm install",)

    def test_returns_hooks_pre_remove_tuple(self) -> None:
        config = ConfigSchema(
            worktree=WorktreeConfig(hooks=HooksConfig(pre_remove=("cleanup.sh",)))
        )
        result = get_value_by_key(config, "worktree.hooks.pre_remove")
        assert result == ("cleanup.sh",)

    def test_returns_hooks_extend_post_add_tuple(self) -> None:
        config = ConfigSchema(
            worktree=WorktreeConfig(hooks=HooksConfig(extend_post_add=("extra.sh",)))
        )
        result = get_value_by_key(config, "worktree.hooks.extend_post_add")
        assert result == ("extra.sh",)

    def test_returns_hooks_extend_pre_remove_tuple(self) -> None:
        config = ConfigSchema(
            worktree=WorktreeConfig(hooks=HooksConfig(extend_pre_remove=("backup.sh",)))
        )
        result = get_value_by_key(config, "worktree.hooks.extend_pre_remove")
        assert result == ("backup.sh",)

    def test_returns_hooks_exclude_post_add_tuple(self) -> None:
        config = ConfigSchema(
            worktree=WorktreeConfig(hooks=HooksConfig(exclude_post_add=("skip.sh",)))
        )
        result = get_value_by_key(config, "worktree.hooks.exclude_post_add")
        assert result == ("skip.sh",)

    def test_returns_hooks_exclude_pre_remove_tuple(self) -> None:
        config = ConfigSchema(
            worktree=WorktreeConfig(hooks=HooksConfig(exclude_pre_remove=("old.sh",)))
        )
        result = get_value_by_key(config, "worktree.hooks.exclude_pre_remove")
        assert result == ("old.sh",)


class TestGetValueByKeyMissingKey:
    def test_returns_none_for_nonexistent_path(self) -> None:
        config = ConfigSchema()
        result = get_value_by_key(config, "worktree.nonexistent")
        assert result is None

    def test_returns_none_for_invalid_deep_path(self) -> None:
        config = ConfigSchema()
        result = get_value_by_key(config, "worktree.sync.nonexistent")
        assert result is None


class TestGetValueByKeyNoneIntermediate:
    def test_returns_none_for_missing_deep_path(self) -> None:
        # Tests that deeply nested paths through nonexistent keys return None
        # ConfigSchema always has defaults, so we test a path that starts
        # with a key that doesn't exist on ConfigSchema
        config = ConfigSchema()
        result = get_value_by_key(config, "nonexistent.deep.path")
        assert result is None


class TestGetValueByKeyEmptyString:
    def test_returns_entire_config_for_empty_string(self) -> None:
        config = ConfigSchema(worktree=WorktreeConfig(protected=True))
        result = get_value_by_key(config, "")
        assert result == config


class TestGetValueByKeyLeadingDot:
    def test_strips_leading_dot_and_processes(self) -> None:
        config = ConfigSchema(worktree=WorktreeConfig(protected=True))
        result = get_value_by_key(config, ".worktree.protected")
        assert result is True


class TestGetValueByKeyTrailingDot:
    def test_strips_trailing_dot_and_processes(self) -> None:
        config = ConfigSchema(worktree=WorktreeConfig(default_location="local"))
        result = get_value_by_key(config, "worktree.default_location.")
        assert result == "local"


class TestGetValueByKeyConsecutiveDots:
    def test_returns_none_for_consecutive_dots(self) -> None:
        config = ConfigSchema()
        result = get_value_by_key(config, "worktree..sync")
        assert result is None


class TestGetValueByKeyTupleValues:
    def test_returns_tuple_unchanged(self) -> None:
        config = ConfigSchema(
            worktree=WorktreeConfig(
                sync=SyncConfig(link=(".env", "CLAUDE.md", ".gemini/"))
            )
        )
        result = get_value_by_key(config, "worktree.sync.link")
        assert result == (".env", "CLAUDE.md", ".gemini/")
        assert isinstance(result, tuple)


class TestGetValueProvenanceFromProject:
    def test_identifies_project_layer_as_source(self, tmp_path: Path) -> None:
        project_config = ConfigSchema(worktree=WorktreeConfig(default_location="local"))
        project_file = ConfigFile(
            path=tmp_path / ".rig.toml",
            layer=ConfigLayer.PROJECT,
            exists=True,
            content=project_config,
        )
        resolved = ResolvedConfig(
            config=project_config,
            layers=(project_file,),
            provenance={"worktree.default-location": project_file},
            warnings=(),
        )

        value, source = get_value_provenance(resolved, "worktree.default_location")

        assert value == "local"
        assert source == project_file


class TestGetValueProvenanceFromLocal:
    def test_identifies_local_layer_when_it_overrides(self, tmp_path: Path) -> None:
        local_config = ConfigSchema(worktree=WorktreeConfig(protected=True))
        project_file = ConfigFile(
            path=tmp_path / ".rig.toml",
            layer=ConfigLayer.PROJECT,
            exists=True,
            content=ConfigSchema(worktree=WorktreeConfig(protected=False)),
        )
        local_file = ConfigFile(
            path=tmp_path / ".rig.local.toml",
            layer=ConfigLayer.LOCAL,
            exists=True,
            content=local_config,
        )
        resolved = ResolvedConfig(
            config=local_config,
            layers=(project_file, local_file),
            provenance={"worktree.protected": local_file},
            warnings=(),
        )

        value, source = get_value_provenance(resolved, "worktree.protected")

        assert value is True
        assert source == local_file
        assert source is not None
        assert source.layer == ConfigLayer.LOCAL


class TestGetValueProvenanceMultipleLayers:
    def test_returns_most_specific_layer(self, tmp_path: Path) -> None:
        global_file = ConfigFile(
            path=tmp_path / "global.toml",
            layer=ConfigLayer.GLOBAL,
            exists=True,
            content=ConfigSchema(worktree=WorktreeConfig(default_location="sibling")),
        )
        project_file = ConfigFile(
            path=tmp_path / ".rig.toml",
            layer=ConfigLayer.PROJECT,
            exists=True,
            content=ConfigSchema(worktree=WorktreeConfig(default_location="local")),
        )
        local_file = ConfigFile(
            path=tmp_path / ".rig.local.toml",
            layer=ConfigLayer.LOCAL,
            exists=True,
            content=ConfigSchema(),  # Doesn't set this value
        )
        # Final merged config has "local" from project
        merged_config = ConfigSchema(worktree=WorktreeConfig(default_location="local"))

        resolved = ResolvedConfig(
            config=merged_config,
            layers=(global_file, project_file, local_file),
            provenance={"worktree.default-location": project_file},
            warnings=(),
        )

        value, source = get_value_provenance(resolved, "worktree.default_location")

        assert value == "local"
        assert source == project_file


class TestGetValueProvenanceMissingKey:
    def test_returns_none_none_for_missing_key(self, tmp_path: Path) -> None:
        project_file = ConfigFile(
            path=tmp_path / ".rig.toml",
            layer=ConfigLayer.PROJECT,
            exists=True,
            content=ConfigSchema(),
        )
        resolved = ResolvedConfig(
            config=ConfigSchema(),
            layers=(project_file,),
            provenance={},
            warnings=(),
        )

        value, source = get_value_provenance(resolved, "worktree.nonexistent")

        assert value is None
        assert source is None


class TestGetValueProvenanceDefaultValue:
    def test_returns_default_value_with_none_source(self, tmp_path: Path) -> None:
        # For values that are defaults (no layer set them), source should be None
        project_file = ConfigFile(
            path=tmp_path / ".rig.toml",
            layer=ConfigLayer.PROJECT,
            exists=True,
            content=ConfigSchema(),  # All defaults
        )
        resolved = ResolvedConfig(
            config=ConfigSchema(),
            layers=(project_file,),
            provenance={},  # Empty provenance because nothing was explicitly set
            warnings=(),
        )

        # default_location has a default value of "sibling"
        value, source = get_value_provenance(resolved, "worktree.default_location")

        # Value exists (from defaults), but no layer set it
        assert value == "sibling"
        assert source is None


class TestGetValueProvenanceExtendModifier:
    def test_identifies_layer_with_extend_modifier(self, tmp_path: Path) -> None:
        # When a layer uses extend-link, the provenance should point to that layer
        global_config = ConfigSchema(
            worktree=WorktreeConfig(sync=SyncConfig(link=(".env",)))
        )
        local_config = ConfigSchema(
            worktree=WorktreeConfig(sync=SyncConfig(extend_link=(".venv",)))
        )
        global_file = ConfigFile(
            path=tmp_path / "global.toml",
            layer=ConfigLayer.GLOBAL,
            exists=True,
            content=global_config,
        )
        local_file = ConfigFile(
            path=tmp_path / ".rig.local.toml",
            layer=ConfigLayer.LOCAL,
            exists=True,
            content=local_config,
        )
        # After merging, the link would be (".env", ".venv")
        merged_config = ConfigSchema(
            worktree=WorktreeConfig(sync=SyncConfig(link=(".env", ".venv")))
        )
        resolved = ResolvedConfig(
            config=merged_config,
            layers=(global_file, local_file),
            # extend-link modifies sync.link, so both layers contribute
            provenance={"worktree.sync.extend-link": local_file},
            warnings=(),
        )

        _value, source = get_value_provenance(resolved, "worktree.sync.extend_link")

        assert source == local_file
        assert source is not None
        assert source.layer == ConfigLayer.LOCAL


class TestGetValueProvenanceMergedList:
    def test_identifies_most_recent_modifier_for_merged_list(
        self, tmp_path: Path
    ) -> None:
        # When lists are merged from multiple layers, provenance tracks the modifier
        global_config = ConfigSchema(
            worktree=WorktreeConfig(hooks=HooksConfig(post_add=("npm install",)))
        )
        project_config = ConfigSchema(
            worktree=WorktreeConfig(
                hooks=HooksConfig(extend_post_add=("pip install -e .",))
            )
        )
        local_config = ConfigSchema(
            worktree=WorktreeConfig(hooks=HooksConfig(extend_post_add=("just setup",)))
        )
        global_file = ConfigFile(
            path=tmp_path / "global.toml",
            layer=ConfigLayer.GLOBAL,
            exists=True,
            content=global_config,
        )
        project_file = ConfigFile(
            path=tmp_path / ".rig.toml",
            layer=ConfigLayer.PROJECT,
            exists=True,
            content=project_config,
        )
        local_file = ConfigFile(
            path=tmp_path / ".rig.local.toml",
            layer=ConfigLayer.LOCAL,
            exists=True,
            content=local_config,
        )
        # After merging: post_add = ("npm install", "pip install -e .", "just setup")
        merged_config = ConfigSchema(
            worktree=WorktreeConfig(
                hooks=HooksConfig(
                    post_add=("npm install", "pip install -e .", "just setup")
                )
            )
        )
        resolved = ResolvedConfig(
            config=merged_config,
            layers=(global_file, project_file, local_file),
            # The final extend came from local, so that's tracked for extend-post-add
            provenance={
                "worktree.hooks.post-add": global_file,
                "worktree.hooks.extend-post-add": local_file,
            },
            warnings=(),
        )

        # Query the base post_add value (set by global)
        value, source = get_value_provenance(resolved, "worktree.hooks.post_add")

        assert value == ("npm install", "pip install -e .", "just setup")
        assert source == global_file
        assert source is not None
        assert source.layer == ConfigLayer.GLOBAL


class TestFilterLayersAll:
    def test_returns_all_files_when_layers_is_none(self, tmp_path: Path) -> None:
        global_file = ConfigFile(
            path=tmp_path / "global.toml",
            layer=ConfigLayer.GLOBAL,
            exists=True,
            content=ConfigSchema(),
        )
        project_file = ConfigFile(
            path=tmp_path / ".rig.toml",
            layer=ConfigLayer.PROJECT,
            exists=True,
            content=ConfigSchema(),
        )
        local_file = ConfigFile(
            path=tmp_path / ".rig.local.toml",
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

        result = filter_layers(resolved, layers=None)

        assert len(result) == 3
        assert result == (global_file, project_file, local_file)


class TestFilterLayersSpecific:
    def test_returns_only_specified_layer(self, tmp_path: Path) -> None:
        global_file = ConfigFile(
            path=tmp_path / "global.toml",
            layer=ConfigLayer.GLOBAL,
            exists=True,
            content=ConfigSchema(),
        )
        project_file = ConfigFile(
            path=tmp_path / ".rig.toml",
            layer=ConfigLayer.PROJECT,
            exists=True,
            content=ConfigSchema(),
        )
        resolved = ResolvedConfig(
            config=ConfigSchema(),
            layers=(global_file, project_file),
            provenance={},
            warnings=(),
        )

        result = filter_layers(resolved, layers={ConfigLayer.PROJECT})

        assert len(result) == 1
        assert result[0] == project_file


class TestFilterLayersMultiple:
    def test_returns_multiple_specified_layers(self, tmp_path: Path) -> None:
        global_file = ConfigFile(
            path=tmp_path / "global.toml",
            layer=ConfigLayer.GLOBAL,
            exists=True,
            content=ConfigSchema(),
        )
        project_file = ConfigFile(
            path=tmp_path / ".rig.toml",
            layer=ConfigLayer.PROJECT,
            exists=True,
            content=ConfigSchema(),
        )
        local_file = ConfigFile(
            path=tmp_path / ".rig.local.toml",
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

        result = filter_layers(
            resolved, layers={ConfigLayer.PROJECT, ConfigLayer.LOCAL}
        )

        assert len(result) == 2
        assert result == (project_file, local_file)


class TestFilterLayersExcludesMissing:
    def test_excludes_missing_files_by_default(self, tmp_path: Path) -> None:
        existing_file = ConfigFile(
            path=tmp_path / ".rig.toml",
            layer=ConfigLayer.PROJECT,
            exists=True,
            content=ConfigSchema(),
        )
        missing_file = ConfigFile(
            path=tmp_path / ".rig.local.toml",
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

        result = filter_layers(resolved)

        assert len(result) == 1
        assert result[0] == existing_file


class TestFilterLayersIncludesMissing:
    def test_includes_missing_when_requested(self, tmp_path: Path) -> None:
        existing_file = ConfigFile(
            path=tmp_path / ".rig.toml",
            layer=ConfigLayer.PROJECT,
            exists=True,
            content=ConfigSchema(),
        )
        missing_file = ConfigFile(
            path=tmp_path / ".rig.local.toml",
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

        result = filter_layers(resolved, include_missing=True)

        assert len(result) == 2
        assert result == (existing_file, missing_file)


class TestFilterLayersPreservesOrder:
    def test_maintains_resolution_order_in_results(self, tmp_path: Path) -> None:
        global_file = ConfigFile(
            path=tmp_path / "global.toml",
            layer=ConfigLayer.GLOBAL,
            exists=True,
            content=ConfigSchema(),
        )
        project_file = ConfigFile(
            path=tmp_path / ".rig.toml",
            layer=ConfigLayer.PROJECT,
            exists=True,
            content=ConfigSchema(),
        )
        local_file = ConfigFile(
            path=tmp_path / ".rig.local.toml",
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

        # Request layers in reverse order
        result = filter_layers(resolved, layers={ConfigLayer.LOCAL, ConfigLayer.GLOBAL})

        # Should still be in resolution order (GLOBAL before LOCAL)
        assert len(result) == 2
        assert result[0].layer == ConfigLayer.GLOBAL
        assert result[1].layer == ConfigLayer.LOCAL
