"""Unit tests for configuration schema.

Tests focus on:
- Default values matching the specification
- Nested dataclass independence (default_factory correctness)
- Public API exports
"""

import rig.config as config_module
from rig.config import (
    ConfigSchema,
    HooksConfig,
    PathPatterns,
    SyncConfig,
    WorktreeConfig,
)


class TestDefaultValues:
    def test_pathpatterns_defaults_match_spec(self) -> None:
        patterns = PathPatterns()
        assert patterns.sibling == "../{repo}-{branch}"
        assert patterns.local == ".worktrees/{branch}"
        assert patterns.pr == "../{repo}-pr-{number}"

    def test_syncconfig_defaults_are_empty(self) -> None:
        sync = SyncConfig()
        assert sync.link == ()
        assert sync.copy == ()
        assert sync.extend_link == ()
        assert sync.extend_copy == ()
        assert sync.exclude_link == ()
        assert sync.exclude_copy == ()

    def test_hooksconfig_defaults_are_empty(self) -> None:
        hooks = HooksConfig()
        assert hooks.post_add == ()
        assert hooks.pre_remove == ()
        assert hooks.extend_post_add == ()
        assert hooks.extend_pre_remove == ()
        assert hooks.exclude_post_add == ()
        assert hooks.exclude_pre_remove == ()

    def test_worktreeconfig_defaults_match_spec(self) -> None:
        config = WorktreeConfig()
        assert config.default_location == "sibling"
        assert config.delete_branch is True
        assert config.protected is False


class TestNestedDefaults:
    def test_worktreeconfig_nested_are_independent(self) -> None:
        c1 = WorktreeConfig()
        c2 = WorktreeConfig()
        assert c1.paths is not c2.paths
        assert c1.sync is not c2.sync
        assert c1.hooks is not c2.hooks

    def test_configschema_nested_are_independent(self) -> None:
        s1 = ConfigSchema()
        s2 = ConfigSchema()
        assert s1.worktree is not s2.worktree


class TestPublicAPI:
    def test_exports_expected_symbols(self) -> None:
        expected = {
            "ConfigError",
            "ConfigFile",
            "ConfigFileAccessError",
            "ConfigLayer",
            "ConfigParseError",
            "ConfigSchema",
            "ConfigValidationError",
            "HooksConfig",
            "LayerSpec",
            "LocationStrategy",
            "OutputFormat",
            "PathPatterns",
            "PathPlaceholder",
            "ResolvedConfig",
            "ResolvedMergeWarning",
            "SyncConfig",
            "WorktreeConfig",
            "discover_config_files",
            "filter_layers",
            "find_ancestor_configs",
            "get_global_config_path",
            "get_local_config_path",
            "get_project_config_path",
            "get_value_by_key",
            "get_value_provenance",
            "get_worktree_config_path",
            "parse_config_file",
            "resolve_config",
            "to_dict",
            "to_json",
            "to_toml",
        }
        assert set(config_module.__all__) == expected

    def test_exports_are_accessible(self) -> None:
        for name in config_module.__all__:
            assert hasattr(config_module, name)
