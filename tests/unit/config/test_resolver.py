"""Unit tests for configuration resolution with provenance tracking.

Tests cover resolve_config function, multi-layer merging, provenance tracking,
and the critical spec example verification.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from rig.config import (
    ConfigLayer,
    ConfigSchema,
    HooksConfig,
    PathPatterns,
    SyncConfig,
    WorktreeConfig,
)
from rig.config._discovery import ConfigFile
from rig.config._resolver import (
    ResolvedConfig,
    _build_provenance_map,
    _extract_provenance_from_config,
    resolve_config,
)

if TYPE_CHECKING:
    import pytest


class TestResolveConfig:
    def test_no_config_files_returns_defaults(self, tmp_path: Path) -> None:
        project_root = tmp_path / "project"
        project_root.mkdir()
        home_dir = tmp_path / "home"
        home_dir.mkdir()

        resolved = resolve_config(project_root, home_dir=home_dir)

        assert resolved.config == ConfigSchema()
        assert len(resolved.layers) >= 2  # at least global and project
        assert resolved.warnings == ()
        assert resolved.provenance == {}

    def test_single_global_config_only(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Mock the home directory to use our temp path
        home_dir = tmp_path / "home"
        home_dir.mkdir()
        global_config_dir = home_dir / ".local" / "rig"
        global_config_dir.mkdir(parents=True)
        global_config = global_config_dir / "config.toml"
        global_config.write_text('[worktree]\ndefault-location = "local"')

        # Mock Path.home() to return our temp home
        monkeypatch.setattr(Path, "home", lambda: home_dir)

        project_root = tmp_path / "project"
        project_root.mkdir()

        resolved = resolve_config(project_root, home_dir=home_dir)

        assert resolved.config.worktree.default_location == "local"
        assert resolved.warnings == ()

    def test_single_project_config_only(self, tmp_path: Path) -> None:
        project_root = tmp_path / "project"
        project_root.mkdir()
        project_config = project_root / ".rig.toml"
        project_config.write_text("[worktree]\nprotected = true")

        home_dir = tmp_path / "home"
        home_dir.mkdir()

        resolved = resolve_config(project_root, home_dir=home_dir)

        assert resolved.config.worktree.protected is True
        assert resolved.warnings == ()

    def test_project_overrides_global(self, tmp_path: Path) -> None:
        home_dir = tmp_path / "home"
        home_dir.mkdir()
        global_config_dir = home_dir / ".local" / "rig"
        global_config_dir.mkdir(parents=True)
        global_config = global_config_dir / "config.toml"
        global_config.write_text('[worktree]\ndefault-location = "sibling"')

        project_root = tmp_path / "project"
        project_root.mkdir()
        project_config = project_root / ".rig.toml"
        project_config.write_text('[worktree]\ndefault-location = "local"')

        resolved = resolve_config(project_root, home_dir=home_dir)

        assert resolved.config.worktree.default_location == "local"

    def test_local_overrides_project(self, tmp_path: Path) -> None:
        project_root = tmp_path / "project"
        project_root.mkdir()
        project_config = project_root / ".rig.toml"
        project_config.write_text("[worktree]\ndelete-branch = true")
        local_config = project_root / ".rig.local.toml"
        local_config.write_text("[worktree]\ndelete-branch = false")

        home_dir = tmp_path / "home"
        home_dir.mkdir()

        resolved = resolve_config(project_root, home_dir=home_dir)

        assert resolved.config.worktree.delete_branch is False

    def test_ancestor_configs_in_order(self, tmp_path: Path) -> None:
        # Create hierarchy: home/parent/child/project
        home_dir = tmp_path / "home"
        home_dir.mkdir()

        parent_dir = home_dir / "parent"
        parent_dir.mkdir()
        parent_config = parent_dir / ".rig.toml"
        parent_config.write_text("""
[worktree.sync]
link = ["parent-file"]
""")

        child_dir = parent_dir / "child"
        child_dir.mkdir()
        child_config = child_dir / ".rig.toml"
        child_config.write_text("""
