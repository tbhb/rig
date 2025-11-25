from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from rig.config import (
    ConfigFile,
    ConfigFileAccessError,
    ConfigLayer,
    discover_config_files,
    find_ancestor_configs,
    get_global_config_path,
    get_local_config_path,
    get_project_config_path,
)
from rig.config._paths import resolve_path_safely

if TYPE_CHECKING:
    from collections.abc import Callable


# =============================================================================
# Path Functions Tests (from _paths.py)
# =============================================================================


class TestGetGlobalConfigPath:
    def test_returns_home_local_rig_config(self) -> None:
        result = get_global_config_path()
        assert result == Path.home() / ".local" / "rig" / "config.toml"

    def test_returns_absolute_path(self) -> None:
        result = get_global_config_path()
        assert result.is_absolute()


class TestGetProjectConfigPath:
    def test_returns_rig_toml_in_project_root(self, tmp_path: Path) -> None:
        result = get_project_config_path(tmp_path)
        assert result == tmp_path / ".rig.toml"

    def test_returns_absolute_path(self, tmp_path: Path) -> None:
        result = get_project_config_path(tmp_path)
        assert result.is_absolute()


class TestGetLocalConfigPath:
    def test_returns_rig_local_toml_in_project_root(self, tmp_path: Path) -> None:
        result = get_local_config_path(tmp_path)
        assert result == tmp_path / ".rig.local.toml"

    def test_returns_absolute_path(self, tmp_path: Path) -> None:
        result = get_local_config_path(tmp_path)
        assert result.is_absolute()


class TestResolvePathSafely:
    def test_resolves_relative_paths(self, tmp_path: Path) -> None:
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        relative = subdir / ".." / "subdir"
        result = resolve_path_safely(relative)
        assert result == subdir.resolve()

    def test_resolves_dot_components(self, tmp_path: Path) -> None:
        path_with_dots = tmp_path / "." / "subdir" / ".." / "."
        result = resolve_path_safely(path_with_dots)
        assert result == tmp_path.resolve()

    def test_raises_config_file_access_error_on_oserror(
        self, tmp_path: Path
    ) -> None:
        with patch.object(Path, "resolve", side_effect=OSError("mock error")):
            with pytest.raises(ConfigFileAccessError) as exc_info:
                resolve_path_safely(tmp_path)
            assert "mock error" in str(exc_info.value)

    def test_returns_absolute_path(self, tmp_path: Path) -> None:
        result = resolve_path_safely(tmp_path)
        assert result.is_absolute()


# =============================================================================
# ConfigFile Dataclass Tests
# =============================================================================


class TestConfigFile:
    def test_is_frozen(self, tmp_path: Path) -> None:
        config_file = ConfigFile(
            path=tmp_path / "config.toml",
            layer=ConfigLayer.PROJECT,
            exists=True,
        )
        with pytest.raises(FrozenInstanceError):
            config_file.path = tmp_path / "other.toml"  # pyright: ignore[reportAttributeAccessIssue]

    def test_has_expected_fields(self, tmp_path: Path) -> None:
        path = tmp_path / "config.toml"
        config_file = ConfigFile(
            path=path,
            layer=ConfigLayer.GLOBAL,
            exists=True,
            content=None,
        )
        assert config_file.path == path
        assert config_file.layer == ConfigLayer.GLOBAL
        assert config_file.exists is True
        assert config_file.content is None

    def test_content_defaults_to_none(self, tmp_path: Path) -> None:
        config_file = ConfigFile(
            path=tmp_path / "config.toml",
            layer=ConfigLayer.PROJECT,
            exists=False,
        )
        assert config_file.content is None

    def test_uses_slots(self) -> None:
        assert hasattr(ConfigFile, "__slots__")


# =============================================================================
# discover_config_files Function Tests
# =============================================================================


