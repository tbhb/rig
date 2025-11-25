"""Property-based tests for config file discovery.

These tests verify invariants that must hold regardless of directory structure,
path depth, or file existence. Uses Hypothesis to generate varied path scenarios.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from hypothesis import given, settings, strategies as st

from rig.config import (
    ConfigLayer,
    discover_config_files,
    find_ancestor_configs,
)

# --- Hypothesis Strategies ---


directory_depth = st.integers(min_value=1, max_value=10)

valid_dirname = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789_",
    min_size=1,
    max_size=20,
).filter(lambda s: s and not s.startswith("_"))


# --- Discovery Invariants ---


class TestDiscoveryInvariants:
    @settings(max_examples=50)
    @given(depth=directory_depth)
    def test_discovered_files_always_start_with_global_layer(
        self,
        depth: int,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            project = tmp_path
            for i in range(depth):
                project = project / f"dir{i}"
            project.mkdir(parents=True)

            files = discover_config_files(project, home_dir=tmp_path)

            assert len(files) >= 1
            assert files[0].layer == ConfigLayer.GLOBAL

    @settings(max_examples=50)
    @given(depth=directory_depth)
    def test_discovered_files_always_end_with_local_layer(
        self,
        depth: int,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            project = tmp_path
            for i in range(depth):
                project = project / f"dir{i}"
            project.mkdir(parents=True)

            files = discover_config_files(project, home_dir=tmp_path)

            assert len(files) >= 1
            assert files[-1].layer == ConfigLayer.LOCAL

    @settings(max_examples=50)
    @given(depth=directory_depth)
    def test_ancestors_always_ordered_farthest_to_nearest(
        self,
        depth: int,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            current = tmp_path
            for i in range(depth):
                current = current / f"level{i}"
                current.mkdir()
                (current / ".rig.toml").write_text("")

            project = current / "project"
            project.mkdir()

            ancestors = find_ancestor_configs(project, home_dir=tmp_path)

            if len(ancestors) >= 2:
                for i in range(len(ancestors) - 1):
                    farthest = ancestors[i]
                    nearer = ancestors[i + 1]
                    assert len(farthest.parts) < len(nearer.parts)

    @settings(max_examples=50)
    @given(depth=directory_depth)
    def test_discovery_is_deterministic(
        self,
        depth: int,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            project = tmp_path
            for i in range(depth):
                project = project / f"dir{i}"
            project.mkdir(parents=True)

            files_first = discover_config_files(project, home_dir=tmp_path)
            files_second = discover_config_files(project, home_dir=tmp_path)

            assert files_first == files_second


# --- Path Properties ---


class TestPathProperties:
    @settings(max_examples=50)
    @given(depth=directory_depth)
    def test_all_discovered_paths_are_absolute(
        self,
        depth: int,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            project = tmp_path
            for i in range(depth):
                project = project / f"dir{i}"
            project.mkdir(parents=True)

            files = discover_config_files(project, home_dir=tmp_path)

            for config_file in files:
                assert config_file.path.is_absolute()

    @settings(max_examples=50)
    @given(depth=directory_depth)
    def test_project_config_is_in_project_root(
        self,
        depth: int,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            project = tmp_path
            for i in range(depth):
                project = project / f"dir{i}"
            project.mkdir(parents=True)

            files = discover_config_files(project, home_dir=tmp_path)
            project_files = [f for f in files if f.layer == ConfigLayer.PROJECT]

            assert len(project_files) == 1
            assert project_files[0].path.parent == project
            assert project_files[0].path.name == ".rig.toml"

    @settings(max_examples=50)
    @given(depth=directory_depth)
    def test_local_config_is_in_project_root(
        self,
        depth: int,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            project = tmp_path
            for i in range(depth):
                project = project / f"dir{i}"
            project.mkdir(parents=True)

            files = discover_config_files(project, home_dir=tmp_path)
            local_files = [f for f in files if f.layer == ConfigLayer.LOCAL]

            assert len(local_files) == 1
            assert local_files[0].path.parent == project
            assert local_files[0].path.name == ".rig.local.toml"


# --- Ancestor Properties ---


class TestAncestorProperties:
    @settings(max_examples=50)
    @given(depth=directory_depth)
    def test_ancestor_count_bounded_by_directory_depth(
        self,
        depth: int,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            current = tmp_path
            for i in range(depth):
                current = current / f"dir{i}"
                current.mkdir()
                (current / ".rig.toml").write_text("")

            project = current / "project"
            project.mkdir()

            ancestors = find_ancestor_configs(project, home_dir=tmp_path)

            assert len(ancestors) <= depth

    @settings(max_examples=50)
    @given(depth=directory_depth)
    def test_ancestor_paths_are_between_home_and_project(
        self,
        depth: int,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            current = tmp_path
            for i in range(depth):
                current = current / f"dir{i}"
                current.mkdir()
                (current / ".rig.toml").write_text("")

            project = current / "project"
            project.mkdir()

            ancestors = find_ancestor_configs(project, home_dir=tmp_path)
            resolved_home = tmp_path.resolve()
            resolved_project = project.resolve()

            for ancestor_path in ancestors:
                ancestor_dir = ancestor_path.parent.resolve()
                assert ancestor_dir != resolved_home
                assert ancestor_dir != resolved_project
                assert str(ancestor_dir).startswith(str(resolved_home))

    @settings(max_examples=50)
    @given(depth=directory_depth)
    def test_find_ancestor_excludes_project_directory(
        self,
        depth: int,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            project = tmp_path
            for i in range(depth):
                project = project / f"dir{i}"
            project.mkdir(parents=True)

            (project / ".rig.toml").write_text("")

            ancestors = find_ancestor_configs(project, home_dir=tmp_path)

            for ancestor_path in ancestors:
                assert ancestor_path.parent != project


# --- Layer Structure Properties ---


class TestLayerStructureProperties:
    @settings(max_examples=50)
    @given(depth=directory_depth)
    def test_exactly_one_global_layer(
        self,
        depth: int,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            project = tmp_path
            for i in range(depth):
                project = project / f"dir{i}"
            project.mkdir(parents=True)

            files = discover_config_files(project, home_dir=tmp_path)
            global_files = [f for f in files if f.layer == ConfigLayer.GLOBAL]

            assert len(global_files) == 1

    @settings(max_examples=50)
    @given(depth=directory_depth)
    def test_exactly_one_project_layer(
        self,
        depth: int,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            project = tmp_path
            for i in range(depth):
                project = project / f"dir{i}"
            project.mkdir(parents=True)

            files = discover_config_files(project, home_dir=tmp_path)
            project_files = [f for f in files if f.layer == ConfigLayer.PROJECT]

            assert len(project_files) == 1

    @settings(max_examples=50)
    @given(depth=directory_depth)
    def test_exactly_one_local_layer(
        self,
        depth: int,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            project = tmp_path
            for i in range(depth):
                project = project / f"dir{i}"
            project.mkdir(parents=True)

            files = discover_config_files(project, home_dir=tmp_path)
            local_files = [f for f in files if f.layer == ConfigLayer.LOCAL]

            assert len(local_files) == 1

    @settings(max_examples=50)
    @given(depth=directory_depth)
    def test_layer_order_is_global_ancestor_project_local(
        self,
        depth: int,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            current = tmp_path
            for i in range(depth):
                current = current / f"dir{i}"
                current.mkdir()
                (current / ".rig.toml").write_text("")

            project = current / "project"
            project.mkdir()

            files = discover_config_files(project, home_dir=tmp_path)
            layers = [f.layer for f in files]

            assert layers[0] == ConfigLayer.GLOBAL
            assert layers[-2] == ConfigLayer.PROJECT
            assert layers[-1] == ConfigLayer.LOCAL

            for layer in layers[1:-2]:
                assert layer == ConfigLayer.ANCESTOR


# --- Existence Properties ---


class TestExistenceProperties:
    @settings(max_examples=50)
    @given(depth=directory_depth)
    def test_exists_flag_reflects_file_presence(
        self,
        depth: int,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            project = tmp_path
            for i in range(depth):
                project = project / f"dir{i}"
            project.mkdir(parents=True)

            (project / ".rig.toml").write_text("")

            files = discover_config_files(project, home_dir=tmp_path)

            for config_file in files:
                if config_file.layer == ConfigLayer.PROJECT:
                    assert config_file.exists is True
                elif config_file.layer == ConfigLayer.LOCAL:
                    assert config_file.exists is False

    @settings(max_examples=50)
    @given(depth=directory_depth)
    def test_nonexistent_files_still_included_in_discovery(
        self,
        depth: int,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            project = tmp_path
            for i in range(depth):
                project = project / f"dir{i}"
            project.mkdir(parents=True)

            files = discover_config_files(project, home_dir=tmp_path)

            assert len(files) >= 3


# --- ConfigFile Properties ---


class TestConfigFileProperties:
    @settings(max_examples=50)
    @given(depth=directory_depth)
    def test_config_file_is_immutable(
        self,
        depth: int,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            project = tmp_path
            for i in range(depth):
                project = project / f"dir{i}"
            project.mkdir(parents=True)

            files = discover_config_files(project, home_dir=tmp_path)

            for config_file in files:
                with pytest.raises(AttributeError):
                    config_file.path = tmp_path / "hacked"  # pyright: ignore[reportAttributeAccessIssue]
                with pytest.raises(AttributeError):
                    config_file.layer = ConfigLayer.GLOBAL  # pyright: ignore[reportAttributeAccessIssue]
                with pytest.raises(AttributeError):
                    config_file.exists = True  # pyright: ignore[reportAttributeAccessIssue]

    @settings(max_examples=50)
    @given(depth=directory_depth)
    def test_config_file_content_initially_none(
        self,
        depth: int,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            project = tmp_path
            for i in range(depth):
                project = project / f"dir{i}"
            project.mkdir(parents=True)

            files = discover_config_files(project, home_dir=tmp_path)

            for config_file in files:
                assert config_file.content is None


# --- Boundary Condition Properties ---


class TestBoundaryConditionProperties:
    @settings(max_examples=50)
    @given(depth=directory_depth)
    def test_home_dir_not_included_in_ancestors(
        self,
        depth: int,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            (tmp_path / ".rig.toml").write_text("")

            current = tmp_path
            for i in range(depth):
                current = current / f"dir{i}"
            current.mkdir(parents=True)

            ancestors = find_ancestor_configs(current, home_dir=tmp_path)

            for ancestor_path in ancestors:
                assert ancestor_path.parent.resolve() != tmp_path.resolve()

    @settings(max_examples=50)
    @given(depth=directory_depth)
    def test_discovery_handles_no_ancestor_configs(
        self,
        depth: int,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            project = tmp_path
            for i in range(depth):
                project = project / f"dir{i}"
            project.mkdir(parents=True)

            files = discover_config_files(project, home_dir=tmp_path)
            ancestor_files = [f for f in files if f.layer == ConfigLayer.ANCESTOR]

            assert ancestor_files == []
            assert len(files) == 3

    def test_discovery_with_single_level_project(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()

        files = discover_config_files(project, home_dir=tmp_path)

        assert len(files) == 3
        assert files[0].layer == ConfigLayer.GLOBAL
        assert files[1].layer == ConfigLayer.PROJECT
        assert files[2].layer == ConfigLayer.LOCAL

    def test_discovery_with_project_at_home_boundary(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()

        (tmp_path / ".rig.toml").write_text("")

        files = discover_config_files(project, home_dir=tmp_path)
        ancestor_files = [f for f in files if f.layer == ConfigLayer.ANCESTOR]

        assert ancestor_files == []