[worktree.sync]
extend-link = ["child-file"]
""")

        project_root = child_dir / "project"
        project_root.mkdir()

        resolved = resolve_config(project_root, home_dir=home_dir)

        # Should be: parent-file (from parent), then child-file (from child)
        assert resolved.config.worktree.sync.link == ("parent-file", "child-file")

    def test_full_precedence_stack(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Set up all layers
        home_dir = tmp_path / "home"
        home_dir.mkdir()
        global_config_dir = home_dir / ".local" / "rig"
        global_config_dir.mkdir(parents=True)
        global_config = global_config_dir / "config.toml"
        global_config.write_text("""
[worktree]
default-location = "sibling"
[worktree.sync]
link = ["global-file"]
""")

        # Mock Path.home() to return our temp home
        monkeypatch.setattr(Path, "home", lambda: home_dir)

        ancestor_dir = home_dir / "work"
        ancestor_dir.mkdir()
        ancestor_config = ancestor_dir / ".rig.toml"
        ancestor_config.write_text("""
[worktree.sync]
extend-link = ["ancestor-file"]
""")

        project_root = ancestor_dir / "project"
        project_root.mkdir()
        project_config = project_root / ".rig.toml"
        project_config.write_text("""
[worktree]
delete-branch = false
[worktree.sync]
extend-link = ["project-file"]
""")

        local_config = project_root / ".rig.local.toml"
        local_config.write_text("""
[worktree]
protected = true
[worktree.sync]
extend-link = ["local-file"]
""")

        resolved = resolve_config(project_root, home_dir=home_dir)

        assert resolved.config.worktree.default_location == "sibling"
        assert resolved.config.worktree.delete_branch is False
        assert resolved.config.worktree.protected is True
        assert resolved.config.worktree.sync.link == (
            "global-file",
            "ancestor-file",
            "project-file",
            "local-file",
        )

    def test_layers_tuple_includes_nonexistent_files(self, tmp_path: Path) -> None:
        project_root = tmp_path / "project"
        project_root.mkdir()
        home_dir = tmp_path / "home"
        home_dir.mkdir()

        resolved = resolve_config(project_root, home_dir=home_dir)

        # Should have entries for global, project, local even if they don't exist
        layer_types = {layer.layer for layer in resolved.layers}
        assert ConfigLayer.GLOBAL in layer_types
        assert ConfigLayer.PROJECT in layer_types
        assert ConfigLayer.LOCAL in layer_types

    def test_warnings_collected_from_all_layers(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        home_dir = tmp_path / "home"
        home_dir.mkdir()
        global_config_dir = home_dir / ".local" / "rig"
        global_config_dir.mkdir(parents=True)
        global_config = global_config_dir / "config.toml"
        # Global config sets the base link list
        global_config.write_text("""
[worktree.sync]
link = ["a"]
""")

        # Mock Path.home() to return our temp home
        monkeypatch.setattr(Path, "home", lambda: home_dir)

        project_root = tmp_path / "project"
        project_root.mkdir()
        project_config = project_root / ".rig.toml"
        # Project tries to exclude items that don't exist
        project_config.write_text("""
[worktree.sync]
exclude-link = ["nonexistent1"]
""")

        local_config = project_root / ".rig.local.toml"
        # Local also tries to exclude an item that doesn't exist
        local_config.write_text("""
[worktree.sync]
exclude-link = ["nonexistent2"]
""")

        resolved = resolve_config(project_root, home_dir=home_dir)

        assert len(resolved.warnings) == 2
        warning_items = {w.excluded_item for w in resolved.warnings}
        assert warning_items == {"nonexistent1", "nonexistent2"}

    def test_spec_example_verification(self, tmp_path: Path) -> None:
        """Verify the exact example from the spec resolves correctly.

        From spec:
        - .rig.toml: link = [".envrc", "CLAUDE.md", ".gemini/"]
        - .rig.local.toml: extend-link = [".my-tool-config"],
                           exclude-copy = ["data/fixtures/"]
        - .rig.worktree.toml: extend-link = ["experiments/config/"],
                              exclude-link = [".envrc"]

        Expected result: ["CLAUDE.md", ".gemini/", ".my-tool-config"]
        (Note: .rig.worktree.toml is not part of this stage)
        """
        project_root = tmp_path / "project"
        project_root.mkdir()

        project_config = project_root / ".rig.toml"
        project_config.write_text("""