class TestDiscoverConfigFiles:
    def test_returns_global_first(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()
        files = discover_config_files(project, home_dir=tmp_path)
        assert files[0].layer == ConfigLayer.GLOBAL

    def test_returns_project_before_local(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()
        files = discover_config_files(project, home_dir=tmp_path)
        layers = [f.layer for f in files]
        project_idx = layers.index(ConfigLayer.PROJECT)
        local_idx = layers.index(ConfigLayer.LOCAL)
        assert project_idx < local_idx

    def test_returns_ancestors_between_global_and_project(
        self, tmp_path: Path
    ) -> None:
        home = tmp_path / "home"
        home.mkdir()
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        project = workspace / "project"
        project.mkdir()
        ancestor_config = workspace / ".rig.toml"
        ancestor_config.touch()

        files = discover_config_files(project, home_dir=home)
        layers = [f.layer for f in files]
        global_idx = layers.index(ConfigLayer.GLOBAL)
        ancestor_idx = layers.index(ConfigLayer.ANCESTOR)
        project_idx = layers.index(ConfigLayer.PROJECT)
        assert global_idx < ancestor_idx < project_idx

    def test_includes_nonexistent_files_with_exists_false(
        self, tmp_path: Path
    ) -> None:
        project = tmp_path / "project"
        project.mkdir()
        files = discover_config_files(project, home_dir=tmp_path)
        for config_file in files:
            assert config_file.exists is False

    def test_marks_existing_files_with_exists_true(self, tmp_path: Path) -> None:
        home = tmp_path / "home"
        home.mkdir()
        global_dir = home / ".local" / "rig"
        global_dir.mkdir(parents=True)
        (global_dir / "config.toml").touch()

        project = tmp_path / "project"
        project.mkdir()
        (project / ".rig.toml").touch()
        (project / ".rig.local.toml").touch()

        with patch(
            "rig.config._paths.get_home_directory", return_value=home
        ):
            files = discover_config_files(project, home_dir=home)

        existing_files = [f for f in files if f.exists]
        assert len(existing_files) == 3
        existing_layers = {f.layer for f in existing_files}
        assert existing_layers == {
            ConfigLayer.GLOBAL,
            ConfigLayer.PROJECT,
            ConfigLayer.LOCAL,
        }

    def test_uses_correct_layers(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()
        files = discover_config_files(project, home_dir=tmp_path)
        layers = [f.layer for f in files]
        assert layers[0] == ConfigLayer.GLOBAL
        assert layers[-2] == ConfigLayer.PROJECT
        assert layers[-1] == ConfigLayer.LOCAL

    def test_returns_tuple(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()
        files = discover_config_files(project, home_dir=tmp_path)
        assert isinstance(files, tuple)

    def test_global_path_is_correct(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()
        files = discover_config_files(project, home_dir=tmp_path)
        global_file = files[0]
        expected_global = Path.home() / ".local" / "rig" / "config.toml"
        assert global_file.path == expected_global

    def test_project_path_is_correct(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()
        files = discover_config_files(project, home_dir=tmp_path)
        project_file = next(f for f in files if f.layer == ConfigLayer.PROJECT)
        assert project_file.path == project / ".rig.toml"

    def test_local_path_is_correct(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()
        files = discover_config_files(project, home_dir=tmp_path)
        local_file = next(f for f in files if f.layer == ConfigLayer.LOCAL)
        assert local_file.path == project / ".rig.local.toml"


# =============================================================================
# find_ancestor_configs Function Tests
# =============================================================================


class TestFindAncestorConfigs:
    def test_returns_empty_when_no_ancestors(self, tmp_path: Path) -> None:
        home = tmp_path / "home"
        home.mkdir()
        project = home / "project"
        project.mkdir()
        result = find_ancestor_configs(project, home_dir=home)
        assert result == ()

    def test_returns_farthest_to_nearest_order(self, tmp_path: Path) -> None:
        home = tmp_path / "home"
        home.mkdir()
        level1 = tmp_path / "level1"
        level1.mkdir()
        level2 = level1 / "level2"
        level2.mkdir()
        level3 = level2 / "level3"
        level3.mkdir()

        (level1 / ".rig.toml").touch()
        (level2 / ".rig.toml").touch()

        result = find_ancestor_configs(level3, home_dir=home)
        assert len(result) == 2
        assert result[0] == level1 / ".rig.toml"
        assert result[1] == level2 / ".rig.toml"

    def test_stops_at_home_directory(self, tmp_path: Path) -> None:
        home = tmp_path / "home"
        home.mkdir()
        (tmp_path / ".rig.toml").touch()

        project = home / "workspace" / "project"
        project.mkdir(parents=True)

        workspace_config = home / "workspace" / ".rig.toml"
        workspace_config.touch()

        result = find_ancestor_configs(project, home_dir=home)
        config_paths = [str(p) for p in result]
        assert str(tmp_path / ".rig.toml") not in config_paths
        assert str(workspace_config) in config_paths

    def test_excludes_start_directory(self, tmp_path: Path) -> None:
        home = tmp_path / "home"
        home.mkdir()
        project = tmp_path / "project"
        project.mkdir()
        (project / ".rig.toml").touch()

        result = find_ancestor_configs(project, home_dir=home)
        assert project / ".rig.toml" not in result

    def test_handles_deeply_nested_path(self, tmp_path: Path) -> None:
        home = tmp_path / "home"
        home.mkdir()
        current = tmp_path
        for i in range(10):
            current = current / f"level{i}"
            current.mkdir()
            if i % 3 == 0:
                (current / ".rig.toml").touch()

        result = find_ancestor_configs(current, home_dir=home)
        assert len(result) == 3
        assert result[0] == tmp_path / "level0" / ".rig.toml"
        level3_path = tmp_path / "level0" / "level1" / "level2" / "level3"
        assert result[1] == level3_path / ".rig.toml"
        level6_path = level3_path / "level4" / "level5" / "level6"
        assert result[2] == level6_path / ".rig.toml"

    def test_returns_tuple(self, tmp_path: Path) -> None:
        home = tmp_path / "home"
        home.mkdir()
        project = home / "project"
        project.mkdir()
        result = find_ancestor_configs(project, home_dir=home)
        assert isinstance(result, tuple)

    def test_returns_only_existing_configs(self, tmp_path: Path) -> None:
        home = tmp_path / "home"
        home.mkdir()
        level1 = tmp_path / "level1"
        level1.mkdir()
        level2 = level1 / "level2"
        level2.mkdir()
        (level1 / ".rig.toml").touch()

        result = find_ancestor_configs(level2, home_dir=home)
        assert len(result) == 1
        assert result[0] == level1 / ".rig.toml"


# =============================================================================
# Edge Cases (from stage-1-loading.md)
# =============================================================================


class TestDiscoveryEdgeCases:
    def test_discovery_with_no_config_files_exist(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()
        files = discover_config_files(project, home_dir=tmp_path)
        for config_file in files:
            assert config_file.exists is False
        assert len(files) >= 3

    def test_discovery_with_only_global_config(self, tmp_path: Path) -> None:
        home = tmp_path / "home"
        home.mkdir()
        global_dir = home / ".local" / "rig"
        global_dir.mkdir(parents=True)
        (global_dir / "config.toml").touch()

        project = tmp_path / "project"
        project.mkdir()

        with patch("rig.config._paths.get_home_directory", return_value=home):
            files = discover_config_files(project, home_dir=home)

        existing_files = [f for f in files if f.exists]
        assert len(existing_files) == 1
        assert existing_files[0].layer == ConfigLayer.GLOBAL

    def test_discovery_with_multiple_ancestor_configs(
        self, tmp_path: Path
    ) -> None:
        home = tmp_path / "home"
        home.mkdir()

        workspace = tmp_path / "workspace"
        workspace.mkdir()
        (workspace / ".rig.toml").touch()

        org = workspace / "org"
        org.mkdir()
        (org / ".rig.toml").touch()

        team = org / "team"
        team.mkdir()
        (team / ".rig.toml").touch()

        project = team / "project"
        project.mkdir()

        files = discover_config_files(project, home_dir=home)
        ancestor_files = [f for f in files if f.layer == ConfigLayer.ANCESTOR]
        assert len(ancestor_files) == 3
        assert ancestor_files[0].path == workspace / ".rig.toml"
        assert ancestor_files[1].path == org / ".rig.toml"
        assert ancestor_files[2].path == team / ".rig.toml"

    def test_discovery_with_all_config_types_present(
        self, tmp_path: Path
    ) -> None:
        home = tmp_path / "home"
        home.mkdir()
        global_dir = home / ".local" / "rig"
        global_dir.mkdir(parents=True)
        (global_dir / "config.toml").touch()

        workspace = tmp_path / "workspace"
        workspace.mkdir()
        (workspace / ".rig.toml").touch()

        project = workspace / "project"
        project.mkdir()
        (project / ".rig.toml").touch()
        (project / ".rig.local.toml").touch()

        with patch("rig.config._paths.get_home_directory", return_value=home):
            files = discover_config_files(project, home_dir=home)

        existing_files = [f for f in files if f.exists]
        assert len(existing_files) == 4

        layers = [f.layer for f in existing_files]
        assert ConfigLayer.GLOBAL in layers
        assert ConfigLayer.ANCESTOR in layers
        assert ConfigLayer.PROJECT in layers
        assert ConfigLayer.LOCAL in layers


class TestAncestorEdgeCases:
    def test_ancestor_stops_at_filesystem_root(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()
        result = find_ancestor_configs(project, home_dir=Path("/nonexistent"))
        for path in result:
            assert path.is_relative_to(tmp_path) or not path.exists()

    def test_ancestor_handles_symlinked_directories(
        self, tmp_path: Path
    ) -> None:
        home = tmp_path / "home"
        home.mkdir()

        real_dir = tmp_path / "real"
        real_dir.mkdir()
        (real_dir / ".rig.toml").touch()

        project = real_dir / "project"
        project.mkdir()

        symlink = tmp_path / "symlink"
        symlink.symlink_to(real_dir)
        symlinked_project = symlink / "project"

        result = find_ancestor_configs(symlinked_project, home_dir=home)
        assert len(result) == 1


class TestPermissionErrors:
    def test_safe_exists_handles_permission_error(
        self, tmp_path: Path
    ) -> None:
        project = tmp_path / "project"
        project.mkdir()

        with patch("pathlib.Path.exists", side_effect=PermissionError("denied")):
            with pytest.raises(ConfigFileAccessError) as exc_info:
                discover_config_files(project, home_dir=tmp_path)
            assert "permission denied" in str(exc_info.value)

    def test_safe_exists_handles_oserror_as_nonexistent(
        self, tmp_path: Path
    ) -> None:
        project = tmp_path / "project"
        project.mkdir()

        original_exists = Path.exists

        def mock_exists(self: Path) -> bool:
            if self.name == "config.toml":
                raise OSError(22, "Invalid argument")
            return original_exists(self)

        with patch.object(Path, "exists", mock_exists):
            files = discover_config_files(project, home_dir=tmp_path)

        global_file = files[0]
        assert global_file.exists is False


class TestDefaultHomeDirectory:
    def test_discover_config_files_uses_default_home_dir(
        self, tmp_path: Path
    ) -> None:
        project = tmp_path / "project"
        project.mkdir()
        files = discover_config_files(project)
        assert files[0].layer == ConfigLayer.GLOBAL
        assert len(files) >= 3

    def test_find_ancestor_configs_uses_default_home_dir(
        self, tmp_path: Path
    ) -> None:
        project = tmp_path / "project"
        project.mkdir()
        result = find_ancestor_configs(project)
        assert isinstance(result, tuple)


# =============================================================================
# Fixtures for complex test scenarios
# =============================================================================


@pytest.fixture
def nested_project_structure(tmp_path: Path) -> dict[str, Path]:
    home = tmp_path / "home"
    home.mkdir()

    workspace = tmp_path / "workspace"
    workspace.mkdir()

    org = workspace / "myorg"
    org.mkdir()

    project = org / "myproject"
    project.mkdir()

    return {
        "home": home,
        "workspace": workspace,
        "org": org,
        "project": project,
        "tmp_path": tmp_path,
    }


@pytest.fixture
def config_file_creator() -> Callable[[Path], Path]:
    def _create(directory: Path) -> Path:
        config = directory / ".rig.toml"
        config.touch()
        return config

    return _create


class TestWithFixtures:
    def test_nested_structure_without_configs(
        self, nested_project_structure: dict[str, Path]
    ) -> None:
        files = discover_config_files(
            nested_project_structure["project"],
            home_dir=nested_project_structure["home"],
        )
        ancestor_files = [f for f in files if f.layer == ConfigLayer.ANCESTOR]
        assert all(not f.exists for f in ancestor_files)

    def test_nested_structure_with_configs(
        self,
        nested_project_structure: dict[str, Path],
        config_file_creator: Callable[[Path], Path],
    ) -> None:
        workspace_config = config_file_creator(nested_project_structure["workspace"])
        org_config = config_file_creator(nested_project_structure["org"])

        files = discover_config_files(
            nested_project_structure["project"],
            home_dir=nested_project_structure["home"],
        )
        ancestor_files = [
            f for f in files if f.layer == ConfigLayer.ANCESTOR and f.exists
        ]
        assert len(ancestor_files) == 2
        assert ancestor_files[0].path == workspace_config
        assert ancestor_files[1].path == org_config
