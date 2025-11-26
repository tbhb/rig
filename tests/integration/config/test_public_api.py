from __future__ import annotations

from typing import TYPE_CHECKING

from rig.config import (
    ConfigLayer,
    filter_layers,
    get_value_by_key,
    get_value_provenance,
    get_worktree_config_path,
    parse_config_file,
    resolve_config,
    to_dict,
    to_toml,
)

if TYPE_CHECKING:
    from pathlib import Path


class TestPublicAPIIntegration:
    def test_get_value_by_key_with_resolved_config(
        self,
        global_config_file: Path,
        project_config_file: Path,
        temp_home: Path,
    ) -> None:
        assert global_config_file.exists()
        project_dir = project_config_file.parent

        resolved = resolve_config(project_dir, home_dir=temp_home)

        # Query scalar values
        assert get_value_by_key(resolved.config, "worktree.default-location") == "local"
        # Query nested section values using snake_case
        assert (
            get_value_by_key(resolved.config, "worktree.paths.sibling")
            == "../{repo}-{branch}"
        )
        # Query array values
        link_value = get_value_by_key(resolved.config, "worktree.sync.link")
        assert link_value == (".env", "node_modules")
        # Query with kebab-case
        assert get_value_by_key(resolved.config, "worktree.delete-branch") is True

    def test_get_value_provenance_tracks_source_file(
        self,
        project_config_file: Path,
        local_config_file: Path,
        temp_home: Path,
    ) -> None:
        project_dir = project_config_file.parent

        resolved = resolve_config(project_dir, home_dir=temp_home)

        # default-location comes from project config
        value, source = get_value_provenance(resolved, "worktree.default-location")
        assert value == "local"
        assert source is not None
        assert source.path == project_config_file
        assert source.layer == ConfigLayer.PROJECT

        # protected comes from local config
        value, source = get_value_provenance(resolved, "worktree.protected")
        assert value is True
        assert source is not None
        assert source.path == local_config_file
        assert source.layer == ConfigLayer.LOCAL

    def test_filter_layers_with_real_files(
        self,
        project_config_file: Path,
        local_config_file: Path,
        temp_home: Path,
    ) -> None:
        assert local_config_file.exists()
        project_dir = project_config_file.parent

        resolved = resolve_config(project_dir, home_dir=temp_home)

        # Filter to get only existing files (project + local)
        existing = filter_layers(resolved, include_missing=False)
        assert len(existing) == 2
        existing_paths = {f.path for f in existing}
        assert project_config_file in existing_paths
        assert local_config_file in existing_paths

        # Filter by specific layer
        project_only = filter_layers(resolved, layers={ConfigLayer.PROJECT})
        assert len(project_only) == 1
        assert project_only[0].path == project_config_file

        # Filter for local layer
        local_only = filter_layers(resolved, layers={ConfigLayer.LOCAL})
        assert len(local_only) == 1
        assert local_only[0].path == local_config_file

        # include_missing shows global even though it doesn't exist
        all_layers = filter_layers(resolved, include_missing=True)
        global_layers = [f for f in all_layers if f.layer == ConfigLayer.GLOBAL]
        assert len(global_layers) == 1
        assert global_layers[0].exists is False

    def test_to_toml_round_trip_with_parse(
        self, project_config_file: Path, temp_home: Path, tmp_path: Path
    ) -> None:
        project_dir = project_config_file.parent

        resolved = resolve_config(project_dir, home_dir=temp_home)

        # Serialize to TOML
        toml_str = to_toml(resolved.config)

        # Write to a temp file
        round_trip_file = tmp_path / ".rig.toml"
        round_trip_file.write_text(toml_str)

        # Parse it back
        parsed = parse_config_file(round_trip_file)

        # Compare key values (note: full equality may differ due to defaults)
        resolved_location = resolved.config.worktree.default_location
        assert parsed.worktree.default_location == resolved_location
        assert parsed.worktree.delete_branch == resolved.config.worktree.delete_branch
        assert parsed.worktree.protected == resolved.config.worktree.protected
        # Arrays should round-trip correctly
        assert parsed.worktree.sync.link == resolved.config.worktree.sync.link

    def test_to_dict_with_resolved_config(
        self,
        global_config_file: Path,
        project_config_file: Path,
        temp_home: Path,
    ) -> None:
        assert global_config_file.exists()
        project_dir = project_config_file.parent

        resolved = resolve_config(project_dir, home_dir=temp_home)

        # Convert to dict
        data = to_dict(resolved.config)

        # Verify structure uses kebab-case keys
        assert "worktree" in data
        worktree = data["worktree"]
        assert isinstance(worktree, dict)
        assert worktree.get("default-location") == "local"
        assert worktree.get("delete-branch") is True
        # Check nested paths
        paths = worktree.get("paths")
        assert isinstance(paths, dict)
        assert paths.get("sibling") == "../{repo}-{branch}"

    def test_get_worktree_config_path_integration(self, project_dir: Path) -> None:
        worktree_path = project_dir / "feature-branch"
        worktree_path.mkdir()

        config_path = get_worktree_config_path(worktree_path)

        # Verify it produces the expected path
        assert config_path == worktree_path / ".rig.worktree.toml"
        assert config_path.parent == worktree_path
        assert config_path.name == ".rig.worktree.toml"