[worktree.sync]
link = [".envrc", "CLAUDE.md", ".gemini/"]
""")

        local_config = project_root / ".rig.local.toml"
        local_config.write_text("""
[worktree.sync]
extend-link = [".my-tool-config"]
exclude-copy = ["data/fixtures/"]
""")

        # Note: We don't test .rig.worktree.toml here since it's not in scope
        # The second exclude-link would happen in the worktree layer

        home_dir = tmp_path / "home"
        home_dir.mkdir()

        resolved = resolve_config(project_root, home_dir=home_dir)

        # Without the worktree layer, we should have:
        # [".envrc", "CLAUDE.md", ".gemini/", ".my-tool-config"]
        assert resolved.config.worktree.sync.link == (
            ".envrc",
            "CLAUDE.md",
            ".gemini/",
            ".my-tool-config",
        )

    def test_spec_example_with_additional_layer_for_full_resolution(
        self, tmp_path: Path
    ) -> None:
        """Test the full spec example including the exclude from a third file.

        This simulates what would happen if we had a worktree config.
        """
        project_root = tmp_path / "project"
        project_root.mkdir()

        # Layer 1: Project
        project_config = project_root / ".rig.toml"
        project_config.write_text("""
[worktree.sync]
link = [".envrc", "CLAUDE.md", ".gemini/"]
""")

        # Layer 2: Local
        local_config = project_root / ".rig.local.toml"
        local_config.write_text("""
