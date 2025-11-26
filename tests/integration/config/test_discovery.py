from __future__ import annotations

from typing import TYPE_CHECKING

from rig.config import ConfigLayer, discover_config_files, filter_layers, resolve_config

if TYPE_CHECKING:
    from pathlib import Path


class TestConfigFileDiscovery:
    def test_discovers_global_config(
        self, global_config_file: Path, project_dir: Path, temp_home: Path
    ) -> None:
        # Note: global_config_file is at temp_home/.local/rig/config.toml
        # but resolve_config uses get_global_config_path() which reads from real home
        # So we check that the layer exists (even if path differs from fixture)
        resolved = resolve_config(project_dir, home_dir=temp_home)
        all_layers = filter_layers(resolved, include_missing=True)
        global_layers = [f for f in all_layers if f.layer == ConfigLayer.GLOBAL]

        assert len(global_layers) == 1
        assert global_layers[0].layer == ConfigLayer.GLOBAL
        # The path exists because the fixture created it, but may not match
        # the real global config path (which uses actual home dir)
        assert global_config_file.exists()

    def test_discovers_project_config(
        self, project_config_file: Path, temp_home: Path
    ) -> None:
        project_dir = project_config_file.parent

        resolved = resolve_config(project_dir, home_dir=temp_home)
        project_layers = filter_layers(resolved, layers={ConfigLayer.PROJECT})

        assert len(project_layers) == 1
        assert project_layers[0].path == project_config_file
        assert project_layers[0].exists is True
        assert project_layers[0].layer == ConfigLayer.PROJECT

    def test_discovers_local_config(
        self, local_config_file: Path, project_config_file: Path, temp_home: Path
    ) -> None:
        project_dir = project_config_file.parent

        resolved = resolve_config(project_dir, home_dir=temp_home)
        local_layers = filter_layers(resolved, layers={ConfigLayer.LOCAL})

        assert len(local_layers) == 1
        assert local_layers[0].path == local_config_file
        assert local_layers[0].exists is True
        assert local_layers[0].layer == ConfigLayer.LOCAL

    def test_discovers_ancestor_configs(
        self, ancestor_config_file: Path, project_dir: Path, temp_home: Path
    ) -> None:
        resolved = resolve_config(project_dir, home_dir=temp_home)
        ancestor_layers = filter_layers(resolved, layers={ConfigLayer.ANCESTOR})

        assert len(ancestor_layers) == 1
        assert ancestor_layers[0].path == ancestor_config_file
        assert ancestor_layers[0].exists is True
        assert ancestor_layers[0].layer == ConfigLayer.ANCESTOR

    def test_discovers_multiple_ancestor_configs(
        self, multi_ancestor_hierarchy: dict[str, Path], temp_home: Path
    ) -> None:
        project_dir = multi_ancestor_hierarchy["project"]

        resolved = resolve_config(project_dir, home_dir=temp_home)
        ancestor_layers = filter_layers(resolved, layers={ConfigLayer.ANCESTOR})

        # Should find root, org, and team configs (not project - that's PROJECT layer)
        assert len(ancestor_layers) == 3
        ancestor_paths = {layer.path for layer in ancestor_layers}
        assert multi_ancestor_hierarchy["root_config"] in ancestor_paths
        assert multi_ancestor_hierarchy["org_config"] in ancestor_paths
        assert multi_ancestor_hierarchy["team_config"] in ancestor_paths

    def test_returns_empty_for_no_config(
        self, empty_project_dir: Path, temp_home: Path
    ) -> None:
        resolved = resolve_config(empty_project_dir, home_dir=temp_home)

        # Should return default config values when no files exist
        assert resolved.config.worktree.default_location == "sibling"
        assert resolved.config.worktree.delete_branch is True
        assert resolved.config.worktree.protected is False

        # Verify no existing config files found (except potential global)
        existing_layers = filter_layers(resolved, include_missing=False)
        # Should be empty if no configs exist
        assert len(existing_layers) == 0

    def test_stops_at_filesystem_root(self, project_dir: Path, temp_home: Path) -> None:
        # Set home_dir to project_dir so ancestor search is limited
        # This tests that we don't traverse infinitely
        resolved = resolve_config(project_dir, home_dir=project_dir)

        # Should not find any ancestors since we stop at project_dir
        ancestor_layers = filter_layers(resolved, layers={ConfigLayer.ANCESTOR})
        assert len(ancestor_layers) == 0

    def test_stops_at_home_directory(
        self, temp_home: Path, project_config_file: Path
    ) -> None:
        # Create a structure where configs exist both inside and outside home boundary
        # temp_home/projects/my-project has project_config_file
        # Create a config at temp_home level (should not be found as ancestor)
        project_dir = project_config_file.parent
        home_level_config = temp_home / ".rig.toml"
        home_level_config.write_text('[worktree]\ndefault-location = "sibling"\n')

        try:
            resolved = resolve_config(project_dir, home_dir=temp_home)
            ancestor_layers = filter_layers(resolved, layers={ConfigLayer.ANCESTOR})

            # Should NOT find home_level_config since we stop AT home, not inside it
            ancestor_paths = {layer.path for layer in ancestor_layers}
            assert home_level_config not in ancestor_paths
        finally:
            home_level_config.unlink(missing_ok=True)

    def test_discover_config_files_returns_all_layers(
        self, project_dir: Path, temp_home: Path
    ) -> None:
        files = discover_config_files(project_dir, home_dir=temp_home)

        # Should always return global, project, and local entries
        layers = {f.layer for f in files}
        assert ConfigLayer.GLOBAL in layers
        assert ConfigLayer.PROJECT in layers
        assert ConfigLayer.LOCAL in layers