[worktree.sync]
extend-link = [".my-tool-config"]
""")

        home_dir = tmp_path / "home"
        home_dir.mkdir()

        resolved = resolve_config(project_root, home_dir=home_dir)

        # After project + local:
        # [".envrc", "CLAUDE.md", ".gemini/", ".my-tool-config"]
        assert resolved.config.worktree.sync.link == (
            ".envrc",
            "CLAUDE.md",
            ".gemini/",
            ".my-tool-config",
        )

        # Now simulate a third layer that excludes .envrc
        # (This would normally be worktree config, but we can test the logic)
        from rig.config._merge import merge_sync_configs  # noqa: PLC0415

        third_layer = SyncConfig(exclude_link=(".envrc",))
        final_sync, _ = merge_sync_configs(
            resolved.config.worktree.sync,
            third_layer,
            ConfigLayer.LOCAL,
        )

        # After excluding .envrc: ["CLAUDE.md", ".gemini/", ".my-tool-config"]
        assert final_sync.link == ("CLAUDE.md", ".gemini/", ".my-tool-config")


class TestBuildProvenanceMap:
    def test_empty_layers_returns_empty_map(self) -> None:
        provenance = _build_provenance_map(())

        assert provenance == {}

    def test_single_layer_tracks_all_keys(self, tmp_path: Path) -> None:
        config = ConfigSchema(
            worktree=WorktreeConfig(
                default_location="local",
                sync=SyncConfig(link=("CLAUDE.md",)),
            )
        )
        config_file = ConfigFile(
            path=tmp_path / ".rig.toml",
            layer=ConfigLayer.PROJECT,
            exists=True,
            content=config,
        )

        provenance = _build_provenance_map((config_file,))

        assert "worktree.default-location" in provenance
        assert provenance["worktree.default-location"] == config_file
        assert "worktree.sync.link" in provenance
        assert provenance["worktree.sync.link"] == config_file

    def test_later_layer_overrides_earlier(self, tmp_path: Path) -> None:
        global_config = ConfigSchema(
            worktree=WorktreeConfig(default_location="sibling")
        )
        project_config = ConfigSchema(worktree=WorktreeConfig(default_location="local"))

        global_file = ConfigFile(
            path=tmp_path / "global.toml",
            layer=ConfigLayer.GLOBAL,
            exists=True,
            content=global_config,
        )
        project_file = ConfigFile(
            path=tmp_path / "project.toml",
            layer=ConfigLayer.PROJECT,
            exists=True,
            content=project_config,
        )

        provenance = _build_provenance_map((global_file, project_file))

        assert provenance["worktree.default-location"] == project_file

    def test_extend_modifiers_tracked(self, tmp_path: Path) -> None:
        config = ConfigSchema(
            worktree=WorktreeConfig(sync=SyncConfig(extend_link=(".envrc",)))
        )
        config_file = ConfigFile(
            path=tmp_path / ".rig.local.toml",
            layer=ConfigLayer.LOCAL,
            exists=True,
            content=config,
        )

        provenance = _build_provenance_map((config_file,))

        assert "worktree.sync.extend-link" in provenance
        assert provenance["worktree.sync.extend-link"] == config_file

    def test_layers_with_no_content_ignored(self, tmp_path: Path) -> None:
        config = ConfigSchema(worktree=WorktreeConfig(default_location="local"))

        file_with_content = ConfigFile(
            path=tmp_path / "exists.toml",
            layer=ConfigLayer.PROJECT,
            exists=True,
            content=config,
        )
        file_without_content = ConfigFile(
            path=tmp_path / "missing.toml",
            layer=ConfigLayer.LOCAL,
            exists=False,
            content=None,
        )

        provenance = _build_provenance_map((file_with_content, file_without_content))

        assert "worktree.default-location" in provenance
        assert provenance["worktree.default-location"] == file_with_content

    def test_default_values_not_tracked(self) -> None:
        # ConfigSchema with all defaults
        default_config = ConfigSchema()
        config_file = ConfigFile(
            path=Path("/test.toml"),
            layer=ConfigLayer.PROJECT,
            exists=True,
            content=default_config,
        )

        provenance = _build_provenance_map((config_file,))

        # No keys should be tracked since everything is default
        assert provenance == {}


class TestExtractProvenanceFromConfig:
    def test_default_config_extracts_no_keys(self) -> None:
        config = ConfigSchema()

        keys = _extract_provenance_from_config(config)

        assert keys == set()

    def test_extracts_scalar_worktree_fields(self) -> None:
        config = ConfigSchema(
            worktree=WorktreeConfig(
                default_location="local",
                delete_branch=False,
                protected=True,
            )
        )

        keys = _extract_provenance_from_config(config)

        assert "worktree.default-location" in keys
        assert "worktree.delete-branch" in keys
        assert "worktree.protected" in keys

    def test_extracts_path_patterns(self) -> None:
        config = ConfigSchema(
            worktree=WorktreeConfig(
                paths=PathPatterns(
                    sibling="../custom-{branch}",
                    local=".wt/{branch}",
                )
            )
        )

        keys = _extract_provenance_from_config(config)

        assert "worktree.paths.sibling" in keys
        assert "worktree.paths.local" in keys
        # pr is default, shouldn't be tracked
        assert "worktree.paths.pr" not in keys

    def test_extracts_sync_base_lists(self) -> None:
        config = ConfigSchema(
            worktree=WorktreeConfig(
                sync=SyncConfig(
                    link=("CLAUDE.md",),
                    copy=("data/",),
                )
            )
        )

        keys = _extract_provenance_from_config(config)

        assert "worktree.sync.link" in keys
        assert "worktree.sync.copy" in keys

    def test_extracts_sync_extend_exclude_modifiers(self) -> None:
        config = ConfigSchema(
            worktree=WorktreeConfig(
                sync=SyncConfig(
                    extend_link=(".envrc",),
                    exclude_link=(".gemini/",),
                    extend_copy=("cache/",),
                    exclude_copy=("tmp/",),
                )
            )
        )

        keys = _extract_provenance_from_config(config)

        assert "worktree.sync.extend-link" in keys
        assert "worktree.sync.exclude-link" in keys
        assert "worktree.sync.extend-copy" in keys
        assert "worktree.sync.exclude-copy" in keys

    def test_extracts_hooks_base_lists(self) -> None:
        config = ConfigSchema(
            worktree=WorktreeConfig(
                hooks=HooksConfig(
                    post_add=("npm install",),
                    pre_remove=("cleanup.sh",),
                )
            )
        )

        keys = _extract_provenance_from_config(config)

        assert "worktree.hooks.post-add" in keys
        assert "worktree.hooks.pre-remove" in keys

    def test_extracts_hooks_extend_exclude_modifiers(self) -> None:
        config = ConfigSchema(
            worktree=WorktreeConfig(
                hooks=HooksConfig(
                    extend_post_add=("direnv allow",),
                    exclude_post_add=("old.sh",),
                    extend_pre_remove=("backup.sh",),
                    exclude_pre_remove=("skip.sh",),
                )
            )
        )

        keys = _extract_provenance_from_config(config)

        assert "worktree.hooks.extend-post-add" in keys
        assert "worktree.hooks.exclude-post-add" in keys
        assert "worktree.hooks.extend-pre-remove" in keys
        assert "worktree.hooks.exclude-pre-remove" in keys

    def test_keys_use_kebab_case(self) -> None:
        config = ConfigSchema(
            worktree=WorktreeConfig(
                default_location="local",
                delete_branch=False,
                sync=SyncConfig(extend_link=("file",)),
                hooks=HooksConfig(post_add=("cmd",)),
            )
        )

        keys = _extract_provenance_from_config(config)

        # All keys should use kebab-case (hyphens, not underscores)
        assert "worktree.default-location" in keys
        assert "worktree.delete-branch" in keys
        assert "worktree.sync.extend-link" in keys
        assert "worktree.hooks.post-add" in keys

        # Verify no underscore versions
        assert "worktree.default_location" not in keys
        assert "worktree.delete_branch" not in keys

    def test_complex_config_extracts_all_modified_keys(self) -> None:
        config = ConfigSchema(
            worktree=WorktreeConfig(
                default_location="local",
                protected=True,
                paths=PathPatterns(sibling="../custom"),
                sync=SyncConfig(
                    link=("CLAUDE.md",),
                    extend_copy=("data/",),
                ),
                hooks=HooksConfig(
                    post_add=("npm install",),
                    extend_pre_remove=("cleanup.sh",),
                ),
            )
        )

        keys = _extract_provenance_from_config(config)

        expected = {
            "worktree.default-location",
            "worktree.protected",
            "worktree.paths.sibling",
            "worktree.sync.link",
            "worktree.sync.extend-copy",
            "worktree.hooks.post-add",
            "worktree.hooks.extend-pre-remove",
        }
        assert keys == expected


class TestResolvedConfig:
    def test_resolved_config_dataclass_structure(self, tmp_path: Path) -> None:
        project_root = tmp_path / "project"
        project_root.mkdir()
        home_dir = tmp_path / "home"
        home_dir.mkdir()

        resolved = resolve_config(project_root, home_dir=home_dir)

        assert isinstance(resolved, ResolvedConfig)
        assert isinstance(resolved.config, ConfigSchema)
        assert isinstance(resolved.layers, tuple)
        assert isinstance(resolved.provenance, dict)
        assert isinstance(resolved.warnings, tuple)

    def test_resolved_config_layers_in_correct_order(self, tmp_path: Path) -> None:
        project_root = tmp_path / "project"
        project_root.mkdir()
        home_dir = tmp_path / "home"
        home_dir.mkdir()

        resolved = resolve_config(project_root, home_dir=home_dir)

        # Extract the layers that appear
        layers_order = [layer.layer for layer in resolved.layers]

        # Verify order: GLOBAL appears before PROJECT, PROJECT before LOCAL
        global_idx = layers_order.index(ConfigLayer.GLOBAL)
        project_idx = layers_order.index(ConfigLayer.PROJECT)
        local_idx = layers_order.index(ConfigLayer.LOCAL)

        assert global_idx < project_idx < local_idx
